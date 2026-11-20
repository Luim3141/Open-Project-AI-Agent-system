"""Research only: exact Unicode offsets; plaintext and permitted values are NOT secret-scrubbed."""
import hashlib
import json
import re

_STRING = re.compile(r'"(?:\\.|[^"\\])*"')
_FIELDS = {'text', 'title', 'subject', 'description', 'summary', 'comment', 'note', 'report', 'message', 'explanation'}
_SENTENCE = re.compile(r'.+?(?:[.!?](?=\s|$)|$)')
_SCALAR = re.compile(r'(?:true|false|null|-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)(?=\s*[,}\]])')
_SECRET_FIELD = re.compile(r'password|secret|token|credential|api[_-]?key|authorization|private',re.I)


def _json_end(source, start, limit):
    stack=[];quoted=False;escaped=False
    for index in range(start,min(len(source),start+limit)):
        char=source[index]
        if quoted:
            if escaped:escaped=False
            elif char=='\\':escaped=True
            elif char=='"':quoted=False
        elif char=='"':quoted=True
        elif char in '{[':
            stack.append(char)
            if len(stack)>64:return None
        elif char in '}]':
            if not stack or stack.pop()!={'}':'{',']':'['}[char]:return None
            if not stack:return index+1
    return None


def extract_spans(source, *, max_chars=800, max_source_chars=512000, max_spans=1500, fields=None, include_scalars=True):
    if (not isinstance(source,str) or type(max_chars) is not int or type(max_source_chars) is not int or type(max_spans) is not int
            or max_source_chars<1 or len(source)>max_source_chars or not 20<=max_chars<=64000 or max_spans<1):
        raise ValueError('SOURCE_SPAN_BOUNDS_INVALID')
    source_hash=hashlib.sha256(source.encode()).hexdigest();spans=[]
    fields=_FIELDS if fields is None else frozenset(fields)
    def add(start,end,kind):
        while start<end and source[start].isspace():start+=1
        while end>start and source[end-1].isspace():end-=1
        if start==end:return
        value=source[start:end]
        for sentence in _SENTENCE.finditer(value):
            a=start+sentence.start();b=start+sentence.end()
            while a<b and source[a].isspace():a+=1
            while b>a and source[b-1].isspace():b-=1
            if a==b or b-a>max_chars:continue
            raw=source[a:b]
            spans.append({'start':a,'end':b,'raw':raw,'sha256':hashlib.sha256(raw.encode()).hexdigest(),
                          'source_sha256':source_hash,'kind':kind})
            if len(spans)>max_spans:raise ValueError('SOURCE_SPAN_COUNT_EXCEEDED')
    pos=0
    while pos<len(source):
        line_end=source.find('\n',pos)
        line_end=len(source) if line_end<0 else line_end
        start=pos
        while start<line_end and source[start].isspace():start+=1
        is_json=False
        if start<line_end and source[start] in '{[':
            peek=start+1
            while peek<len(source) and peek<start+128000 and source[peek].isspace():peek+=1
            next_char=source[peek] if peek<len(source) and peek<start+128000 else ''
            is_json=bool(next_char) and (next_char in ('"','}') if source[start]=='{' else next_char in ('"','{','[',']','-','0','1','2','3','4','5','6','7','8','9','n','t','f'))
        if not is_json:
            add(pos,line_end,'text');pos=line_end+1;continue
        end=_json_end(source,start,128000)
        if end is None:break
        block=source[start:end]
        def reject_duplicates(pairs):
            result={}
            for key,value in pairs:
                if key in result:raise ValueError('DUPLICATE_JSON_KEY')
                result[key]=value
            return result
        def reject_constant(_):raise ValueError('INVALID_JSON_CONSTANT')
        try:root_value=json.loads(block,object_pairs_hook=reject_duplicates,parse_constant=reject_constant)
        except (ValueError,RecursionError):pos=end;continue
        def whitespace(cursor):
            while cursor<end and source[cursor].isspace():cursor+=1
            return cursor
        def parse(cursor,field='',tainted=False,key_start=None,path=()):
            cursor=whitespace(cursor);char=source[cursor]
            if char=='{':
                cursor=whitespace(cursor+1)
                while source[cursor]!='}':
                    key=_STRING.match(source,cursor,end)
                    if key is None:raise ValueError('INVALID_JSON_KEY')
                    name=json.loads(key.group());colon=whitespace(key.end())
                    if source[colon]!=':':raise ValueError('INVALID_JSON_COLON')
                    cursor=whitespace(parse(colon+1,name,tainted or bool(_SECRET_FIELD.search(name)),key.start(),path+(name,)))
                    if source[cursor]==',':cursor=whitespace(cursor+1)
                    elif source[cursor]!='}':raise ValueError('INVALID_JSON_OBJECT')
                return cursor+1
            if char=='[':
                cursor=whitespace(cursor+1)
                while source[cursor]!=']':
                    cursor=whitespace(parse(cursor,field,tainted,path=path))
                    if source[cursor]==',':cursor=whitespace(cursor+1)
                    elif source[cursor]!=']':raise ValueError('INVALID_JSON_ARRAY')
                return cursor+1
            if char=='"':
                value=_STRING.match(source,cursor,end)
                if value is None:raise ValueError('INVALID_JSON_STRING')
                if not tainted and (field in fields or '*' in fields):
                    before=len(spans);add(value.start()+1,value.end()-1,'json:'+field)
                    for span in spans[before:]:span['json_path']=list(path)
                return value.end()
            scalar=_SCALAR.match(source,cursor,end)
            if scalar is None:raise ValueError('INVALID_JSON_SCALAR')
            if include_scalars and not tainted and key_start is not None:
                before=len(spans);add(key_start,scalar.end(),'json_scalar')
                for span in spans[before:]:span.update(json_path=list(path),json_value=json.loads(scalar.group()))
            return scalar.end()
        before=len(spans)
        try:parse(start)
        except (ValueError,IndexError,RecursionError):raise ValueError('SOURCE_JSON_PARSE_FAILED') from None
        context=('RECEIPT' if isinstance(root_value,dict) and set(root_value)&{'head_sha','test_evidence','review_evidence','dev_execution','delivery'}
                 else 'PLAN' if isinstance(root_value,dict) and set(root_value)&{'assignment','functional_specification'} else 'OBJECT')
        for span in spans[before:]:span['json_context']=context
        pos=end
    return spans
