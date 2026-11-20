"""Research only: readable JSON string escapes with reversible exact raw citations.

No summaries, aliases, HTML decoding, secret scrubbing or answerability claims.
Input spans must come from the authorized/version-checked source_spans extractor.
"""
import hashlib
import json
import re

_ESCAPE = re.compile(r'\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4})')


def readable_span(source, span):
    if not isinstance(source, str) or len(source) > 512000 or not isinstance(span, dict):
        raise ValueError('READABLE_SPAN_INVALID')
    start, end = span.get('start'), span.get('end')
    if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(source):
        raise ValueError('READABLE_SPAN_OFFSETS_INVALID')
    raw = source[start:end]
    if (len(raw) > 10000 or raw != span.get('raw') or hashlib.sha256(raw.encode()).hexdigest() != span.get('sha256')
            or hashlib.sha256(source.encode()).hexdigest() != span.get('source_sha256')):
        raise ValueError('READABLE_SPAN_IDENTITY_MISMATCH')
    decode_json = span.get('kind', '').startswith('json:')
    expected = json.loads('"' + raw + '"') if decode_json else raw
    chars, offsets = [], []
    position = 0
    while position < len(raw):
        finish = position + 1
        value = raw[position]
        if decode_json and value == '\\':
            match = _ESCAPE.match(raw, position)
            if match is None:
                raise ValueError('READABLE_JSON_ESCAPE_INVALID')
            finish = match.end()
            if raw[position:finish].startswith('\\u') and 0xD800 <= int(raw[position + 2:finish], 16) <= 0xDBFF:
                second = _ESCAPE.match(raw, finish)
                if second is None or not second.group().startswith('\\u') or not 0xDC00 <= int(second.group()[2:], 16) <= 0xDFFF:
                    raise ValueError('READABLE_JSON_SURROGATE_INVALID')
                finish = second.end()
            value = json.loads('"' + raw[position:finish] + '"')
        if len(value) != 1 or 0xD800 <= ord(value) <= 0xDFFF:
            raise ValueError('READABLE_JSON_CHARACTER_INVALID')
        chars.append(value)
        offsets.append((start + position, start + finish))
        position = finish
    assert ''.join(chars) == expected
    # Collapse only whitespace; every displayed character retains its complete raw interval.
    rendered, mapping = [], []
    for value, interval in zip(chars, offsets):
        if value.isspace():
            if rendered and rendered[-1] == ' ':
                mapping[-1] = (mapping[-1][0], interval[1])
            else:
                rendered.append(' ')
                mapping.append(interval)
        else:
            rendered.append(value)
            mapping.append(interval)
    while rendered and rendered[0] == ' ':
        rendered.pop(0)
        mapping.pop(0)
    while rendered and rendered[-1] == ' ':
        rendered.pop()
        mapping.pop()
    return {**span, 'readable': ''.join(rendered), 'raw_intervals': mapping}


def raw_citation(source, span, quote):
    """Resolve an unambiguous exact readable quote; cite the original raw interval."""
    verified = readable_span(source, span)
    if (not isinstance(quote, str) or not quote or len(quote) > 10000
            or verified['readable'].find(quote) < 0
            or verified['readable'].find(quote) != verified['readable'].rfind(quote)):
        raise ValueError('READABLE_QUOTE_NOT_UNIQUE')
    index = verified['readable'].index(quote)
    start = verified['raw_intervals'][index][0]
    end = verified['raw_intervals'][index + len(quote) - 1][1]
    raw = source[start:end]
    return {'start': start, 'end': end, 'raw': raw, 'sha256': hashlib.sha256(raw.encode()).hexdigest(),
            'source_sha256': verified['source_sha256']}
