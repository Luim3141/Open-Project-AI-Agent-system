"""Bilingual intent anchors complement dense recall; assertions still require source text."""
import re
import unicodedata

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',value.casefold().replace('đ','d')) if not unicodedata.combining(c))

# Domain synonyms describe capabilities, not document IDs or benchmark query identities.
CONCEPTS={
 'casefold':(r'hoa thuong|case.?insensitive|ignore case|international character|quoc te|sharp s|\bss\b|\bunicode\b',r'casefold|unicode|hoa thuong|case.?insensitive'),
 'search':(r'tim kiem|tra cuu|\bsearch\b|wildcard|\blike\b',r'\bsearch\b|tim kiem|\blike\b|casefold'),
 'health':(r'suc khoe|con song|\balive\b|\bhealthz?\b|readiness|kiem tra app',r'healthz|health|suc khoe'),
 'summary':(r'thong ke|bao nhieu|statistics|\bsummary\b|\bcounts?\b|tong so|so lieu tong hop',r'summary|counts?|thong ke'),
 'category':(r'phan loai|danh muc|\bcategor(?:y|ies)\b|\bnhom\b|\blabels?\b',r'category|categories|danh muc|phan loai'),
 'export':(r'\bxuat\b|\bcsv\b|\bexport\b|spreadsheet|bang tinh',r'\bcsv\b|export|xuat'),
 'auth':(r'dang nhap|\blogin\b|\boauth\b|\bsign.?in\b',r'\boauth\b|\blogin\b|dang nhap'),
 'photo':(r'\bcamera\b|chup anh|\bphoto\b',r'\bcamera\b|\bphoto\b|chup anh'),
 'map':(r'ban do|\bmap\b|\bgps\b|location tracking',r'\bgps\b|\bmap\b|ban do'),
 'stock':(r'ton kho|warehouse|\bstock\b|inventory',r'warehouse|inventory|ton kho'),
 'payments':(r'chuyen khoan|ngan hang|\bbank\b|payment|billing checkout',r'chuyen khoan|ngan hang|\bbank\b|payment'),
 'translation':(r'tu dich|translated|translation|tieng nhat|\bjapanese\b',r'translation|translated|tieng nhat|\bjapanese\b'),
 'speech':(r'loi noi|\bspeech\b|transcrib|transcript',r'transcrib|transcript|loi noi|\bspeech\b'),
 'encryption':(r'ma hoa|encryption|\baes\b',r'ma hoa|encryption|\baes\b'),
 'signature':(r'chu ky so|digital signatures?',r'chu ky so|digital signatures?'),
 'failover':(r'da vung|multiregion|failover',r'da vung|multiregion|failover'),
 'email':(r'\bemail\b|\bsmtp\b|thu dien tu',r'\bemail\b|\bsmtp\b|thu dien tu'),
 'pdf':(r'\bpdf\b',r'\bpdf\b'),
}

def evidence(query,text):
    q,t=normalize(query),normalize(text)
    concepts=[key for key,(pattern,_) in CONCEPTS.items() if re.search(pattern,q)]
    if not concepts:return False
    if any(not re.search(CONCEPTS[key][1],t) for key in concepts):return False
    entities=re.findall(r'/(?:[a-zA-Z0-9_.{}?-]+/)*[a-zA-Z0-9_.{}?-]+',q)
    if any(entity not in t for entity in entities):return False
    acronyms=re.findall(r'\b[A-Z][A-Z0-9_]{1,}\b',query)
    if any(normalize(word) not in t for word in acronyms if word not in {'GET','POST','PUT','PATCH','DELETE','SS'}):return False
    return True
