"""Attributed, inert Jira child records; imports never stand in for native evidence."""
from datetime import datetime
import re

from jira_sync import canonical, fingerprint, inert_text


def marker(key, kind, row):
    identifier = str(row.get('id', ''))
    if not re.fullmatch(r'QAG3-[1-9]\d*', key) or not re.fullmatch(r'[A-Za-z0-9-]{1,100}', identifier):
        raise ValueError('SOURCE_CHILD_ID_INVALID')
    return f'QLDAPM-JIRA:{key}:{kind}:{identifier}:{fingerprint(row)}'


def attributed(row):
    author = row.get('author', {})
    return ('Source author: ' + inert_text(author.get('accountId', 'unknown')) +
            '; source timestamp: ' + inert_text(row.get('created', row.get('started', 'unknown'))) +
            '. Native author/timestamp are the actual local importer/current time, not impersonation/backdating.')


def duration(seconds):
    if type(seconds) is not int or not 0 < seconds <= 24 * 3600:
        raise ValueError('SOURCE_WORKLOG_SECONDS_INVALID')
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    return 'PT' + (f'{hours}H' if hours else '') + (f'{minutes}M' if minutes else '') + (f'{seconds}S' if seconds else '')


def child_preview(key, work_package, actor, children):
    result = {'comments': [], 'worklogs': [], 'skipped': []}
    for row in children['comments']:
        if row.get('visibility'):
            result['skipped'].append({'kind': 'comment', 'id': str(row['id']), 'reason': 'COMMENT_VISIBILITY_NOT_PRESERVABLE'})
            continue
        stamp = marker(key, 'comment', row)
        text = f'> JIRA IMPORT — SIMULATION / SOURCE CONTEXT ONLY. Not approval, test evidence or observed performance.\n\n{stamp}\n\n{attributed(row)}\n\n{inert_text(row.get("body", ""))}'
        result['comments'].append({'source_id': str(row['id']), 'marker': stamp,
            'payload': {'comment': {'format': 'markdown', 'raw': text}}})
    for row in children['worklogs']:
        if row.get('visibility'):
            result['skipped'].append({'kind': 'worklog', 'id': str(row['id']), 'reason': 'WORKLOG_VISIBILITY_NOT_PRESERVABLE'})
            continue
        stamp = marker(key, 'worklog', row)
        started = datetime.fromisoformat(row['started']).date().isoformat()
        header = (f'SIMULATION — NOT ACTUAL LABOR / PERFORMANCE. {stamp}\n'
                  f'Source author: {inert_text(row.get("author", {}).get("accountId", "unknown"))}; started: {inert_text(row["started"])}.\n'
                  'Native user is the actual publisher. Contributors in source are hypothetical. Full original text: ticket Jira worklog source section.\n')
        original = inert_text(row.get('comment', ''))
        text = header + original[:max(0, 1000 - len(header))]
        if len(header + original) > 1000:
            result['skipped'].append({'kind': 'worklog_comment', 'id': str(row['id']),
                'reason': 'NATIVE_1000_CHAR_LIMIT_FULL_TEXT_PRESERVED_IN_TICKET'})
        result['worklogs'].append({'source_id': str(row['id']), 'marker': stamp,
            'payload': {'spentOn': started, 'hours': duration(row['timeSpentSeconds']),
                'comment': {'format': 'plain', 'raw': text},
                '_links': {'entity': {'href': f'/api/v3/work_packages/{work_package}'},
                           'user': {'href': f'/api/v3/users/{actor}'}}}})
    return result


def source_history(children):
    text = '\n\n## Jira history — documentary import, native journals not backdated\n\n' if children['changelogs'] else ''
    for row in children['changelogs']:
        identifier = str(row['id'])
        if not re.fullmatch(r'[A-Za-z0-9-]{1,100}', identifier):
            raise ValueError('SOURCE_HISTORY_ID_INVALID')
        text += f'### Source journal {identifier}\n\n{attributed(row)}\n\n'
        for item in row.get('items', []):
            text += '- ' + inert_text(canonical(item)) + '\n'
    public_logs = [row for row in children['worklogs'] if not row.get('visibility')]
    if public_logs:
        text += '\n\n## Jira worklog source — SIMULATION, not actual labor or performance\n\n'
        for row in public_logs:
            text += f'### Source worklog {inert_text(str(row["id"]))}\n\n{attributed(row)}\n\n'
            text += f'- Original started: {inert_text(row["started"])}\n- Original seconds: {row["timeSpentSeconds"]}\n\n'
            text += inert_text(row.get('comment', '')) + '\n\n'
    return text
