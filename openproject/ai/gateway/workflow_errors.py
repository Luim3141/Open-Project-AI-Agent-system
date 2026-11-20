"""Fixed workflow/execution metadata only. Raw n8n error messages never cross this boundary."""
from datetime import datetime
import re
from zoneinfo import ZoneInfo


def parse(command):
    match = re.fullmatch(r'error:(qldapmManualStatus|qldapmDailyBrief):([1-9][0-9]{0,19}|activation):(\d{4}-\d{2}-\d{2})', command['request_key'])
    day = datetime.fromtimestamp(command['issued_at'], ZoneInfo('Asia/Bangkok')).date().isoformat()
    if not match or match[3] != day:
        raise ValueError('FIXED_WORKFLOW_ERROR_KEY_REQUIRED')
    return {'workflow_id': match[1], 'execution_id': match[2], 'day': day, 'error_code': 'WORKFLOW_FAILED'}
