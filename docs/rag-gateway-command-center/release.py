"""Phase-specific sources/qualification on the existing guarded Core/Gateway operator."""
import copy,json,subprocess,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation import integration_pair_release as release
base=json.loads((OUT/'baseline.json').read_text())['containers']
release.BASE_IMAGES={k:base[n]['image'] for k,n in [('core','qldapm-openproject-web-1'),('gateway','qldapm-ai-gateway-1')]}
release.SOURCES={**{'openproject/ai/gateway/'+n:('gateway','/app/gateway/'+n) for n in ['service.py','knowledge_search.py','knowledge_answer.py','file_knowledge.py','catalog.py']},
    **{'openproject/ai/core/overlay/'+n:('core','/app/'+n) for n in ['app/controllers/qldapm_ai_controller.rb','app/views/qldapm_ai/_engineering_command_center.html.erb','app/views/qldapm_ai/_engineering_knowledge_results.html.erb']}}
release.next_config=copy.deepcopy
def qualified(proof,files):
    assert proof['status']=='PASS' and proof['source_hashes']==files
    assert proof['checks']=={'gateway_contracts':True,'core_transport':True,'templates':True,'source_parity':True}
release.qualified=qualified
bundle=OUT/(sys.argv[2] if len(sys.argv)>2 else 'candidate');action=sys.argv[1]
if (bundle/'manifest.json').exists():
    saved=json.loads((bundle/'manifest.json').read_text())
    release.BASE_IMAGES={role:saved['initial_runtime'][role]['image'] for role in ['core','gateway']}
elif action=='prepare':
    release.BASE_IMAGES={role:json.loads(subprocess.check_output(['docker','inspect',release.TARGETS[role][0]]))[0]['Image'] for role in ['core','gateway']}
if action=='prepare':result=release.prepare(bundle)
elif action=='build':
    if bundle.name=='candidate':result=release.build(bundle)
    else:
        bundle,manifest=release.load_guarded(bundle);old=json.loads((OUT/'candidate/manifest.json').read_text())
        images={};reused=[]
        for role in ['gateway','core']:
            expected={k:v for k,v in manifest['source_hashes'].items() if release.SOURCES[k][0]==role}
            if release.runtime_hashes(role,release.BASE_IMAGES[role])==expected:
                images[role]=release.BASE_IMAGES[role];reused.append(role);continue
            if release.runtime_hashes(role,old['images'][role])==expected:
                images[role]=old['images'][role];reused.append(role);continue
            tag=release.base_tag(release.BASE_IMAGES[role],manifest['base_tag_nonce'])
            release.run(['docker','tag',release.BASE_IMAGES[role],tag]);target='qldapm-'+role+':phase4-'+manifest['base_tag_nonce']
            release.run(['docker','build','--network','none','--pull=false','-f',str(bundle/'context'/('Dockerfile.'+role)),'-t',target,str(bundle/'context')],timeout=600)
            images[role]=json.loads(release.run(['docker','image','inspect',target]))[0]['Id']
            assert release.runtime_hashes(role,images[role])==expected
        manifest.update(state='BUILT_NOT_DEPLOYED',images=images,reused_unchanged=reused)
        release.write_json(bundle/'manifest.json',manifest);result=manifest
elif action=='qualify':
    manifest=json.loads((bundle/'manifest.json').read_text())
    prior_path=OUT/'qualification.json' if (OUT/'qualification.json').exists() else OUT/'qualification-v1.json'
    prior=json.loads(prior_path.read_text()) if prior_path.exists() else {}
    same_gateway=all(prior.get('source_hashes',{}).get(k)==v for k,v in manifest['source_hashes'].items() if release.SOURCES[k][0]=='gateway')
    if bundle.name=='candidate' or not same_gateway:
        subprocess.run([sys.executable,str(OUT/'qualify.py'),'--candidate',str(bundle/'manifest.json')],check=True)
    else:
        regression=json.loads((OUT/'candidate-regression.json').read_text())
        assert regression['gateway']['exit_code']==0 and regression['telegram']['exit_code']==0
        assert all(prior['source_hashes'][k]==v for k,v in manifest['source_hashes'].items() if release.SOURCES[k][0]=='gateway')
        assert subprocess.run(['node',str(ROOT/'openproject/ai/tests/test_owner_live_transport.js')],capture_output=True).returncode==0
        subprocess.run([sys.executable,str(OUT/'mobile_form.py')],check=True)
    code="require 'action_view';require 'json';d=JSON.parse(STDIN.read);d.each{|name,src| RubyVM::InstructionSequence.compile(ActionView::Template::Handlers::ERB::Erubi.new(src).src)};puts 'PASS Rails Erubi template compilation'"
    sources={p:(ROOT/p).read_text(encoding='utf-8') for p,(role,target) in release.SOURCES.items() if role=='core' and p.endswith('.erb')}
    p=subprocess.run(['docker','run','--rm','-i','--network','none','--entrypoint','bundle',manifest['images']['core'],'exec','ruby','-e',code],input=json.dumps(sources),text=True,capture_output=True,timeout=60)
    (OUT/'template-candidate.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr[-300:]
    for role in ['core','gateway']:
        assert release.runtime_hashes(role,manifest['images'][role])=={k:v for k,v in manifest['source_hashes'].items() if release.SOURCES[k][0]==role}
    release.guard_sources(ROOT,manifest['source_hashes'])
    proof={'status':'PASS','source_hashes':manifest['source_hashes'],'checks':{'gateway_contracts':True,'core_transport':True,'templates':True,'source_parity':True},
        'scope':'Immutable source parity, offline Gateway/actor/gates/RAG contracts, real inline JS transport VM, native Rails Erubi compilation. NOT MAIN browser/model/semantic quality acceptance; MAIN read-back required after rollout.'}
    release.write_json(OUT/'qualification.json',proof);result={'status':'PASS','images':manifest['images']}
elif action=='rollout':
    result=release.rollout(bundle,OUT/'qualification.json');release.write_json(OUT/'deployment.json',result)
else:raise ValueError(action)
print(json.dumps({k:v for k,v in result.items() if k in ['state','status','images']}))
