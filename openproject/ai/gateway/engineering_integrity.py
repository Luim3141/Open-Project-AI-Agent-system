"""Read projection only: preserve conflicting historical records for reconciliation."""
def observed_result(result, agent_state):
    if result.get('status') == 'succeeded' and agent_state in {'FAILED', 'CANCELLED'}:
        return {**result, 'status': 'blocked', 'persisted_status': result['status'],
                'integrity_state': 'RECONCILIATION_REQUIRED',
                'error': 'HISTORICAL_OUTCOME_RECONCILIATION_REQUIRED',
                'text': 'Persisted success mâu thuẫn với agent state. Cần đối soát receipts/checkpoint; chưa xác nhận delivery và không tự replay.'}
    return result
