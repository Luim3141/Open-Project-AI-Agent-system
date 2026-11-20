"""Freeze independent labels only when the cited support occurs in one Native document."""
import datetime,hashlib,json
from pathlib import Path

root=Path(__file__).resolve().parent.parent;private=root/'private'
manifest=json.loads((root/'native-source-manifest.json').read_text(encoding='utf-8'))
texts={d['metadata']['native_id']:(private/d['snapshot_file']).read_text(encoding='utf-8') for d in manifest['documents']}
plan=json.loads((root/'evaluation-plan.json').read_text());removed={};counts={}
for split,path in [('dev',root/'dev.json'),('holdout',private/'holdout.json')]:
 data=json.loads(path.read_text(encoding='utf-8'));kept=[];excluded=[]
 for case in data['cases']:
  if case['kind']=='positive':
   hits=[i for i,text in texts.items() if case['support_literal'].casefold() in text.casefold()]
   if hits!=case['relevant_ids']:
    excluded.append({'id':case['id'],'matched_native_ids':hits,'reason':'DUPLICATED_LITERAL_SUPPORT_ACROSS_NATIVE_DOCUMENTS'})
    continue
  kept.append(case)
 archive=path.with_name(path.stem+'-ambiguous-draft.json');assert not archive.exists();path.replace(archive)
 path.write_text(json.dumps({**data,'cases':kept},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 removed[split]=excluded
 counts[split]={'positive':sum(c['kind']=='positive' for c in kept),'negative':sum(c['kind']=='negative' for c in kept),
                'mixed':sum(c['language']=='mixed' for c in kept),'excluded_ambiguous':len(excluded)}
assert counts['dev']['positive']>=12 and counts['dev']['negative']>=12
assert counts['holdout']['positive']>=20 and counts['holdout']['negative']>=20
plan['created_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
plan['dev_sha256']=hashlib.sha256((root/'dev.json').read_bytes()).hexdigest()
plan['holdout_sha256']=hashlib.sha256((private/'holdout.json').read_bytes()).hexdigest()
plan['counts']=counts
plan['independence']+=' Positive cases whose literal support appears in more than one work package were excluded before any scoring, because copied comments create ambiguous citations and document-split leakage. This check cannot detect all paraphrased duplication.'
plan['label_limitations']=['Positive support checked as literal source offset and SHA256.','Negative capability checked by humanlike agent review and absence of a distinctive term; semantic negatives are not human-adjudicated.','VN/EN queries are paired by intent; counts are correlated, not independent samples.','Documents in earlier experiments recur, even though queries were independently authored; prior knowledge of project features may bias authorship.','Human adjudication and independent review after candidate lock remain pending.']
(private/'excluded-ambiguous.json').write_text(json.dumps(removed,indent=2)+'\n')
(root/'evaluation-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print(json.dumps({'status':'FROZEN_BEFORE_ANY_NEW_RETRIEVAL_SCORING','counts':counts,'dev_sha256':plan['dev_sha256'],'holdout_sha256':plan['holdout_sha256']}))
