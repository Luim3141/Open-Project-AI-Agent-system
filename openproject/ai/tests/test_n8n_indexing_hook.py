import unittest
import json
from openproject.ai.gateway.knowledge_storage import (
    KnowledgeStorage,
    KnowledgeStorageConfig,
    SCHEMA_NAME,
)
from openproject.ai.gateway.knowledge_ingestion import (
    KnowledgeIngester,
)
from openproject.ai.gateway.n8n_indexing_hook import (
    IndexingHookHandler,
    IndexingEvent,
    redact_secrets,
    export_indexing_workflow,
)

class TestN8nIndexingHook(unittest.TestCase):
    def setUp(self):
        self.storage = KnowledgeStorage(KnowledgeStorageConfig(schema_name=SCHEMA_NAME, is_mock=True))
        self.storage.migrate_schema()
        self.ingester = KnowledgeIngester(storage=self.storage)
        self.hook = IndexingHookHandler(
            ingester=self.ingester,
            webhook_secret="internal-hook-secret-123",
            rate_limit_per_minute=30,
        )

    def test_secret_redaction(self):
        text_with_secrets = "Project config: token=ghp_1234567890abcdef and password=SuperSecretPassword123."
        redacted = redact_secrets(text_with_secrets)
        self.assertNotIn("ghp_1234567890abcdef", redacted)
        self.assertNotIn("SuperSecretPassword123", redacted)
        self.assertIn("[REDACTED_SECRET]", redacted)

    def test_non_blocking_async_event_intake(self):
        payload = {
            "event_type": "work_package_updated",
            "project_id": "QAG3",
            "source_id": "wp:301",
            "title": "Task 301 updated",
            "content": "Updated description without blocking UI.",
            "allowed_roles": ["PM", "DEV"],
        }
        res = self.hook.handle_event(payload, auth_token="internal-hook-secret-123")
        self.assertTrue(res["accepted"])
        self.assertEqual(res["status"], "QUEUED_OR_INGESTED")
        self.assertEqual(self.storage.count_documents(), 1)

    def test_auth_token_enforcement(self):
        payload = {
            "event_type": "work_package_updated",
            "project_id": "QAG3",
            "source_id": "wp:302",
            "title": "Task 302",
            "content": "Testing auth",
        }
        res = self.hook.handle_event(payload, auth_token="wrong-token")
        self.assertFalse(res["accepted"])
        self.assertEqual(res["error"], "UNAUTHORIZED")
        self.assertEqual(self.storage.count_documents(), 0)

    def test_retry_queue_on_rate_limit(self):
        # Configure hook with tight limit
        tight_hook = IndexingHookHandler(
            ingester=self.ingester,
            webhook_secret="secret",
            rate_limit_per_minute=2,
        )
        # 1st and 2nd pass
        res1 = tight_hook.handle_event({"project_id": "QAG3", "source_id": "wp:1", "title": "T1", "content": "C1"}, "secret")
        res2 = tight_hook.handle_event({"project_id": "QAG3", "source_id": "wp:2", "title": "T2", "content": "C2"}, "secret")
        self.assertTrue(res1["accepted"])
        self.assertTrue(res2["accepted"])

        # 3rd is throttled and queued for retry
        res3 = tight_hook.handle_event({"project_id": "QAG3", "source_id": "wp:3", "title": "T3", "content": "C3"}, "secret")
        self.assertTrue(res3["accepted"])
        self.assertEqual(res3["status"], "BUFFERED_FOR_RETRY")
        self.assertEqual(tight_hook.get_retry_queue_size(), 1)

    def test_export_indexing_workflow_json(self):
        wf = export_indexing_workflow()
        self.assertIn("nodes", wf)
        self.assertIn("connections", wf)
        self.assertEqual(wf["name"], "QLDAPM Local Second Brain Indexing Hook")

if __name__ == '__main__':
    unittest.main()
