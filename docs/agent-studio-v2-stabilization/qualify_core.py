"""Candidate Native metadata on private isolated Main restore, no Main writes."""
import json,os,subprocess,sys,uuid
from pathlib import Path
OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(OUT.parents[1]/'openproject/ai'))
from automation.main_native_clone import main_native_clone
manifest=json.loads((OUT/'candidate/manifest.json').read_text())
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator'/('studio-clone-'+uuid.uuid4().hex)
private.mkdir(parents=True)
result={}
def before_web(name):
    code="""require 'json'
owner=User.find(18)
batch=Qldapm::ObserverPackages.call(owner,6,[379,397])
raise 'BATCH_SCOPE' unless batch[:items].map{|r|r[:id]}.sort==[379,397]
list=Qldapm::ObserverPackages.list(owner,6,'health',20)
raise 'LIST_SCOPE' unless list[:items].all?{|r|r['_links'][:project][:href]=='/api/v3/projects/6'}
escaped=Qldapm::ObserverPackages.list(owner,6,'%_',20)
raise 'WILDCARD_NOT_LITERAL' unless escaped[:items].empty?
begin;Qldapm::ObserverPackages.call(owner,6,[true]);raise 'INVALID_IDS_ACCEPTED';rescue ArgumentError;end
denied=User.where.not(id:18).find{|u|!u.allowed_in_project?(:view_work_packages,Project.find(6))}
raise 'DENY_FIXTURE_MISSING' unless denied
begin;Qldapm::ObserverPackages.call(denied,6,[397]);raise 'DENIED_USER_ACCEPTED';rescue ArgumentError,ActiveRecord::RecordNotFound;end
puts JSON.generate({status:'PASS',batch_ids:batch[:items].map{|r|r[:id]},list_count:list[:items].size,wildcard_escaped:true,denied:true})
"""
    r=subprocess.run(['docker','exec','-i','--user','app',name,'bundle','exec','rails','runner','-'],input=code.encode(),capture_output=True,timeout=240)
    if r.returncode:
        (private/'runner.log').write_bytes(r.stdout+r.stderr);raise RuntimeError('CORE_CLONE_TEST_FAILED_PRIVATE_LOG')
    result.update(json.loads(r.stdout.decode().splitlines()[-1]))
with main_native_clone(private,candidate_web_image=manifest['images']['core'],before_web=before_web,web_start_timeout=240) as clone:
    result.update(image=clone['images']['web'],isolation='Private PG restore, separate internal network/volumes, no provider key',main_writes=0)
(OUT/'core-clone.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
