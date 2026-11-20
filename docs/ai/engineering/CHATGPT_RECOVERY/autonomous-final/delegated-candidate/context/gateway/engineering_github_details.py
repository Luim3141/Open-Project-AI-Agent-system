"""Small read-only GitHub review/CI projection; no review bodies or credentials persist."""
import hashlib
import json
import re
import time
import urllib.request
import math
import httpx
from concurrent.futures import ThreadPoolExecutor


def get_json(path,headers,deadline):
    remaining=deadline-time.monotonic()
    if remaining<=0:raise TimeoutError('GITHUB_SYNC_DEADLINE_EXCEEDED')
    request=urllib.request.Request('https://api.github.com/repos/'+path,headers=headers)
    with urllib.request.urlopen(request,timeout=min(5,remaining)) as response:
        body=response.read(2097153)
    if len(body)>2097152:raise ValueError('GITHUB_DETAILS_RESPONSE_TOO_LARGE')
    return json.loads(body)


def enrich(prs,repo,headers,deadline):
    from .engineering_github_sync import _error_code
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo):raise ValueError('GITHUB_REPOSITORY_INVALID')
    def project(pr):
        item={**pr,'reviews_state':'NOT_CHECKED','checks_state':'NOT_CHECKED'}
        try:
            number=pr.get('number');head=pr.get('head_sha','')
            if type(number) is not int or number<=0 or not re.fullmatch('[a-f0-9]{40}',head):raise ValueError('GITHUB_PR_IDENTITY_INVALID')
            reviews=[]
            for page in range(1,11):
                batch=get_json(f'{repo}/pulls/{number}/reviews?per_page=100&page={page}',headers,deadline)
                if not isinstance(batch,list):raise ValueError('GITHUB_REVIEWS_INVALID')
                reviews.extend(batch)
                if len(batch)<100:break
            else:raise ValueError('GITHUB_REVIEWS_INCOMPLETE')
            latest={}
            for review in reviews:
                if not isinstance(review,dict):raise ValueError('GITHUB_REVIEWS_INVALID')
                actor=(review.get('user') or {}).get('id')
                if actor is not None and review.get('state') in {'APPROVED','CHANGES_REQUESTED','DISMISSED'}:
                    latest[actor]=review
            current=[r['state'] for r in latest.values() if r.get('commit_id')==head]
            review_state=('CHANGES_REQUESTED' if 'CHANGES_REQUESTED' in current else 'APPROVED' if 'APPROVED' in current else
                'NO_CURRENT_REVIEW' if reviews else 'NO_REVIEWS')
            checks=get_json(f'{repo}/commits/{head}/check-runs?per_page=100',headers,deadline)
            statuses=get_json(f'{repo}/commits/{head}/status?per_page=100',headers,deadline)
            runs=checks.get('check_runs');contexts=statuses.get('statuses')
            if not isinstance(runs,list) or not isinstance(contexts,list) or checks.get('total_count',0)>len(runs) or statuses.get('total_count',0)>len(contexts):
                raise ValueError('GITHUB_CHECKS_INCOMPLETE')
            if statuses.get('sha',head)!=head or any(r.get('head_sha',head)!=head for r in runs):
                raise ValueError('GITHUB_CHECK_COMMIT_MISMATCH')
            if any(r.get('conclusion') in {'failure','cancelled','timed_out','action_required','stale','startup_failure'} for r in runs) or any(r.get('state') in {'failure','error'} for r in contexts):state='FAILURE'
            elif any(r.get('status')!='completed' for r in runs) or any(r.get('state')=='pending' for r in contexts):state='PENDING'
            elif not runs and not contexts:state='NOT_CONFIGURED'
            elif any(r.get('conclusion') not in {'success','neutral','skipped'} for r in runs) or any(r.get('state')!='success' for r in contexts):state='UNKNOWN'
            elif any(r.get('conclusion') in {'neutral','skipped'} for r in runs):state='NEUTRAL_OR_SKIPPED'
            else:state='SUCCESS'
            projection={'reviews':sorted((r.get('id'),r.get('state'),r.get('commit_id')) for r in latest.values()),
                'checks':sorted((r.get('id'),r.get('status'),r.get('conclusion')) for r in runs),
                'statuses':sorted((r.get('id'),r.get('state'),r.get('context')) for r in contexts)}
            item.update(reviews_state=review_state,checks_state=state,review_count=len(reviews),check_count=len(runs)+len(contexts),
                details_hash=hashlib.sha256(json.dumps(projection,sort_keys=True).encode()).hexdigest(),details_checked_at=time.time(),details_error=None)
        except Exception as error:
            item['details_error']=_error_code(error)
        return item
    # Rotate the first batch each polling interval so a long PR list can make progress.
    if not prs:return []
    start=(int(time.time()//300)*3)%len(prs)
    ordered=prs[start:]+prs[:start]
    with ThreadPoolExecutor(max_workers=3,thread_name_prefix='github-details') as pool:
        result=list(pool.map(project,ordered))
    return result[-start:]+result[:-start] if start else result


def release_probe():
    with httpx.Client(timeout=2,follow_redirects=False,trust_env=False) as client:
        with client.stream('GET','http://host.docker.internal:18791/release') as response:
            content=bytearray()
            for chunk in response.iter_bytes():
                if len(content)+len(chunk)>8192:raise ValueError('DEMO_RELEASE_RESPONSE_TOO_LARGE')
                content.extend(chunk)
            return httpx.Response(response.status_code,headers=response.headers,content=bytes(content))


def verified_release(service):
    """Private metadata is only an intent; actual loopback HTTP proves deployed identity."""
    try:
        path=service.store.root/'demo-release.json'
        if not path.exists():return {'state':'NOT_OBSERVED','main_merged':False}
        if path.stat().st_size>8192:raise ValueError('DEMO_RELEASE_METADATA_INVALID')
        raw=path.read_bytes();fingerprint=hashlib.sha256(raw).hexdigest()
        cached=getattr(service,'_demo_release_cache',None)
        if cached and cached[0]==fingerprint and time.monotonic()-cached[1]<60:return cached[2]
        metadata=json.loads(raw);head=metadata.get('head_sha');prs=metadata.get('included_prs');deployed=metadata.get('deployed_at')
        if (metadata.get('state')!='INTEGRATION_TEST_RELEASE' or metadata.get('source')!='UNMERGED_INTEGRATION'
            or metadata.get('main_merged') is not False or metadata.get('tests_passed') is not True
            or not isinstance(head,str) or not re.fullmatch('[a-f0-9]{40}',head)
            or not isinstance(prs,list) or not 1<=len(prs)<=100 or any(type(n) is not int or n<1 for n in prs) or len(set(prs))!=len(prs)
            or not isinstance(metadata.get('branch'),str) or not re.fullmatch('[A-Za-z0-9._/-]{1,200}',metadata['branch'])
            or type(deployed) not in (int,float) or not math.isfinite(deployed) or not 0<deployed<=time.time()):
            raise ValueError('DEMO_RELEASE_METADATA_INVALID')
        response=release_probe();observed=json.loads(response.content)
        if (response.status_code!=200 or response.headers.get('x-qldapm-revision')!=head
            or response.headers.get('x-qldapm-release-type')!='UNMERGED_INTEGRATION_TEST_RELEASE'
            or observed!={'revision':head,'type':'UNMERGED_INTEGRATION_TEST_RELEASE','included_prs':prs}):
            raise ValueError('RELEASE_IDENTITY_MISMATCH')
        result={k:metadata[k] for k in ['head_sha','branch','included_prs','deployed_at','source','main_merged']}
        result.update(state='DEPLOYED_TO_DEMO',release_type='UNMERGED_INTEGRATION_TEST_RELEASE',checked_at=time.time(),evidence='ACTUAL_LOOPBACK_RELEASE_JSON_AND_HEADERS')
    except Exception as error:
        from .engineering_github_sync import _error_code
        result={'state':_error_code(error),'checked_at':time.time(),'main_merged':False}
        fingerprint=locals().get('fingerprint','unavailable')
    service._demo_release_cache=(fingerprint,time.monotonic(),result)
    return result


def deployment_projection(service,prs,*,verify_ancestry=False):
    """Poller verifies immutable commit ancestry; UI reads proof bound to current heads."""
    release=verified_release(service)
    if release.get('state')!='DEPLOYED_TO_DEMO':
        return release,[{**p,'deployment_state':'NOT_VERIFIED_DEPLOYED'} for p in prs]
    with service.store.connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS engineering_github_release_ancestry(head_sha TEXT NOT NULL,release_sha TEXT NOT NULL,verified REAL NOT NULL,PRIMARY KEY(head_sha,release_sha))')
    deadline=time.monotonic()+10;result=[]
    for pr in prs:
        item={**pr,'deployment_state':'NOT_VERIFIED_DEPLOYED'};head=pr.get('head_sha');target=release['head_sha']
        if head==target:item['deployment_state']='DEPLOYED_TO_DEMO'
        elif pr['number'] in release['included_prs'] and isinstance(head,str) and re.fullmatch('[a-f0-9]{40}',head):
            with service.store.connect() as db:proof=db.execute('SELECT 1 FROM engineering_github_release_ancestry WHERE head_sha=? AND release_sha=?',(head,target)).fetchone()
            if not proof and verify_ancestry:
                try:
                    from .engineering_github_sync import get_github_token
                    token=get_github_token();headers={'User-Agent':'QLDAPM-Sync/1.0','Accept':'application/vnd.github+json'}
                    if token:headers['Authorization']='Bearer '+token
                    compared=get_json(f'Luim3141/mini-task-manager/compare/{head}...{target}',headers,deadline)
                    if compared.get('status') not in {'ahead','identical'} or compared.get('merge_base_commit',{}).get('sha')!=head or compared.get('base_commit',{}).get('sha')!=head:
                        raise ValueError('DEMO_PR_ANCESTRY_NOT_VERIFIED')
                    with service.store.connect() as db:db.execute('INSERT OR IGNORE INTO engineering_github_release_ancestry VALUES(?,?,?)',(head,target,time.time()))
                    proof=True
                except Exception as error:
                    from .engineering_github_sync import _error_code
                    item['deployment_error']=_error_code(error)
            item['deployment_state']='DEPLOYED_TO_DEMO' if proof else 'INCLUDED_PR_COMMIT_NOT_VERIFIED'
        result.append(item)
    return release,result
