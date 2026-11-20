"""Source inventory and read-only fingerprints. Never emits settings or credential values."""
import ast,hashlib,importlib.util,json,os,sqlite3,subprocess,sys,time
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
def save(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def tree(path):return ast.parse((ROOT/path).read_text(encoding='utf-8-sig'))
def assigned(path,name):
    for n in tree(path).body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets):return ast.literal_eval(n.value)
def inventory():
    rows=[]
    def add(module,feature,source,method,expected):
        rows.append({'id':f'F{len(rows)+1:03}','module':module,'feature':feature,'source':source,'method':method,'expected':expected,'actual':'Chưa chạy trong đợt này','status':'NOT TESTED','evidence':[]})
    app='openproject/ai/gateway/app.py'
    for n in ast.walk(tree(app)):
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Route':
            path=ast.literal_eval(n.args[0]);methods=next((ast.literal_eval(k.value) for k in n.keywords if k.arg=='methods'),['GET','HEAD'])
            add('Gateway route','/'.join(methods)+' '+path,f'{app}:{n.lineno}','contract + MAIN read or isolated mutation','Schema/auth/dependency/error contract; actual business read-back')
    service='openproject/ai/gateway/service.py'
    for n in ast.walk(tree(service)):
        if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and n.target.id=='action':
            for a in ast.literal_eval(n.annotation.slice):add('Gateway command',a,f'{service}:{n.lineno}','isolated contract / authorized read','Validated arguments, project/RBAC, honest status and audit; no forbidden MAIN write')
    tools='openproject/ai/telegram-ai/app/tools.py'
    models=next(n.value for n in tree(tools).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MODELS' for t in n.targets))
    for key in models.keys:add('Telegram tool',ast.literal_eval(key),tools,'contract + live Gateway adapter','Authorized user/project; read actual data or exact confirmation; no replay')
    for module,features in {
      'Telegram':['poller/token/webhook/one-consumer','Vietnamese multi-turn #398','reply notification397 context','pairing/unauthorized/stale/duplicate','restart conversation persistence','network/Gateway reconnect','Gemini exact model/quota/tool feedback'],
      'Runtime':['BA/PM planning379→398','Dev398 exact revision','Reviewer398 verdict/rework','QA398 JUnit64','OFF/AUTO/RUN_ONCE guards','checkpoint/resume/idempotency','Owner gates398 vs DONE397'],
      'Studio':['CommandCenter entry/Project/Task/deep link','Explorer/back/forward/reload','graph/nodes/edges/attempts/runtime/freshness','Inspector/timeline/artifacts/native/PR links','poll/error recovery/no stale overwrite','mobile touch/layout'],
      'Command Center':['Mission Control/queue/current run','Workforce roles/availability','Intake/control actions/gates','Reports/Analysis/read/export/audit'],
      'OpenProject':['projects/search/details/journals/parent','members/ACL/workflow status'],
      'GitHub':['auth/repository/branch/commit/PR15','review/CI/provenance/state sync'],
      'RAG':['known-document lexical/semantic/citations','project/role/actor isolation','index/sync/storage/recovery','Telegram knowledge adapter/report integration'],
      'Notifications':['N01 completed397','N02 dev-only no completion','N03 QA_FAILED','N04 BLOCKED','N05 awaiting owner398','N06 n8n offline/retry','N07 Telegram offline/persistence','N08 duplicate semantics','N09 reply context'],
      'Operations':['startup/restart policy/persistence/networks','controlled Telegram/Gateway restart/no replay']}.items():
        for feature in features:add(module,feature,'Source + linked evidence','component/integration/UI/historical/live as applicable','Functional behavior, distinguish evidence levels')
    save('matrix.json',rows)
    return rows
def baseline():
    sys.path.insert(0,str(ROOT/'docs/agent-studio-v2-stabilization'))
    from preservation import capture
    data=capture();data['at']=time.time();data['git']={'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip(),'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()}
    data['containers']={}
    for name in ['qldapm-openproject-web-1','qldapm-ai-gateway-1','qldapm-ai-telegram-ai-1','qldapm-n8n-main']:
        d=json.loads(subprocess.check_output(['docker','inspect',name]))[0]
        data['containers'][name]={'id':d['Id'],'image':d['Image'],'started_at':d['State']['StartedAt'],'restart_policy':d['HostConfig']['RestartPolicy'],'health':d['State'].get('Health',{}).get('Status')}
    data['sources']={str(f.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest() for base in ['openproject/ai/gateway','openproject/ai/telegram-ai/app','openproject/ai/core/overlay'] for f in (ROOT/base).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix in {'.py','.rb','.erb','.js','.json','.css'}}
    assert not (OUT/'baseline.json').exists();save('baseline.json',data)
    return data
if __name__=='__main__':
    rows=inventory();data=baseline();print(json.dumps({'inventory_rows':len(rows),'module_counts':{m:sum(r['module']==m for r in rows) for m in sorted(set(r['module'] for r in rows))},'baseline_sources':len(data['sources']),'runtime_images':{k:v['image'] for k,v in data['containers'].items()},'mode':data['gateway']['mode'],'active':data['gateway']['active']}))
