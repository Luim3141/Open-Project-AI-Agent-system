import json
import re

# 1. Update engineering_reporting.py
with open('openproject/ai/gateway/engineering_reporting.py', 'rb') as f:
    rep_code = f.read().decode('utf-8').replace('\r\n', '\n')

old_setup = '''def setup_reporting(store: Any) -> None:
    """Ensure engineering_reports table exists."""
    with store.connect() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS engineering_reports ("
            "id TEXT PRIMARY KEY, "
            "project INTEGER NOT NULL, "
            "report_type TEXT NOT NULL, "
            "title TEXT NOT NULL, "
            "document TEXT NOT NULL, "
            "created REAL NOT NULL"
            ")"
        )'''

new_setup = '''def setup_reporting(store: Any) -> None:
    """Ensure engineering_reports, schedules, and notifications tables exist."""
    with store.connect() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS engineering_reports ("
            "id TEXT PRIMARY KEY, "
            "project INTEGER NOT NULL, "
            "report_type TEXT NOT NULL, "
            "title TEXT NOT NULL, "
            "document TEXT NOT NULL, "
            "created REAL NOT NULL"
            ")"
        )
        db.execute(
            "CREATE TABLE IF NOT EXISTS engineering_report_schedules ("
            "project INTEGER PRIMARY KEY, "
            "daily_enabled BOOLEAN NOT NULL DEFAULT 1, "
            "daily_hour INTEGER NOT NULL DEFAULT 8, "
            "daily_minute INTEGER NOT NULL DEFAULT 0, "
            "weekly_enabled BOOLEAN NOT NULL DEFAULT 1, "
            "weekly_day INTEGER NOT NULL DEFAULT 1, "
            "weekly_hour INTEGER NOT NULL DEFAULT 9, "
            "weekly_minute INTEGER NOT NULL DEFAULT 0, "
            "last_daily_run REAL, "
            "last_weekly_run REAL, "
            "timezone TEXT NOT NULL DEFAULT 'Asia/Ho_Chi_Minh', "
            "updated REAL NOT NULL"
            ")"
        )
        db.execute(
            "CREATE TABLE IF NOT EXISTS engineering_notifications ("
            "id TEXT PRIMARY KEY, "
            "project INTEGER NOT NULL, "
            "actor INTEGER, "
            "level TEXT NOT NULL, "
            "title TEXT NOT NULL, "
            "message TEXT NOT NULL, "
            "link TEXT, "
            "unread BOOLEAN NOT NULL DEFAULT 1, "
            "created REAL NOT NULL"
            ")"
        )
        db.execute(
            "INSERT OR IGNORE INTO engineering_report_schedules "
            "(project, daily_enabled, daily_hour, daily_minute, weekly_enabled, weekly_day, weekly_hour, weekly_minute, updated) "
            "VALUES (6, 1, 8, 0, 1, 1, 9, 0, ?)",
            (time.time(),)
        )'''

assert old_setup in rep_code, "old_setup not found"
rep_code = rep_code.replace(old_setup, new_setup)

