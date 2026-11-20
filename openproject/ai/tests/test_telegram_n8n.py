import unittest


class TelegramN8nTests(unittest.TestCase):
    def test_workflow_validates_lease_before_native_send_and_acks_real_message(self):
        from automation.telegram_n8n import build_workflow
        workflow = build_workflow('header-credential', 'telegram-credential')
        nodes = workflow['nodes']
        self.assertEqual([n['type'] for n in nodes], [
            'n8n-nodes-base.webhook', 'n8n-nodes-base.httpRequest', 'n8n-nodes-base.telegram',
            'n8n-nodes-base.code', 'n8n-nodes-base.httpRequest', 'n8n-nodes-base.respondToWebhook'])
        self.assertIn('/internal/notifications/validate', nodes[1]['parameters']['url'])
        self.assertIn('result.message_id', nodes[3]['parameters']['jsCode'])
        self.assertIn('result.chat.id', nodes[3]['parameters']['jsCode'])
        self.assertIn('/internal/notifications/ack', nodes[4]['parameters']['url'])
        self.assertEqual(nodes[0]['parameters']['authentication'], 'headerAuth')
        self.assertEqual(workflow['settings']['saveDataSuccessExecution'], 'none')
        self.assertEqual(workflow['settings']['saveDataErrorExecution'], 'none')
        self.assertNotIn('telegramTrigger', str(workflow))

    def test_no_secrets_or_redirecting_target_in_export(self):
        from automation.telegram_n8n import build_workflow
        self.assertNotIn('accessToken', str(build_workflow('h', 't')))
        for url in ['http://u:p@telegram-ai:8091', 'http://telegram-ai:8091/path', 'http://telegram-ai:8091?x=1']:
            with self.assertRaises(ValueError): build_workflow('h', 't', url)


if __name__ == '__main__': unittest.main()
