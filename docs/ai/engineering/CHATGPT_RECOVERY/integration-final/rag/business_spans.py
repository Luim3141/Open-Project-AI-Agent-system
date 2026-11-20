"""Research projection: exact source slices with plan/receipt boundaries and types."""
import hashlib,re
from source_spans import extract_spans
from readable_spans import readable_span

FIELDS={'text','title','subject','description','summary','comment','note','report','message','explanation',
        'objective','acceptance','scope','api_behavior','edge_cases','limitations','dependencies','unit','verdict','status'}
BOUNDARY=re.compile(r'(?m)^Bình luận #\d+: ')


def business_spans(source):
    if not isinstance(source,str) or len(source)>512000:raise ValueError('SOURCE_SPAN_BOUNDS_INVALID')
    boundaries=list(BOUNDARY.finditer(source))
    segments=([(0,boundaries[0].start(),False)]+[(m.end(),boundaries[i+1].start() if i+1<len(boundaries) else len(source),True) for i,m in enumerate(boundaries)]
              if boundaries else [(0,len(source),False)])
    result=[];seen=set();source_hash=hashlib.sha256(source.encode()).hexdigest()
    for start,end,comment in segments or [(0,len(source),False)]:
        for span in extract_spans(source[start:end],fields=FIELDS,include_scalars=False):
            path=span.get('json_path',[])
            # A copied parent specification does not prove this child unit implements it.
            if path and path[0]=='functional_specification':continue
            span={**span,'start':span['start']+start,'end':span['end']+start,'source_sha256':source_hash}
            view=readable_span(source,span)['readable'];key=(tuple(path),view)
            if key in seen:continue
            seen.add(key)
            kind='HISTORICAL_RECEIPT' if comment or path and path[0] in {'delivery','test_evidence','review_evidence'} else 'REQUIREMENT' if path and path[0]=='assignment' else 'SOURCE_STATEMENT'
            result.append({**span,'text':view,'evidence_type':kind})
    return result
