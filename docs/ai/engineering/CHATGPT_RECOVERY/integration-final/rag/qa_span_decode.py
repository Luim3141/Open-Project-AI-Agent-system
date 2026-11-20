"""Research-only extractive QA decoding; relevance and extraction do not prove truth."""
import math


def decode_span(source, offsets, sequence_ids, start_logits, end_logits, *, max_answer_tokens=64):
    """Select a contiguous context-only span, or explicit CLS/null; no tuned threshold."""
    size = len(offsets)
    if (not isinstance(source, str) or not size or any(len(values) != size for values in (sequence_ids, start_logits, end_logits))
            or type(max_answer_tokens) is not int or not 1 <= max_answer_tokens <= 128):
        raise ValueError('QA_DECODER_SHAPE_INVALID')
    if any(not math.isfinite(float(value)) for value in (*start_logits, *end_logits)):
        raise ValueError('QA_LOGITS_NONFINITE')
    null = float(start_logits[0]) + float(end_logits[0])
    best = None
    for start in range(size):
        if sequence_ids[start] != 1:
            continue
        a, b = offsets[start]
        if not (type(a) is int and type(b) is int and 0 <= a < b <= len(source)):
            continue
        for end in range(start, min(size, start + max_answer_tokens)):
            if sequence_ids[end] != 1:
                break
            c, d = offsets[end]
            if not (type(c) is int and type(d) is int and a <= c < d <= len(source)):
                continue
            score = float(start_logits[start]) + float(end_logits[end])
            if best is None or score > best['score']:
                best = {'start': a, 'end': d, 'text': source[a:d], 'score': score, 'null_score': null, 'margin': score - null}
    if best is None or best['score'] <= null:
        return None
    return best
