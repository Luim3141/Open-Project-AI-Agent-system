"""Typed diagnostics; quote identity never implies semantic answer support."""
import hashlib
import json
import re
from pathlib import Path

from readable_spans import raw_citation, readable_span


def sha(text):return hashlib.sha256(text.encode()).hexdigest()


class EvidenceError(ValueError):
    def __init__(self, category, rule, context=None):
        self.category=category;self.rule=rule
        self.context={key:value for key,value in (context or {}).items() if (
            key in {'native_id','span_id','start','end'} and type(value) is int) or (
            key in {'document_id','source_sha256','span_sha256'} and isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value)) or (
            key=='case_id' and isinstance(value,str) and re.fullmatch(r'[\w:.-]{1,128}',value)) or (
            key=='candidate_span_ids' and isinstance(value,list) and len(value)<=32 and all(type(item) is int for item in value))}
        super().__init__(rule)

    def diagnostic(self):return {'category':self.category,'rule':self.rule,**self.context}


def validate_response(raw, packet, sources, spans, *, support_check=None, _diagnose_alternatives=True):
    def fail(category,rule,context=None):raise EvidenceError(category,rule,context)
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:fail('FORMAT','DUPLICATE_JSON_KEY')
            result[key]=value
        return result
    if not isinstance(raw,str) or len(raw.encode())>16384:fail('FORMAT','RESPONSE_SIZE_OR_TYPE_INVALID')
    try:body=json.loads(raw,object_pairs_hook=unique)
    except json.JSONDecodeError:fail('FORMAT','MALFORMED_JSON')
    if not isinstance(body,dict) or set(body)!={'matches'} or not isinstance(body['matches'],list) or len(body['matches'])>1:
        fail('FORMAT','RESPONSE_SHAPE_INVALID')
    result=[]
    for match in body['matches']:
        if (not isinstance(match,dict) or set(match)!={'native_id','span_id','answer','quote'}
                or type(match['native_id']) is not int or type(match['span_id']) is not int
                or not isinstance(match['answer'],str) or not 1<=len(match['answer'].strip())<=1000):
            fail('FORMAT','MATCH_SHAPE_INVALID')
        selected=next((s for s in packet['spans'] if s['id']==match['span_id']),None)
        context={'case_id':packet.get('case',{}).get('id'),'native_id':match['native_id'],'span_id':match['span_id']}
        if selected is None:fail('SPAN','SPAN_ID_UNKNOWN',context)
        context.update({key:selected.get(key) for key in ('document_id','source_sha256','span_sha256','start','end')})
        if selected['native_id']!=match['native_id']:fail('SOURCE','NATIVE_SOURCE_MISMATCH',context)
        source=sources.get(selected['document_id'])
        if source is None:fail('SOURCE','SOURCE_NOT_FOUND',context)
        if sha(source)!=selected['source_sha256']:fail('SOURCE','SOURCE_HASH_MISMATCH',context)
        start,end=selected['start'],selected['end']
        if type(start) is not int or type(end) is not int or not 0<=start<end<=len(source):fail('SPAN','SPAN_OFFSETS_INVALID',context)
        span=spans.get((selected['document_id'],start,end))
        if span is None:fail('SPAN','SPAN_OFFSETS_MISMATCH',context)
        if sha(source[start:end])!=selected['span_sha256'] or span.get('sha256')!=selected['span_sha256']:
            fail('SPAN','SPAN_HASH_MISMATCH',context)
        try:view=readable_span(source,span)
        except (ValueError,KeyError,TypeError):fail('SPAN','SPAN_MAPPING_INVALID',context)
        quote=match['quote']
        if not isinstance(quote,str) or not 1<=len(quote)<=10000:fail('QUOTE','QUOTE_SIZE_OR_TYPE_INVALID',context)
        first=view['readable'].find(quote)
        if first<0:
            same=[];other=False
            if _diagnose_alternatives:
                for candidate in packet['spans']:
                    if candidate['id']==selected['id']:continue
                    probe={**match,'native_id':candidate['native_id'],'span_id':candidate['id']}
                    try:
                        validate_response(json.dumps({'matches':[probe]}),packet,sources,spans,_diagnose_alternatives=False)
                    except EvidenceError:continue
                    if candidate['document_id']==selected['document_id'] and candidate['native_id']==selected['native_id']:
                        same.append(candidate['id'])
                    else:other=True
            if same:
                fail('SPAN','SPAN_REFERENCE_MISMATCH' if len(same)==1 else 'QUOTE_AMBIGUOUS_ACROSS_SPANS',
                     {**context,'candidate_span_ids':same[:32]})
            if other:fail('SOURCE','QUOTE_SOURCE_MISMATCH',context)
            fail('QUOTE','QUOTE_NOT_FOUND',context)
        if first!=view['readable'].rfind(quote):fail('QUOTE','QUOTE_AMBIGUOUS',context)
        try:citation=raw_citation(source,span,quote)
        except ValueError:fail('SPAN','CITATION_MAPPING_INVALID',context)
        row={'match':match,'span':selected,'citation':citation,'support':'UNVERIFIED'}
        if support_check is not None:
            if support_check(row) is not True:fail('SUPPORT','UNSUPPORTED_ANSWER',context)
            row['support']='SUPPORTED_BY_CALLER_EVALUATOR'
        result.append(row)
    return result


