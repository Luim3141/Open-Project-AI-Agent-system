import hashlib
import json
import re
import secrets
import sqlite3
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import uuid
from pathlib import Path
from contextlib import contextmanager, nullcontext
from . import RUN_TIMEOUT_SECONDS, RUN_ROUND_LIMITS


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def pacific_day(now):
    start = datetime.fromtimestamp(now, ZoneInfo("America/Los_Angeles")).replace(hour=0, minute=0, second=0, microsecond=0)
    return start.timestamp(), (start + timedelta(days=1)).timestamp()


class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
              CREATE TABLE IF NOT EXISTS tokens(hash TEXT PRIMARY KEY,user_id INTEGER,role TEXT,expires REAL,revoked INTEGER DEFAULT 0);
              CREATE TABLE IF NOT EXISTS audit(id TEXT PRIMARY KEY,at REAL,actor INTEGER,action TEXT,target TEXT,outcome TEXT);
              CREATE TABLE IF NOT EXISTS requests(actor INTEGER,key TEXT,hash TEXT,state TEXT,result TEXT,PRIMARY KEY(actor,key));
              CREATE TABLE IF NOT EXISTS knowledge_sync(id TEXT PRIMARY KEY,actor INTEGER NOT NULL,native_id INTEGER NOT NULL CHECK(native_id>0),request_key TEXT NOT NULL,state TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,next_at REAL NOT NULL DEFAULT 0,lease TEXT,lease_until REAL,error TEXT,result TEXT,UNIQUE(actor,request_key));
              CREATE TABLE IF NOT EXISTS operational_reports(id TEXT PRIMARY KEY,actor INTEGER NOT NULL,project INTEGER NOT NULL,kind TEXT NOT NULL,hash TEXT NOT NULL,document TEXT NOT NULL,refs TEXT NOT NULL,created REAL NOT NULL,last_seen REAL NOT NULL,UNIQUE(actor,project,kind,hash));
              CREATE TABLE IF NOT EXISTS native_index_cursor(actor INTEGER NOT NULL,project INTEGER NOT NULL,native_id INTEGER NOT NULL,version INTEGER NOT NULL,hash TEXT NOT NULL,visible INTEGER NOT NULL,observed REAL NOT NULL,PRIMARY KEY(actor,project,native_id));
              CREATE TABLE IF NOT EXISTS native_index_scans(actor INTEGER NOT NULL,project INTEGER NOT NULL,generation INTEGER NOT NULL,document TEXT NOT NULL,PRIMARY KEY(actor,project));
              CREATE TABLE IF NOT EXISTS knowledge_feedback(id TEXT PRIMARY KEY,actor INTEGER NOT NULL,project INTEGER NOT NULL,document TEXT NOT NULL,hash TEXT NOT NULL,state TEXT NOT NULL,created REAL NOT NULL,reviewer INTEGER,result TEXT);
              CREATE TABLE IF NOT EXISTS qa_evidence(id TEXT PRIMARY KEY,actor INTEGER NOT NULL,project INTEGER NOT NULL,document TEXT NOT NULL,hash TEXT NOT NULL,state TEXT NOT NULL,created REAL NOT NULL,reviewer INTEGER);
              CREATE TABLE IF NOT EXISTS qa_test_runs(id TEXT PRIMARY KEY,actor INTEGER NOT NULL,project INTEGER NOT NULL,document TEXT NOT NULL,created REAL NOT NULL);
              CREATE TABLE IF NOT EXISTS native_phase_documents(id TEXT PRIMARY KEY,actor INTEGER NOT NULL,project INTEGER NOT NULL,document TEXT NOT NULL,hash TEXT NOT NULL,state TEXT NOT NULL,created REAL NOT NULL);
              CREATE TABLE IF NOT EXISTS native_phase_reviews(artifact TEXT PRIMARY KEY REFERENCES native_phase_documents(id),document TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS qa_evidence_reviews(evidence TEXT NOT NULL,stage TEXT NOT NULL,document TEXT NOT NULL,PRIMARY KEY(evidence,stage));
              CREATE TABLE IF NOT EXISTS local_deliveries(id TEXT PRIMARY KEY,document TEXT NOT NULL,hash TEXT NOT NULL,state TEXT NOT NULL,attempts INTEGER NOT NULL,next_at REAL NOT NULL,error TEXT);
              CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,actor INTEGER,action TEXT,payload TEXT,hash TEXT,state TEXT,result TEXT,created REAL);
              CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY,actor INTEGER,payload TEXT,hash TEXT,expires REAL,state TEXT,result TEXT);
              CREATE TABLE IF NOT EXISTS ai_runs(id TEXT PRIMARY KEY,actor INTEGER,state TEXT,result TEXT,created REAL);
              CREATE TABLE IF NOT EXISTS ai_queue(id TEXT PRIMARY KEY,actor INTEGER,payload TEXT,state TEXT,created REAL,lease_until REAL,served INTEGER DEFAULT 0,kind TEXT);
              CREATE INDEX IF NOT EXISTS ai_queue_pending ON ai_queue(state,actor,created);
              CREATE TABLE IF NOT EXISTS agent_tasks(id TEXT PRIMARY KEY,actor INTEGER NOT NULL,project INTEGER NOT NULL,conversation TEXT NOT NULL,document TEXT NOT NULL,expires REAL NOT NULL);
              CREATE TABLE IF NOT EXISTS agent_runs(id TEXT PRIMARY KEY,task_id TEXT NOT NULL,actor INTEGER NOT NULL,project INTEGER NOT NULL,document TEXT NOT NULL);
              CREATE INDEX IF NOT EXISTS agent_runs_scope ON agent_runs(actor,project);
              CREATE TABLE IF NOT EXISTS ui_nonces(nonce TEXT PRIMARY KEY,expires REAL);
              CREATE TABLE IF NOT EXISTS automation_runs(id TEXT PRIMARY KEY,request_key TEXT NOT NULL UNIQUE,hash TEXT NOT NULL,created REAL NOT NULL,receipt TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS automation_nonces(nonce TEXT PRIMARY KEY,hash TEXT NOT NULL,expires REAL NOT NULL);
              CREATE TABLE IF NOT EXISTS daily_briefs(actor INTEGER NOT NULL,project INTEGER NOT NULL,day TEXT NOT NULL,document TEXT NOT NULL,PRIMARY KEY(actor,project,day));
              CREATE TABLE IF NOT EXISTS gemini_usage(project TEXT,at REAL,input_tokens INTEGER);
              CREATE TABLE IF NOT EXISTS gemini_blocks(project TEXT PRIMARY KEY,reason TEXT);
              CREATE TABLE IF NOT EXISTS gemini_recovery(project TEXT PRIMARY KEY,reason TEXT,retry_at REAL);
              CREATE TABLE IF NOT EXISTS gemini_call_receipts(id TEXT PRIMARY KEY,project TEXT NOT NULL,actor INTEGER,run_id TEXT,document TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS business_runs(id TEXT PRIMARY KEY,actor INTEGER NOT NULL,project INTEGER NOT NULL,document TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS wbs_documents(id TEXT PRIMARY KEY,actor INTEGER NOT NULL,project INTEGER NOT NULL,hash TEXT NOT NULL,document TEXT NOT NULL);
              CREATE INDEX IF NOT EXISTS gemini_receipt_run ON gemini_call_receipts(actor,run_id);
              CREATE TABLE IF NOT EXISTS execution_events(sequence INTEGER PRIMARY KEY AUTOINCREMENT,event_id TEXT NOT NULL UNIQUE,run_id TEXT NOT NULL,actor INTEGER NOT NULL,project INTEGER NOT NULL,document TEXT NOT NULL);
              CREATE INDEX IF NOT EXISTS execution_event_scope ON execution_events(actor,project,run_id,sequence);
              CREATE INDEX IF NOT EXISTS gemini_usage_time ON gemini_usage(project,at);
            """)
            audit_columns = {row[1] for row in db.execute("PRAGMA table_info(audit)")}
            for name, declaration in (("version", "TEXT"), ("project_id", "INTEGER"), ("run_id", "TEXT"), ("task_id", "TEXT"), ("trace_id", "TEXT")):
                if name not in audit_columns:
                    db.execute("ALTER TABLE audit ADD COLUMN " + name + " " + declaration)
            if "payload" not in {row[1] for row in db.execute("PRAGMA table_info(requests)")}:
                db.execute("ALTER TABLE requests ADD COLUMN payload TEXT")
            if "request_key" not in {row[1] for row in db.execute("PRAGMA table_info(jobs)")}:
                db.execute("ALTER TABLE jobs ADD COLUMN request_key TEXT")
                db.execute("CREATE UNIQUE INDEX jobs_request_key ON jobs(actor,request_key)")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.root / "gateway.sqlite", timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        try:
            with db:
                yield db
        finally:
            db.close()

    def accept_automation_status(self, command):
        if command['kind'] != 'status':
            raise ValueError('STATUS_COMMAND_REQUIRED')
        return self.begin_automation(command)[0]

    def begin_automation(self, command, project=None, targets=None):
        if command['kind'] not in {'status', 'daily_brief', 'weekly_summary', 'workflow_error'}:
            raise ValueError('KNOWN_AUTOMATION_KIND_REQUIRED')
        error = None
        if command['kind'] == 'workflow_error':
            from .workflow_errors import parse
            if type(project) is not int or project <= 0:
                raise PermissionError('WORKFLOW_PROJECT_REQUIRED')
            error = parse(command)
        semantic_hash = digest(canonical({key: command[key] for key in ('version', 'kind', 'request_key')}))
        body_hash = digest(canonical(command))
        now = time.time()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            now = time.time()
            if not -15 <= now - command['issued_at'] <= 60:
                raise PermissionError('COMMAND_EXPIRED_OR_FUTURE')
            db.execute('DELETE FROM automation_nonces WHERE expires<?', (now,))
            nonce = db.execute('SELECT hash FROM automation_nonces WHERE nonce=?', (command['nonce'],)).fetchone()
            if nonce and nonce['hash'] != body_hash:
                raise PermissionError('AUTOMATION_NONCE_REPLAY_DENIED')
            existing = db.execute('SELECT hash,receipt FROM automation_runs WHERE request_key=?', (command['request_key'],)).fetchone()
            if existing and existing['hash'] != semantic_hash:
                raise PermissionError('AUTOMATION_IDEMPOTENCY_CONFLICT')
            if nonce and not existing:
                raise PermissionError('AUTOMATION_RECEIPT_MISSING; reconcile, never replay')
            if not nonce:
                db.execute('INSERT INTO automation_nonces VALUES(?,?,?)', (command['nonce'], body_hash, command['issued_at'] + 75))
            if existing:
                return json.loads(existing['receipt']), False
            identifier = str(uuid.uuid4())
            receipt = {'run_id': identifier, 'trace_id': identifier, 'request_key': command['request_key'],
                       'kind': command['kind'], 'state': 'RUNNING' if command['kind'] in {'daily_brief','weekly_summary'} else 'COMPLETED', 'authority': 'machine', 'actor_id': None,
                       'component': 'gateway', 'status': 'ok', 'model_calls': 0, 'native_write_allowed': False}
            if command['kind'] in {'daily_brief','weekly_summary'}:
                target_count = targets if targets is not None else command.get('targets', 5)
                receipt.update(project_id=project, status='COLLECTING', targets=target_count)
            if error is not None:
                receipt.update(project_id=project, status='WORKFLOW_FAILED', **error)
            db.execute('INSERT INTO automation_runs VALUES(?,?,?,?,?)', (identifier, command['request_key'], semantic_hash, now, canonical(receipt)))
            db.execute('INSERT INTO audit(id,at,actor,action,target,outcome,run_id,trace_id) VALUES(?,?,NULL,?,?,?,?,?)',
                       (identifier, now, 'automation_command', command['kind'], 'ok', identifier, identifier))
            return receipt, True

    def workflow_alerts(self, project):
        with self.connect() as db:
            rows = db.execute("SELECT created,receipt FROM automation_runs WHERE json_extract(receipt,'$.kind')='workflow_error' AND json_extract(receipt,'$.project_id')=? ORDER BY created DESC LIMIT 10", (project,)).fetchall()
            alerts = []
            for row in rows:
                receipt = json.loads(row['receipt'])
                alerts.append({**{key: receipt[key] for key in ('run_id', 'trace_id', 'workflow_id', 'execution_id', 'day', 'error_code')},
                               'observed_at': row['created']})
            return alerts

    def daily_brief(self, actor, project, day):
        with self.connect() as db:
            row = db.execute('SELECT document FROM daily_briefs WHERE actor=? AND project=? AND day=?', (actor, project, day)).fetchone()
            return json.loads(row['document']) if row else None

    def finish_daily_brief(self, identifier, reports):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT receipt FROM automation_runs WHERE id=?', (identifier,)).fetchone()
            receipt = json.loads(row['receipt'])
            if receipt['kind'] != 'daily_brief' or receipt['state'] != 'RUNNING':
                raise PermissionError('DAILY_RUN_NOT_COLLECTING')
            if len(reports) == 0 or len(reports) > 20 or len({report['actor'] for report in reports}) != len(reports):
                raise ValueError('VALID_ACTOR_REPORTS_REQUIRED')
            expected_targets = receipt.get('targets', len(reports))
            for report in reports:
                if (report['project'] != receipt['project_id'] or report['run_id'] != identifier
                        or 'daily:' + report['day'] != receipt['request_key'] or report['state'] not in {'READY', 'DENIED', 'OFFLINE'}):
                    raise PermissionError('DAILY_REPORT_SCOPE_MISMATCH')
                db.execute('INSERT INTO daily_briefs VALUES(?,?,?,?) ON CONFLICT(actor,project,day) DO UPDATE SET document=excluded.document',
                           (report['actor'], report['project'], report['day'], canonical(report)))
                from .notification_delivery import enqueue
                enqueue(db,'daily_brief',report['day'],report['actor'],report['project'],digest(canonical(report)))
                db.execute('INSERT INTO audit(id,at,actor,action,target,outcome,project_id,run_id,trace_id) VALUES(?,?,?,?,?,?,?,?,?)',
                           (str(uuid.uuid4()), time.time(), report['actor'], 'daily_brief_snapshot', 'native', report['state'], report['project'], identifier, identifier))
            ready = sum(report['state'] == 'READY' for report in reports)
            receipt.update(state='COMPLETED', status='READY' if ready == expected_targets else 'PARTIAL', ready=ready, unavailable=expected_targets-ready)
            db.execute('UPDATE automation_runs SET receipt=? WHERE id=?', (canonical(receipt), identifier))
            return receipt

    def fail_daily_brief(self, identifier=None):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            rows = db.execute('SELECT id,receipt FROM automation_runs' + (' WHERE id=?' if identifier else ''), (identifier,) if identifier else ()).fetchall()
            failed = 0
            for row in rows:
                receipt = json.loads(row['receipt'])
                if receipt['kind'] in {'daily_brief','weekly_summary'} and receipt['state'] == 'RUNNING':
                    receipt.update(state='FAILED', status='INTERRUPTED_NO_REPLAY', reconcile_required=True)
                    db.execute('UPDATE automation_runs SET receipt=? WHERE id=?', (canonical(receipt), row['id']))
                    db.execute('INSERT INTO audit(id,at,actor,action,target,outcome,run_id,trace_id) VALUES(?,?,NULL,?,?,?,?,?)',
                               (str(uuid.uuid4()), time.time(), 'automation_recovery', receipt['kind'], 'FAILED_NO_REPLAY', row['id'], row['id']))
                    failed += 1
            return failed

    def finish_weekly_summary(self, identifier, reports):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT receipt FROM automation_runs WHERE id=?',(identifier,)).fetchone()
            receipt=json.loads(row['receipt']) if row else {}
            if receipt.get('kind')!='weekly_summary' or receipt.get('state')!='RUNNING':
                raise PermissionError('WEEKLY_RUN_NOT_COLLECTING')
            if len(reports)!=receipt['targets'] or not 1<=len(reports)<=20 or len({r['actor'] for r in reports})!=len(reports):
                raise ValueError('VALID_WEEKLY_TARGET_REPORTS_REQUIRED')
            for report in reports:
                if report['state'] not in {'READY','DENIED','OFFLINE'}:
                    raise ValueError('VALID_WEEKLY_REPORT_STATE_REQUIRED')
                if report['state']=='READY':
                    saved=db.execute("SELECT hash FROM operational_reports WHERE id=? AND actor=? AND project=? AND kind='weekly_summary'",
                        (report['report_id'],report['actor'],receipt['project_id'])).fetchone()
                    if saved is None or saved['hash']!=report['report_sha256']:
                        raise PermissionError('WEEKLY_REPORT_PERSISTENCE_REQUIRED')
            ready=sum(r['state']=='READY' for r in reports)
            receipt.update(state='COMPLETED',status='READY' if ready==len(reports) else 'PARTIAL',
                ready=ready,unavailable=len(reports)-ready,reports=reports)
            db.execute('UPDATE automation_runs SET receipt=? WHERE id=?',(canonical(receipt),identifier))
            return receipt

    def issue_token(self, user_id, role, op_token, ttl=86400):
        path = self.root / "credentials.json"
        credentials = json.loads(path.read_text()) if path.exists() else {}
        credentials[str(user_id)] = op_token
        temporary = path.with_suffix(".tmp")
        temporary.write_text(canonical(credentials), encoding="utf-8")
        temporary.replace(path)
        token = secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute("INSERT INTO tokens(hash,user_id,role,expires) VALUES(?,?,?,?)",
                       (digest(token), user_id, role, time.time() + ttl))
        return token

    def create_agent_task(self, actor, project, task):
        from .agent_models import AgentTask
        task = AgentTask.from_json(task.model_dump_json())
        if (task.actor_id, task.project_id) != (actor, project):
            raise PermissionError("AGENT_TASK_SCOPE_MISMATCH")
        if task.expires_at <= time.time():
            raise ValueError("AGENT_TASK_EXPIRED")
        document = task.model_dump_json()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO agent_tasks VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING",
                       (task.task_id, actor, project, task.conversation_id, document, task.expires_at))
            row = db.execute("SELECT actor,project,document FROM agent_tasks WHERE id=?", (task.task_id,)).fetchone()
            if (row["actor"], row["project"]) != (actor, project):
                raise PermissionError("AGENT_TASK_NOT_FOUND")
            if row["document"] != document:
                raise ValueError("AGENT_TASK_ID_REUSED")
        return task

    def agent_task(self, actor, project, identifier):
        from .agent_models import AgentTask
        with self.connect() as db:
            row = db.execute("SELECT document FROM agent_tasks WHERE id=? AND actor=? AND project=?", (identifier, actor, project)).fetchone()
            if not row and actor == 18 and project in (5, 6):
                row = db.execute("SELECT document FROM agent_tasks WHERE id=? AND project=?", (identifier, project)).fetchone()
        if not row:
            raise PermissionError("AGENT_TASK_NOT_FOUND")
        task = AgentTask.from_json(row["document"])
        if (task.task_id, task.project_id) != (identifier, project):
            raise ValueError("AGENT_TASK_SCOPE_MISMATCH")
        if task.actor_id != actor and not (actor == 18 and project in (5, 6)):
            raise ValueError("AGENT_TASK_SCOPE_MISMATCH")
        return task

    def create_agent_run(self, actor, project, run):
        from .agent_models import AgentRun, AgentTask
        run = AgentRun.from_json(run.model_dump_json())
        if (run.actor_id, run.project_id) != (actor, project):
            raise PermissionError("AGENT_RUN_SCOPE_MISMATCH")
        if run.state != "QUEUED" or run.result is not None:
            raise ValueError("AGENT_NEW_RUN_MUST_BE_QUEUED")
        document = run.model_dump_json()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT document FROM agent_tasks WHERE id=? AND actor=? AND project=?", (run.task_id, actor, project)).fetchone()
            if not row:
                raise PermissionError("AGENT_TASK_NOT_FOUND")
            task = AgentTask.from_json(row["document"])
            if (task.task_id, task.actor_id, task.project_id) != (run.task_id, actor, project):
                raise ValueError("AGENT_TASK_SCOPE_MISMATCH")
            if task.expires_at <= time.time():
                raise ValueError("AGENT_TASK_EXPIRED")
            db.execute("INSERT INTO agent_runs VALUES(?,?,?,?,?) ON CONFLICT(id) DO NOTHING",
                       (run.run_id, run.task_id, actor, project, document))
            old = db.execute("SELECT actor,project,document FROM agent_runs WHERE id=?", (run.run_id,)).fetchone()
            if (old["actor"], old["project"]) != (actor, project):
                raise PermissionError("AGENT_RUN_NOT_FOUND")
            if old["document"] != document:
                raise ValueError("AGENT_RUN_ID_REUSED")
        return run

    def agent_run(self, actor, project, identifier):
        from .agent_models import AgentRun
        with self.connect() as db:
            row = db.execute("SELECT document FROM agent_runs WHERE id=? AND actor=? AND project=?", (identifier, actor, project)).fetchone()
            if not row and actor == 18 and project in (5, 6):
                row = db.execute("SELECT document FROM agent_runs WHERE id=? AND project=?", (identifier, project)).fetchone()
        if not row:
            raise PermissionError("AGENT_RUN_NOT_FOUND")
        run = AgentRun.from_json(row["document"])
        if (run.run_id, run.project_id) != (identifier, project):
            raise ValueError("AGENT_RUN_SCOPE_MISMATCH")
        if run.actor_id != actor and not (actor == 18 and project in (5, 6)):
            raise ValueError("AGENT_RUN_SCOPE_MISMATCH")
        return run

    @staticmethod
    def agent_page_bounds(limit, offset):
        if type(limit) is not int or not 1 <= limit <= 50 or type(offset) is not int or not 0 <= offset <= 2147483647:
            raise ValueError("AGENT_PAGE_LIMIT_1_50_OFFSET_NONNEGATIVE_INT")

    def agent_progress(self, actor, project, identifier):
        from .agent_models import AgentProgress
        run = self.agent_run(actor, project, identifier)
        with self.connect() as db:
            receipt = db.execute("SELECT id FROM ai_runs WHERE id=? AND (actor=? OR (?=18 AND ? IN (5, 6)))", (identifier, run.actor_id, actor, project)).fetchone()
        return AgentProgress.from_run(run, receipt["id"] if receipt else None).model_dump()

    def agent_runs_page(self, actor, project, limit=20, offset=0):
        from .agent_models import AgentRun, AgentProgress, AgentRunPage
        self.agent_page_bounds(limit, offset)
        is_owner = (actor == 18 and project in (5, 6))
        with self.connect() as db:
            if is_owner:
                total = db.execute("SELECT COUNT(*) FROM agent_runs WHERE project=?", (project,)).fetchone()[0]
                rows = db.execute("""SELECT a.id,a.document,r.id AS receipt_id FROM agent_runs a
                    LEFT JOIN ai_runs r ON r.id=a.id AND r.actor=a.actor
                    WHERE a.project=? ORDER BY a.rowid DESC LIMIT ? OFFSET ?""", (project, limit, offset)).fetchall()
            else:
                total = db.execute("SELECT COUNT(*) FROM agent_runs WHERE actor=? AND project=?", (actor, project)).fetchone()[0]
                rows = db.execute("""SELECT a.id,a.document,r.id AS receipt_id FROM agent_runs a
                    LEFT JOIN ai_runs r ON r.id=a.id AND r.actor=a.actor
                    WHERE a.actor=? AND a.project=? ORDER BY a.rowid DESC LIMIT ? OFFSET ?""", (actor, project, limit, offset)).fetchall()
        items = []
        for row in rows:
            run = AgentRun.from_json(row["document"])
            if (run.run_id, run.project_id) != (row["id"], project):
                raise ValueError("AGENT_RUN_SCOPE_MISMATCH")
            if not is_owner and run.actor_id != actor:
                raise ValueError("AGENT_RUN_SCOPE_MISMATCH")
            items.append(AgentProgress.from_run(run, row["receipt_id"]))
        return AgentRunPage(items=items, total=total, limit=limit, offset=offset,
            next_offset=offset + len(items) if offset + len(items) < total else None).model_dump()

    def agent_trace_page(self, actor, project, identifier, limit=20, offset=0):
        from .agent_models import AgentTraceEvent, AgentTracePage
        self.agent_page_bounds(limit, offset)
        run = self.agent_run(actor, project, identifier)
        is_owner = (actor == 18 and project in (5, 6))
        with self.connect() as db:
            if is_owner:
                total = db.execute("SELECT COUNT(*) FROM audit WHERE project_id=? AND run_id=?", (project, identifier)).fetchone()[0]
                rows = db.execute("""SELECT id AS event_id,at,actor AS actor_id,project_id,run_id,task_id,trace_id,action,target,outcome,version
                    FROM audit WHERE project_id=? AND run_id=? ORDER BY at,id LIMIT ? OFFSET ?""",
                    (project, identifier, limit, offset)).fetchall()
            else:
                total = db.execute("SELECT COUNT(*) FROM audit WHERE actor=? AND project_id=? AND run_id=?", (actor, project, identifier)).fetchone()[0]
                rows = db.execute("""SELECT id AS event_id,at,actor AS actor_id,project_id,run_id,task_id,trace_id,action,target,outcome,version
                    FROM audit WHERE actor=? AND project_id=? AND run_id=? ORDER BY at,id LIMIT ? OFFSET ?""",
                    (actor, project, identifier, limit, offset)).fetchall()
        items = [AgentTraceEvent.model_validate(dict(row)) for row in rows]
        return AgentTracePage(items=items, total=total, limit=limit, offset=offset,
            next_offset=offset + len(items) if offset + len(items) < total else None).model_dump()

    def execution_records(self,actor,project,identifier):
        from .execution_events import ExecutionEvent
        run=self.agent_run(actor,project,identifier)
        is_owner = (actor == 18 and project in (5, 6))
        with self.connect() as db:
            if is_owner:
                rows=db.execute('SELECT sequence,document FROM execution_events WHERE project=? AND run_id=? ORDER BY sequence LIMIT 200',(project,identifier)).fetchall()
                receipts=db.execute('SELECT document FROM gemini_call_receipts WHERE run_id=? ORDER BY rowid LIMIT 200',(identifier,)).fetchall()
            else:
                rows=db.execute('SELECT sequence,document FROM execution_events WHERE actor=? AND project=? AND run_id=? ORDER BY sequence LIMIT 200',(actor,project,identifier)).fetchall()
                receipts=db.execute('SELECT document FROM gemini_call_receipts WHERE actor=? AND run_id=? ORDER BY rowid LIMIT 200',(actor,identifier)).fetchall()
        events=[ExecutionEvent.model_validate({**json.loads(row['document']),'sequence':row['sequence']}).model_dump() for row in rows]
        if any(e['run_id']!=identifier or e['trace_id']!=run.trace_id for e in events):raise PermissionError('EXECUTION_EVENT_SCOPE_MISMATCH')
        if not is_owner and any(json.loads(r[0]).get('actor')!=actor or json.loads(r[0]).get('run_id')!=identifier for r in receipts):raise PermissionError('EXECUTION_RECEIPT_SCOPE_MISMATCH')
        if is_owner and any(json.loads(r[0]).get('run_id')!=identifier for r in receipts):raise PermissionError('EXECUTION_RECEIPT_SCOPE_MISMATCH')
        return events,[json.loads(r[0]) for r in receipts]

    def execution_history(self,actor,project,limit=10,offset=0,search='',state='ALL',order='desc'):
        from .business_runs import history
        return history(self,actor,project,limit,offset,search,state,order)

    def transition_agent_run(self, actor, project, identifier, expected, state, result=None):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            return self._transition_agent_run(db, actor, project, identifier, expected, state, result)

    @staticmethod
    def _transition_agent_run(db, actor, project, identifier, expected, state, result=None):
        from .agent_models import AGENT_TRANSITIONS, AgentRun, AgentResult
        if not isinstance(expected, str) or not isinstance(state, str) or state not in AGENT_TRANSITIONS.get(expected, set()):
            raise ValueError("AGENT_TRANSITION_DENIED; started or terminal runs are never requeued")
        terminal = state in {"REVIEW", "FAILED", "COMPLETED"}
        if terminal != (result is not None):
            raise ValueError("AGENT_TERMINAL_RESULT_REQUIRED")
        if result is not None:
            result = AgentResult.from_json(result.model_dump_json())
        now = time.time()
        row = db.execute("SELECT document FROM agent_runs WHERE id=? AND actor=? AND project=?", (identifier, actor, project)).fetchone()
        if not row:
            raise PermissionError("AGENT_RUN_NOT_FOUND")
        run = AgentRun.from_json(row["document"])
        if (run.run_id, run.actor_id, run.project_id) != (identifier, actor, project):
            raise ValueError("AGENT_RUN_SCOPE_MISMATCH")
        if run.state != expected:
            raise ValueError("AGENT_STATE_CHANGED; inspect current run, no blind retry")
        if state == "RUNNING":
            task = db.execute("SELECT expires FROM agent_tasks WHERE id=? AND actor=? AND project=?", (run.task_id, actor, project)).fetchone()
            if not task or task["expires"] <= now:
                raise ValueError("AGENT_TASK_EXPIRED_OR_NOT_FOUND")
        updated = AgentRun.model_validate({**run.model_dump(), "state": state,
            "updated_at": max(now, run.updated_at), "result": result})
        db.execute("UPDATE agent_runs SET document=? WHERE id=? AND actor=? AND project=?",
                   (updated.model_dump_json(), identifier, actor, project))
        db.execute("INSERT INTO audit(id,at,actor,action,target,outcome,project_id,run_id,task_id,trace_id) VALUES(?,?,?,'agent_run_state',?,?,?,?,?,?)",
                   (str(uuid.uuid4()), now, actor, identifier, state, project, identifier, run.task_id, run.trace_id))
        return updated

    @staticmethod
    def _sync_agent(db, identifier, state, source=None):
        from .agent_models import AgentRun, AgentResult
        from .presentation import safe_text
        row = db.execute("SELECT document FROM agent_runs WHERE id=?", (identifier,)).fetchone()
        if not row:
            return
        run = AgentRun.from_json(row["document"])
        if run.state == state:
            return
        if run.state in {"WAITING_QUOTA", "WAITING_PROVIDER", "BLOCKED_KEY_OR_MODEL"} and state != "FAILED":
            run = Store._transition_agent_run(db, run.actor_id, run.project_id, identifier, run.state, "QUEUED")
            if run.state == state:
                return
        result = None
        if state in {"REVIEW", "FAILED", "COMPLETED"}:
            source = source or {}
            text = source.get("text") or source.get("message") or "Xem receipt của lượt xử lý; không tự gửi lại thao tác ghi."
            result = AgentResult.from_json(canonical(source['agent_result'])) if source.get('agent_result') else AgentResult(run_id=run.run_id, task_id=run.task_id, actor_id=run.actor_id,
                project_id=run.project_id, trace_id=run.trace_id, state=state, summary=safe_text(text)[:6000],
                receipt_ids=[identifier], model_used=bool(source.get("usage")),
                error_code="AI_RUN_FAILED_OR_UNKNOWN" if state == "FAILED" else None)
        Store._transition_agent_run(db, run.actor_id, run.project_id, identifier, run.state, state, result)

    def reserve_gemini(self, project, limits, input_tokens):
        """One shared project budget, persisted before outbound; unknown failures are not refunded."""
        now = time.time()
        day_start, next_reset = pacific_day(now)
        reason = None
        retry_at = None
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = self.active_gemini_block(db, project, now)
            if row:
                reason = "GEMINI_CIRCUIT_OPEN; no outbound request; last_error=" + row[0]
            else:
                counts = db.execute("SELECT COUNT(*),COALESCE(SUM(input_tokens),0) FROM gemini_usage WHERE project=? AND at>?",
                                    (project, now - 60)).fetchone()
                daily = db.execute("SELECT COUNT(*) FROM gemini_usage WHERE project=? AND at>=?", (project, day_start)).fetchone()[0]
                if counts[0] >= limits["rpm"]:
                    reason = "GEMINI_LOCAL_RPM_EXHAUSTED"
                    stamps = db.execute("SELECT at FROM gemini_usage WHERE project=? AND at>? ORDER BY at", (project, now - 60)).fetchall()
                    retry_at = stamps[-limits["rpm"]][0] + 60.1
                elif counts[1] + input_tokens > limits["tpm"]:
                    reason = "GEMINI_LOCAL_TPM_EXHAUSTED"
                    remaining = counts[1]
                    if input_tokens <= limits["tpm"]:
                        for stamp, amount in db.execute("SELECT at,input_tokens FROM gemini_usage WHERE project=? AND at>? ORDER BY at", (project, now - 60)):
                            remaining -= amount
                            if remaining + input_tokens <= limits["tpm"]:
                                retry_at = stamp + 60.1
                                break
                elif daily >= limits["rpd"]:
                    reason = "GEMINI_LOCAL_RPD_EXHAUSTED"
                    retry_at = next_reset + 0.1
                else:
                    reservation = db.execute("INSERT INTO gemini_usage VALUES(?,?,?)", (project, now, input_tokens)).lastrowid
        if reason:
            error = ValueError(reason)
            error.retry_at = retry_at
            raise error
        return reservation

    def settle_gemini_input(self, reservation, project, actual_input):
        if type(actual_input) is not int or actual_input < 0:
            raise ValueError('PROVIDER_INPUT_USAGE_INVALID')
        with self.connect() as db:
            db.execute('UPDATE gemini_usage SET input_tokens=? WHERE rowid=? AND project=?',
                       (actual_input, reservation, project))

    def provider_receipt(self, document):
        # Internal metadata only: never prompts, source content, keys or response bodies.
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO gemini_call_receipts VALUES(?,?,?,?,?)',
                (document['id'],document['project'],document.get('actor'),document.get('run_id'),canonical(document)))

    @staticmethod
    def active_gemini_block(db, project, now):
        row = db.execute("SELECT b.reason,r.retry_at FROM gemini_blocks b LEFT JOIN gemini_recovery r ON r.project=b.project AND r.reason=b.reason WHERE b.project=?", (project,)).fetchone()
        return row if row and (row["retry_at"] is None or row["retry_at"] > now) else None

    def gemini_block(self, project):
        with self.connect() as db:
            row = self.active_gemini_block(db, project, time.time())
        return dict(row) if row else None

    def provider_wait(self, policy):
        """Advisory admission for never-started intents; reserve_gemini remains the atomic hard gate."""
        now, project, limits = time.time(), policy["project"], policy["limits"]
        day_start, next_reset = pacific_day(now)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self.expire_queue(db, now)
            block = self.active_gemini_block(db, project, now)
            if block:
                state = "WAITING_QUOTA" if "QUOTA" in block["reason"] or "EXHAUSTED" in block["reason"] else "WAITING_PROVIDER"
                if any(code in block["reason"] for code in ("AUTH_", "PERMISSION_", "MODEL_", "BILLING_")):
                    state = "BLOCKED_KEY_OR_MODEL"
                return {"queue_state": state, "retry_at": block["retry_at"]}
            daily = db.execute("SELECT COUNT(*) FROM gemini_usage WHERE project=? AND at>=?", (project, day_start)).fetchone()[0]
            if daily >= limits["rpd"]:
                return {"queue_state": "WAITING_QUOTA", "retry_at": next_reset + 0.1}
            rows = db.execute("SELECT at,input_tokens FROM gemini_usage WHERE project=? AND at>? ORDER BY at", (project, now - 60)).fetchall()
            if len(rows) >= limits["rpm"]:
                return {"queue_state": "WAITING_QUOTA", "retry_at": rows[-limits["rpm"]][0] + 60.1}
            if sum(row[1] for row in rows) >= limits["tpm"]:
                return {"queue_state": "WAITING_QUOTA", "retry_at": rows[0][0] + 60.1}
        return None

    def wait_queued(self, waiting):
        message = {"WAITING_QUOTA": "Đang chờ quota Gemini miễn phí, yêu cầu vẫn được giữ trong hàng đợi.",
                   "WAITING_PROVIDER": "Gemini tạm gián đoạn, yêu cầu vẫn chờ và sẽ tiếp tục sau cooldown.",
                   "BLOCKED_KEY_OR_MODEL": "Gemini đang bị chặn bởi cấu hình hoặc quyền truy cập; yêu cầu được giữ để quản trị viên kiểm tra."}[waiting["queue_state"]]
        message = waiting["queue_state"] + " — " + message
        result = canonical({**waiting, "status": "waiting", "tools": [], "message": message, "text": message})
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE ai_runs SET result=? WHERE state='running' AND id IN (SELECT id FROM ai_queue WHERE state='queued' AND COALESCE(json_extract(payload,'$.engine'),'gemini') NOT IN ('supervisor','openclaw')) AND result<>?",
                       (result, result))
            for row in db.execute("SELECT a.id FROM agent_runs a JOIN ai_queue q ON q.id=a.id WHERE q.state='queued' AND COALESCE(json_extract(q.payload,'$.engine'),'gemini') NOT IN ('supervisor','openclaw')").fetchall():
                self._sync_agent(db, row["id"], waiting["queue_state"])

    def block_gemini(self, project, reason, cooldown=None):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT OR REPLACE INTO gemini_blocks VALUES(?,?)", (project, reason))
            db.execute("DELETE FROM gemini_recovery WHERE project=?", (project,))
            if cooldown is not None:
                db.execute("INSERT INTO gemini_recovery VALUES(?,?,?)", (project, reason, time.time() + cooldown))

    def authenticate(self, token):
        with self.connect() as db:
            row = db.execute("SELECT * FROM tokens WHERE hash=? AND revoked=0 AND expires>?",
                             (digest(token), time.time())).fetchone()
        if not row:
            raise PermissionError("INVALID_OR_EXPIRED_TOKEN")
        return dict(row)

    def revoke_token(self, token):
        with self.connect() as db:
            db.execute("UPDATE tokens SET revoked=1 WHERE hash=?", (digest(token),))

    def credential(self, user_id):
        return json.loads((self.root / "credentials.json").read_text())[str(user_id)]

    def record(self, actor, action, target, outcome, correlation=None, version=None, *, connection=None):
        from .agent_trace import current_run
        correlation = correlation or str(uuid.uuid4())
        binding = current_run.get()
        scope = binding[1] if binding and binding[0].root.resolve() == self.root.resolve() and binding[1].actor_id == actor else None
        target_text = str(target)[:256]
        version_text = str(version)[:256] if version is not None else None
        if scope:
            code = action in {"trace_worker", "trace_native", "trace_provider"} and re.fullmatch(r"[A-Za-z_]{1,40}", target_text)
            if not (code or target_text in {"qldapm-local", "request_scope"} or re.fullmatch(r"[0-9]{1,16}|[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", target_text)):
                target_text = "scoped-resource"
            if version_text is not None and not re.fullmatch(r"[0-9]{1,16}|[a-f0-9]{64}", version_text):
                version_text = None
        with (self.connect() if connection is None else nullcontext(connection)) as db:
            db.execute("INSERT INTO audit(id,at,actor,action,target,outcome,version,project_id,run_id,task_id,trace_id) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                       (correlation, time.time(), actor, action, target_text, outcome, version_text,
                        scope.project_id if scope else None, scope.run_id if scope else None, scope.task_id if scope else None, scope.trace_id if scope else None))
        return correlation

    def begin(self, actor, key, payload):
        if not key or len(key) > 100:
            raise ValueError("IDEMPOTENCY_KEY_REQUIRED")
        fingerprint = digest(canonical(payload))
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM requests WHERE actor=? AND key=?", (actor, key)).fetchone()
            if row:
                if row["hash"] != fingerprint:
                    raise ValueError("IDEMPOTENCY_KEY_REUSED")
                if row["state"] != "done":
                    # Deterministic cache repair is safe to retry; Native writes still require reconciliation.
                    if payload.get("action") in {"knowledge_ingest", "knowledge_file_ingest", "knowledge_incremental_sync", "knowledge_feedback_submit", "knowledge_feedback_apply", "wbs_draft", "wbs_adopt", "wbs_next", "wbs_from_ba", "qa_evidence_capture", "qa_transition_prepare", "qa_test_run", "qa_evidence_from_run", "qa_application_proof_admit"}:
                        return None
                    raise ValueError("OUTCOME_UNKNOWN_RECONCILE_FIRST")
                return json.loads(row["result"])
            db.execute("INSERT INTO requests(actor,key,hash,state,payload) VALUES(?,?,?,'pending',?)",
                       (actor, key, fingerprint, canonical(payload)))
        return None

    def finish(self, actor, key, result, knowledge_id=None, knowledge_ids=None):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if knowledge_id is not None:
                self._enqueue_knowledge_sync(db,actor,key,knowledge_id,result)
            if knowledge_ids is not None:
                self._enqueue_multiple_knowledge_sync(db,actor,key,knowledge_ids,result)
            count=db.execute("UPDATE requests SET state='done',result=? WHERE actor=? AND key=?",
                       (canonical(result), actor, key)).rowcount
            if (knowledge_id is not None or knowledge_ids is not None) and count!=1:
                raise ValueError('NATIVE_REQUEST_RECEIPT_REQUIRED')

    def _enqueue_multiple_knowledge_sync(self, db, actor, key, identifiers, result):
        if (not isinstance(identifiers,list) or not 1 <= len(identifiers) <= 2000 or
                any(type(i) is not int or i <= 0 for i in identifiers) or len(identifiers) != len(set(identifiers))):
            raise ValueError('KNOWLEDGE_NATIVE_IDS_REQUIRED')
        result['knowledge_syncs'] = []
        for identifier in sorted(identifiers):
            receipt = {}
            # Older workers can still ingest these jobs without parsing a suffixed proposal UUID.
            self._enqueue_knowledge_sync(db,actor,'dependency:'+key+':native:'+str(identifier),identifier,receipt)
            result['knowledge_syncs'].append(receipt['knowledge_sync'])

    def _enqueue_knowledge_sync(self, db, actor, key, knowledge_id, result):
        if type(knowledge_id) is not int or knowledge_id <= 0:
            raise ValueError('KNOWLEDGE_NATIVE_ID_REQUIRED')
        identifier=str(uuid.uuid5(uuid.NAMESPACE_URL,f'qldapm.knowledge-sync:{actor}:{key}'))
        db.execute("INSERT OR IGNORE INTO knowledge_sync(id,actor,native_id,request_key,state) VALUES(?,?,?,?,'pending')",
            (identifier,actor,knowledge_id,key))
        result['knowledge_sync']={'id':identifier,'state':'pending','native_id':knowledge_id}
        from .agent_trace import current_run
        binding=current_run.get()
        if binding and binding[0].root.resolve()==self.root.resolve() and binding[1].actor_id==actor:
            result['knowledge_sync'].update(run_id=binding[1].run_id,trace_id=binding[1].trace_id)

    def knowledge_sync(self, actor, identifier):
        with self.connect() as db:
            row=db.execute('SELECT id,native_id,state,attempts,next_at,error,result FROM knowledge_sync WHERE id=? AND actor=?',
                (identifier,actor)).fetchone()
        if not row:
            raise PermissionError('KNOWLEDGE_SYNC_NOT_FOUND')
        return {**dict(row),'result':json.loads(row['result']) if row['result'] else None}

    def claim_knowledge_sync(self, now=None):
        now=time.time() if now is None else now
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute("UPDATE knowledge_sync SET state='dlq',error='WORKER_LEASE_EXHAUSTED' WHERE state='running' AND lease_until<=? AND attempts>=5",(now,))
            row=db.execute("SELECT * FROM knowledge_sync WHERE (state IN ('pending','retry') AND next_at<=?) OR (state='running' AND lease_until<=? AND attempts<5) ORDER BY next_at,id LIMIT 1",(now,now)).fetchone()
            if not row:
                return None
            lease=str(uuid.uuid4())
            db.execute("UPDATE knowledge_sync SET state='running',attempts=attempts+1,lease=?,lease_until=? WHERE id=?",(lease,now+300,row['id']))
            return {**dict(row),'state':'running','attempts':row['attempts']+1,'lease':lease}

    def finish_knowledge_sync(self, claim, result, error=None, now=None):
        now=time.time() if now is None else now
        if error is not None and not re.fullmatch('[A-Z_]{1,80}',error):
            raise ValueError('FIXED_ERROR_CODE_REQUIRED')
        success=not error and result and result.get('vector_indexed') is True
        state='verified' if success else 'dlq' if claim['attempts']>=5 else 'retry'
        next_at=now if success else now+5*2**(claim['attempts']-1)
        with self.connect() as db:
            return db.execute("UPDATE knowledge_sync SET state=?,next_at=?,error=?,result=?,lease=NULL,lease_until=NULL WHERE id=? AND state='running' AND lease=?",
                (state,next_at,None if success else error or 'VECTOR_INDEX_PENDING',canonical(result) if result else None,claim['id'],claim['lease'])).rowcount==1

    def retry_knowledge_sync(self, actor, identifier):
        self.knowledge_sync(actor,identifier)
        with self.connect() as db:
            count=db.execute("UPDATE knowledge_sync SET state='pending',attempts=0,next_at=0,error=NULL WHERE id=? AND actor=? AND state='dlq'",(identifier,actor)).rowcount
        if count!=1:
            raise ValueError('KNOWLEDGE_SYNC_NOT_IN_DLQ')
        return self.knowledge_sync(actor,identifier)

    def save_report(self, actor, project, kind, document, references):
        if kind not in {'knowledge_integrity','weekly_summary','sprint_risk','health'}:
            raise ValueError('FIXED_REPORT_KIND_REQUIRED')
        refs=sorted((item['id'],item['lockVersion']) for item in references)
        fingerprint=digest(canonical({'document':document,'references':refs}))
        identifier=str(uuid.uuid5(uuid.NAMESPACE_URL,f'qldapm.report:{actor}:{project}:{kind}:{fingerprint}'))
        now=time.time()
        with self.connect() as db:
            db.execute('INSERT INTO operational_reports VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET last_seen=excluded.last_seen',
                (identifier,actor,project,kind,fingerprint,canonical(document),canonical(refs),now,now))
            from .notification_delivery import enqueue
            enqueue(db,'report',identifier,actor,project,fingerprint)
        saved=self.report(actor,project,identifier)
        return {'report_id':identifier,'report_sha256':saved['sha256'],'last_observed_at':saved['last_observed_at']}

    def report(self, actor, project, identifier):
        with self.connect() as db:
            row=db.execute('SELECT * FROM operational_reports WHERE id=? AND actor=? AND project=?',(identifier,actor,project)).fetchone()
        if not row:
            raise PermissionError('REPORT_NOT_FOUND')
        document=json.loads(row['document']);refs=json.loads(row['refs'])
        if digest(canonical({'document':document,'references':refs}))!=row['hash']:
            raise ValueError('REPORT_HASH_MISMATCH')
        return {'id':row['id'],'kind':row['kind'],'sha256':row['hash'],'created_at':row['created'],
            'last_observed_at':row['last_seen'],'document':document,'references':refs}

    def request_status(self, actor, key):
        with self.connect() as db:
            row = db.execute("SELECT key,state,result FROM requests WHERE actor=? AND key=?", (actor, key)).fetchone()
        if not row:
            raise ValueError("REQUEST_NOT_FOUND")
        return {"key": row["key"], "state": row["state"], "result": json.loads(row["result"]) if row["result"] else None}

    def finish_reconciliation(self,actor,key,found,project,knowledge_id=None,native_qa_proposal=None,native_dependency_proposal=None,knowledge_ids=None,native_delete_proposal=None,native_phase_proposal=None):
        with self.connect() as db:
            db.execute('begin immediate')
            row=db.execute('select state,result,payload from requests where actor=? and key=?',(actor,key)).fetchone()
            if not row:raise ValueError('PENDING_REQUEST_NOT_FOUND')
            if row['state']=='done':return json.loads(row['result'])
            proposal=None;scope=None
            native_proposal = native_qa_proposal or native_dependency_proposal or native_delete_proposal or native_phase_proposal
            if native_proposal is not None:
                proposal=db.execute('select * from proposals where id=? and actor=?',(native_proposal,actor)).fetchone()
                command=json.loads(proposal['payload']) if proposal else {}
                pending=json.loads(row['payload']) if row['payload'] else {}
                expected_actions = {'delete_work_package'} if native_delete_proposal else {'create_dependency','update_dependency','delete_dependency'} if native_dependency_proposal else {'transition'}
                proof = found.get('signature') if native_delete_proposal else found.get('relation') if native_dependency_proposal else found.get('phase_native') if native_phase_proposal else found.get('qa_native')
                if (key!='proposal-'+native_proposal or not proposal or proposal['state'] not in {'executing','failed_or_unknown'} or
                        digest(canonical({'actor':actor,'command':command}))!=proposal['hash'] or command.get('action') not in expected_actions or
                        command.get('arguments')!=pending.get('arguments') or not proof):
                    raise PermissionError('EXACT_NATIVE_DELETE_PROPOSAL_RECONCILIATION_REQUIRED' if native_delete_proposal else 'EXACT_DEPENDENCY_PROPOSAL_RECONCILIATION_REQUIRED' if native_dependency_proposal else 'EXACT_QA_PROPOSAL_RECONCILIATION_REQUIRED')
                from .agent_trace import current_run
                binding=current_run.get()
                scope=binding[1] if binding and binding[0].root.resolve()==self.root.resolve() and binding[1].actor_id==actor and binding[1].project_id==project else None
            identifier=str(uuid.uuid4())
            response={'result':found,'reconciled':True,'correlation_id':identifier}
            if proposal is not None:
                response['prior_confirmation_result']=json.loads(proposal['result']) if proposal['result'] else None
                if scope:response['origin']={'run_id':scope.run_id,'trace_id':scope.trace_id,'proposal_id':native_proposal}
            if knowledge_id is not None:
                self._enqueue_knowledge_sync(db,actor,key,knowledge_id,response)
            if knowledge_ids is not None:
                self._enqueue_multiple_knowledge_sync(db,actor,key,knowledge_ids,response)
            db.execute("update requests set state='done',result=? where actor=? and key=? and state='pending'",(canonical(response),actor,key))
            if proposal is not None:
                db.execute("update proposals set state='done',result=? where id=? and actor=?",(canonical(response),native_proposal,actor))
            db.execute('insert into audit(id,at,actor,action,target,outcome,project_id,run_id,task_id,trace_id) values(?,?,?,?,?,?,?,?,?,?)',
                (identifier,time.time(),actor,'reconcile_request',native_proposal or key,
                 'DELETE_NATIVE_RECEIPT_PROVEN' if native_delete_proposal else 'DEPENDENCY_NATIVE_RECEIPT_PROVEN' if native_dependency_proposal else 'PHASE_NATIVE_RECEIPT_PROVEN' if native_phase_proposal else 'QA_NATIVE_RECEIPT_PROVEN' if proposal is not None else 'ok',project,
                 scope.run_id if scope else None,scope.task_id if scope else None,scope.trace_id if scope else None))
            return response

    def pending_request(self, actor, key):
        with self.connect() as db:
            row = db.execute("SELECT payload FROM requests WHERE actor=? AND key=? AND state='pending'", (actor, key)).fetchone()
        if not row or not row["payload"]:
            raise ValueError("PENDING_REQUEST_NOT_FOUND")
        return json.loads(row["payload"])

    def enqueue(self, actor, action, payload, request_key=None):
        job_id = str(uuid.uuid4())
        body = canonical({"actor": actor, "action": action, "payload": payload})
        with self.connect() as db:
            db.execute("INSERT INTO jobs(id,actor,action,payload,hash,state,created,request_key) VALUES(?,?,?,?,?,'queued',?,?)",
                       (job_id, actor, action, canonical(payload), digest(body), time.time(), request_key))
        return self.job(actor, job_id)

    def job_for_request(self, actor, key):
        with self.connect() as db:
            row = db.execute("SELECT id FROM jobs WHERE actor=? AND request_key=?", (actor, key)).fetchone()
        return self.job(actor, row["id"]) if row else None

    def job(self, actor, job_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=? AND actor=?", (job_id, actor)).fetchone()
        if not row:
            raise PermissionError("JOB_NOT_FOUND")
        return {"id": row["id"], "action": row["action"], "hash": row["hash"], "state": row["state"],
                "payload": json.loads(row["payload"]), "result": json.loads(row["result"]) if row["result"] else None}

    def broker_job(self, operation, identifier=None, state=None, result=None):
        """Fixed local-operator queue operations; never exposed through REST/MCP."""
        with self.connect() as db:
            if operation == "queued":
                return [dict(row) for row in db.execute("SELECT id,action FROM jobs WHERE state='queued' ORDER BY created LIMIT 20")]
            if operation == "unresolved":
                row = db.execute("SELECT id FROM jobs WHERE state IN ('running','failed_or_unknown') LIMIT 1").fetchone()
                return dict(row) if row else None
            if operation == "inspect":
                row = db.execute("SELECT * FROM jobs WHERE id=?", (identifier,)).fetchone()
                if not row:
                    raise ValueError("JOB_NOT_FOUND")
                return dict(row)
            db.execute("BEGIN IMMEDIATE")
            if operation == "claim":
                row = db.execute("SELECT id FROM jobs WHERE state IN ('running','failed_or_unknown') LIMIT 1").fetchone()
                if row:
                    raise PermissionError("OPERATOR_RECONCILIATION_REQUIRED: " + row["id"])
                count = db.execute("UPDATE jobs SET state='running' WHERE id=? AND state='queued'", (identifier,)).rowcount
            elif operation == "finish" and state in {"done", "failed_or_unknown"}:
                count = db.execute("UPDATE jobs SET state=?,result=? WHERE id=? AND state='running'",
                                   (state, canonical(result), identifier)).rowcount
            elif operation == "reconcile":
                count = db.execute("UPDATE jobs SET state='operator_reconciled' WHERE id=? AND state IN ('running','failed_or_unknown')",
                                   (identifier,)).rowcount
            else:
                raise ValueError("BROKER_QUEUE_OPERATION_DENIED")
            if count != 1:
                raise ValueError("JOB_CHANGED_OR_NOT_QUEUED")
            return None

    def propose(self, actor, payload):
        identifier = str(uuid.uuid4())
        fingerprint = digest(canonical({"actor": actor, "command": payload}))
        with self.connect() as db:
            db.execute("INSERT INTO proposals VALUES(?,?,?,?,?,'pending',NULL)",
                       (identifier, actor, canonical(payload), fingerprint, time.time() + 900))
        return self.proposal(actor, identifier)

    def proposal(self, actor, identifier):
        with self.connect() as db:
            row = db.execute("SELECT * FROM proposals WHERE id=? AND actor=?", (identifier, actor)).fetchone()
        if not row:
            raise PermissionError("PROPOSAL_NOT_FOUND")
        result=json.loads(row['result']) if row['result'] else None
        synchronization={}
        if result and result.get('knowledge_sync'):
            job=self.knowledge_sync(actor,result['knowledge_sync']['id'])
            synchronization={'knowledge_sync':job,'lifecycle':'VERIFIED_COMPLETED' if job['state']=='verified' else
                'RAG_SYNC_FAILED' if job['state']=='dlq' else 'NATIVE_CONFIRMED_RAG_PENDING'}
        elif result and result.get('knowledge_syncs'):
            jobs = [self.knowledge_sync(actor,entry['id']) for entry in result['knowledge_syncs']]
            states = {job['state'] for job in jobs}
            synchronization = {'knowledge_syncs':jobs,'lifecycle':'VERIFIED_COMPLETED' if states == {'verified'} else
                               'RAG_SYNC_FAILED' if 'dlq' in states else 'NATIVE_CONFIRMED_RAG_PENDING'}
        return {"id": row["id"], "hash": row["hash"], "expires": row["expires"], "state": row["state"],
                "command": json.loads(row["payload"]), "result": json.loads(row["result"]) if row["result"] else None,
                "human_confirmation_required": True,**synchronization}

    def claim_proposal(self, actor, identifier, fingerprint):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload,hash FROM proposals WHERE id=? AND actor=?", (identifier, actor)).fetchone()
            if row:
                payload = json.loads(row["payload"])
                if digest(canonical({"actor": actor, "command": payload})) != row["hash"]:
                    raise ValueError("PROPOSAL_PAYLOAD_CHANGED")
            cursor = db.execute("UPDATE proposals SET state='executing' WHERE id=? AND actor=? AND hash=? AND state='pending' AND expires>?",
                                (identifier, actor, fingerprint, time.time()))
            if cursor.rowcount != 1:
                raise ValueError("STALE_EXPIRED_OR_CONSUMED_PROPOSAL")
            return payload

    def reject_proposal(self, actor, identifier, fingerprint):
        with self.connect() as db:
            cursor = db.execute("UPDATE proposals SET state='rejected' WHERE id=? AND actor=? AND hash=? AND state='pending' AND expires>?",
                                (identifier, actor, fingerprint, time.time()))
            if cursor.rowcount != 1:
                raise ValueError("STALE_EXPIRED_OR_CONSUMED_PROPOSAL")

    def history(self, actor):
        with self.connect() as db:
            return {"audit": [dict(row) for row in db.execute("SELECT * FROM audit WHERE actor=? ORDER BY at DESC LIMIT 30", (actor,))],
                    "runs": [dict(row) for row in db.execute("SELECT r.id,CASE WHEN json_extract(b.document,'$.state')='RECONCILED_SUCCESS' THEN 'reconciled_success' WHEN json_extract(b.document,'$.state') IN ('NATIVE_CONFIRMED','COMPLETED','REVIEW') THEN 'done' ELSE r.state END state,r.created FROM ai_runs r LEFT JOIN business_runs b ON b.id=r.id AND b.actor=r.actor WHERE r.actor=? ORDER BY r.created DESC LIMIT 20", (actor,))],
                    "proposals": [dict(row) for row in db.execute("SELECT id,state,expires FROM proposals WHERE actor=? ORDER BY expires DESC LIMIT 20", (actor,))]}

    def project_audit(self, users):
        actors = [int(actor) for actor in users]
        if not actors:
            return []
        with self.connect() as db:
            return [dict(row) for row in db.execute(
                "SELECT actor,action,target,at,outcome FROM audit WHERE actor IN (" + ",".join("?" for _ in actors) + ") ORDER BY at DESC LIMIT 100", actors)]

    def finish_proposal(self, actor, identifier, result, state="done"):
        with self.connect() as db:
            db.execute("UPDATE proposals SET state=?,result=? WHERE id=? AND actor=? AND state='executing'",
                       (state, canonical(result), identifier, actor))

    def consume_nonce(self, nonce, expires):
        with self.connect() as db:
            db.execute("DELETE FROM ui_nonces WHERE expires<?", (time.time(),))
            try:
                db.execute("INSERT INTO ui_nonces VALUES(?,?)", (nonce, expires))
            except sqlite3.IntegrityError:
                raise PermissionError("UI_ASSERTION_REPLAY") from None

    def create_run(self, actor):
        identifier = str(uuid.uuid4())
        with self.connect() as db:
            db.execute("INSERT INTO ai_runs VALUES(?,?,'running',NULL,?)", (identifier, actor, time.time()))
        return identifier

    def complete_read_run(self, actor, result, command=None):
        key = command.get("idempotency_key") if command else None
        if command and (not key or len(key) > 100):
            raise ValueError("IDEMPOTENCY_KEY_REQUIRED")
        now, identifier, correlation = time.time(), str(uuid.uuid4()), str(uuid.uuid4())
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if command:
                old = db.execute("SELECT * FROM requests WHERE actor=? AND key=?", (actor, key)).fetchone()
                if old:
                    if old["hash"] != digest(canonical(command)):
                        raise ValueError("IDEMPOTENCY_KEY_REUSED")
                    if old["state"] != "done":
                        raise ValueError("OUTCOME_UNKNOWN_RECONCILE_FIRST")
                    response = json.loads(old["result"])
                    run = db.execute("SELECT result FROM ai_runs WHERE actor=? AND id=?", (actor, response["result"]["id"])).fetchone()
                    if not run or json.loads(run[0]).get("source_fingerprint") != result["source_fingerprint"]:
                        raise ValueError("STALE_READ_RECEIPT; use a new request key for current native data")
                    return response
            response = {"result": {"id": identifier, "state": "done", "source": "native", "model_used": False},
                        "correlation_id": correlation}
            db.execute("INSERT INTO ai_runs VALUES(?,?,'done',?,?)", (identifier, actor, canonical(result), now))
            db.execute("INSERT INTO audit(id,at,actor,action,target,outcome) VALUES(?,?,?,'start_ai_run',?,'native_read')",
                       (correlation, now, actor, identifier))
            if command:
                db.execute("INSERT INTO requests(actor,key,hash,state,result,payload) VALUES(?,?,?,'done',?,?)",
                           (actor, key, digest(canonical(command)), canonical(response), canonical(command)))
        return response

    def enqueue_run(self, actor, payload, command=None, kind="interactive", agent_task=None):
        from .agent_models import AgentTask, AgentRun
        if not isinstance(kind, str) or kind not in RUN_ROUND_LIMITS:
            raise ValueError("AI_QUEUE_KIND_INVALID")
        if agent_task is not None:
            agent_task = AgentTask.from_json(agent_task.model_dump_json())
            if (agent_task.actor_id != actor or agent_task.run_class != kind or payload.get("prompt") != agent_task.instruction
                    or payload.get("allow_routine_writes") is not False or payload.get("write_scope_ids") != []
                    or not isinstance(payload.get("policy_sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", payload["policy_sha256"])):
                raise PermissionError("AGENT_QUEUE_SCOPE_OR_CONSENT_DENIED")
        key = command.get("idempotency_key") if command else None
        if command and (not key or len(key) > 100):
            raise ValueError("IDEMPOTENCY_KEY_REQUIRED")
        now, identifier, correlation = time.time(), str(uuid.uuid4()), str(uuid.uuid4())
        request_hash = digest(canonical({"command": command, "agent_task": agent_task.model_dump()} if agent_task and payload.get('engine') not in {'supervisor','supervisor_gemini'} else command))
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if command:
                old = db.execute("SELECT * FROM requests WHERE actor=? AND key=?", (actor, key)).fetchone()
                if old:
                    if old["hash"] != request_hash:
                        raise ValueError("IDEMPOTENCY_KEY_REUSED")
                    if old["state"] != "done":
                        raise ValueError("OUTCOME_UNKNOWN_RECONCILE_FIRST")
                    return json.loads(old["result"])
            if agent_task is not None:
                task = db.execute("SELECT document FROM agent_tasks WHERE id=? AND actor=? AND project=?",
                                  (agent_task.task_id, actor, agent_task.project_id)).fetchone()
                if not task or task["document"] != agent_task.model_dump_json():
                    raise PermissionError("AGENT_STORED_TASK_REQUIRED")
                if agent_task.expires_at <= now:
                    raise ValueError("AGENT_TASK_EXPIRED")
            pending = db.execute("SELECT actor,COUNT(*) FROM ai_queue WHERE state='queued' GROUP BY actor").fetchall()
            if sum(row[1] for row in pending) >= 100 or dict(pending).get(actor, 0) >= 20:
                raise ValueError("AI_QUEUE_FULL; try later with the same request key")
            result = {"id": identifier, "state": "running", "routine_writes_authorized": payload["allow_routine_writes"],
                      "write_scope_ids": payload["write_scope_ids"], "run_class": kind, "max_rounds": RUN_ROUND_LIMITS[kind]}
            response = {"result": result, "correlation_id": correlation}
            if agent_task is not None:
                result.update(agent_task_id=agent_task.task_id, trace_id=correlation)
                run = AgentRun(run_id=identifier, task_id=agent_task.task_id, actor_id=actor,
                    project_id=agent_task.project_id, trace_id=correlation, created_at=now, updated_at=now)
                db.execute("INSERT INTO agent_runs VALUES(?,?,?,?,?)",
                           (identifier, agent_task.task_id, actor, agent_task.project_id, run.model_dump_json()))
            progress = {"status": "waiting", "queue_state": "QUEUED", "tools": [],
                        "engine":'gemini_supervisor' if payload.get('engine')=='supervisor_gemini' else 'local_supervisor' if payload.get('engine')=='supervisor' else 'gemini',
                        "text": "Yêu cầu đã xếp hàng, đang chờ lượt xử lý.",
                        "message": "Yêu cầu đã xếp hàng, đang chờ lượt xử lý."}
            db.execute("INSERT INTO ai_runs VALUES(?,?,'running',?,?)", (identifier, actor, canonical(progress), now))
            if 'business_read_only' in payload:
                from .business_runs import initial_document
                db.execute('insert into business_runs values(?,?,?,?)',(identifier,actor,payload['native_project_id'],canonical(initial_document(payload))))
            if agent_task is not None:
                from .execution_events import append
                for event in ['REQUEST_RECEIVED','AUTHORIZED','QUEUED']:append(db,run,event,status='QUEUED',key=event)
            db.execute("INSERT INTO ai_queue(id,actor,payload,state,created,kind) VALUES(?,?,?,'queued',?,?)",
                       (identifier, actor, canonical(payload), now, kind))
            db.execute("INSERT INTO audit(id,at,actor,action,target,outcome,project_id,run_id,task_id,trace_id) VALUES(?,?,?,'start_ai_run',?,'queued',?,?,?,?)",
                       (correlation, now, actor, identifier, agent_task.project_id if agent_task else None,
                        identifier if agent_task else None, agent_task.task_id if agent_task else None, correlation if agent_task else None))
            if command:
                db.execute("INSERT INTO requests(actor,key,hash,state,result,payload) VALUES(?,?,?,'done',?,?)",
                           (actor, key, request_hash, canonical(response), canonical(command)))
        return response

    @staticmethod
    def expire_queue(db, now):
        # A claimed run is never replayed; allow the isolated worker's hard deadline plus shutdown margin.
        from .presentation import execution_report
        expired = db.execute("SELECT r.* FROM ai_runs r JOIN ai_queue q ON q.id=r.id WHERE q.state='executing' AND q.lease_until<=?", (now,)).fetchall()
        for row in expired:
            progress = json.loads(row["result"]) if row["result"] else {}
            report = execution_report(progress.get("tools", []))
            result = {**progress, **report,
                      "status": "partial" if report["status"] in {"succeeded", "proposed", "partial"} else "failed",
                      "error": "AI_RUN_INTERRUPTED_OR_UNKNOWN; reconcile tool receipts, no auto retry"}
            db.execute("UPDATE ai_runs SET state='failed_or_unknown',result=? WHERE id=? AND state='running'",
                       (canonical(result), row["id"]))
            db.execute("UPDATE ai_queue SET state='finished' WHERE id=?", (row["id"],))
            Store._sync_agent(db, row["id"], "FAILED", result)

    def claim_run(self, local_only=False, *, openclaw_only=False):
        now = time.time()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self.expire_queue(db, now)
            if db.execute("SELECT 1 FROM ai_queue WHERE state='executing' LIMIT 1").fetchone():
                return None
            # Global served sequence gives each waiting actor a turn, even when timestamps tie.
            row = db.execute("""SELECT q.* FROM ai_queue q
                LEFT JOIN (SELECT actor,MAX(served) AS last_served FROM ai_queue GROUP BY actor) f ON f.actor=q.actor
                WHERE q.state='queued' AND (?=0 OR json_extract(q.payload,'$.engine')='supervisor')
                  AND (?=1 AND json_extract(q.payload,'$.engine')='openclaw'
                    OR ?=0 AND COALESCE(json_extract(q.payload,'$.engine'),'gemini')!='openclaw')
                ORDER BY CASE q.kind WHEN 'interactive' THEN 0 WHEN 'agent' THEN 1 WHEN 'report' THEN 2 ELSE 3 END,
                         COALESCE(f.last_served,0),q.created,q.rowid LIMIT 1""",(int(local_only),int(openclaw_only),int(openclaw_only))).fetchone()
            if not row:
                return None
            bound = db.execute("SELECT t.expires FROM agent_runs a JOIN agent_tasks t ON t.id=a.task_id WHERE a.id=?", (row["id"],)).fetchone()
            if bound and bound["expires"] <= now:
                failure = {"status": "failed", "tools": [], "error": "AGENT_TASK_EXPIRED", "text": "Tham chiếu đã hết hạn; yêu cầu chưa được thực thi."}
                db.execute("UPDATE ai_runs SET state='failed_or_unknown',result=? WHERE id=?", (canonical(failure), row["id"]))
                db.execute("UPDATE ai_queue SET state='finished' WHERE id=?", (row["id"],))
                self._sync_agent(db, row["id"], "FAILED", failure)
                return None
            self._sync_agent(db, row["id"], "RUNNING")
            sequence = db.execute("SELECT COALESCE(MAX(served),0)+1 FROM ai_queue").fetchone()[0]
            db.execute("UPDATE ai_queue SET state='executing',served=?,lease_until=? WHERE id=?",
                       (sequence, max(now + RUN_TIMEOUT_SECONDS + 120, float(json.loads(row['payload']).get('deadline',now))+120) if openclaw_only else now + RUN_TIMEOUT_SECONDS + 120, row["id"]))
            db.execute("UPDATE ai_runs SET result=? WHERE id=? AND state='running'",
                       (canonical({"status": "running", "queue_state": "EXECUTING", "tools": [],
                                   "text": "Đang xử lý yêu cầu."}), row["id"]))
        return {"id": row["id"], "actor": row["actor"], **json.loads(row["payload"])}

    def queue_pending(self):
        with self.connect() as db:
            return db.execute("SELECT 1 FROM ai_queue WHERE state IN ('queued','executing') LIMIT 1").fetchone() is not None

    def run_class(self, actor, identifier):
        with self.connect() as db:
            row = db.execute("SELECT kind FROM ai_queue WHERE id=? AND actor=?", (identifier, actor)).fetchone()
        return row["kind"] if row else "interactive"

    def finish_run(self, actor, identifier, result, state):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            changed = db.execute("UPDATE ai_runs SET state=?,result=? WHERE id=? AND actor=? AND state='running'", (state, canonical(result), identifier, actor)).rowcount
            db.execute("UPDATE ai_queue SET state='finished' WHERE id=? AND actor=?", (identifier, actor))
            if changed:
                target = "FAILED" if state != "done" or result.get("status") in {"failed", "partial"} else "REVIEW" if result.get("status") == "proposed" else "COMPLETED"
                self._sync_agent(db, identifier, target, result)
                row=db.execute('SELECT document FROM agent_runs WHERE id=? AND actor=?',(identifier,actor)).fetchone()
                if row:
                    from .agent_models import AgentRun
                    from .execution_events import append
                    scope=AgentRun.from_json(row[0])
                    queued=db.execute('SELECT payload FROM ai_queue WHERE id=? AND actor=?',(identifier,actor)).fetchone()
                    contract=json.loads(queued[0]) if queued else {}
                    suffix=(':engineering-'+str(contract.get('attempt',0))+'-'+str(contract.get('recovery_count',0))) if contract.get('engine')=='openclaw' else ''
                    append(db,scope,'RESULT_AVAILABLE',status=target,key='RESULT_AVAILABLE'+suffix)
                    append(db,scope,'RUN_FAILED' if target=='FAILED' else 'RUN_COMPLETED',status=target,key='RUN_TERMINAL'+suffix)

    def progress_run(self, actor, identifier, result):
        with self.connect() as db:
            db.execute("UPDATE ai_runs SET result=? WHERE id=? AND actor=? AND state='running'", (canonical(result), identifier, actor))

    def cancel_agent_run(self, actor, project, identifier):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute("""SELECT a.document,q.payload,r.result FROM agent_runs a JOIN ai_queue q ON q.id=a.id
                JOIN ai_runs r ON r.id=a.id AND r.actor=a.actor WHERE a.id=? AND a.actor=? AND a.project=?""",
                (identifier,actor,project)).fetchone()
            if not row and actor == 18 and project in (5, 6):
                row = db.execute("""SELECT a.document,q.payload,r.result FROM agent_runs a JOIN ai_queue q ON q.id=a.id
                    JOIN ai_runs r ON r.id=a.id AND r.actor=a.actor WHERE a.id=? AND a.project=?""",
                    (identifier,project)).fetchone()
            if not row or json.loads(row['payload']).get('engine') not in {'supervisor','supervisor_gemini'}:
                raise PermissionError('LOCAL_AGENT_RUN_NOT_FOUND')
            state = json.loads(row['document'])['state']
            if state in {'COMPLETED','FAILED','REVIEW'}:
                return {'id':identifier,'state':state,'cancelled':False}
            result={**(json.loads(row['result']) if row['result'] else {}),
                    'status':'failed','error':'AGENT_CANCELLED','text':'Đã hủy phân tích; kết quả đã nhận được giữ lại. Không có native mutation.','tools':[]}
            run_actor = json.loads(row['document'])['actor_id']
            db.execute("UPDATE ai_runs SET state='failed_or_unknown',result=? WHERE id=? AND actor=?",(canonical(result),identifier,run_actor))
            # Retain the lease for an executing read-only worker until its deadline; no overlapping claims.
            db.execute("UPDATE ai_queue SET state='finished' WHERE id=? AND state='queued'",(identifier,))
            self._sync_agent(db,identifier,'FAILED',result)
            from .agent_models import AgentRun
            from .execution_events import append
            scope = AgentRun.from_json(row['document'])
            append(db,scope,'RESULT_AVAILABLE',status='FAILED',key='RESULT_AVAILABLE')
            append(db,scope,'RUN_FAILED',status='FAILED',key='RUN_TERMINAL',error_code='AGENT_CANCELLED')
        self.record(actor,'cancel_agent_run',identifier,'cancelled')
        return {'id':identifier,'state':'FAILED','cancelled':True}

    def run(self, actor, identifier):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self.expire_queue(db, time.time())
            row = db.execute("SELECT * FROM ai_runs WHERE id=? AND actor=?", (identifier, actor)).fetchone()
            if not row and actor == 18:
                row = db.execute("SELECT * FROM ai_runs WHERE id=?", (identifier,)).fetchone()
            queued = db.execute("SELECT 1 FROM ai_queue WHERE id=?", (identifier,)).fetchone()
        if not row:
            raise PermissionError("AI_RUN_NOT_FOUND")
        if not queued and row["state"] == "running" and row["created"] < time.time() - RUN_TIMEOUT_SECONDS - 60:
            from .presentation import execution_report
            progress = json.loads(row["result"]) if row["result"] else {}
            report = execution_report(progress.get("tools", []))
            self.finish_run(actor, identifier, {**progress, **report,
                "status": "partial" if report["status"] in {"succeeded", "proposed", "partial"} else "failed",
                "heading": "Yêu cầu bị gián đoạn — kết quả đã nhận vẫn được giữ",
                "error": "AI_RUN_INTERRUPTED_OR_UNKNOWN; reconcile tool receipts, no auto retry"}, "failed_or_unknown")
            return self.run(actor, identifier)
        return {"id": identifier, "state": row["state"], "result": json.loads(row["result"]) if row["result"] else None}
