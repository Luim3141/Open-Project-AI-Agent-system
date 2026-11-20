"""Keep retrieved sources separate from an answer until answerability is qualified."""


def retrieval_response(items, dense_state):
    """Do not turn relevance, an exact quote, or an HTTP success into a verified answer."""
    if not items:
        state = 'NO_EVIDENCE'
        reason = 'Không tìm thấy bằng chứng phù hợp trong các nguồn hiện hành mà bạn được phép đọc.'
        code = 'NO_AUTHORIZED_CURRENT_EVIDENCE'
    else:
        state = 'UNVERIFIED_RETRIEVAL'
        reason = 'Đã tìm thấy nguồn liên quan. Bộ kiểm chứng khả năng trả lời chưa đạt quality gate nên chưa tạo câu trả lời.'
        code = 'ANSWERABILITY_NOT_QUALIFIED'
    return {
        'answerability': {'state': state, 'reason': reason},
        'answer': None,
        'reason_code': code,
        'retrieval_state': dense_state,
    }
