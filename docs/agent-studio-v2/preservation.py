"""Hash private settings and persisted integrations; no secret values leave process."""
import hashlib,json,os,sqlite3,subprocess,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/telegram-ai'
def capture():
    files={str(p.relative_to(private)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [private/'.env',*(private/'secrets').glob('*')] if p.is_file()}
    with sqlite3.connect((private/'state/telegram.sqlite').as_uri()+'?mode=ro',uri=True) as db:
        tables={}
        for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
            assert table.replace('_','').isalnum()
            rows=db.execute('SELECT * FROM "'+table+'" ORDER BY rowid').fetchall()
            tables[table]={'rows':len(rows),'sha256':hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()}
    program="""const {DatabaseSync}=require('node:sqlite');const {createHash}=require('node:crypto');const d=new DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});const pin=t=>d.prepare('SELECT * FROM '+t+' ORDER BY id').all().map(r=>({id:r.id,sha256:createHash('sha256').update(JSON.stringify(r)).digest('hex')}));console.log(JSON.stringify({workflows:pin('workflow_entity'),credentials:pin('credentials_entity')}));d.close();"""
    n8n=json.loads(subprocess.check_output(['docker','exec','qldapm-n8n-main','node','-e',program]))
    containers={}
    for name in ['qldapm-ai-telegram-ai-1','qldapm-n8n-main']:
        row=json.loads(subprocess.check_output(['docker','inspect',name]))[0]
        containers[name]={'id':row['Id'],'image':row['Image'],'started_at':row['State']['StartedAt'],'state':row['State']['Status'],'health':row['State'].get('Health',{}).get('Status')}
    return {'files':files,'telegram_tables':tables,'n8n':n8n,'containers':containers}
if __name__=='__main__':
    phase=sys.argv[1];value=capture()
    if phase=='before':
        target=OUT/'preservation-before.json';assert not target.exists()
    else:
        before=json.loads((OUT/'preservation-before.json').read_text());assert value==before,'BOT_OR_N8N_CHANGED';target=OUT/'preservation-after.json'
    target.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PRESERVED' if phase!='before' else 'BASELINED','telegram_tables':len(value['telegram_tables']),'n8n_workflows':len(value['n8n']['workflows']),'n8n_credentials':len(value['n8n']['credentials'])}))
