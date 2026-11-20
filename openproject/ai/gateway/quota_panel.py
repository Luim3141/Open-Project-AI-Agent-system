"""Local reservation ledger, not live Google billing or total provider token usage."""
import time
import json
from .store import pacific_day

def get_quota_panel_data(store, actor_id, project_id, config=None, policy=None):
    config=config or {}
    maximum=len(config.get('users',{})) or 5
    if not policy or not {'project','quota','limits','model'} <= policy.keys():
        return {'available':False,'error':'PROVIDER_POLICY_NOT_VERIFIED','limits':None,'usage_today':None,
            'provider_details':{'active_model':None,'google_status':'NOT_VERIFIED','billing_checked_live':False},
            'multi_user_allocation':{'max_active_users':maximum,'allocation_policy':'SHARED_FAIR_QUEUE'}}
    now=time.time()
    start,reset=pacific_day(now)
    try:
        with store.connect() as db:
            day=db.execute('SELECT COUNT(*) FROM gemini_usage WHERE project=? AND at>=?',(policy['project'],start)).fetchone()[0]
            minute=db.execute('SELECT COUNT(*),COALESCE(SUM(input_tokens),0) FROM gemini_usage WHERE project=? AND at>?',(policy['project'],now-60)).fetchone()
            receipts=[json.loads(r[0]) for r in db.execute(
                'SELECT document FROM gemini_call_receipts WHERE project=? AND actor=? ORDER BY rowid DESC LIMIT 50',(policy['project'],actor_id))]
        waiting=store.provider_wait(policy)
    except Exception:
        return {'available':False,'error':'QUOTA_STORE_UNAVAILABLE','limits':policy['quota'],'usage_today':None,
            'provider_details':{'active_model':policy['model'],'google_status':'UNKNOWN','billing_checked_live':False}}
    live=[r for r in receipts if r['phase']=='generateContent' and r['state']=='LIVE_SUCCESS']
    actual_tokens=sum((r.get('usage') or {}).get('totalTokenCount',0) for r in live)
    status=waiting['queue_state'] if waiting else 'LOCAL_BUDGET_AVAILABLE'
    if live and not waiting:
        status=f'LIVE_GEMINI last successful receipts: {len(live)} calls, {actual_tokens} provider tokens. Provider remaining quota: unavailable'
    return {'available':True,'tier':'FREE_TIER_CONFIGURED','billing_protection':'FREE_ONLY_NO_PAID_FALLBACK',
        'billing_configuration':'BILLING_CONFIGURATION_UNCHANGED — OWNER_ATTESTED',
        'provider_remaining_quota':'unavailable','observed_actor_recent_usage':{'successful_calls':len(live),'total_tokens':actual_tokens},
        'limits':policy['quota'],'local_safety_limits':policy['limits'],
        'usage_today':{'day_start':start,'next_reset':reset,'rpd_used':day,
            'rpd_remaining':max(0,policy['limits']['rpd']-day),'percent_used':round(100*day/policy['limits']['rpd'],1),
            'actor_rpd_used':None},
        'usage_last_60s':{'rpm_reserved':minute[0],'input_tpm_reserved':minute[1],
            'total_tpm_used':None,'total_tokens_remaining':None},
        'usage_basis':'LOCAL_RESERVATIONS; includes unknown outcomes; excludes other clients and provider output tokens',
        'multi_user_allocation':{'max_active_users':maximum,'allocation_policy':'SHARED_FAIR_QUEUE','nominal_per_user_rpd':None},
        'provider_details':{'model_policy':'FREE_ONLY','active_model':policy['model'],'allowed_models':[policy['model']],
            'google_status':status,
            'billing_checked_live':False,'network_checked_now':False,'quota_reset_schedule':'00:00 America/Los_Angeles'}}
