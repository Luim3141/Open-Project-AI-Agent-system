"""One-shot read-only observation of actual Main scheduled executions; never invokes workflows."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

from automation.main_operations import PRIVATE_ROOT

ROOT=PRIVATE_ROOT/'natural-schedule-observations'
ZONE=ZoneInfo('Asia/Bangkok')
WORKFLOWS={
 'WF07':('BpCQrGR866vg4BqQ','0 0 8 * * *','daily_brief'),
 'WF12':('ZkgS8RZbPRA2zbhQ','0 0 17 * * 5','weekly_summary'),
 'WF16':('5FRYNPSot18UDpKa','0 */15 * * * *','health_monitor'),
}
N8N=r"""const{DatabaseSync}=require('node:sqlite'),{parse}=require('/usr/local/lib/node_modules/n8n/node_modules/flatted');
const d=new DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});const id=process.argv[1];
const w=d.prepare('select id,active,activeVersionId,nodes,settings from workflow_entity where id=?').get(id);
const executions=d.prepare("select id,mode,status,finished,startedAt,stoppedAt,retryOf,retrySuccessId,workflowVersionId from execution_entity where workflowId=? and mode='trigger' order by id desc limit 50").all(id);
for(const row of executions){const stored=d.prepare('select data from execution_data where executionId=?').get(row.id);if(stored){const obj=parse(stored.data);row.execution_error=!!obj.resultData.error;const last=obj.resultData.lastNodeExecuted;const run=obj.resultData.runData[last]?.at(-1);row.output=run?.data?.main?.[0]?.[0]?.json??null;row.workflow_version=row.workflowVersionId??null;}}
w.nodes=JSON.parse(w.nodes);w.settings=JSON.parse(w.settings);console.log(JSON.stringify({workflow:w,executions}));d.close();"""


def docker(*args):
    result=subprocess.run(['docker',*args],capture_output=True,timeout=40)
    if result.returncode:raise RuntimeError('READ_ONLY_DOCKER_PROBE_FAILED')
    return result.stdout


def due_time(code,value):
    at=dt.datetime.fromisoformat(value)
    if at.tzinfo is None:raise ValueError('EXPLICIT_TIMEZONE_REQUIRED')
    at=at.astimezone(ZONE)
    if at.second or at.microsecond or (code=='WF07' and (at.hour,at.minute)!=(8,0)) or (code=='WF12' and (at.weekday(),at.hour,at.minute)!=(4,17,0)) or (code=='WF16' and at.minute%15):
        raise ValueError('PRODUCTION_SCHEDULE_TIME_REQUIRED')
    return at


def assess(code,at,snapshot,ledger,now):
    result={'workflow':code,'scheduled_at':at.isoformat(),'observed_at':now.isoformat(),'native_writes_by_observer':0}
    if now<at:return {**result,'status':'PENDING_SCHEDULED_OBSERVATION'}
    spec=WORKFLOWS[code];w=snapshot['workflow']
    cron=[i.get('expression') for n in w['nodes'] if n['type']=='n8n-nodes-base.scheduleTrigger' and not n.get('disabled') for i in n.get('parameters',{}).get('rule',{}).get('interval',[])]
    if w['id']!=spec[0] or not w['active'] or not w['activeVersionId'] or w['settings'].get('timezone')!='Asia/Bangkok' or spec[1] not in cron:
        return {**result,'status':'WORKFLOW_CONFIG_CHANGED'}
    matches=[]
    for row in snapshot['executions']:
        started=dt.datetime.fromisoformat(row['startedAt'].replace(' ','T').replace('Z','+00:00'))
        if started.tzinfo is None:started=started.replace(tzinfo=dt.timezone.utc)
        if row['mode']=='trigger' and at<=started<at+dt.timedelta(minutes=5):matches.append(row)
    if not matches:return {**result,'status':'PENDING_SCHEDULED_OBSERVATION' if now<at+dt.timedelta(minutes=5) else 'SCHEDULE_NOT_OBSERVED'}
    if len(matches)!=1:return {**result,'status':'DUPLICATE_SCHEDULED_EXECUTIONS','execution_ids':[x['id'] for x in matches]}
    row=matches[0];result.update(execution_id=row['id'],trigger_at_utc=row['startedAt'],stopped_at_utc=row['stoppedAt'],workflow_version=row.get('workflow_version'),retry_of=row.get('retryOf'),retry_success_id=row.get('retrySuccessId'),execution_error=bool(row.get('execution_error')))
    if row.get('workflow_version')!=w['activeVersionId']:return {**result,'status':'EXECUTION_VERSION_NOT_VERIFIED'}
    if row['status']!='success' or not row['finished'] or row.get('execution_error'):return {**result,'status':'FAILED_OR_UNFINISHED_EXECUTION'}
    output=row.get('output') or {};business=output.get('result') or {};result['business_state']=business.get('state')
    if not ledger or ledger.get('result')!=business or ledger.get('actor') is not None or business.get('actor_id') is not None or business.get('authority')!='machine' or business.get('project_id')!=5 or type(business.get('model_calls')) is not int or business['model_calls']!=0 or business.get('native_write_allowed') is not False:
        return {**result,'status':'RECEIPT_OR_AUTHORITY_MISMATCH'}
    if code=='WF16':
        if not ledger.get('hash_valid') or output.get('sha256')!=ledger.get('sha256') or output.get('correlation_id')!=ledger.get('id') or ledger.get('request_key')!=str(int(at.timestamp())//900):return {**result,'status':'RECEIPT_HASH_MISMATCH'}
        result.update(receipt_id=ledger['id'],idempotency_key='health_monitor:'+ledger['request_key'],cached=output.get('cached'))
        return {**result,'status':'OBSERVED_HEALTHY' if business.get('state')=='HEALTHY' else 'OBSERVED_DEGRADED'}
    key=('daily:'+at.date().isoformat()) if code=='WF07' else ('weekly:'+(at.date()-dt.timedelta(days=at.weekday())).isoformat())
    result.update(receipt_id=business.get('run_id'),idempotency_key=business.get('request_key'),ready=business.get('ready'),targets=business.get('targets'))
    if (ledger.get('id')!=business.get('run_id') or ledger.get('request_key')!=key or business.get('request_key')!=key or business.get('kind')!=spec[2] or business.get('state')!='COMPLETED' or business.get('status')!='READY' or business.get('ready')!=business.get('targets') or type(business.get('targets')) is not int or not 1<=business['targets']<=20):
        return {**result,'status':'BUSINESS_RESULT_NOT_READY'}
    return {**result,'status':'OBSERVED_READY','retry_count':None,'retry_count_scope':'Not inferred from n8n success; execution and Gateway receipt retained'}


def observe(code,at,now=None):
    now=now or dt.datetime.now(ZONE)
    if now<at:return assess(code,at,None,None,now)
    snapshot=json.loads(docker('exec','qldapm-n8n-main','node','-e',N8N,WORKFLOWS[code][0]))
    preliminary=assess(code,at,snapshot,None,now)
    if preliminary['status']!='RECEIPT_OR_AUTHORITY_MISMATCH':return preliminary
    row=next(r for r in snapshot['executions'] if r['id']==preliminary['execution_id'])
    output=row.get('output') or {};receipt=output.get('result') or {}
    identifier=output.get('correlation_id') if code=='WF16' else receipt.get('run_id')
    if not isinstance(identifier,str):return preliminary
    # UUID parameters are bound by SQLite; no credentials, Service or Native APIs are needed.
    probe="import json,sqlite3,hashlib;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);identifier="+repr(identifier)+"\n"
    if code=='WF16':
        probe+="r=d.execute(\"select id,actor,outcome,version,target from audit where id=? and action='health_monitor'\",(identifier,)).fetchone();print(json.dumps(None if not r else dict(id=r[0],actor=r[1],result=json.loads(r[2]),sha256=r[3],request_key=r[4],hash_valid=hashlib.sha256(r[2].encode()).hexdigest()==r[3])))"
    else:
        probe+="r=d.execute('select id,request_key,receipt from automation_runs where id=?',(identifier,)).fetchone();print(json.dumps(None if not r else dict(id=r[0],request_key=r[1],result=json.loads(r[2]),actor=json.loads(r[2]).get('actor_id'))))"
    ledger=json.loads(docker('exec','qldapm-ai-gateway-1','python','-c',probe))
    return assess(code,at,snapshot,ledger,now)


def save_result(result):
    ROOT.mkdir(parents=True,exist_ok=True)
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    key=result['workflow']+'-'+result['scheduled_at'][:10]
    (ROOT/(key+'-'+stamp+'.json')).write_text(json.dumps(result,indent=2))
    temporary=ROOT/(key+'.tmp');temporary.write_text(json.dumps(result,indent=2));temporary.replace(ROOT/(key+'-latest.json'))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--target',choices=WORKFLOWS);p.add_argument('--at');p.add_argument('--due',action='store_true');a=p.parse_args()
    if a.due and (a.target or a.at) or not a.due and not (a.target and a.at):p.error('Use --due OR --target with --at')
    plan=json.loads((ROOT/'plan.json').read_text()) if a.due else [{'workflow':a.target,'scheduled_at':a.at}]
    results=[]
    for item in plan:
        code=item['workflow'];at=due_time(code,item['scheduled_at']);now=dt.datetime.now(ZONE)
        if a.due and now<at:continue
        previous=ROOT/(code+'-'+at.date().isoformat()+'-latest.json')
        if a.due and previous.is_file():
            saved=json.loads(previous.read_text())
            if saved.get('scheduled_at')==at.isoformat() and saved.get('status') in {'OBSERVED_READY','OBSERVED_HEALTHY'}:continue
        try:result=observe(code,at,now)
        except Exception as error:result={'workflow':code,'scheduled_at':at.isoformat(),'observed_at':now.isoformat(),'status':'OBSERVATION_BLOCKED','error_type':type(error).__name__,'native_writes_by_observer':0}
        save_result(result);results.append(result)
    print(json.dumps(results,ensure_ascii=False,indent=2))
    return int(any(r['status'] not in {'OBSERVED_READY','OBSERVED_HEALTHY','PENDING_SCHEDULED_OBSERVATION'} for r in results))


if __name__=='__main__':raise SystemExit(main())
