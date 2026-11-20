"""Experimental fail-closed identifier check; not wired into production search."""
import re

_PATH = re.compile(r'(?<!\w)/(?:[A-Za-z0-9_{}-]+/)*[A-Za-z0-9_{}-]+')
_TOKEN = re.compile(r'[^\W\d_][\w.-]*', re.UNICODE)


def identifiers(query):
    paths = list(_PATH.finditer(query))
    candidates = [(m.start(), m.group()) for m in paths]
    for match in _TOKEN.finditer(query):
        token = match.group().rstrip('.-')
        if not token.isascii() or len(token) < 3 or any(p.start() <= match.start() < p.end() for p in paths):
            continue
        mid_sentence = bool(query[:match.start()].strip())
        if ('_' in token or '.' in token or any(c.isdigit() for c in token)
                or token.isupper() or re.search(r'[a-z][A-Z]', token)
                or (mid_sentence and token[0].isupper() and token[1:].islower())):
            candidates.append((match.start(), token))
    return list(dict.fromkeys(token for _, token in sorted(candidates)))


def missing_identifiers(query, authorized_documents):
    documents = list(authorized_documents)
    return [token for token in identifiers(query) if not any(
        re.search(r'(?<![\w])' + re.escape(token) + r'(?![\w])', doc, re.IGNORECASE)
        for doc in documents)]