def repair_span_reference(raw, packet, sources, spans):
    """Repair one uniquely attributable pointer; semantic support stays unverified."""
    try:
        validate_response(raw,packet,sources,spans)
        return raw,[]
    except EvidenceError as error:
        if error.rule!='SPAN_REFERENCE_MISMATCH' or len(error.context.get('candidate_span_ids',[]))!=1:raise
        target=error.context['candidate_span_ids'][0]
    body=json.loads(raw);match=body['matches'][0];previous=match['span_id'];match['span_id']=target
    repaired=json.dumps(body,ensure_ascii=False)
    validate_response(repaired,packet,sources,spans)
    return repaired,[{'rule':'UNIQUE_EXACT_QUOTE_SAME_SOURCE','from_span_id':previous,'to_span_id':target}]


def parse_with_reformat(raw, validator, reformat=None):
    try:return validator(raw)
    except EvidenceError as error:
        if error.category!='FORMAT' or reformat is None:raise
    return validator(reformat(raw))


def capture_response(response, path):
    """Capture once before parsing; private bounded redacted body + original digest."""
    def redact(value):
        if isinstance(value,dict):
            return {key:'[REDACTED]' if re.search(r'password|secret|token|credential|api.?key|authorization',key,re.I) else redact(item) for key,item in value.items()}
        if isinstance(value,list):return [redact(item) for item in value]
        if not isinstance(value,str):return value
        if value.lstrip().startswith(('{','[')):
            try:return redact(json.loads(value))
            except ValueError:pass
        value=re.sub(r'-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----','[REDACTED]',value,flags=re.S)
        value=re.sub(r'''(?i)["']?(?:password|secret|token|api.?key|authorization)["']?\s*[:=]\s*(?:"[^"]*"|'[^']*'|[^\s,;]+)|\b(?:Bearer\s+[\w.~+/=-]{8,}|gh[pousr]_[\w]{20,}|github_pat_[\w]{20,}|AIza[\w-]{20,}|sk-[\w-]{20,})''','[REDACTED]',value)
        return re.sub(r'\beyJ[\w-]{10,}\.[\w-]{10,}\.[\w-]{10,}\b','[REDACTED]',value)
    raw=json.dumps(response,ensure_ascii=False,sort_keys=True)
    preview=json.dumps(redact(response),ensure_ascii=False)[:8192] if len(raw.encode())<=65536 else ''
    # Bound bytes too: a Vietnamese/Unicode preview may exceed its character count.
    preview=preview.encode()[:8192].decode(errors='ignore')
    record={'response_sha256':sha(raw),'response_bytes':len(raw.encode()),'redacted_preview':preview,'body_omitted':not preview}
    with Path(path).open('x',encoding='utf-8') as stream:json.dump(record,stream,ensure_ascii=False)
    return {key:value for key,value in record.items() if key!='redacted_preview'}
