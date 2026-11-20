import hashlib
import json
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path


def canonical(value): return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def code_hash(value): return hashlib.sha256(value.encode()).hexdigest()


class Repository:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS pair_codes(hash TEXT PRIMARY KEY,user_id INTEGER,projects TEXT,expires REAL,used INTEGER DEFAULT 0,attempts INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS pairs(user_id INTEGER PRIMARY KEY,chat_id INTEGER UNIQUE,projects TEXT,notifications INTEGER DEFAULT 1,paired_at REAL,revoked INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS memories(user_id INTEGER,chat_id INTEGER,document TEXT,PRIMARY KEY(user_id,chat_id));
            CREATE TABLE IF NOT EXISTS confirmations(id TEXT PRIMARY KEY,user_id INTEGER,chat_id INTEGER,document TEXT,expires REAL,state TEXT);
            CREATE TABLE IF NOT EXISTS updates(id INTEGER PRIMARY KEY,created REAL);
            CREATE TABLE IF NOT EXISTS rate_limits(user_id INTEGER,bucket INTEGER,count INTEGER,PRIMARY KEY(user_id,bucket));
            CREATE TABLE IF NOT EXISTS notification_context(chat_id INTEGER,message_id INTEGER,document TEXT,PRIMARY KEY(chat_id,message_id));
            CREATE TABLE IF NOT EXISTS model_budget(day INTEGER PRIMARY KEY,calls INTEGER);
            CREATE TABLE IF NOT EXISTS command_audit(id TEXT PRIMARY KEY,user_id INTEGER,chat_id INTEGER,document TEXT,created REAL);
            ''')
            if 'notification_types' not in {row[1] for row in db.execute('PRAGMA table_info(pairs)')}:
                db.execute('ALTER TABLE pairs ADD COLUMN notification_types TEXT')

    @contextmanager
    def connect(self):
        connection=sqlite3.connect(self.path,timeout=10);connection.row_factory=sqlite3.Row
        connection.execute('PRAGMA journal_mode=WAL');connection.execute('PRAGMA foreign_keys=ON')
        try:
            with connection: yield connection
        finally: connection.close()

    def create_pairing(self,user_id,projects,ttl=300):
        if type(user_id) is not int or user_id<=0 or not projects or any(type(p) is not int or p<=0 for p in projects):
            raise ValueError('NUMERIC_USER_AND_PROJECT_IDS_REQUIRED')
        code=secrets.token_urlsafe(18)
        with self.connect() as db:
            db.execute('DELETE FROM pair_codes WHERE user_id=?',(user_id,))
            db.execute('INSERT INTO pair_codes(hash,user_id,projects,expires) VALUES(?,?,?,?)',(code_hash(code),user_id,canonical(projects),time.time()+ttl))
        return code

    def pair(self,code,user_id,chat_id):
        if type(user_id) is not int or user_id<=0 or chat_id!=user_id:return False
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM pair_codes WHERE user_id=? AND used=0 ORDER BY expires DESC LIMIT 1',(user_id,)).fetchone()
            if not row or row['expires']<time.time() or row['attempts']>=5:return False
            db.execute('UPDATE pair_codes SET attempts=attempts+1 WHERE hash=?',(row['hash'],))
            if not secrets.compare_digest(row['hash'],code_hash(str(code))):return False
            db.execute('UPDATE pair_codes SET used=1 WHERE hash=?',(row['hash'],))
            db.execute('INSERT OR REPLACE INTO pairs(user_id,chat_id,projects,paired_at,revoked) VALUES(?,?,?,?,0)',(user_id,chat_id,row['projects'],time.time()))
            return True

    def authorize(self,user_id,chat_id):
        if user_id!=chat_id or type(user_id) is not int or user_id<=0:return None
        with self.connect() as db:row=db.execute('SELECT * FROM pairs WHERE user_id=? AND chat_id=? AND revoked=0',(user_id,chat_id)).fetchone()
        return {**dict(row),'project_ids':json.loads(row['projects'])} if row else None

    def revoke(self,user_id):
        with self.connect() as db:
            db.execute('UPDATE pairs SET revoked=1 WHERE user_id=?',(user_id,))
            db.execute("UPDATE confirmations SET state='CANCELLED' WHERE user_id=? AND state='PENDING'",(user_id,))

    def recipients(self):
        with self.connect() as db:rows=db.execute('SELECT * FROM pairs WHERE revoked=0 AND notifications=1').fetchall()
        from .notifications import TYPES
        return [{**dict(row),'project_ids':json.loads(row['projects']),'notifications':bool(row['notifications']),
                 'notification_types':json.loads(row['notification_types']) if row['notification_types'] is not None else sorted(TYPES)} for row in rows]

    def set_notifications(self,user_id,enabled):
        with self.connect() as db:db.execute('UPDATE pairs SET notifications=? WHERE user_id=?',(int(enabled),user_id))

    def set_notification_types(self,user_id,types):
        from .notifications import TYPES
        if not isinstance(types,list) or any(kind not in TYPES for kind in types):
            raise ValueError('NOTIFICATION_TYPES_INVALID')
        with self.connect() as db:
            db.execute('UPDATE pairs SET notification_types=? WHERE user_id=?',(canonical(list(dict.fromkeys(types))),user_id))

    def memory(self,user_id,chat_id):
        with self.connect() as db:row=db.execute('SELECT document FROM memories WHERE user_id=? AND chat_id=?',(user_id,chat_id)).fetchone()
        return json.loads(row[0]) if row else {'conversation_id':str(uuid.uuid4()),'current_project_id':None,'current_task_id':None,'current_run_id':None,'recent_messages':[],'summary':'','constraints':[],'pending_action':None,'pending_confirmation':None}

    def save_memory(self,user_id,chat_id,value):
        value={**value,'updated_at':time.time()}
        with self.connect() as db:db.execute('INSERT OR REPLACE INTO memories VALUES(?,?,?)',(user_id,chat_id,canonical(value)))

    def append_message(self,user_id,chat_id,role,text):
        memory=self.memory(user_id,chat_id);messages=memory.setdefault('recent_messages',[])
        messages.append({'role':role,'text':text[:8000],'at':time.time()})
        if len(messages)>16:
            older=messages[:-16]
            # Historical excerpts are explicitly marked; live state always comes from tools.
            memory['summary']=(memory.get('summary','')+'\n'+'\n'.join(m['role']+': '+m['text'][:500] for m in older))[-5000:]
            memory['recent_messages']=messages[-16:]
        self.save_memory(user_id,chat_id,memory)

    def propose(self,user_id,chat_id,document,ttl=180):
        nonce=secrets.token_urlsafe(18)
        with self.connect() as db:
            db.execute("UPDATE confirmations SET state='SUPERSEDED' WHERE user_id=? AND chat_id=? AND state='PENDING'",(user_id,chat_id))
            db.execute('INSERT INTO confirmations VALUES(?,?,?,?,?,?)',(nonce,user_id,chat_id,canonical(document),time.time()+ttl,'PENDING'))
        memory=self.memory(user_id,chat_id);memory.update(pending_action=document,pending_confirmation=nonce);self.save_memory(user_id,chat_id,memory)
        return nonce

    def claim_confirmation(self,nonce,user_id,chat_id):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute("SELECT * FROM confirmations WHERE id=? AND user_id=? AND chat_id=? AND state='PENDING' AND expires>=?",(nonce,user_id,chat_id,time.time())).fetchone()
            if not row:return None
            db.execute("UPDATE confirmations SET state='PROCESSING' WHERE id=?",(nonce,))
        return json.loads(row['document'])

    def finish_confirmation(self,nonce,user_id,chat_id,result):
        with self.connect() as db:db.execute("UPDATE confirmations SET state='DONE' WHERE id=? AND user_id=? AND chat_id=?",(nonce,user_id,chat_id))
        self.audit(user_id,chat_id,{'confirmation_id':nonce,'result':result})
        memory=self.memory(user_id,chat_id);memory.update(pending_action=None,pending_confirmation=None);self.save_memory(user_id,chat_id,memory)

    def cancel_pending(self,user_id,chat_id):
        with self.connect() as db:db.execute("UPDATE confirmations SET state='CANCELLED' WHERE user_id=? AND chat_id=? AND state='PENDING'",(user_id,chat_id))
        memory=self.memory(user_id,chat_id);memory.update(pending_action=None,pending_confirmation=None);self.save_memory(user_id,chat_id,memory)

    def claim_update(self,update_id):
        with self.connect() as db:
            result=db.execute('INSERT OR IGNORE INTO updates VALUES(?,?)',(update_id,time.time()))
            return result.rowcount==1

    def rate_limit(self,user_id,limit=10):
        bucket=int(time.time()//60)
        with self.connect() as db:
            db.execute('INSERT INTO rate_limits VALUES(?,?,1) ON CONFLICT(user_id,bucket) DO UPDATE SET count=count+1',(user_id,bucket))
            return db.execute('SELECT count FROM rate_limits WHERE user_id=? AND bucket=?',(user_id,bucket)).fetchone()[0]<=limit

    def reserve_model_call(self,limit):
        day=int(time.time()//86400)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT calls FROM model_budget WHERE day=?',(day,)).fetchone()
            if row and row[0]>=limit:raise ValueError('GEMINI_DAILY_LOCAL_BUDGET_EXHAUSTED')
            db.execute('INSERT INTO model_budget VALUES(?,1) ON CONFLICT(day) DO UPDATE SET calls=calls+1',(day,))

    def record_notification(self,chat_id,message_id,task_id,project_id,run_id=None):
        with self.connect() as db:db.execute('INSERT OR REPLACE INTO notification_context VALUES(?,?,?)',(chat_id,message_id,canonical({'task_id':task_id,'project_id':project_id,'run_id':run_id})))

    def notification_context(self,chat_id,message_id):
        with self.connect() as db:row=db.execute('SELECT document FROM notification_context WHERE chat_id=? AND message_id=?',(chat_id,message_id)).fetchone()
        return json.loads(row[0]) if row else None

    def audit(self,user_id,chat_id,document):
        with self.connect() as db:db.execute('INSERT INTO command_audit VALUES(?,?,?,?,?)',(str(uuid.uuid4()),user_id,chat_id,canonical(document),time.time()))
