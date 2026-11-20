"""Post-hoc DEV selection prototype, never an answerability or authorization decision."""
import re
import unicodedata


def _terms(text):
    text=''.join(c for c in unicodedata.normalize('NFKD',text.casefold().replace('đ','d')) if not unicodedata.combining(c))
    stop={'what','which','where','when','does','the','and','with','for','how','are','was','can','that','this','document','evidence',
          'theo','nao','cua','cho','khi','duoc','trong','voi','nhu','mot','nhung','bao','gi','co','la','de','va'}
    return {v[:-1] if len(v)>4 and v.endswith('s') else v for v in re.findall(r'\w+',text) if len(v)>2 and v not in stop}


def select_spans(query,spans,limit=8):
    if not isinstance(query,str) or type(limit) is not int or not 1<=limit<=8:raise ValueError('SPAN_SELECTION_BOUNDS_INVALID')
    ordered=sorted(spans,key=lambda span:(span['start'],span['end']))
    if len(ordered)<=limit:return ordered
    terms=_terms(query);chosen=[];seen=set()
    def take(span):
        key=(span['start'],span['end'])
        if key not in seen and len(chosen)<limit:chosen.append(span);seen.add(key)
    for span in ordered[:2]+ordered[-2:]:take(span)
    for span in sorted(ordered,key=lambda span:(-len(terms&_terms(span['raw'])),span['start'])):take(span)
    return sorted(chosen,key=lambda span:(span['start'],span['end']))
