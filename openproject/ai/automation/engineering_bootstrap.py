"""Install only selected role instructions/skills in root-owned OpenClaw workspaces."""
import hashlib
import json

from gateway.engineering_personas import instructions

ROLE_SKILL={'dev':'engineering-development','reviewer':'engineering-review','qa':'engineering-qa'}


def install(worker,unit,application):
    files={};roles={}
    for role,skill in ROLE_SKILL.items():
        workspace='/opt/qldapm/agents/'+unit+'/'+role
        body=(worker.ROOT/'openproject/ai/engineering_skills'/skill/'SKILL.md').read_text(encoding='utf-8')
        persona=instructions(role,application)
        files[workspace+'/AGENTS.md']=persona+'\n## Activated engineering skill\n\n'+body
        files[workspace+'/SOUL.md']=f'# {role}\n{persona}\nUse concise evidence-oriented handoff. Keep reviewer independent from Dev; QA executes and reports actual commands/exit codes.\n'
        files[workspace+'/skills/'+skill+'/SKILL.md']=body
        files[application+'/skills/'+skill+'/SKILL.md']=body
        roles[role]={'workspace':application,'cwd':application,'skills':[skill],'contextInjection':'always'}
        if role=='qa':roles[role]['tools']={'profile':'coding','deny':['write','edit','apply_patch']}
    code=('from pathlib import Path\nimport os\n'
        'for name,body in document["files"].items():\n'
        ' p=Path(name);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body);p.chmod(0o444)\n'
        ' for parent in [p.parent,*list(p.parents)[:3]]:\n'
        '  if str(parent).startswith("/opt/qldapm/agents/"):parent.chmod(0o755)\n'
        'p=Path("/home/openclaw/.openclaw/openclaw.json");c=json.loads(p.read_text())\n'
        'for role,settings in document["roles"].items():c["agents"]["entries"][role].update(settings)\n'
        'c.setdefault("skills",{}).setdefault("workshop",{})["autonomous"]={"mode":"off"}\n'
        'p.write_text(json.dumps(c));p.chmod(0o600);os.chown(p,1000,1000)\n')
    worker.python(code,{'files':files,'roles':roles},root=True)
    worker.wsl(['/usr/local/bin/openclaw','config','validate'])
    return {'roles':roles,'files_sha256':{name:hashlib.sha256(body.encode()).hexdigest() for name,body in files.items()},
        'context_injection':'always for selected roles; shared default unchanged','workshop_autonomous':'off'}


def activate(worker,unit,role,application):
    """Sequential role sessions share the scoped application filesystem boundary."""
    source='/opt/qldapm/agents/'+unit+'/'+role
    result=worker.python('from pathlib import Path\nimport hashlib\nresult={}\n'
        'for name in document["names"]:\n'
        ' origin=Path(document["source"])/name;target=Path(document["application"])/name\n'
        ' if target.exists() and target.stat().st_uid!=0:\n'
        '  old=target.read_bytes();backup=Path(document["source"]).parent/("preserved-"+name.replace("/","__")+"-"+hashlib.sha256(old).hexdigest());backup.write_bytes(old);backup.chmod(0o600)\n'
        ' target.write_bytes(origin.read_bytes());target.chmod(0o444)\n'
        ' import os;os.chown(target,0,0);result[name]=hashlib.sha256(target.read_bytes()).hexdigest()\n'
        'print(json.dumps(result))',{'source':source,'application':application,'names':['AGENTS.md','SOUL.md','skills/'+ROLE_SKILL[role]+'/SKILL.md']},root=True)
    return json.loads(result.stdout)


def verify_files(worker,application,expected):
    current=json.loads(worker.python('from pathlib import Path\nimport hashlib\nprint(json.dumps({name:hashlib.sha256((Path(document["application"])/name).read_bytes()).hexdigest() for name in document["names"]}))',{'application':application,'names':list(expected)}).stdout)
    if current!=expected:raise RuntimeError('ENGINEERING_BOOTSTRAP_CHANGED')
    return True


def verify_report(document,role):
    report=document.get('result',{}).get('meta',{}).get('systemPromptReport',{})
    files=report.get('injectedWorkspaceFiles',[])
    injected={v.get('name') for v in files if not v.get('missing') and not v.get('truncated') and v.get('injectedChars',v.get('rawChars',0))>0}
    skills={v['name'] for v in report.get('skills',{}).get('entries',[])}
    if not {'AGENTS.md','SOUL.md'}<=injected or skills!={ROLE_SKILL[role]}:
        raise RuntimeError('ENGINEERING_PERSONA_SKILL_NOT_LOADED')
    return {'role':role,'workspace':report.get('workspaceDir'),'persona_injected':sorted(injected),
        'skills_loaded':sorted(skills),'skills_hash':report.get('skills',{}).get('hash'),'system_prompt_source':report.get('source')}
