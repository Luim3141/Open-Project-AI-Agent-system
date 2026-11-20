"""Immutable pair: Rails session/CSRF and actual Native transitions on isolated Main clone."""
import ast,base64,datetime,json,os,subprocess,sys,importlib
from pathlib import Path
caption='--caption' in sys.argv;reports='--reports' in sys.argv or caption;polish='--polish' in sys.argv or reports
reuse_core='--reuse-core' in sys.argv
suffix='-caption' if caption else '-reports' if reports else '-polish' if polish else ''
release_setup=importlib.import_module('release_caption' if caption else 'release_reports' if reports else 'release_polish' if polish else 'release_cc')
from automation.main_native_clone import main_native_clone
OUT=Path(__file__).parent;ROOT=OUT.resolve().parents[4];release=release_setup.release
bundle,manifest=release.load_guarded(release_setup.BUNDLE);images=manifest['images']
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator'/('cc-qualification-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S'));private.mkdir()
def run(*args,data=None,timeout=300):
    p=subprocess.run(['docker',*args],input=data,capture_output=True,timeout=timeout)
    if p.returncode:(private/'failure.log').write_bytes(p.stdout+p.stderr);raise RuntimeError('CC_QUALIFICATION_FAILED_PRIVATE_LOG '+str(private))
    return p.stdout

# Clone-only API credentials and authentication fixtures; production MFA is untouched.
tree=ast.parse((OUT.parent/'integration-final/functional-completion/qualify_core.py').read_text())
ruby=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ruby' for t in n.targets))
start=ruby.index('# Actual Native HTTP on clone;');end=ruby.index('# Exact Rails routing/login filter',start)
ruby=ruby[:start]+"File.write('/tmp/cc-credentials.json',JSON.generate([18,20,25].to_h{|id|[id,Token::API.create_and_return_value(User.find(id))]}))\n"+ruby[end:]
ruby=ruby.replace("native_http:'PASS'","native_http:'SEPARATE_ACTUAL_NATIVE_CASE'")
old="command=JSON.parse(http.response.body);raise 'SYNC_FRESH_FRAGMENTS_FAILED' unless command['result']['request_id']==request_id && command['correlation_id']=='trace-command' && command['fragments']['tab-github'].include?('Remote changed')"
assert ruby.count(old)==1
ruby=ruby.replace(old,"command=JSON.parse(http.response.body);raise 'FAST_PERSISTED_ACK_FAILED' unless command['result']['request_id']==request_id && command['correlation_id']=='trace-command' && !command.key?('engineering') && !command.key?('fragments')")
ruby=ruby.replace("'status'=>'SUCCESS','command_id'=>'command-1'","'status'=>'QUEUED','operation_id'=>'operation-1','operation_state'=>'QUEUED','command_id'=>'command-1'")
if polish:
    marker="raise 'CSRF_TOKEN_MISSING' unless csrf"
    assert ruby.count(marker)==1
    ruby=ruby.replace(marker,marker+"\nreport_initializer=html.css('script').find{|s|s.text.include?('window.qccReportReader =')}\nraise 'REPORT_INITIALIZER_MISSING_OR_CSP_BLOCKED' unless report_initializer && report_initializer['nonce'].present?\n")
if reports:
    marker=" when 'engineering_report_get' then "
    assert ruby.count(marker)==1
    ruby=ruby.replace(marker,marker+"(command[:arguments][:id] || command[:arguments]['id'])=='audit-fixture' ? {'id'=>'audit-fixture','report_type'=>'WORKFLOW_AUDIT','facts'=>{'lock_version'=>3},'provenance'=>{'correlation_id'=>'fixture-trace'}} : ")
    marker='before_calls=Qldapm::AiBridge.observed.size'
    assert ruby.count(marker)==1
    ruby=ruby.replace(marker,"http.get('/projects/ai-dev-demo/qldapm-ai/reports/audit-fixture',headers:{'Accept'=>'application/json'})\nraise 'STRUCTURED_AUDIT_VIEW_FAILED' unless http.response.status==200 && JSON.parse(http.response.body).dig('reader','rendered_html').include?('lock_version')\n"+marker)
if caption:
    marker="raise 'CSRF_TOKEN_MISSING' unless csrf"
    assert ruby.count(marker)==1
    ruby=ruby.replace(marker,marker+"\nraise 'AI_NATIVE_NAVIGATION_NOT_FULL' unless html.at_css('#qldapm-command-center')['data-turbo']=='false'\nmenu=html.at_css('a.qldapm-ai-menu-item');raise 'AI_MENU_NAVIGATION_NOT_FULL' unless menu && menu['data-turbo']=='false'\n")
