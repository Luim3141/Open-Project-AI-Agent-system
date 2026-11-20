#!/usr/bin/env python3
"""QLDAPM progress tracker, Python stdlib only, no network or system mutations."""
import argparse
import datetime as dt
import json
import os
import re
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'TASKS.json'
PLAN = ROOT / 'IMPLEMENTATION_PLAN.md'
DASH = ROOT / 'PROGRESS_DASHBOARD.md'
STATUS = ['TODO', 'IN_PROGRESS', 'REVIEW', 'BLOCKED', 'DONE', 'SKIPPED']


def load():
    obj = json.loads(DATA.read_text(encoding='utf-8'))
    if 'tasks' not in obj:
        raise ValueError('TASKS.json missing tasks')
    return obj


def save(obj):
    text = json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    fd, temp = tempfile.mkstemp(dir=ROOT, prefix='.tasks-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(text)
        os.replace(temp, DATA)
    finally:
        if os.path.exists(temp):
            os.remove(temp)


def completed_dependencies(task, by_id):
    return [d for d in task['dependencies'] if by_id[d]['status'] != 'DONE']


def required_earlier_phase_incomplete(task, obj):
    phase = task['phase']
    return sorted({t['phase'] for t in obj['tasks'] if t['required'] and t['phase'] < phase and t['status'] != 'DONE'})


def check(obj):
    tasks = obj['tasks']
    ids = [t['id'] for t in tasks]
    errors = []
    if len(ids) != len(set(ids)):
        errors.append('Duplicated task ids')
    by_id = {t['id']: t for t in tasks}
    for t in tasks:
        if t['status'] not in STATUS:
            errors.append(f"{t['id']}: bad status {t['status']}")
        for d in t.get('dependencies', []):
            if d not in by_id:
                errors.append(f"{t['id']}: unknown dependency {d}")
        if t['status'] == 'DONE':
            if not t.get('evidence') or not t.get('tests'):
                errors.append(f"{t['id']}: DONE requires evidence and tests")
            if any(by_id.get(d, {}).get('status') != 'DONE' for d in t.get('dependencies', [])):
                errors.append(f"{t['id']}: DONE with incomplete dependencies")
        if t['status'] == 'SKIPPED' and not t.get('notes'):
            errors.append(f"{t['id']}: SKIPPED needs approved rationale")
    return errors


def set_state(args, obj):
    by_id = {t['id']: t for t in obj['tasks']}
    if args.task_id not in by_id:
        raise ValueError('Unknown task ID: ' + args.task_id)
    t = by_id[args.task_id]
    if args.status == 'DONE':
        unmet = completed_dependencies(t, by_id)
        if unmet:
            raise ValueError(f"Cannot DONE {t['id']}; dependencies not DONE: {', '.join(unmet)}")
        prev = required_earlier_phase_incomplete(t, obj)
        if prev:
            raise ValueError(f"Cannot DONE {t['id']}; earlier phase gates incomplete: {', '.join(prev)}")
        ev = list(t.get('evidence', [])) + (args.evidence or [])
        tests = args.tests or t.get('tests', '')
        if not ev or not tests:
            raise ValueError('DONE needs --evidence path(s) and --tests PASS or NOT_APPLICABLE:<reason>')
        if tests != 'PASS' and not (tests.startswith('NOT_APPLICABLE:') and len(tests.split(':', 1)[1].strip()) >= 10):
            raise ValueError('DONE tests must PASS or NOT_APPLICABLE:<justification>')
        if not args.note and not t.get('notes'):
            raise ValueError('DONE needs --note describing actual verification')
        for e in ev:
            # proof is a file within project/package; no fabricated URLs or text-only evidence.
            if e.startswith('http://') or e.startswith('https://'):
                raise ValueError(f'Evidence should be a local file path, not URL: {e}')
            candidates = [ROOT / e, ROOT.parents[1] / e, Path(e)]
            if not any(c.is_file() and c.stat().st_size > 0 for c in candidates):
                raise ValueError(f'Evidence file missing or empty: {e} (create real redacted report/log first)')
        t['evidence'] = list(dict.fromkeys(ev))
        t['tests'] = tests
    else:
        if args.evidence:
            t['evidence'] = list(dict.fromkeys(t.get('evidence', []) + args.evidence))
        if args.tests:
            t['tests'] = args.tests
    if args.status == 'SKIPPED' and not args.note:
        raise ValueError('SKIPPED needs --note with explicit approval or optional rationale')
    if args.status == 'BLOCKED' and not args.note:
        raise ValueError('BLOCKED needs --note with the blocker and free-only alternative')
    if args.status == 'IN_PROGRESS':
        unmet = completed_dependencies(t, by_id)
        if unmet:
            raise ValueError(f"Cannot start {t['id']}; dependencies not DONE: {', '.join(unmet)}")
        prev = required_earlier_phase_incomplete(t, obj)
        if prev:
            raise ValueError(f"Cannot start {t['id']}; earlier phase gates incomplete: {', '.join(prev)}")
    if args.note:
        t['notes'] = args.note
    t['status'] = args.status
    t['updated_at'] = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    save(obj)
    print(f"Updated {t['id']} => {args.status}")
    report(load())


def report(obj):
    tasks = obj['tasks']
    main = [x for x in tasks if x['required']]
    total = len(main)
    done = sum(x['status'] == 'DONE' for x in main)
    stats = Counter(x['status'] for x in main)
    phases = sorted(set(t['phase'] for t in tasks))
    lines = [
        '# QLDAPM — PROGRESS DASHBOARD',
        '',
        '**AUTO GENERATED** from `TASKS.json`. Chỉ trạng thái có evidence thực mới được tính DONE. Không sửa file này bằng tay.',
        '',
        f'**MVP hoàn thành: {done}/{total} task = {(100.0*done/total) if total else 0:.1f}%**  · Optional: {sum(x["status"] == "DONE" for x in tasks if not x["required"])}/{sum(not x["required"] for x in tasks)}',
        '',
        '| Status | Required count |', '|---|---:|',
    ]
    for s in STATUS:
        lines.append(f'| {s} | {stats[s]} |')
    uat = obj.get('post_deployment_uat')
    live = obj.get('gemini_live_deployment')
    monitor = obj.get('execution_monitor')
    if monitor:
        lines[2:2] = [
            f'**Execution Monitor hiện hành:** `{monitor["status"]}` — [qualification và approval]({monitor["evidence"]}).',
            '',
            'Xem bằng chứng clone, runtime Staging và deployment approval; 113 task lịch sử không thay thế nghiệm thu Monitor.',
            '',
        ]
    elif live:
        lines[2:2] = [
            f'**Gemini live hiện hành:** `{live["status"]}` — [nghiệm thu Staging]({live["evidence"]}).',
            '',
            'Local 5 users; billing BILLING_CONFIGURATION_UNCHANGED — OWNER_ATTESTED; capacity20 hoãn; Main chưa promote. '
            '113 task bên dưới là lịch sử giữ nguyên, không phải kiểm toán lại; xem extension Gemini và CSV cho live UAT.',
            '',
        ]
    elif uat:
        lines[2:2] = [
            f'**UAT hiện hành:** `{uat["status"]}` — [{uat["run"]}]({uat["evidence"]}).',
            '',
            'Local 5 users; live Gemini G2 chờ owner xác minh; capacity20 hoãn; Main chưa promote. '
            '113 task bên dưới là trạng thái lịch sử được giữ nguyên, không phải nghiệm thu lại bởi UAT.',
            '',
        ]
    lines += ['', '## Mức độ theo phase', '', '| Phase | DONE/Total | % | Gate | In progress | Blocked |', '|---|---:|---:|---|---:|---:|']
    for phase in phases:
        p = [x for x in tasks if x['phase'] == phase]
        d = sum(x['status'] == 'DONE' for x in p)
        gate = 'PASS' if all(x['status']=='DONE' for x in p if x['required']) else 'OPEN'
        if not any(x['required'] for x in p):
            gate = 'OPTIONAL'
        lines.append(f"| {phase} | {d}/{len(p)} | {100*d/len(p):.1f}% | {gate} | {sum(x['status']=='IN_PROGRESS' for x in p)} | {sum(x['status']=='BLOCKED' for x in p)} |")
    blocked = [x for x in tasks if x['status'] == 'BLOCKED']
    ongoing = [x for x in tasks if x['status'] in ('IN_PROGRESS', 'REVIEW')]
    by_id = {t['id']:t for t in tasks}
    first_open_phase = next((phase for phase in phases if any(t['required'] and t['status'] != 'DONE' for t in tasks if t['phase']==phase)), None)
    ready = [t for t in tasks if t['phase'] == first_open_phase and t['status'] == 'TODO' and not completed_dependencies(t, by_id)]
    lines += ['', '## Ready (phụ thuộc hoàn thành, gate phase hợp lệ)', '']
    if ready:
        lines += [f"- [ ] **{t['id']}** — {t['title']}" for t in ready[:12]]
    else:
        lines.append('_Chưa có task ready; xem blockers/dependencies._')
    lines += ['', '## In progress / Review', '']
    lines += [f"- **{t['id']}** `{t['status']}` — {t['title']}" for t in ongoing] or ['_Không có._']
    lines += ['', '## Blocked', '']
    lines += [f"- **{t['id']}** — {t.get('notes') or 'Missing blocker explanation'}" for t in blocked] or ['_Không có._']
    scope = '5 local users; capacity20 DEFERRED_BY_OWNER' if uat else '1–20 LAN users (MAX_ACTIVE_USERS=20)'
    provider = 'Free-only Gemini; live G2 BLOCKED_OWNER_VERIFICATION' if uat else 'Free-only Gemini API allowlist (model/project rate limits verified)'
    lines += ['', '## Chính sách tài chính và an toàn', '', f'- {provider}; Google AI Pro coding entitlement separate from API.', f'- Windows local: user MANUALLY starts Docker Desktop; previously running containers auto-recover; no Windows sign-in startup. {scope}, no GitHub Research/VPS/paid services.', '- PM-only-write; no bypass of native gates/consent/idempotency.']
    DASH.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    plan = PLAN.read_text(encoding='utf-8')
    changes = 0
    for t in tasks:
        pat = re.compile(r'(?m)^- \[(?: |x)\] (\*\*\['+re.escape(t['id'])+r'\]\*\*)')
        replacement = '- [' + ('x' if t['status'] == 'DONE' else ' ') + '] '+r'\1'
        plan, n = pat.subn(replacement, plan)
        if n != 1:
            raise ValueError(f'IMPLEMENTATION_PLAN checklist missing or duplicated ID {t["id"]}: found {n}')
        changes += n
    PLAN.write_text(plan, encoding='utf-8')
    print(f'MVP {done}/{total} ({100*done/total:.1f}%) · ready {len(ready)} · blocked {len(blocked)} · checklist synced: {changes}')


def show(obj, phase):
    tasks = [t for t in obj['tasks'] if not phase or t['phase'] == phase]
    for t in tasks:
        deps = ','.join(t['dependencies']) or '-'
        print(f"{t['id']} {t['status']:<11} [{deps}] {t['title']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('report')
    sub.add_parser('validate')
    show_cmd = sub.add_parser('show'); show_cmd.add_argument('--phase', default=None)
    sc = sub.add_parser('set'); sc.add_argument('task_id'); sc.add_argument('status', choices=STATUS)
    sc.add_argument('--evidence', action='append', default=[])
    sc.add_argument('--tests', default=''); sc.add_argument('--note', default='')
    args = parser.parse_args()
    obj = load()
    errors = check(obj)
    if errors:
        for e in errors:
            print('ERROR:',e, file=sys.stderr)
        if args.action != 'show':
            return 1
    if args.action == 'validate':
        print(f"Valid task registry: {len(obj['tasks'])} tasks, {sum(x['required'] for x in obj['tasks'])} MVP required; errors={len(errors)}")
        return 0 if not errors else 1
    if args.action == 'report':
        report(obj)
    elif args.action == 'show':
        show(obj, args.phase)
    elif args.action == 'set':
        set_state(args,obj)
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print('ERROR:',e,file=sys.stderr)
        sys.exit(2)
