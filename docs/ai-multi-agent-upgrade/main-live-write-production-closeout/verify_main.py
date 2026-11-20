"""Post-deploy read-only verification and source/protected-data checks; never submits a run."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'openproject/ai'))
from gateway.native import Native
from jira_sync_backup import database_state,inspect
def run(*args,data=None):
    p=subprocess.run(args,input=data,capture_output=True,timeout=180);assert p.returncode==0,'VERIFY_FAILED_OUTPUT_WITHHELD';return p.stdout
def main():
    b=json.loads((OUT/'baseline.json').read_text());q=json.loads((OUT/'qualification.json').read_text());record=next(p for p in (OUT/'deployment-citation-fix.json',OUT/'deployment-read-fix.json',OUT/'deployment.json') if p.exists());d=json.loads(record.read_text())
    assert d['phase']=='MAIN_DEPLOYED_HEALTH_PASS'
    live=json.loads((OUT/'live-run.json').read_text())['run_id'] if (OUT/'live-run.json').exists() and '--no-live' not in sys.argv else None
    snapshot=json.loads(run('docker','exec','-i','qldapm-ai-gateway-1','python','-',*([live] if live else []),data=(OUT/'main_snapshot.py').read_bytes()))
    (OUT/('main-after-live.json' if live else 'main-before-live.json')).write_text(json.dumps(snapshot,indent=2,ensure_ascii=False),encoding='utf-8')
    old=snapshot['runs'][0];assert old['effective_state']=='reconciled_success' and old['worker_state']=='failed_or_unknown'
    assert old['completion']['native']=='RECONCILED_SUCCESS' and old['synthesis_origin']=='SYSTEM' and old['monitor_state']=='RECONCILED_SUCCESS'
    assert snapshot['busy']==snapshot['pending']==0
    if live:
        new=snapshot['runs'][1];receipts=new['receipts'];gens=[r for r in receipts if r['phase']=='generateContent']
        assert 0<len(receipts)<=6 and 0<len(gens)<=3 and all(r['state']=='LIVE_SUCCESS' and r['http_status']==200 for r in receipts)
        assert new['worker_state']==new['effective_state']=='done' and new['completion']['state']=='COMPLETED'
        assert new['completion']['synthesis']=='MODEL_COMPLETE' and new['synthesis_origin']=='MODEL' and new['model_used'] is True
        assert new['monitor_state']=='COMPLETED' and new['monitor_terminal'] and new['final_text']
        assert all(c['action'] not in {'create_work_package','update_work_package','comment','transition'} for c in new['tools'])
        assert {367,50}<={c['native_id'] for c in new['tools']}
        assert snapshot['counters']['receipts']-d['counters']['receipts']==len(receipts)
        assert snapshot['counters']['usage']-d['counters']['usage']==len(receipts),'UNUSED_QUOTA_RESERVATION'
        assert snapshot['counters']['runs']==d['counters']['runs']+1
        initial=json.loads((OUT/'live-initial-failure.json').read_text())['receipts'] if (OUT/'live-initial-failure.json').exists() else []
        assert len(initial)+len(receipts)<=6 and sum(r['phase']=='generateContent' for r in initial+receipts)<=3,'OWNER_TOTAL_BUDGET_EXCEEDED'
    state=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway';credentials=json.loads((state/'credentials.json').read_text())
    n=Native('http://localhost:8088',credentials['19'],5);assert n.identity(19)['role']=='PM';rows=n.packages();assert len(rows)==330
    item=n.package(367)
    for name,href in {'project':'/api/v3/projects/5','parent':'/api/v3/work_packages/50','assignee':'/api/v3/users/23','type':'/api/v3/types/10','author':'/api/v3/users/19'}.items():assert item['_links'][name]['href']==href
    assert item['subject']=='test'
    qa=Native('http://localhost:8088',credentials['23'],5);assert qa.identity(23)['role']=='QA' and qa.package(367)['id']==367
    before=json.loads((Path(d['directory'])/'database-before.json').read_text());after=database_state('qldapm-openproject-db-1')
    for table in d['protected_tables']:assert before[table]==after[table],'PROTECTED_NATIVE_TABLE_CHANGED: '+table
    counts=json.loads(run('docker','exec','qldapm-openproject-db-1','psql','-X','-qAt','-U','postgres','-d','openproject','-c',
        "BEGIN READ ONLY; SELECT json_build_object('sprints',(select count(*) from sprints where project_id=5),'versions',(select count(*) from versions where project_id=5)); COMMIT;"))
    assert after['work_packages']['rows']==367 and counts=={'sprints':7,'versions':7}
    for path,h in b['protected_files'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==h
    gateway=json.loads(run('docker','exec','qldapm-ai-gateway-1','python','-c',
        "import hashlib,json;from pathlib import Path;print(json.dumps({str(p.relative_to('/app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/app/gateway').rglob('*') if p.is_file() and '__pycache__' not in str(p)}))"))
    assert all(q['source'].get(p)==h for p,h in gateway.items())
    core=json.loads(run('docker','exec','-i','qldapm-openproject-web-1','ruby','-rjson','-rdigest','-e',
        'paths=JSON.parse(STDIN.read);puts JSON.generate(paths.to_h{|p|[p,Digest::SHA256.file("/app/"+p).hexdigest]})',
        data=json.dumps([p.removeprefix('core/overlay/') for p in q['source'] if p.startswith('core/overlay/')]).encode()))
    assert all(q['source']['core/overlay/'+p]==h for p,h in core.items())
    for name,old in b['containers'].items():
        now=inspect(name);assert now['State']['Running']
        if name not in {'qldapm-ai-gateway-1','qldapm-openproject-web-1'}:assert (now['Id'],now['Image'],now['State']['StartedAt'])==(old['id'],old['image'],old['started'])
    assert inspect('qldapm-ai-gateway-1')['Image']==q['gateway_image'] and inspect('qldapm-openproject-web-1')['Image']==q['core_image']
    result={'passed':True,'stage':'POST_LIVE' if live else 'PRE_LIVE','project_wp':330,'global_wp':367,'sprints':7,'versions':7,
      'native_business_tables_unchanged':d['protected_tables'],'pm_qa_readback':True,'gateway_parity':len(gateway),'core_parity':len(core),
      'other_serving_containers_preserved':16,'gateway_image':q['gateway_image'],'core_image':q['core_image'],'live_run_id':live,'google_http':len(snapshot['runs'][1]['receipts']) if live else 0}
    (OUT/('final-verification.json' if live else 'pre-live-verification.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
