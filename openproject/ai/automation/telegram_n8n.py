"""Dedicated outgoing workflow, built against the installed n8n Telegram v1.2 schema.

Credentials are references only. Never place a Bot Token or shared key in this export.
"""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

NAME = 'QLDAPM — Telegram Agent Notifications'
WEBHOOK = 'qldapm-telegram-agent-notifications'


def build_workflow(notification_credential_id, telegram_credential_id, bot_url='http://telegram-ai:8091'):
    parsed = urlsplit(bot_url)
    if (parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password
            or parsed.path not in {'', '/'} or parsed.query or parsed.fragment):
        raise ValueError('NOTIFICATION_SERVICE_ORIGIN_REQUIRED')
    if not all(isinstance(v, str) and 1 <= len(v) <= 128 for v in (notification_credential_id, telegram_credential_id)):
        raise ValueError('DEDICATED_CREDENTIAL_IDS_REQUIRED')
    notification_credential = {'httpHeaderAuth': {'id': notification_credential_id, 'name': 'QLDAPM Telegram Notification Key'}}

    def http(identifier, name, path, body, x):
        return {'id': identifier, 'name': name, 'type': 'n8n-nodes-base.httpRequest', 'typeVersion': 4.2,
                'position': [x, 200], 'credentials': notification_credential,
                'parameters': {'method': 'POST', 'url': bot_url.rstrip('/')+path,
                               'authentication': 'genericCredentialType', 'genericAuthType': 'httpHeaderAuth',
                               'sendBody': True, 'specifyBody': 'json', 'jsonBody': body,
                               'options': {'timeout': 10000, 'redirect': {'redirect': {'followRedirects': False}}}}}

    nodes = [
        {'id': 'notification-trigger', 'name': 'Notification Outbox Webhook', 'type': 'n8n-nodes-base.webhook',
         'typeVersion': 2, 'position': [0, 200], 'webhookId': WEBHOOK, 'credentials': notification_credential,
         'parameters': {'httpMethod': 'POST', 'path': WEBHOOK, 'authentication': 'headerAuth',
                        'responseMode': 'responseNode', 'options': {}}},
        http('validate', 'Validate Canonical Event And Recipient', '/internal/notifications/validate', '={{ $json.body }}', 260),
        {'id': 'telegram-send', 'name': 'Send Telegram Notification', 'type': 'n8n-nodes-base.telegram',
         'typeVersion': 1.2, 'position': [520, 200],
         'credentials': {'telegramApi': {'id': telegram_credential_id, 'name': 'QLDAPM AI Commander Telegram'}},
         'parameters': {'resource': 'message', 'operation': 'sendMessage', 'chatId': '={{ $json.chat_id }}',
                        'text': '={{ $json.text }}', 'additionalFields': {'parse_mode': 'HTML', 'appendAttribution': False, 'disable_web_page_preview': True}}},
        {'id': 'verify-send', 'name': 'Require Telegram Message Receipt', 'type': 'n8n-nodes-base.code',
         'typeVersion': 2, 'position': [780, 200], 'parameters': {'jsCode':
            "const source=$('Validate Canonical Event And Recipient').first().json; const sent=$json; "
            "if(sent.ok!==true || !Number.isSafeInteger(sent.result?.message_id) || sent.result.message_id<=0 || "
            "sent.result.chat.id!==source.chat_id) throw new Error('TELEGRAM_MESSAGE_RECEIPT_REQUIRED'); "
            "return [{json:{notification_id:source.notification_id,lease:source.lease,"
            "message_id:sent.result.message_id,chat_id:sent.result.chat.id}}];"}},
        http('ack', 'Persist Delivery And Reply Context', '/internal/notifications/ack', '={{ $json }}', 1040),
        {'id': 'reply', 'name': 'Reply Durable Delivery ACK', 'type': 'n8n-nodes-base.respondToWebhook',
         'typeVersion': 1.4, 'position': [1300, 200],
         'parameters': {'respondWith': 'json', 'responseBody': '={{ $json }}', 'options': {}}}
    ]
    connections = {left['name']: {'main': [[{'node': right['name'], 'type': 'main', 'index': 0}]]}
                   for left, right in zip(nodes, nodes[1:])}
    return {'name': NAME, 'nodes': nodes, 'connections': connections,
            'settings': {'executionOrder': 'v1', 'timezone': 'Asia/Bangkok', 'executionTimeout': 60,
                         'saveDataErrorExecution': 'none', 'saveDataSuccessExecution': 'none',
                         'saveManualExecutions': False, 'saveExecutionProgress': False}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--notification-credential-id', required=True)
    parser.add_argument('--telegram-credential-id', required=True)
    parser.add_argument('--bot-url', default='http://telegram-ai:8091')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    workflow = build_workflow(args.notification_credential_id, args.telegram_credential_id, args.bot_url)
    with args.output.open('x', encoding='utf-8') as stream: json.dump(workflow, stream, ensure_ascii=False, indent=2)