proof={}
def before_web(web):
    if reuse_core:
        saved=json.loads((OUT/'clone-qualification-v9.json').read_text());assert saved['status']=='PASS' and saved['images']['core']==images['core']
        expected={k:v for k,v in manifest['source_hashes'].items() if release.SOURCES[k][0]=='core'}
        assert release.runtime_hashes('core',images['core'])==expected
        proof['core']={**saved['core'],'reused_exact_core_image':True,'evidence':'clone-qualification-v9.json'}
        bootstrap="raise 'CLONE_ONLY' unless ENV['QLDAPM_TEST_ONLY']=='true';File.write('/tmp/cc-credentials.json',JSON.generate([18,20,25].to_h{|id|[id,Token::API.create_and_return_value(User.find(id))]}))"
        run('exec','-i',web,'bundle','exec','rails','runner','-',data=bootstrap.encode(),timeout=240)
    else:
        output=run('exec','-i',web,'bundle','exec','rails','runner','-',data=ruby.encode(),timeout=240)
        proof['core']=json.loads(output.decode().splitlines()[-1]);assert proof['core']['status']=='PASS'
    (private/'credentials.json').write_bytes(run('exec',web,'cat','/tmp/cc-credentials.json'))

# A private SQLite backup preserves the actual persisted source events/contracts.
release.snapshot_sqlite(private)
config=json.loads(release.run(['docker','exec','qldapm-ai-gateway-1','python','-c',"import json;print(json.dumps(json.load(open('/state/config.json'))))"]))
config['openproject_url']='http://web:8080';config['engineering']['status_sync']=json.loads((OUT/'status-sync-policy-draft.json').read_text())
config['engineering']['github_sync']['enabled']=False
(private/'config.json').write_text(json.dumps(config))
code=r'''
import json,time
from pathlib import Path
from gateway.store import Store,canonical
from gateway.service import Service
from gateway.engineering import scoped_service,control
from gateway import engineering_status_sync as sync
from gateway.engineering_github_operations import enqueue,snapshot
from gateway.engineering_lifecycle import resume,cancel
root=Path('/state');store=Store(root);config=json.load(open(root/'config.json'));service=scoped_service(Service(store,config,'/workspaces'),6)
sources=sync.sources(service);targets=set(config['engineering']['status_sync']['historical_native_ids']);sources=[s for s in sources if s['native_id'] in targets]
assert len(sources)==5
rows=[]
for source in sources:
 if not INCREMENTAL:
  preview=sync.preview(service,source);assert preview['state']=='DRY_RUN',preview
 history=[]
 for _ in range(10):
  result=sync.reconcile(service,source);history.append(result)
  if result['state']!='SYNCING':break
 if result['state']!='STATUS_SYNC_VERIFIED':raise AssertionError(result)
 policy,native,item=sync._context(service,source)
 assert item['_links']['status']['href']=='/api/v3/statuses/41' and item['lockVersion']==10
 assert sync.reconcile(service,source)['state']=='STATUS_SYNC_VERIFIED'
 rows.append({'native_id':source['native_id'],'path':[r.get('native_status_id') for r in history if r['reason']=='NATIVE_STEP_VERIFIED'],'version':item['lockVersion'],'result':result})
commands=[]
try:
 for mode in ['AUTO','PAUSED','OFF','PAUSED']:
  r=control(service,18,mode);assert r['accepted'];commands.append({k:r.get(k) for k in ['command_id','accepted','desired_state','current_state','reason_code']})
 rid=next(s['run_id'] for s in sources if s['native_id']==391)
 assert resume(service,18,rid,0)['deduplicated'] is True
 assert cancel(service,18,rid)['cancelled'] is False
 from gateway.engineering import admit
 try:admit(service,18,{},'clone-no-eligible')
 except ValueError as e:assert str(e)=='NO_ELIGIBLE_WORK'
 else:raise AssertionError('NO_ELIGIBLE_RESPONSE_MISSING')
 first=enqueue(service,18,'clone-sync-one');second=enqueue(service,18,'clone-sync-two');assert first['operation_id']==second['operation_id']
 sync.tick(service)
finally:control(service,18,'PAUSED')
print(json.dumps({'status':'PASS','native':rows,'controls':commands,'resume_succeeded_deduplicated':True,'cancel_finished_noop':True,'no_eligible_work':True,'github_admission_duplicate_safe':True,'generation_calls':0,'new_coding_runs':0}))
'''
code=code.replace('INCREMENTAL','True' if polish else 'False')
with main_native_clone(private/'native',candidate_web_image=images['core'],before_web=before_web) as clone:
    output=run('run','--rm','--pull','never','--network',clone['network'],'--read-only','--tmpfs','/tmp:mode=1777',
        '--cap-drop','ALL','--security-opt','no-new-privileges:true','--memory','768m','--cpus','1',
        '--mount',f'type=bind,source={private},target=/state','--entrypoint','python',images['gateway'],'-c',code,timeout=300)
    proof['gateway_native']=json.loads(output.decode().splitlines()[-1]);assert proof['gateway_native']['status']=='PASS'
proof.update(status='PASS',images=images,source_hashes=manifest['source_hashes'],main_writes=0,provider_generation_calls=0,
    scope='Actual Rails routes/session/CSRF/render and fast ACK at synthetic Gateway boundary; actual candidate Gateway Service to Native HTTP/forms/workflow/readback in isolated clone',
    finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(OUT/('clone-qualification'+suffix+'.json')).write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'status':proof['status'],'images':images,'native':proof['gateway_native']['native']}))
