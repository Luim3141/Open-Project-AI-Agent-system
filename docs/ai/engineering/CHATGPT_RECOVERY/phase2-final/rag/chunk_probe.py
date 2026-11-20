"""Bounded dev-only chunk diagnostic. Never changes SQLite/Qdrant."""
exec((__import__('pathlib').Path(__file__).with_name('diagnose.py')).read_text().split('root =')[0])
import sqlite3
root=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/semantic-review-20261102'
points=json.loads((root/'source-vectors.json').read_text())
db=sqlite3.connect(f'file:{(root/"knowledge.sqlite").as_posix()}?mode=ro',uri=True)
docs=[dict(zip(['hash','title','content','id'],r)) for r in db.execute("SELECT source_hash,title,content,json_extract(metadata,'$.native_id') FROM knowledge_documents WHERE project_id='6' AND json_extract(metadata,'$.actor_id')=20")]
cases=[('kiểm tra sức khỏe máy chủ',384),('service health check endpoint',384),('tìm kiếm không phân biệt hoa thường unicode',383),('case insensitive unicode search',383),('thống kê số lượng công việc theo trạng thái',386),('count tasks by status',386),('upload user avatar',None),('database backup retention policy',None),('send transactional email',None)]
client=VectorClient(timeout=60)
try:
    for doc in docs:
        if doc['id'] not in (383,384,386):continue
        doc['title_vec']=client.embed_texts([doc['title']])[0]
        doc['first_line_vec']=client.embed_texts([doc['content'].split('\n')[0]])[0]
    out=[]
    for query,native in cases:
        q=client.embed_texts([query])[0]
        scores=[]
        for d in docs:
            if 'title_vec' not in d:continue
            existing=[cosine(q,p['vector']) for p in points if p['payload']['document_id']==d['hash']]
            scores.append({'native_id':d['id'],'old_max':max(existing),'title':cosine(q,d['title_vec'])})
        out.append({'query':query,'expected':native,'scores':scores})
    (root/'phase2-chunk-probe.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
    print(json.dumps(out,ensure_ascii=False,indent=2))
finally:client.close();db.close()