additional_reporting_functions = '''

def get_schedule(service: Any, actor: int) -> Dict[str, Any]:
    from .engineering import authorized
    authorized(service, actor)
    setup_reporting(service.store)
    with service.store.connect() as db:
        row = db.execute("SELECT * FROM engineering_report_schedules WHERE project=6").fetchone()
    if not row:
        return {"project": 6, "daily_enabled": True, "daily_hour": 8, "daily_minute": 0, "weekly_enabled": True, "weekly_day": 1, "weekly_hour": 9, "weekly_minute": 0}
    return dict(row)


def update_schedule(service: Any, actor: int, config: Dict[str, Any]) -> Dict[str, Any]:
    from .engineering import authorized
    authorized(service, actor)
    setup_reporting(service.store)
    now = time.time()
    with service.store.connect() as db:
        db.execute(
            "UPDATE engineering_report_schedules SET "
            "daily_enabled=?, daily_hour=?, daily_minute=?, weekly_enabled=?, weekly_day=?, weekly_hour=?, weekly_minute=?, updated=? "
            "WHERE project=6",
            (
                int(bool(config.get("daily_enabled", True))),
                int(config.get("daily_hour", 8)),
                int(config.get("daily_minute", 0)),
                int(bool(config.get("weekly_enabled", True))),
                int(config.get("weekly_day", 1)),
                int(config.get("weekly_hour", 9)),
                int(config.get("weekly_minute", 0)),
                now,
            )
        )
    service.store.record(actor, "engineering_report_schedule_updated", "project6", "ok")
    return get_schedule(service, actor)


def list_notifications(service: Any, actor: int, limit: int = 10, unread_only: bool = False) -> List[Dict[str, Any]]:
    setup_reporting(service.store)
    with service.store.connect() as db:
        query = "SELECT * FROM engineering_notifications WHERE project=6"
        params = []
        if unread_only:
            query += " AND unread=1"
        query += " ORDER BY created DESC LIMIT ?"
        params.append(limit)
        rows = db.execute(query, tuple(params)).fetchall()
    return [dict(r) for r in rows]


def dismiss_notification(service: Any, actor: int, notification_id: str) -> Dict[str, Any]:
    setup_reporting(service.store)
    with service.store.connect() as db:
        count = db.execute("UPDATE engineering_notifications SET unread=0 WHERE id=? AND project=6", (notification_id,)).rowcount
    return {"id": notification_id, "dismissed": count > 0}


def check_and_run_scheduled_reports(service: Any, actor: int = 20, now: Optional[float] = None) -> Dict[str, Any]:
    """Autonomous reporting check independent of Engineering AUTO mode."""
    setup_reporting(service.store)
    now = time.time() if now is None else now
    with service.store.connect() as db:
        sched = db.execute("SELECT * FROM engineering_report_schedules WHERE project=6").fetchone()
    if not sched:
        return {"checked": False, "reason": "NO_SCHEDULE"}

    reports_generated = []
    last_daily = sched["last_daily_run"] or 0
    if sched["daily_enabled"] and (now - last_daily >= 82800):
        try:
            doc = generate_report(service, actor, "DAILY", include_narrative=False)
            with service.store.connect() as db:
                db.execute("UPDATE engineering_report_schedules SET last_daily_run=? WHERE project=6", (now,))
                db.execute(
                    "INSERT INTO engineering_notifications (id, project, actor, level, title, message, link, created) "
                    "VALUES (?, 6, ?, 'SUCCESS', 'Báo cáo Tiến độ Hằng ngày', ?, ?, ?)",
                    (
                        str(uuid.uuid4()),
                        actor,
                        f"Báo cáo tiến độ hằng ngày ({doc['title']}) đã được tự động tạo theo lịch.",
                        "/projects/ai-dev-demo/qldapm_ai/engineering",
                        now,
                    )
                )
            reports_generated.append({"type": "DAILY", "id": doc["id"]})
        except Exception as exc:
            logger.warning(f"Auto daily report generation failed: {exc}")

    last_weekly = sched["last_weekly_run"] or 0
    if sched["weekly_enabled"] and (now - last_weekly >= 6 * 86400):
        try:
            doc = generate_report(service, actor, "WEEKLY", include_narrative=False)
            with service.store.connect() as db:
                db.execute("UPDATE engineering_report_schedules SET last_weekly_run=? WHERE project=6", (now,))
                db.execute(
                    "INSERT INTO engineering_notifications (id, project, actor, level, title, message, link, created) "
                    "VALUES (?, 6, ?, 'SUCCESS', 'Báo cáo Tiến độ Hằng tuần', ?, ?, ?)",
                    (
                        str(uuid.uuid4()),
                        actor,
                        f"Báo cáo tiến độ tuần ({doc['title']}) đã được tự động tạo theo lịch.",
                        "/projects/ai-dev-demo/qldapm_ai/engineering",
                        now,
                    )
                )
            reports_generated.append({"type": "WEEKLY", "id": doc["id"]})
        except Exception as exc:
            logger.warning(f"Auto weekly report generation failed: {exc}")

    return {"checked": True, "generated": reports_generated}
'''

rep_code = rep_code.rstrip() + additional_reporting_functions

