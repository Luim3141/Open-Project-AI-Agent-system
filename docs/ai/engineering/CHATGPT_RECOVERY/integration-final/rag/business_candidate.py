"""Frozen research candidate: scoped union retrieval + conservative extractive answers."""
import hashlib,json,math,re,sqlite3,unicodedata
from business_spans import business_spans
from readable_spans import raw_citation

def sha(value):return hashlib.sha256(value.encode()).hexdigest()
def norm(value):return ' '.join(re.findall('[a-z0-9]+',unicodedata.normalize('NFKD',value.casefold().replace('đ','d')).encode('ascii','ignore').decode()))

# Domain vocabulary, not task IDs, answer labels, output-specific cutoffs or model guesses.
ALIASES={
 'sqlite':['sqlite','sqlite3'],'persist':['persist','persistence','persisting','saved','luu tru','ben vung'],
 'create':['create','creating','tao','add task','them cong viec'],'list':['list','listing','liet ke','danh sach'],
 'task':['task','tasks','work item','work package','cong viec'],'count':['count','dem','so luong'],
 'summary':['summary','tong hop','thong ke'],'csv':['csv'],'unicode':['unicode','tieng viet'],
 'casefold':['casefold','case insensitive','hoa thuong'],'filter':['filter','loc'],'category':['category','phan loai'],
 'exists':['exists','existence','ton tai'],'title':['title','tieu de'],'detail':['details','detail','chi tiet'],
 'health':['healthz','health check','kiem tra suc khoe'],'history':['history','lich su'],
 'restore':['restore','restores','restored','restoration','recovery','phuc hoi'],'mapping':['mapping','anh xa'],
 'receipt':['receipt','bien nhan'],'failure':['failure','failed','that bai'],'citation':['citation','trich dan'],
 'retry':['retry','thu lai'],'seconds':['seconds','second','giay'],'coding':['coding','lap trinh','viet code'],
 'replacement':['replacement','replaces','thay the'],'negation':['not','never','khong']}
STOP=set(norm('which what who where is are a an the with and or of for in to into on from does do did can will has have should how many before after current currently native source document sources item items handle handles handling responsible entry entries database status compare show find please task nao gi la va voi cua cho de tai tu dang hien hanh hien trang nguon tai lieu co khong can tim nhung nao viec duoc bao nhieu doi truoc khi nay mot theo voi').split())
STOP.update(norm('thuoc phai loai type use uses dung su dung').split())
ENTITY=re.compile(r'(?:\b(?:wp|work package)\s*#?\s*|(?<!\w)#)([1-9][0-9]*)\b',re.I)
DISCOVERY=re.compile(r'\b(?:which task|which work|find|cong viec nao|task nao|tim cong viec|muc tieu|yeu cau)\b')
FACT=re.compile(r'\b(?:not|never|requires|preserved|khong|can|duoc giu)\b')

def constraints(query):
    cleaned=ENTITY.sub('',query);plain=norm(cleaned);groups=set();covered=set()
    for group,aliases in ALIASES.items():
        for alias in aliases:
            if re.search(r'(?<!\w)'+re.escape(alias)+r'(?!\w)',plain):groups.add(group);covered.update(alias.split())
    unknown=set(plain.split())-covered-STOP
    return groups,unknown

def covers(text,groups,unknown):
    plain=norm(text);words=set(plain.split())
    return unknown<=words and all(any(re.search(r'(?<!\w)'+re.escape(alias)+r'(?!\w)',plain) for alias in ALIASES[group]) for group in groups)

def negated_groups(text):
    result=set()
    folded=unicodedata.normalize('NFKD',text.casefold().replace('đ','d')).encode('ascii','ignore').decode()
    for clause in re.findall(r'\b(?:not|never|khong)\b(.*?)(?:[,;.!?]|\bbut\b|\bnhung\b|$)',folded):
        for group in ALIASES.keys()-{'negation','task','replacement'}:
            if covers(clause,{group},set()):result.add(group)
    return result


