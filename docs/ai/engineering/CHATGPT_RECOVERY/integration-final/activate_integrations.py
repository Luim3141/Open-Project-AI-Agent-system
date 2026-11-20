"""Activate only qualified Project6 integrations; preserve original config for rollback."""
import copy,datetime,hashlib,json,os,re,subprocess,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation import integration_pair_release as release
OUT=Path(__file__).parent
FIXTURE=('# Project6 controlled integration qualification fixture\n'
         'This local test document verifies pinned source ingestion, search and citation through WF01.\n'
         'The Project6 qualification marker is ORBIT-RECEIPT-20261103.\n'
         'This fixture does not certify semantic retrieval quality or Owner acceptance.\n').encode('utf-8')
SOURCE_KEY='project6-integration-qualification'

def next_config(before):
    assert before.get('maintenance') is not True
    assert before['engineering']['github_sync']=={'enabled':False,'actor':18,'interval_seconds':300}
    assert before.get('n8n_integration',{}).get('enabled') is False
    assert re.fullmatch('[a-f0-9]{64}',before.get('n8n_lifecycle',{}).get('signing_key',''))
    after=copy.deepcopy(before)
    after['engineering']['github_sync']['enabled']=True
    after['n8n_integration'].update(enabled=True,base_url='http://qldapm-n8n-main:5678')
    assert SOURCE_KEY not in after.get('file_sources',{})
    after.setdefault('file_sources',{})[SOURCE_KEY]={'project_id':6,'allowed_roles':['PM'],
        'root':'/state/knowledge_sources','path':'/state/knowledge_sources/project6-integration-qualification.md',
        'sha256':hashlib.sha256(FIXTURE).hexdigest()}
    return after

def main(bundle):
    manifest=json.loads((bundle/'manifest.json').read_text());deployment=json.loads((bundle/'deployment.json').read_text())
    proof=json.loads((OUT/'github/qualification.json').read_text())
    release.qualified(proof,manifest['source_hashes'])
    for path,expected in proof['evidence_sha256'].items():assert release.sha(ROOT/path)==expected,'QUALIFICATION_EVIDENCE_CHANGED'
    assert deployment['status']=='DEPLOYED_SOURCE_AND_RELEASE_READBACK_VERIFIED' and deployment['images']==manifest['images']
    for role,image in manifest['images'].items():
        row=release.inspect(role)
        assert row['Image']==image and row['State']['Health']['Status']=='healthy'
        assert release.runtime_hashes(role)=={k:v for k,v in manifest['source_hashes'].items() if release.SOURCES[k][0]==role}
    n8n=json.loads((OUT/'n8n/deployment.json').read_text())
    assert n8n['status']=='DEPLOYED_PENDING_GATEWAY_EVENT_READBACK' and n8n['credentials_users_preserved'] and n8n['unchanged_other_workflows']==9
    assert json.loads(release.run(['docker','inspect','qldapm-n8n-main']))[0]['Image']==n8n['image']
    release.queue()
    path=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway/config.json'
    raw=path.read_bytes();before=json.loads(raw);after=next_config(before)
    fixture=path.parent/'knowledge_sources/project6-integration-qualification.md'
    fixture.parent.mkdir(exist_ok=True)
    assert not fixture.exists(),'PRESERVE_EXISTING_FIXTURE'
    fixture.write_bytes(FIXTURE)
    private=path.parent.parent/'operator'/('integration-activation-'+uuid.uuid4().hex);private.mkdir()
    (private/'config-before.json').write_bytes(raw)
    # Code rollback never discards Native/GitHub effects already observed after enabling.
    try:
        release.write_json(path,after)
        release.run(['docker','restart','--time','45','qldapm-ai-gateway-1'])
        release.healthy('gateway',manifest['images']['gateway']);release.queue()
        assert json.loads(release.run(['docker','exec','qldapm-ai-gateway-1','python','-c',"import json; c=json.load(open('/state/config.json')); print(json.dumps({'github':c['engineering']['github_sync']['enabled'],'events':c['n8n_integration']['enabled']}))"]))=={'github':True,'events':True}
        result={'status':'ENABLED_PENDING_BUSINESS_READBACK','github_actor':18,'github_interval_seconds':300,'event_project':6,'private_backup':str(private),'images':manifest['images'],'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        release.write_json(OUT/'integration-activation.json',result);print(json.dumps(result))
    except Exception:
        path.write_bytes(raw);release.run(['docker','restart','--time','45','qldapm-ai-gateway-1']);release.healthy('gateway',manifest['images']['gateway']);raise

if __name__=='__main__':
    if sys.argv[1:] == ['self-check']:
        original={'engineering':{'github_sync':{'enabled':False,'actor':18,'interval_seconds':300},'github_token':'preserved'},'n8n_integration':{'enabled':False},'n8n_lifecycle':{'enabled':True,'signing_key':'a'*64},'project_id':5}
        saved=copy.deepcopy(original);updated=next_config(original)
        assert original==saved and updated['n8n_lifecycle']==original['n8n_lifecycle'] and updated['project_id']==5
        assert updated['file_sources'][SOURCE_KEY]['project_id']==6 and updated['file_sources'][SOURCE_KEY]['sha256']==hashlib.sha256(FIXTURE).hexdigest()
        assert updated['engineering']['github_token']=='preserved' and updated['engineering']['github_sync']['enabled'] is True
        for value in (True,None):
            bad=copy.deepcopy(original);bad['n8n_integration']['enabled']=value
            try:next_config(bad)
            except AssertionError:pass
            else:raise AssertionError('FAIL_OPEN')
        print('SELF_CHECK_PASS')
    else:main(Path(sys.argv[1]).resolve())
