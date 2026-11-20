"""Read-only repeatable MAIN status samples; credentials stay in private storage."""
import datetime,json,math,os,statistics,subprocess,sys,time,uuid
from pathlib import Path
import httpx

OUT=Path(__file__).parent
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/cc-stabilization'
token=json.loads((private/'baseline-native.json').read_text(encoding='utf-8'))['token']
label=sys.argv[1]
assert label in {'before','resource-after','final'}
rows=[]
with httpx.Client(trust_env=False,timeout=60) as client:
    for index in range(30):
        start=time.monotonic()
        r=client.post('http://127.0.0.1:18089/api/v1/commands',headers={'Host':'qldapm-ai-gateway-1:8090','Authorization':'Bearer '+token},json={'action':'engineering_status','arguments':{},'project_id':6,'idempotency_key':str(uuid.uuid4())})
        elapsed=time.monotonic()-start
        assert r.status_code==200, r.status_code
        status=r.json()['result']
        assert status['mode']=='PAUSED' and status['queue']['active']==0
        row={'index':index,'seconds':round(elapsed,4),'bytes':len(r.content)}
        rows.append(row)
        print(json.dumps(row),flush=True)
        (private/'button-audit-status.json').write_text(json.dumps(status,ensure_ascii=False),encoding='utf-8')
ordered=sorted(r['seconds'] for r in rows)
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'route':'MAIN Gateway HTTP engineering_status; not browser usable time','samples':len(rows),'p50':statistics.median(ordered),'p95_nearest_rank':ordered[math.ceil(.95*len(ordered))-1],'rows':rows,'resource':json.loads(subprocess.check_output(['docker','inspect','qldapm-ai-gateway-1']))[0]['HostConfig']['NanoCpus']}
result['images']={name:json.loads(subprocess.check_output(['docker','inspect',name]))[0]['Image'] for name in ['qldapm-ai-gateway-1','qldapm-openproject-web-1']}
result['scenario']='New HTTP client connection then repeated requests; running app, not cold boot. Concurrent normal UI polling may be present.'
result['first_request_seconds']=rows[0]['seconds']
result['resource_snapshot']=subprocess.check_output(['docker','stats','qldapm-ai-gateway-1','qldapm-openproject-web-1','qldapm-n8n-main','--no-stream','--format','{{.Name}} {{.CPUPerc}} {{.MemUsage}}']).decode().strip()
(OUT/(label+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
