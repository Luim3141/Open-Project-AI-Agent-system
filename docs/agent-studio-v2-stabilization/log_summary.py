"""Extract only route/status/duration/request IDs; discard raw logs in memory."""
import json,re,subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent
result={}
for name in ('qldapm-ai-gateway-1','qldapm-openproject-web-1'):
    p=subprocess.run(['docker','logs','--timestamps','--since','4h','--tail','30000',name],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
    rows=[];routes={}
    for line in (p.stdout+'\n'+p.stderr).splitlines():
        stamp=line.split(' ',1)[0];ids=re.findall(r'\b[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}\b',line);rid=ids[0] if ids else None
        start=re.search(r'Started (GET|POST) "([^"?]+)',line)
        if start and rid:routes[rid]=start.group(2)
        access=re.search(r'"(GET|POST) (/[^ ?"]+)(?:[^\"]*)HTTP/1\.[01]" ([1-5][0-9]{2})',line)
        complete=re.search(r'Completed ([1-5][0-9]{2}).*? in ([0-9.]+)ms',line)
        if access and (access.group(2) in {'/internal/ui','/api/v1/commands'}):rows.append({'at':stamp,'method':access.group(1),'route':access.group(2),'status':int(access.group(3))})
        elif complete and rid and '/qldapm-ai' in routes.get(rid,''):rows.append({'at':stamp,'route':routes[rid],'request_id':rid,'status':int(complete.group(1)),'duration_ms':float(complete.group(2))})
    result[name]={'matching_requests':len(rows),'status_counts':{str(s):sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})},'failures':[r for r in rows if r['status']>=400][-80:],'slow':[r for r in rows if r.get('duration_ms',0)>3000][-30:]}
(OUT/'log-baseline.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
