"""Independent synthetic pairs; no project source or held-out benchmark access."""
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
PRIVATE = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator/integration-final-qa-reader'
WORK = PRIVATE / 'synthetic-unpadded'
DATA, OUTPUT = WORK / 'input', WORK / 'output'
DATA.mkdir(parents=True, exist_ok=True)
OUTPUT.mkdir(parents=True, exist_ok=True)
assert not (OUTPUT / 'scores.json').exists(), 'PRESERVE_PREVIOUS_EXPERIMENT'
cases = [
    ('en-duration', 'How many days may a reader borrow a book?', 'A reader may borrow a book for 14 days.', '14 days'),
    ('vi-duration', 'Độc giả mượn sách trong bao nhiêu ngày?', 'Độc giả được mượn sách trong 14 ngày.', '14 ngày'),
    ('en-absent', 'How much is the penalty for returning a book late?', 'A reader may borrow a book for 14 days.', None),
    ('vi-absent', 'Mức phạt trả sách quá hạn là bao nhiêu tiền?', 'Độc giả được mượn sách trong 14 ngày.', None),
    ('en-technical-negative', 'Which Redis cluster stores the borrowed books?', 'The library stores its books in SQLite.', None),
    ('vi-technical-negative', 'Cụm Redis nào lưu thông tin mượn sách?', 'Thư viện lưu thông tin sách trong SQLite.', None),
    ('en-condition', 'When does the valve close?', 'The valve closes when pressure exceeds 80 psi.', 'pressure exceeds 80 psi'),
    ('vi-condition', 'Van đóng khi nào?', 'Van đóng khi áp suất vượt quá 80 psi.', 'áp suất vượt quá 80 psi'),
]
(DATA / 'pairs.json').write_text(json.dumps({'pairs': [{'id': identity, 'query': query, 'passage': passage} for identity, query, passage, _ in cases]}, ensure_ascii=False), encoding='utf-8')
previous = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator/phase2-reranker'
mount = lambda source, target, ro=True: ['--mount', f'type=bind,source={source.resolve()},target={target}' + (',readonly' if ro else '')]
command = ['docker', 'run', '--rm', '--network', 'none', '--cpus', '1', '--memory', '1280m']
command += mount(PRIVATE / 'assets', '/model') + mount(previous / 'venv', '/experiment/venv')
command += mount(ROOT, '/src') + mount(DATA, '/data') + mount(OUTPUT, '/output', False)
command += ['--entrypoint', '/experiment/venv/bin/python', 'sha256:698db791f8e96e8c0db6253457a75348eade5dff3c89e2d1ae314083387fcceb', '/src/qa_reader_offline.py']
run = subprocess.run(command, capture_output=True, timeout=90)
if run.returncode:
    raise RuntimeError('QA_SMOKE_FAILED: ' + run.stderr.decode(errors='replace')[-1500:])
result = json.loads((OUTPUT / 'scores.json').read_text(encoding='utf-8'))
rows = {row['id']: row for row in result['rows']}
checks = {identity: (rows[identity]['answer'] is None if expected is None else
                    rows[identity]['answer'] is not None and expected in rows[identity]['answer']['text'])
          for identity, _, _, expected in cases}
public = {key: value for key, value in result.items() if key != 'rows'}
public.update(checks=checks, status='SYNTHETIC_ONLY_NOT_ACCEPTANCE', rows=result['rows'])
(ROOT / 'qa-reader-synthetic-unpadded.json').write_text(json.dumps(public, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(public, ensure_ascii=False))
