"""Qualify a pinned Gateway in a disposable Native/PG/Qdrant clone, using host Ollama only for embeddings."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sqlite3

from automation.main_native_clone import main_native_clone
from automation.main_operations import private_path


def run(*args, data=None, timeout=600):
    result=subprocess.run(['docker',*args],input=data,capture_output=True,timeout=timeout)
    if result.returncode:
        raise RuntimeError('CLONE_DOCKER_COMMAND_FAILED: '+result.stderr.decode(errors='replace')[-1000:])
    return result.stdout


def qualify(output, image, baseline=None):
    output=private_path(output);output.mkdir(exist_ok=False)
    gateway_image=json.loads(run('image','inspect',image))[0]['Id']
    vector_image=json.loads(run('inspect','qldapm-qdrant'))[0]['Image']
    with main_native_clone(output/'native') as clone:
        prefix='qldapm-comment-'+clone['id']
        names={'gateway':prefix+'-gateway','vector':prefix+'-vector'}
        embedding_network=prefix+'-embedding'
        label='org.qldapm.comment-clone='+clone['id']
        client=output/'client';client.mkdir();(client/'state').mkdir()
        if baseline is not None:
            baseline=private_path(baseline)
            with sqlite3.connect(baseline.as_uri()+'?mode=ro&immutable=1',uri=True) as source,sqlite3.connect(client/'state/knowledge.sqlite') as target:
                if source.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('CLONE_BASELINE_INVALID')
                source.backup(target)
        (client/'clone.json').write_text(json.dumps(clone))
        shutil.copy2(Path(__file__).parents[1]/'tests/comment_sync_native_client.py',client/'client.py')
        # Only clone-local credentials are minted; no Main credentials or Gemini key are copied.
        ruby="require 'json'; puts JSON.generate([18,19,20].to_h { |id| [id,Token::API.create_and_return_value(User.find(id))] })"
        credentials=run('exec','--user','app',clone['web'],'bundle','exec','rails','runner',ruby)
        credentials=json.loads(credentials.decode().splitlines()[-1])
        (client/'credentials.json').write_text(json.dumps(credentials))
        config={'project_id':5,'gateway_mode':'native','openproject_url':'http://web:8080',
                'users':{'18':'AI_SYSTEM_OWNER','19':'PM','20':'BA'},
                'native_incremental_sync':{'enabled':True,'actor':18}}
        metadata=json.loads(run('exec','qldapm-ai-gateway-1','python','-c',
            "import json;from pathlib import Path;c=json.loads(Path('/state/config.json').read_text());assert c['project_id']==5;print(json.dumps({k:c[k] for k in ['source_field','type_ids','status_ids']}))"))
        config.update(metadata)
        (client/'config.json').write_text(json.dumps(config))
        created=[]
        try:
            run('network','create','--label',label,embedding_network);created.append(('network',embedding_network))
            run('run','-d','--pull','never','--name',names['vector'],'--label',label,'--network',clone['network'],
                '--network-alias','fixture-vector','--read-only','--tmpfs','/qdrant/storage:size=256m,mode=1777',
                '--tmpfs','/qdrant/snapshots:size=64m,mode=1777','--tmpfs','/tmp:size=32m,mode=1777',
                '--memory','384m','--cpus','1','--pids-limit','128','--cap-drop','ALL',
                '--security-opt','no-new-privileges:true','-e','QDRANT__TELEMETRY_DISABLED=true',vector_image)
            created.append(('container',names['vector']))
            run('run','-d','--pull','never','--name',names['gateway'],'--label',label,'--network',clone['network'],
                '--read-only','--tmpfs','/tmp:size=128m,mode=1777','--memory','768m','--cpus','1.5','--pids-limit','128',
                '--cap-drop','ALL','--security-opt','no-new-privileges:true',
                '-e','QLDAPM_AI_RUNTIME=','-e','PYTHONPATH=/app','-e','QLDAPM_COMMENT_SYNC_CLONE='+clone['id'],
                '-e','QLDAPM_QDRANT_URL=http://fixture-vector:6333',
                '-e','QLDAPM_OLLAMA_URL=http://host.docker.internal:11434',
                '--mount',f'type=bind,source={client},target=/qualification',gateway_image,'sleep','3600')
            created.append(('container',names['gateway']))
            run('network','connect',embedding_network,names['gateway'])
            print('Clone Gateway/Qdrant started; running actual Native activities and BGE-M3 tests',flush=True)
            result=subprocess.run(['docker','exec',names['gateway'],'python','/qualification/client.py'],capture_output=True,timeout=2400)
            (output/'client.log').write_bytes(result.stdout+result.stderr)
            if result.returncode:
                raise RuntimeError('COMMENT_CLONE_TEST_FAILED_SEE_PRIVATE_CLIENT_LOG')
            evidence=json.loads((client/'result.json').read_text())
            evidence.update(gateway_image=gateway_image,core_image=clone['images']['web'],
                source_dump_sha256=clone['source_dump_sha256'],isolation='Separate PG, Gateway SQLite, Qdrant, credentials and networks; host Ollama embeddings only')
            (output/'result.json').write_text(json.dumps(evidence,indent=2))
            return evidence
        finally:
            for kind,name in reversed(created):
                inspect=['inspect',name] if kind=='container' else ['network','inspect',name]
                own=json.loads(run(*inspect))[0]
                labels=own['Config'].get('Labels',{}) if kind=='container' else own.get('Labels',{})
                if labels.get('org.qldapm.comment-clone')!=clone['id']:
                    raise RuntimeError('CLONE_RESOURCE_LABEL_CHANGED')
                run('rm','-f',name) if kind=='container' else run('network','rm',name)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output');parser.add_argument('--image',required=True);parser.add_argument('--baseline')
    args=parser.parse_args();print(json.dumps(qualify(args.output,args.image,args.baseline),indent=2))
