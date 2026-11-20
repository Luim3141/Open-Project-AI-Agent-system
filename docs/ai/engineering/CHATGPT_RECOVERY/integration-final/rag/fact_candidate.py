"""Research only: typed fact retrieval; selector IDs cannot introduce new prose."""
import json,math
from business_candidate import BusinessCandidate, constraints, norm
from business_facts import facts


class FactCandidate(BusinessCandidate):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.db.execute('DELETE FROM candidate_fts');self.rowids={}
        for doc,record in self.records.items():
            self.spans[doc]=facts(record)
            body='\n'.join(dict.fromkeys(f"{s['label']}: {s['text']}" for s in self.spans[doc]))
            self.projections[doc]=(record['title']+'\n'+body)[:6000]
            row=self.db.execute('INSERT INTO candidate_fts(title,body) VALUES(?,?)',(norm(record['title']),norm(body))).lastrowid
            self.rowids[row]=doc

    def packet(self,query,dense=()):
        ranked=self.retrieve(query,dense);groups,unknown=constraints(query)
        terms=set(norm(query).split());selected=[];remaining=4300
        for doc in ranked:
            pool=self.spans[doc]
            def relevance(span):
                words=set(norm(span['label']+' '+span['text']).split())
                return (-len(words&terms),span['start'])
            # Titles establish identity, never implementation proof. Other facts remain typed.
            ordered=sorted(pool,key=relevance)
            title=next((s for s in pool if s['evidence_type']=='SOURCE_TITLE'),None)
            if title:ordered=[title]+[s for s in ordered if s!=title]
            for span in ordered[:6]:
                item={'id':len(selected),'native_id':self.records[doc]['metadata']['native_id'],
                      'type':span['evidence_type'],'label':span['label'],'text':span['text']}
                size=len(json.dumps(item,ensure_ascii=False,separators=(',',':')))
                if len(span['text'])>360 or size>remaining:continue
                selected.append({**item,'document_id':doc,'span':span});remaining-=size
        return {'query':query,'retrieved_native_ids':[self.records[d]['metadata']['native_id'] for d in ranked],
                'facts':selected,'context_chars':4300-remaining}

    @staticmethod
    def model_input(packet):
        return {'question':packet['query'],'facts':[{k:v for k,v in f.items() if k not in {'span','document_id'}} for f in packet['facts']]}

    def fact_payload(self,doc,span):
        return {**self.dense_payload(doc),'start':span['start'],'end':span['end'],'span_sha256':span['sha256'],
                'label':span['label'],'evidence_type':span['evidence_type']}

    def semantic_packet(self,query,dense,fact_hits):
        lookup={(doc,s['start'],s['end']):s for doc,spans in self.spans.items() for s in spans};valid=[]
        for hit in fact_hits:
            payload=hit.get('payload',{});doc=payload.get('document_id');score=hit.get('score')
            span=lookup.get((doc,payload.get('start'),payload.get('end')))
            if (span is None or type(score) not in (int,float) or not math.isfinite(score)
                    or payload!=self.fact_payload(doc,span)):continue
            valid.append((score,doc,span))
        valid.sort(key=lambda row:-row[0]);source_hits=[]
        for score,doc,_ in valid:
            if doc not in [h['payload']['document_id'] for h in source_hits]:source_hits.append({'score':score,'payload':self.dense_payload(doc)})
        ranked=self.retrieve(query,[*source_hits,*dense]);selected=[];counts={};remaining=2200;seen=set()
        for _,doc,span in valid:
            if doc not in ranked or counts.get(doc,0)>=4 or len(selected)>=12:continue
            key=(doc,span['evidence_type'],norm(span['text']))
            if key in seen:continue
            item={'id':len(selected),'native_id':self.records[doc]['metadata']['native_id'],
                  'type':span['evidence_type'],'label':span['label'],'text':span['text']}
            size=len(json.dumps(item,ensure_ascii=False,separators=(',',':')))
            if len(span['text'])>360 or size>remaining:continue
            selected.append({**item,'document_id':doc,'span':span});remaining-=size;seen.add(key);counts[doc]=counts.get(doc,0)+1
        return {'query':query,'retrieved_native_ids':[self.records[d]['metadata']['native_id'] for d in ranked],
                'facts':selected,'context_chars':2200-remaining}

    def render(self,packet,selected):
        if not isinstance(selected,dict) or set(selected)!={'fact_ids'}:raise ValueError('SELECTOR_FORMAT')
        ids=selected['fact_ids'];available={f['id']:f for f in packet['facts']}
        if (not isinstance(ids,list) or len(ids)>4 or any(type(i) is not int or i not in available for i in ids)
                or len(set(ids))!=len(ids)):raise ValueError('SELECTOR_ID')
        citations=[];lines=[]
        for identifier in ids:
            fact=available[identifier];span=fact['span'];doc=fact['document_id']
            citations.append(self.citation(doc,span))
            lines.append(f"WP #{fact['native_id']} [{fact['type']}] {fact['label']}: {fact['text']}")
        return {'state':'EXTRACTED_EVIDENCE' if ids else 'NO_EVIDENCE','answer':'\n'.join(lines) if ids else None,
                'citations':citations,'retrieved_native_ids':packet['retrieved_native_ids'],
                'support':'SEMANTIC_SELECTION_REQUIRES_EVALUATION','answer_method':'TYPED_SOURCE_EXTRACTION'}
