"""Independent read-only CSV/source reconciliation. No Jira writes or fake worklogs."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from docx import Document

root = Path(__file__).resolve().parents[2]
csv_path = root / 'Jira_WBS_QAG3_v7_DRAFT.csv'
with csv_path.open(encoding='utf-8-sig', newline='') as stream:
    rows = list(csv.DictReader(stream))
assert len(rows) == 329
assert all(None not in r and all(v is not None for v in r.values()) for r in rows)
assert Counter(r['Issue Type'] for r in rows) == {'Epic': 11, 'Task': 53, 'Sub-task': 265}
by_id = {r['Issue ID']: r for r in rows}
by_source = {r['Source ID']: r for r in rows}
assert len(by_id) == len(by_source) == len(rows)
source = Document(root / 'user-story-web-quan-ly-du-an-rut-gon.docx')
checked_ac = 0
for table in source.tables[2:]:
    for row in table.rows[1:]:
        source_id, story = row.cells[1].text.split('\n', 1)
        task = by_source[source_id]
        assert task['Issue Type'] == 'Task'
        assert task['Description'].startswith(story + '\n')
        assert task['Acceptance Criteria'] == row.cells[2].text
        assert by_id[task['Parent']]['Source ID'] == 'E' + row.cells[0].text.split('EPIC ')[1]
        checked_ac += len(task['Acceptance Criteria'].splitlines())
        children = [r for r in rows if r['Parent'] == task['Issue ID']]
        assert Counter(r['Proposed Role'] for r in children) == {'BA': 1, 'BE': 1, 'FE': 1, 'QA': 1, 'PM': 1}
        assert sum(int(r['Simulation Estimate Hours']) for r in children) == int(task['Simulation Estimate Hours'])
assert checked_ac == 106
for row in rows:
    assert row['Project Key'] == 'QAG3' and row['Approval'] == 'DRAFT' and row['Status'] == 'NEW'
    assert not row['Assignee'] and not row['Issue Key'] and not row['Original Estimate']
    assert row['Proposed Assignee Email']
    assert row['Source ID'] != 'E11'
    if row['Issue Type'] == 'Epic':
        assert not row['Parent'] and not row['Simulation Points']
        assert len([r for r in rows if r['Parent'] == row['Issue ID']]) in (4, 5, 6)
    elif row['Issue Type'] == 'Sub-task':
        assert by_id[row['Parent']]['Issue Type'] == 'Task'
        assert row['Checklist']
        if row['Proposed Role'] == 'PM':
            assert 'Các Subtask BA/BE/FE/QA' in row['Checklist']
        if row['Proposed Role'] == 'QA':
            assert 'Không DONE khi còn lỗi' in row['Checklist']
    for value in row.values():
        assert not value.startswith(('=', '+', '-', '@', '\t', '\r'))
simulated = sum(int(r['Simulation Estimate Hours']) for r in rows if r['Issue Type'] == 'Sub-task')
assert simulated == sum(int(r['Simulation Estimate Hours']) for r in rows if r['Issue Type'] == 'Task') == 1297
print(json.dumps({'result': 'PASS', 'rows': len(rows), 'sourceAC': checked_ac, 'simulatedHours': simulated,
                  'sha256': hashlib.sha256(csv_path.read_bytes()).hexdigest()}, ensure_ascii=False))