class BusinessCandidate:
    def __init__(self,records,*,project_id,source_actor,role,current_sources):
        self.records={};self.spans={};self.projections={};self.db=sqlite3.connect(':memory:')
        self.db.execute('CREATE VIRTUAL TABLE candidate_fts USING fts5(title,body)');self.rowids={}
        for record in records:
            meta=record.get('metadata',{});identifier=meta.get('native_id');content=record.get('content','');doc=record.get('document_id')
            expected=current_sources.get(identifier)
            if (project_id!=6 or record.get('project_id')!=6 or role not in record.get('allowed_roles',[]) or meta.get('actor_id')!=source_actor
                    or type(identifier) is not int or record.get('source_id')!=f'actor:{source_actor}:wp:{identifier}'
                    or expected!={'lock_version':meta.get('lock_version'),'document_id':doc}
                    or sha(content)!=record.get('source_sha256') or sha('6:WORK_PACKAGE:'+record['source_id']+':'+content.strip())!=doc
                    or not content.startswith(record['title']+'\n')):continue
            header=meta.get('native_header',{});start,end=header.get('start'),header.get('end')
            if type(start) is not int or type(end) is not int or not 0<=start<end<=len(content):continue
            raw=content[start:end]
            if sha(raw)!=header.get('sha256') or json.loads(raw)!={'native_fields':meta.get('native_fields')}:continue
            if meta['native_fields'].get('native_id')!=identifier or meta['native_fields'].get('lock_version')!=meta['lock_version']:continue
            self.records[doc]=record;self.spans[doc]=business_spans(content)
            primary=[s['text'] for s in self.spans[doc] if s['evidence_type']!='HISTORICAL_RECEIPT']
            self.projections[doc]='\n'.join(dict.fromkeys([record['title'],*primary]))[:6000]
            row=self.db.execute('INSERT INTO candidate_fts(title,body) VALUES(?,?)',(norm(record['title']),norm('\n'.join(primary)))).lastrowid;self.rowids[row]=doc

    def dense_payload(self,doc):
        record=self.records[doc];meta=record['metadata']
        return {'document_id':doc,'project_id':6,'actor_id':meta['actor_id'],'allowed_roles':record['allowed_roles'],
                'native_id':meta['native_id'],'lock_version':meta['lock_version'],'source_sha256':record['source_sha256'],
                'projection_sha256':sha(self.projections[doc])}

    def safe_dense(self,results):
        accepted=[]
        for item in results:
            payload=item.get('payload',{});doc=payload.get('document_id');score=item.get('score')
            if doc not in self.records or payload!=self.dense_payload(doc) or type(score) not in (int,float) or not math.isfinite(score):continue
            if doc not in accepted:accepted.append(doc)
        return accepted

    def retrieve(self,query,dense=()):
        ids={int(value) for value in ENTITY.findall(query)};groups,unknown=constraints(query)
        reference=bool(ids and 'replacement' in groups)
        terms=sorted(set(norm(ENTITY.sub('',query)).split())|groups|{word for group in groups for alias in ALIASES[group] for word in alias.split()})
        expression=' OR '.join('"'+term+'"' for term in terms[:60])
        lexical=[self.rowids[row[0]] for row in self.db.execute('SELECT rowid FROM candidate_fts WHERE candidate_fts MATCH ? ORDER BY bm25(candidate_fts,8,1) LIMIT 30',(expression,))] if expression else []
        exact=[doc for doc,r in self.records.items() if (all(re.search(r'\bWP\s*#?\s*'+str(identifier)+r'\b',r['content'],re.I) for identifier in ids) if reference else r['metadata']['native_id'] in ids)]
        ranks={}
        for lane in (exact,lexical,self.safe_dense(dense)):
            for rank,doc in enumerate(lane,1):ranks[doc]=ranks.get(doc,0)+1/(60+rank)
        if ids:ranks={doc:score for doc,score in ranks.items() if doc in exact}
        return sorted(ranks,key=lambda doc:(-ranks[doc],doc))[:5]

    def citation(self,doc,span,quote=None,kind=None):
        record=self.records[doc];quote=quote or span['text'];exact=raw_citation(record['content'],span,quote)
        return {'document_id':doc,'native_id':record['metadata']['native_id'],'lock_version':record['metadata']['lock_version'],
                'citation':f"/work_packages/{record['metadata']['native_id']}",'evidence_type':kind or span['evidence_type'],
                **exact,'quote':quote}

    def answer(self,query,dense=()):
        ranked=self.retrieve(query,dense);ids={int(value) for value in ENTITY.findall(query)};plain=norm(ENTITY.sub('',query));groups,unknown=constraints(query)
        result={'state':'NO_EVIDENCE','answer':None,'citations':[],'retrieved_native_ids':[self.records[d]['metadata']['native_id'] for d in ranked],
                'answer_method':'DETERMINISTIC_EXTRACTIVE','generation_calls':0,'reason':'MISSING_EXPLICIT_SUPPORT'}
        if not ranked:return result
        lines=[];citations=[]
        field='status' if re.search(r'\b(?:status|trang thai)\b',plain) else 'type' if re.search(r'\b(?:type|loai)\b',plain) else 'lock_version' if re.search(r'\b(?:version|phien ban)\b',plain) else None
        if field=='type' and 'coding' in groups:field=None
        if ids and field:
            if not ids<={self.records[d]['metadata']['native_id'] for d in ranked}:return result
            for doc in ranked:
                record=self.records[doc];meta=record['metadata'];header=meta['native_header'];raw=record['content'][header['start']:header['end']]
                span={**header,'raw':raw,'source_sha256':record['source_sha256'],'text':raw,'evidence_type':'NATIVE_FIELD'}
                lines.append(f"WP #{meta['native_id']} — {field}: {meta['native_fields'][field]}");citations.append(self.citation(doc,span))
        elif not plain and ids:
            for doc in ranked:
                record=self.records[doc];span={'start':0,'end':len(record['title']),'raw':record['title'],'text':record['title'],'sha256':sha(record['title']),'source_sha256':record['source_sha256'],'evidence_type':'SOURCE_TITLE'}
                lines.append(f"WP #{record['metadata']['native_id']} — {record['title']}");citations.append(self.citation(doc,span))
        elif re.search(r'\b(?:implemented|verified|running|da thuc hien|dang chay)\b',plain):
            return {**result,'reason':'RUNTIME_PROOF_NOT_AVAILABLE'}
        elif groups or unknown:
            discovery=bool(DISCOVERY.search(plain));candidates=[]
            for doc in ranked:
                record=self.records[doc]
                for span in self.spans[doc]:
                    if span['evidence_type']=='HISTORICAL_RECEIPT' or span.get('json_path',[None])[0]=='native_fields':continue
                    if not discovery and (span['start']==0 or span['evidence_type']=='REQUIREMENT' or not FACT.search(norm(span['text']))):continue
                    if not covers(span['text'],groups,unknown):continue
                    if discovery:
                        negated=negated_groups(span['text'])
                        targets=groups-{'negation','task','replacement'}
                        if 'negation' in groups and not targets<=negated or 'negation' not in groups and targets&negated:continue
                    candidates.append((span['start']!=0,ranked.index(doc),len(span['text']),doc,span))
            if candidates:
                *_,doc,span=min(candidates,key=lambda row:row[:3]);record=self.records[doc]
                lines=[f"WP #{record['metadata']['native_id']} — {span['text']}"];citations=[self.citation(doc,span)]
        if lines:result.update(state='SUPPORTED',answer='\n'.join(lines),citations=citations,reason='EXACT_NATIVE_FIELD' if field and ids else 'EXPLICIT_SOURCE_QUOTE')
        return result
