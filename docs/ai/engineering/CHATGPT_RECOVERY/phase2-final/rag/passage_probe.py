"""Dev-only representation experiment at unchanged 0.65 floor."""
exec((__import__('pathlib').Path(__file__).with_name('diagnose.py')).read_text().split('root =')[0])
import re,sqlite3
root=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/semantic-review-20261102'
db=sqlite3.connect(f'file:{(root/"knowledge.sqlite").as_posix()}?mode=ro',uri=True)
docs=[dict(zip(['hash','content','id'],r)) for r in db.execute("SELECT source_hash,content,json_extract(metadata,'$.native_id') FROM knowledge_documents WHERE project_id='6' AND json_extract(metadata,'$.actor_id')=20 AND json_extract(metadata,'$.native_id') IN (383,384,386)")]
cases=[('kiểm tra sức khỏe máy chủ',384),('service health check endpoint',384),('tìm kiếm không phân biệt hoa thường unicode',383),('case insensitive unicode search',383),('thống kê số lượng công việc theo trạng thái',386),('count tasks by status',386),('upload user avatar',None),('database backup retention policy',None),('send transactional email',None)]
client=VectorClient(timeout=60)
try:
    for doc in docs:
        passages=[]
        for text in re.split(r'\n|(?<=\"),(?=\")',doc['content']):
            text=text.strip()
            if 40 <= len(text) <=600 and ' ' in text and text not in passages:passages.append(text)
        doc['passages']=passages
        # Each call retains production's 90 second total bound and batch size <=2.
        doc['vectors']=[]
        for start in range(0,len(passages),32):doc['vectors'].extend(client.embed_texts(passages[start:start+32]))
    out=[]
    for query,native in cases:
        q=client.embed_texts([query])[0];scores=[]
        for d in docs:
            ranked=sorted([(cosine(q,v),p) for p,v in zip(d['passages'],d['vectors'])],reverse=True)
            scores.append({'native_id':d['id'],'score':ranked[0][0],'passage':ranked[0][1]})
        out.append({'query':query,'expected':native,'scores':scores})
    (root/'phase2-passage-probe.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
    print(json.dumps([{**r,'scores':[{k:v for k,v in s.items() if k!='passage'} for s in r['scores']]} for r in out],ensure_ascii=False,indent=2))
finally:client.close();db.close()
