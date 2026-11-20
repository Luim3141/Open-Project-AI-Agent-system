"""Patch gateway and openproject files for Milestone 1 (Owner access)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def patch_file(path: Path, replacements: list[tuple[str, str]]):
    text = path.read_text(encoding='utf-8')
    for target, repl in replacements:
        if target not in text:
            # Try normalizing CRLF / LF
            target_norm = target.replace('\r\n', '\n')
            text_norm = text.replace('\r\n', '\n')
            if target_norm not in text_norm:
                raise ValueError(f"Target string not found in {path}:\n{target[:100]}")
            text = text_norm.replace(target_norm, repl.replace('\r\n', '\n'))
        else:
            text = text.replace(target, repl)
    path.write_text(text, encoding='utf-8')
    print(f"Patched {path}")


def main():
    # 1. gateway/service.py
    service_path = ROOT / "openproject/ai/gateway/service.py"
    patch_file(service_path, [
        (
            "self.config['project_id'] == 5\n                and AI_SYSTEM_OWNER in identity.get('capabilities', [])):",
            "self.config['project_id'] in (5, 6)\n                and AI_SYSTEM_OWNER in identity.get('capabilities', [])):"
        ),
        (
            """            if self.config.get('_engineering_scope'):
                with self.store.connect() as db:row=db.execute('SELECT payload FROM ai_queue WHERE id=? AND actor=?',(args['id'],actor)).fetchone()
                if row and json.loads(row[0]).get('engine')=='openclaw':
                    from .engineering_monitor import project
                    return project(self,who,authorized,task,run,json.loads(row[0]),receipts,events)""",
            """            if self.config.get('_engineering_scope'):
                with self.store.connect() as db:row=db.execute("SELECT q.actor, q.payload FROM ai_queue q WHERE q.id=? AND json_extract(q.payload,'$.project_id')=6 AND json_extract(q.payload,'$.engine')='openclaw'",(args['id'],)).fetchone()
                if row:
                    run_owner = row['actor']
                    run = self.store.agent_run(run_owner, 6, args['id'])
                    task = self.store.agent_task(run_owner, 6, run.task_id)
                    events, receipts = self.store.execution_records(run_owner, 6, args['id'])
                    from .engineering_monitor import project
                    return project(self,who,authorized,task,run,json.loads(row['payload']),receipts,events)"""
        ),
        (
            """        if action == "get_ai_run":
            self.keys(args, {"id"}, {"id"})
            run = self.store.run(actor, args["id"])
            result = run.get("result") or {}
            if self.config.get('_engineering_scope'):
                scoped_run=self.store.agent_run(actor,6,args['id'])
                scoped_task=self.store.agent_task(actor,6,scoped_run.task_id)""",
            """        if action == "get_ai_run":
            self.keys(args, {"id"}, {"id"})
            if self.config.get('_engineering_scope'):
                with self.store.connect() as db:q_row = db.execute("SELECT actor FROM ai_queue WHERE id=? AND json_extract(payload,'$.project_id')=6",(args['id'],)).fetchone()
                run_actor = q_row['actor'] if q_row else actor
            else:
                run_actor = actor
            run = self.store.run(run_actor, args["id"])
            result = run.get("result") or {}
            if self.config.get('_engineering_scope'):
                scoped_run=self.store.agent_run(run_actor,6,args['id'])
                scoped_task=self.store.agent_task(run_actor,6,scoped_run.task_id)"""
        )
    ])

    # 2. gateway/native.py
    native_path = ROOT / "openproject/ai/gateway/native.py"
    patch_file(native_path, [
        (
            """        if user.get("admin"):
            if not (expected == 18 and self.project_id == 5 and user.get("login") == "op-owner" and user.get("status") == "active"):
                raise PermissionError("IDENTITY_MISMATCH_OR_ADMIN_TOKEN")
            proof = self.call("/api/v3/qldapm/permissions")
            if not (proof.get("actor") == expected and proof.get("project_id") == self.project_id
                    and proof.get("role") == AI_SYSTEM_OWNER and AI_SYSTEM_OWNER in proof.get("capabilities", [])):
                raise PermissionError("AI_SYSTEM_OWNER_CAPABILITY_REQUIRED")
            return {"user_id": expected, "name": user.get("name"), "role": AI_SYSTEM_OWNER,
                    "project_id": self.project_id, "capabilities": [AI_SYSTEM_OWNER]}""",
            """        if user.get("admin"):
            if not (expected == 18 and self.project_id in (5, 6) and user.get("login") == "op-owner" and user.get("status") == "active"):
                raise PermissionError("IDENTITY_MISMATCH_OR_ADMIN_TOKEN")
            proof = self.call(f"/api/v3/qldapm/permissions?project_id={self.project_id}" if self.project_id == 6 else "/api/v3/qldapm/permissions")
            if not (proof.get("actor") == expected and proof.get("project_id") == self.project_id
                    and proof.get("role") == AI_SYSTEM_OWNER and AI_SYSTEM_OWNER in proof.get("capabilities", [])):
                raise PermissionError("AI_SYSTEM_OWNER_CAPABILITY_REQUIRED")
            return {"user_id": expected, "name": user.get("name"), "role": AI_SYSTEM_OWNER,
                    "project_id": self.project_id, "capabilities": [AI_SYSTEM_OWNER]}"""
        )
    ])

    # 3. gateway/business_runs.py
    business_runs_path = ROOT / "openproject/ai/gateway/business_runs.py"
    patch_file(business_runs_path, [
        (
            """    params=(actor,project,actor,project,state,state,'%'+search+'%')
    with store.connect() as db:
        total=db.execute('select count(*) from ('+query+')',params).fetchone()[0]
        rows=db.execute(query+' order by created '+order+',id '+order+' limit ? offset ?',(*params,limit,offset)).fetchall()
        items=[]
        for row in rows:
            receipts=[json.loads(r[0]) for r in db.execute('select document from gemini_call_receipts where actor=? and run_id=?',(actor,row['id']))]""",
            """    if project == 6:
        query=\"\"\"with entries as (
            select a.id,a.document,t.document task,0 business,json_extract(a.document,'$.created_at') created,
              json_extract(a.document,'$.state') state,json_extract(t.document,'$.instruction') request,r.result
            from agent_runs a join agent_tasks t on t.id=a.task_id and t.actor=a.actor and t.project=a.project
            left join ai_runs r on r.id=a.id and r.actor=a.actor where a.project=6
            union all
            select b.id,b.document,null,1,r.created,json_extract(b.document,'$.state'),json_extract(b.document,'$.request'),r.result
            from business_runs b join ai_runs r on r.id=b.id and r.actor=b.actor where b.project=6
            ) select * from entries where (?='ALL' or state=?) and request like ?\"\"\"
        params=(state,state,'%'+search+'%')
    else:
        params=(actor,project,actor,project,state,state,'%'+search+'%')
    with store.connect() as db:
        total=db.execute('select count(*) from ('+query+')',params).fetchone()[0]
        rows=db.execute(query+' order by created '+order+',id '+order+' limit ? offset ?',(*params,limit,offset)).fetchall()
        items=[]
        for row in rows:
            receipts=[json.loads(r[0]) for r in db.execute('select document from gemini_call_receipts where run_id=?',(row['id'],))] if project == 6 else [json.loads(r[0]) for r in db.execute('select document from gemini_call_receipts where actor=? and run_id=?',(actor,row['id']))]"""
        )
    ])

    # 4. core/overlay/app/models/qldapm/rbac.rb
    rbac_path = ROOT / "openproject/ai/core/overlay/app/models/qldapm/rbac.rb"
    patch_file(rbac_path, [
        (
            """    def self.ai_system_owner?(project, user, fresh: false)
      return false unless managed?(project) && project.id == 5 && user.is_a?(User) && user.id == 18
      current = fresh ? User.find_by(id: user.id) : user
      current && current.active? && current.admin? && current.login == "op-owner"
    end""",
            """    def self.ai_system_owner?(project, user, fresh: false)
      return false unless user.is_a?(User) && user.id == 18
      return false unless (project&.id == 5 && project&.identifier == "qldapm-local") ||
                          (project&.id == 6 && project&.identifier == "ai-dev-demo")
      current = fresh ? User.find_by(id: user.id) : user
      current && current.active? && current.admin? && current.login == "op-owner"
    end"""
        )
    ])

    # 5. core/overlay/lib/api/v3/qldapm/gates_api.rb
    gates_api_path = ROOT / "openproject/ai/core/overlay/lib/api/v3/qldapm/gates_api.rb"
    patch_file(gates_api_path, [
        (
            """          resource :permissions do
            get do
              project = Project.visible(current_user).find_by!(identifier: "qldapm-local")""",
            """          resource :permissions do
            get do
              project_ident = (params[:project_id].to_s == "6" || params[:project_id].to_s == "ai-dev-demo") ? "ai-dev-demo" : "qldapm-local"
              project = Project.visible(current_user).find_by!(identifier: project_ident)"""
        )
    ])

    # 6. core/overlay/app/controllers/qldapm_ai_controller.rb
    controller_path = ROOT / "openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb"
    patch_file(controller_path, [
        (
            """    if engineering_project?
      @role = Qldapm::Rbac.role(@project, User.current, fresh: true)
      return deny_access unless @role == 'PM' && !User.current.admin?
      return deny_access unless %w[show command executions execution].include?(action_name)
      @tools = %w[engineering_status engineering_run_once engineering_control engineering_plan engineering_cancel engineering_resume]
      return
    end""",
            """    if engineering_project?
      @role = Qldapm::Rbac.role(@project, User.current, fresh: true)
      return deny_access unless %w[PM AI_SYSTEM_OWNER].include?(@role)
      return deny_access unless %w[show command executions execution].include?(action_name)
      @tools = %w[engineering_status engineering_run_once engineering_control engineering_plan engineering_cancel engineering_resume]
      return
    end"""
        ),
        (
            """    if engineering_project?
      return head :forbidden unless @role == 'PM' && %w[engineering_status engineering_run_once engineering_control engineering_plan engineering_cancel engineering_resume].include?(action)""",
            """    if engineering_project?
      return head :forbidden unless %w[PM AI_SYSTEM_OWNER].include?(@role) && %w[engineering_status engineering_run_once engineering_control engineering_plan engineering_cancel engineering_resume].include?(action)"""
        )
    ])

    # 7. automation/EngineeringCore.Dockerfile
    dockerfile_core = ROOT / "openproject/ai/automation/EngineeringCore.Dockerfile"
    dockerfile_core.write_text(
        "FROM qldapm-phase2-base:core-08df5e2bda40\n"
        "COPY --chown=app:app core/overlay/app/models/qldapm/rbac.rb /app/app/models/qldapm/rbac.rb\n"
        "COPY --chown=app:app core/overlay/lib/api/v3/qldapm/gates_api.rb /app/lib/api/v3/qldapm/gates_api.rb\n"
        "COPY --chown=app:app core/overlay/app/controllers/qldapm_ai_controller.rb /app/app/controllers/qldapm_ai_controller.rb\n"
        "COPY --chown=app:app core/overlay/app/views/qldapm_ai/engineering.html.erb /app/app/views/qldapm_ai/engineering.html.erb\n",
        encoding='utf-8'
    )
    print("Updated EngineeringCore.Dockerfile")


if __name__ == "__main__":
    main()
