"""Isolated repo-file evidence experiment; never imported by production Gateway."""
import ast,hashlib,re,unicodedata

def clauses(text,kind):
    spans=[]
    if kind=='py':
        lines=text.splitlines(keepends=True);offsets=[0]
        for line in lines:offsets.append(offsets[-1]+len(line))
        for node in ast.walk(ast.parse(text)):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                first=min([node.lineno]+[d.lineno for d in node.decorator_list])
                start=offsets[first-1];end=offsets[node.end_lineno]
                if end-start<=1800:spans.append((start,end))
    else:
        for match in re.finditer(r'[^\n]+',text):
            if match.group().lstrip().startswith(('#','```','---')):continue
            if 30<=len(match.group().strip())<=1200:spans.append(match.span())
            elif len(match.group())>1200:
                for sentence in re.finditer(r'.+?(?:[.!?](?=\s)|$)',match.group()):
                    if 30<=len(sentence.group().strip())<=1200:spans.append((match.start()+sentence.start(),match.start()+sentence.end()))
    out=[]
    for start,end in sorted(set(spans)):
        while start<end and text[start].isspace():start+=1
        while end>start and text[end-1].isspace():end-=1
        value=text[start:end]
        out.append({'start':start,'end':end,'text':value,'sha256':hashlib.sha256(value.encode()).hexdigest()})
    return out

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',value.casefold().replace('đ','d')) if not unicodedata.combining(c))

def constraints_supported(query,evidence):
    anchors=re.findall(r'`([^`]+)`|"([^"\n]+)"|(?<!\w)(/[-\w/{},.]+)|(?<!\w)(\d+(?:\.\d+)*)(?!\w)',query)
    plain=normalize(evidence)
    return all(normalize(next(a for a in groups if a)) in plain for groups in anchors)

STOP=set(normalize('the a an and or of to in on for with by from this that these those is are was were be does do how what which when where who can under according about through as before after only all must may should have has it its into each every already been document documented historical recorded decision design report source revision code describe described implement implementation specification API app task task_id theo tai lieu bao cao thiet ke quyet dinh lich su duoc ghi nhan trong cua va hay hoac la co duoc nhu the nao gi khi neu de cho voi ve mot cac nhung nguoi dung he thong ung dung truoc sau dieu kien yeu cau can phai mo ta theo source').split())

def content_terms(value):
    terms=set(re.findall(r'\w+',normalize(value)))
    # A tiny language-neutral normalization; no held-out topic or negative capability lists.
    return {t[:-1] if t.endswith('s') and len(t)>4 else t for t in terms if len(t)>1 and t not in STOP}

def authorized_sources(manifest,project,role,actor,revisions):
    return [s for s in manifest['sources'] if s['scope']['project_id']==project and role in s['scope']['allowed_roles']
        and s['scope']['actor_id']==actor and revisions.get(s['source_key'])==s['source_revision']]

def normalize_question(query):
    # Source/as-of qualifiers stay in the original query and scope; remove only model-query framing.
    def framing(match):
        prefix=normalize(match.group())
        metadata=re.search(r'\b(document|report|source|readme|revision|design|decision|adr)\b|tai lieu|thiet ke|quyet dinh|bao cao',prefix)
        condition=re.search(r'\b(not|never|no|if|when|unless|without|before|after|case|khong|chua|neu|khi|truoc|sau)\b|truong hop|\b\d[\d/-]*\b',prefix)
        return '' if metadata and not condition else match.group()
    value=re.sub(r'^(?:According to|Under|In)\s+.+?[,;]\s*',framing,query,flags=re.I)
    value=re.sub(r'^(?:According to|Under|In)\s+.+?\s+(?=how\b|what\b|which\b|can\b|does\b)',framing,value,flags=re.I)
    value=re.sub(r'^(?:Theo|Trong)\s+[^,]+,\s*',framing,value,flags=re.I)
    grammar={'what','which','how','does','do','the','a','an','is','are','of','be','duoc','lam','the','nao','nhung','gi'}
    return ' '.join(t for t in value.split() if normalize(t.strip('.,?!;:')) not in grammar)
