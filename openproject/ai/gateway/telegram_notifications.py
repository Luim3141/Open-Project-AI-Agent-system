"""Canonical notification candidates from the Observer, never from a UI or n8n verdict."""
import hashlib
import math
from urllib.parse import urlsplit


TYPES = {'TASK_COMPLETED', 'TASK_BLOCKED', 'AGENT_FAILED', 'QA_FAILED', 'AWAITING_APPROVAL', 'PR_CREATED'}


def events(snapshot):
    if (type(snapshot.get('task_id')) is not int or snapshot['task_id'] <= 0
            or type(snapshot.get('project_id')) is not int or snapshot['project_id'] <= 0):
        return []
    result = []
    source = [e for e in snapshot.get('events', []) if isinstance(e, dict)
              and isinstance(e.get('event_id'), str) and e['event_id']
              and type(e.get('timestamp')) in (int, float) and math.isfinite(e['timestamp'])]
    source.sort(key=lambda e: (e['timestamp'], e['event_id']))

    def add(kind, evidence, timestamp, run_id=None, uri=None):
        identifier = hashlib.sha256(f"{snapshot['project_id']}:{snapshot['task_id']}:{kind}:{evidence}".encode()).hexdigest()
        document = {'event_id': identifier, 'event_type': kind, 'task_id': snapshot['task_id'],
                    'project_id': snapshot['project_id'], 'workflow_run_id': run_id,
                    'source_record_id': evidence, 'timestamp': timestamp}
        if uri: document['uri'] = uri
        result.append(document)

    # A final successful agent run is not proof of business acceptance.
    acceptance = snapshot.get('acceptance') or {}
    if source and not snapshot.get('source_conflicts'):
        last = source[-1]
        if (acceptance.get('status') in {'FULLY_COMPLETED', 'COMPLETED'}
                and acceptance.get('required_gates') and acceptance.get('missing_gates') == []
                and all(isinstance(gate, dict) and gate.get('passed') is True for gate in acceptance['required_gates'])
                and acceptance.get('evidence_refs')):
            add('TASK_COMPLETED', str(acceptance['evidence_refs']), last['timestamp'], snapshot.get('latest_run_id'))
        elif acceptance.get('status') in {'AWAITING_OWNER_APPROVAL', 'AWAITING_APPROVAL'}:
            add('AWAITING_APPROVAL', last['event_id'], last['timestamp'], snapshot.get('latest_run_id'))
    for event in source[-100:]:
        kind = event.get('event_type')
        if kind in {'AGENT_FAILED', 'QA_FAILED'}:
            add('AGENT_FAILED', event['event_id'], event['timestamp'], event.get('run_id'))
            if event.get('agent_id') == 'qa' or kind == 'QA_FAILED':
                add('QA_FAILED', event['event_id'], event['timestamp'], event.get('run_id'))
        if (kind in {'AGENT_FAILED', 'RUN_FAILED', 'WORKFLOW_BLOCKED'}
                and snapshot.get('workflow_status') == 'BLOCKED'):
            add('TASK_BLOCKED', event['event_id'], event['timestamp'], event.get('run_id'))
    for artifact in snapshot.get('artifacts', [])[-100:]:
        if not isinstance(artifact, dict): continue
        uri, identifier, created = artifact.get('uri', ''), artifact.get('artifact_id'), artifact.get('created_at')
        parsed = urlsplit(uri) if isinstance(uri, str) else None
        if (artifact.get('type') in {'github_pr', 'pr', 'pull_request'} and identifier
                and artifact.get('verification_status') == 'VERIFIED'
                and parsed and parsed.scheme == 'https' and parsed.hostname == 'github.com'
                and not parsed.username and not parsed.password and '/pull/' in parsed.path
                and type(created) in (int, float) and math.isfinite(created)):
            add('PR_CREATED', str(identifier), created, artifact.get('run_id'), uri)
    return result
