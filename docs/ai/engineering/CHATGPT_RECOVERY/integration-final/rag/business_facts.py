"""Typed compact facts; raw source/offsets stay authoritative, never rendered guesses."""
import hashlib,re
from source_spans import extract_spans
from readable_spans import readable_span

BOUNDARY=re.compile(r'(?m)^Bình luận #(\d+): ')
NOISE=re.compile(r'^(?:id|.*_ids?|.*sha(?:256)?|.*hash|baseRefName|headRefName|headRefOid|url|pr_url|nonce|lease|claim|command|artifact|files_changed|run_artifacts|virtual_executor|reviewers|Native_assignee)$',re.I)
SENTENCE=re.compile(r'.+?(?:[.!?](?=\s|$)|$)')

def facts(record):
    source=record['content'];markers=list(BOUNDARY.finditer(source));header=record['metadata']['native_header']
    sections=([(0,markers[0].start(),None)]+[(m.end(),markers[i+1].start() if i+1<len(markers) else len(source),int(m[1])) for i,m in enumerate(markers)]
              if markers else [(0,len(source),None)])
    rows={}
    for start,end,activity in sections:
        for span in extract_spans(source[start:end],max_chars=64000,fields={'*'}):
            path=span.get('json_path',[])
            if 'functional_specification' in path or any(NOISE.fullmatch(key) for key in path):continue
            span={**span,'start':start+span['start'],'end':start+span['end'],'source_sha256':record['source_sha256']}
            view=readable_span(source,span)
            if re.fullmatch(r'(?:[a-f0-9]{20,}|\[Native-reference:[^]]+\])',view['readable']):continue
            native=header['start']<=span['start']<span['end']<=header['end']
            kind='NATIVE_FIELD' if native else 'HISTORICAL_RECEIPT' if activity is not None or span.get('json_context')=='RECEIPT' else 'REQUIREMENT' if span.get('json_context')=='PLAN' else 'SOURCE_STATEMENT'
            if span['start']==0:kind='SOURCE_TITLE'
            # Decode first: escaped newlines must not make a valid long JSON value disappear.
            for match in SENTENCE.finditer(view['readable']):
                a,b=match.span()
                while a<b and view['readable'][a].isspace():a+=1
                while b>a and view['readable'][b-1].isspace():b-=1
                if a==b or b-a>800:continue
                raw_start=view['raw_intervals'][a][0];raw_end=view['raw_intervals'][b-1][1];raw=source[raw_start:raw_end]
                item={**span,'start':raw_start,'end':raw_end,'raw':raw,'sha256':hashlib.sha256(raw.encode()).hexdigest(),
                      'text':view['readable'][a:b],'label':'.'.join(path) if path else 'source.text','evidence_type':kind,'activity_id':activity}
                assert readable_span(source,item)['readable']==item['text']
                rows[(kind,tuple(path),item['text'])]=item
    return sorted(rows.values(),key=lambda row:row['start'])
