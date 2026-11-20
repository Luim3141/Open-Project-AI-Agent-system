"""Incremental Phase2 deployment, pinned to the last serving manifest."""
import datetime
import json
import shutil
import argparse
import re

from automation.engineering_deploy import ROOT,PRIVATE,AI_ENV,CORE_ENV,run,inspect,replace_env,health


def deploy(revision='r2'):
    if not re.fullmatch('r[1-9][0-9]*',revision):raise ValueError('DEPLOY_REVISION_INVALID')
    path=ROOT/'docs/ai/engineering/deployment.json';previous=json.loads(path.read_text())
    gateway=inspect('qldapm-ai-gateway-1');core=inspect('qldapm-openproject-web-1')
    if gateway['Image']!=previous['gateway_deployed'] or core['Image']!=previous['core_deployed']:
        raise ValueError('DEPLOY_SERVING_BASELINE_CHANGED')
    import sqlite3; count=int(sqlite3.connect(str(PRIVATE.parent/'gateway/gateway.sqlite')).execute("SELECT count(*) FROM ai_queue WHERE state!='finished'").fetchone()[0])
    if count:raise ValueError('DEPLOY_ACTIVE_AI_RUN_HOLD')
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup=PRIVATE/('engineering-continuation-'+stamp);backup.mkdir(parents=True)
    bridge=CORE_ENV.parent/'ui-bridge.yml'
    for source,target in [(AI_ENV,'ai.env'),(CORE_ENV,'core.env'),(bridge,'ui-bridge.yml'),(path,'previous-deployment.json')]:shutil.copy2(source,backup/target)
    # Build products must already exist; do not rebuild/restart unrelated containers.
    gateway_tag='qldapm-ai:engineering-continuation-'+revision+'-20261030';core_tag='qldapm-core:engineering-continuation-'+revision+'-20261030'
    run(['docker','image','inspect',gateway_tag]);core_product=json.loads(run(['docker','image','inspect',core_tag]))[0]
    core_changed=core_product['Id']!=core['Image']
    replace_env(AI_ENV,'AI_IMAGE',gateway_tag)
    if core_changed:
        config=json.loads(bridge.read_text());config['services']['web']['image']=core_tag;bridge.write_text(json.dumps(config,indent=2))
    run(['docker','compose','--env-file',str(AI_ENV),'-f',str(ROOT/'openproject/ai/compose.yml'),'-f',str(ROOT/'openproject/ai/gemini-free.main.yml'),'up','-d','--no-deps','gateway'])
    health('qldapm-ai-gateway-1')
    if core_changed:
        run(['docker','compose','--env-file',str(CORE_ENV),'-f',str(ROOT/'openproject/compose.yml'),'-f',str(bridge),'up','-d','--no-deps','web'])
        health('qldapm-openproject-web-1')
    previous.setdefault('continuation_history',[]).append({'backup':str(backup),'gateway_before':gateway['Image'],'core_before':core['Image']})
    previous.update(gateway_deployed=inspect('qldapm-ai-gateway-1')['Image'],core_deployed=inspect('qldapm-openproject-web-1')['Image'],gateway_revision='continuation-'+revision,core_revision='continuation-'+revision if core_changed else previous['core_revision'],gateway_health='healthy',core_health='healthy')
    path.write_text(json.dumps(previous,indent=2)+'\n')
    print(json.dumps({'deployed':True,'backup':str(backup),'gateway':previous['gateway_deployed'],'core':previous['core_deployed']}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--revision',default='r2');deploy(parser.parse_args().revision)
