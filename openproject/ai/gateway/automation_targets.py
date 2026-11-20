"""Explicit scheduled readers; selecting a principal never grants Native permissions."""
from .permissions import AI_SYSTEM_OWNER
from .store import canonical,digest

def select(service,command):
    users=service.config['users']
    configured=service.config.get('automation_readers')
    targets=[(int(actor),role) for actor,role in users.items() if role!=AI_SYSTEM_OWNER]
    if configured is None:return targets,command,None
    if not isinstance(configured,list) or not configured or len(set(configured))!=len(configured) or any(type(actor) is not int or actor<=0 or str(actor) not in users or users[str(actor)]==AI_SYSTEM_OWNER for actor in configured):
        raise PermissionError('AUTOMATION_READER_SELECTION_INVALID')
    selected=[row for row in targets if row[0] in configured]
    selection={'selected_actor_ids':sorted(configured),'excluded_actor_ids':sorted(actor for actor,_ in targets if actor not in configured),
               'reason':'EXPLICIT_CONFIGURED_READERS; native identity/role/permission rechecked per target'}
    # A changed target set gets its own dated receipt; old partial receipts remain immutable history.
    return selected,{**command,'request_key':command['request_key']+':readers-'+digest(canonical(selection))[:12]},selection

def finish(store,result,selection):
    if selection is None:return result
    result={**result,'target_selection':selection}
    with store.connect() as db:db.execute('UPDATE automation_runs SET receipt=? WHERE id=?',(canonical(result),result['run_id']))
    return result