with open('openproject/ai/gateway/engineering_reporting.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(rep_code)
print("UPDATED engineering_reporting.py")

# 2. Update engineering.py status return
with open('openproject/ai/gateway/engineering.py', 'rb') as f:
    eng_code = f.read().decode('utf-8').replace('\r\n', '\n')

old_eng_return = '''    return {'project_id':PROJECT,'mode':mode,'runs':runs,'backlog':units,'tasks':tasks,'plans':plans,'quota':quota,'delivery_worker':worker,'github':github_info,
        'profiles':[engineering_profile(role) for role in ['supervisor','pm','ba','dev','reviewer','qa']]}'''

new_eng_return = '''    from . import engineering_reporting
    try:
        engineering_reporting.check_and_run_scheduled_reports(service, actor)
    except Exception:
        pass
    reporting_schedule = engineering_reporting.get_schedule(service, actor)
    notifications = engineering_reporting.list_notifications(service, actor, limit=5, unread_only=True)
    all_reports = engineering_reporting.list_reports(service, actor, limit=5)
    return {'project_id':PROJECT,'mode':mode,'runs':runs,'backlog':units,'tasks':tasks,'plans':plans,'quota':quota,'delivery_worker':worker,'github':github_info,
        'profiles':[engineering_profile(role) for role in ['supervisor','pm','ba','dev','reviewer','qa']],
        'reporting_schedule':reporting_schedule,'notifications':notifications,'recent_reports':all_reports.get('reports',[])}'''

assert old_eng_return in eng_code, "old_eng_return not found"
eng_code = eng_code.replace(old_eng_return, new_eng_return)

with open('openproject/ai/gateway/engineering.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(eng_code)
print("UPDATED engineering.py")

# 3. Update engineering_github_sync.py
with open('openproject/ai/gateway/engineering_github_sync.py', 'rb') as f:
    gh_code = f.read().decode('utf-8').replace('\r\n', '\n')

old_pr_append = '''        prs.append({
            "number": pr.get("number"),
            "title": pr.get("title"),
            "state": pr.get("state"),
            "is_merged": is_merged,
            "merge_target": merge_target,
            "merged_at": pr.get("merged_at"),
            "head_sha": pr.get("head", {}).get("sha", ""),
            "base_ref": base_ref,
            "html_url": pr.get("html_url", ""),
            "draft": pr.get("draft", False),
            "created_at": pr.get("created_at"),
            "updated_at": pr.get("updated_at"),
        })'''

new_pr_append = '''        reviews_state = "NO_REVIEWS_ON_GITHUB"
        checks_state = "NO_CI_CHECKS_CONFIGURED"
        if token:
            try:
                rev_url = f"https://api.github.com/repos/{repo}/pulls/{pr.get('number')}/reviews"
                rev_req = urllib.request.Request(rev_url, headers=headers)
                with urllib.request.urlopen(rev_req, timeout=5) as rev_resp:
                    rev_data = json.loads(rev_resp.read().decode("utf-8"))
                    if rev_data:
                        reviews_state = rev_data[-1].get("state", "REVIEWED")
                    else:
                        reviews_state = "NO_REVIEWS_ON_GITHUB"
            except Exception:
                reviews_state = "NO_REVIEWS_ON_GITHUB"

        prs.append({
            "number": pr.get("number"),
            "title": pr.get("title"),
            "state": pr.get("state"),
            "is_merged": is_merged,
            "merge_target": merge_target,
            "merged_at": pr.get("merged_at"),
            "head_sha": pr.get("head", {}).get("sha", ""),
            "base_ref": base_ref,
            "html_url": pr.get("html_url", ""),
            "draft": pr.get("draft", False),
            "created_at": pr.get("created_at"),
            "updated_at": pr.get("updated_at"),
            "reviews_state": reviews_state,
            "checks_state": checks_state,
        })'''

assert old_pr_append in gh_code, "old_pr_append not found"
gh_code = gh_code.replace(old_pr_append, new_pr_append)

with open('openproject/ai/gateway/engineering_github_sync.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(gh_code)
print("UPDATED engineering_github_sync.py")

# 4. Update catalog.py
with open('openproject/ai/gateway/catalog.py', 'rb') as f:
    cat_code = f.read().decode('utf-8').replace('\r\n', '\n')

old_cat_head = '''ARGUMENTS = {
    'engineering_report_generate':'{report_type?:DAILY|WEEKLY|ON_DEMAND,include_narrative?:boolean}; Project6 PM/Owner; generates a structured engineering progress report with deterministic factual metrics and optional Gemini narrative','''

new_cat_head = '''ARGUMENTS = {
    'engineering_report_schedule_get':'{}; Project6 PM/Owner; retrieves the automated reporting schedule',
    'engineering_report_schedule_update':'{daily_enabled?:boolean,daily_hour?:int,daily_minute?:int,weekly_enabled?:boolean,weekly_day?:int,weekly_hour?:int,weekly_minute?:int}; Project6 PM/Owner; updates the automated reporting schedule',
    'engineering_notifications_list':'{limit?:int,unread_only?:boolean}; Project6 PM/Owner; retrieves recent system and reporting notifications',
    'engineering_notifications_dismiss':'{id:UUID}; Project6 PM/Owner; marks a notification as read',
    'engineering_report_generate':'{report_type?:DAILY|WEEKLY|ON_DEMAND,include_narrative?:boolean}; Project6 PM/Owner; generates a structured engineering progress report with deterministic factual metrics and optional Gemini narrative','''

assert old_cat_head in cat_code, "old_cat_head not found"
cat_code = cat_code.replace(old_cat_head, new_cat_head)

with open('openproject/ai/gateway/catalog.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(cat_code)
print("UPDATED catalog.py")

# 5. Update permissions.py
with open('openproject/ai/gateway/permissions.py', 'rb') as f:
    perm_code = f.read().decode('utf-8').replace('\r\n', '\n')

old_perm = '''PM_ONLY = {"engineering_report_generate", "engineering_report_list", "engineering_report_get",'''
new_perm = '''PM_ONLY = {"engineering_report_schedule_get", "engineering_report_schedule_update", "engineering_notifications_list", "engineering_notifications_dismiss", "engineering_report_generate", "engineering_report_list", "engineering_report_get",'''

assert old_perm in perm_code, "old_perm not found"
perm_code = perm_code.replace(old_perm, new_perm)

with open('openproject/ai/gateway/permissions.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(perm_code)
print("UPDATED permissions.py")

# 6. Update service.py
with open('openproject/ai/gateway/service.py', 'rb') as f:
    srv_code = f.read().decode('utf-8').replace('\r\n', '\n')

old_lit = '''action: Literal["engineering_report_generate", "engineering_report_list", "engineering_report_get",'''
new_lit = '''action: Literal["engineering_report_schedule_get", "engineering_report_schedule_update", "engineering_notifications_list", "engineering_notifications_dismiss", "engineering_report_generate", "engineering_report_list", "engineering_report_get",'''
assert old_lit in srv_code, "old_lit not found"
srv_code = srv_code.replace(old_lit, new_lit)

old_scope = '''if self.config.get('_engineering_scope') and command.action not in {'engineering_report_generate','engineering_report_list','engineering_report_get','engineering_github_sync','''
new_scope = '''if self.config.get('_engineering_scope') and command.action not in {'engineering_report_schedule_get','engineering_report_schedule_update','engineering_notifications_list','engineering_notifications_dismiss','engineering_report_generate','engineering_report_list','engineering_report_get','engineering_github_sync','''
assert old_scope in srv_code, "old_scope not found"
srv_code = srv_code.replace(old_scope, new_scope)

old_router = '''            elif command.action=='engineering_report_generate':
                from . import engineering_reporting'''
new_router = '''            elif command.action=='engineering_report_schedule_get':
                from . import engineering_reporting
                self.keys(command.arguments,set(),set())
                result=engineering_reporting.get_schedule(self,actor)
            elif command.action=='engineering_report_schedule_update':
                from . import engineering_reporting
                self.keys(command.arguments,{'daily_enabled','daily_hour','daily_minute','weekly_enabled','weekly_day','weekly_hour','weekly_minute'},set())
                result=engineering_reporting.update_schedule(self,actor,command.arguments)
            elif command.action=='engineering_notifications_list':
                from . import engineering_reporting
                self.keys(command.arguments,{'limit','unread_only'},set())
                result=engineering_reporting.list_notifications(self,actor,int(command.arguments.get('limit',10)),bool(command.arguments.get('unread_only',False)))
            elif command.action=='engineering_notifications_dismiss':
                from . import engineering_reporting
                self.keys(command.arguments,{'id'},{'id'})
                result=engineering_reporting.dismiss_notification(self,actor,command.arguments['id'])
            elif command.action=='engineering_report_generate':
                from . import engineering_reporting'''
assert old_router in srv_code, "old_router not found"
srv_code = srv_code.replace(old_router, new_router)

with open('openproject/ai/gateway/service.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(srv_code)
print("UPDATED service.py")
