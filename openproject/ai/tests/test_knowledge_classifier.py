import unittest
from openproject.ai.gateway.knowledge_classifier import (
    KnowledgeDocType,
    KnowledgeDocument,
    classify_document,
    classify_work_package_knowledge,
    SecurityValidationError,
    ALLOWED_PROJECTS,
)

class TestKnowledgeClassifier(unittest.TestCase):
    def setUp(self):
        self.allowed_project = "QAG3"
        self.disallowed_project = "SECRET_PROJ_999"

    def test_classify_valid_internal_types(self):
        # 1. Architecture doc
        doc_arch = classify_document(
            doc_type=KnowledgeDocType.ARCHITECTURE,
            project_id=self.allowed_project,
            source_id="docs/architecture.md",
            title="System Architecture",
            content="TO-BE architecture for 5 LAN users with local Docker.",
            allowed_roles=["PM", "BA", "FE", "BE", "QA"],
        )
        self.assertEqual(doc_arch.doc_type, KnowledgeDocType.ARCHITECTURE)
        self.assertEqual(doc_arch.project_id, "QAG3")
        self.assertTrue(doc_arch.source_hash)

        # 2. ADR doc
        doc_adr = classify_document(
            doc_type=KnowledgeDocType.ADR,
            project_id=self.allowed_project,
            source_id="docs/adr/0003-orchestration.md",
            title="ADR 0003",
            content="ADR: Use typed state machine instead of heavy external frameworks.",
        )
        self.assertEqual(doc_adr.doc_type, KnowledgeDocType.ADR)

        # 3. Sprint report
        doc_sprint = classify_document(
            doc_type=KnowledgeDocType.SPRINT_REPORT,
            project_id=self.allowed_project,
            source_id="sprint_reports/sprint_1.md",
            title="Sprint 1 Report",
            content="Sprint 1 finished with 10 work packages completed.",
        )
        self.assertEqual(doc_sprint.doc_type, KnowledgeDocType.SPRINT_REPORT)

    def test_reject_external_crawl_and_github(self):
        # Reject github.com URLs
        with self.assertRaises(SecurityValidationError):
            classify_document(
                doc_type=KnowledgeDocType.ARCHITECTURE,
                project_id=self.allowed_project,
                source_id="https://github.com/external/repo",
                title="External Repo Doc",
                content="Some crawled content from github.com",
            )

        # Reject web crawling in content
        with self.assertRaises(SecurityValidationError):
            classify_document(
                doc_type=KnowledgeDocType.WORK_PACKAGE,
                project_id=self.allowed_project,
                source_id="wp-123",
                title="Task with external crawler",
                content="Crawler downloaded from https://example.com/api/scrape",
            )

    def test_reject_disallowed_project_or_missing_project(self):
        # Disallowed project
        with self.assertRaises(SecurityValidationError):
            classify_document(
                doc_type=KnowledgeDocType.ARCHITECTURE,
                project_id=self.disallowed_project,
                source_id="arch-1",
                title="Secret Arch",
                content="Architecture of unauthorized project.",
            )

        # Empty project
        with self.assertRaises(SecurityValidationError):
            classify_document(
                doc_type=KnowledgeDocType.WORK_PACKAGE,
                project_id="",
                source_id="wp-1",
                title="No project",
                content="Content without project",
            )

    def test_classify_work_package_ac_and_comments(self):
        wp_data = {
            "id": 101,
            "project_id": "QAG3",
            "subject": "User Authentication UI",
            "description": "Là User, Tôi muốn đăng nhập. Given email valid, When click submit, Then redirect to dashboard.",
            "lock_version": 2,
            "comments": [
                {"id": 501, "author": "QA Lead", "text": "Tested on staging: Pass with 200 OK."},
                {"id": 502, "author": "BE Dev", "text": "Added rate limit guard."}
            ]
        }

        docs = classify_work_package_knowledge(wp_data)
        self.assertGreaterEqual(len(docs), 2)  # WP + AC + Comments

        types = [d.doc_type for d in docs]
        self.assertIn(KnowledgeDocType.WORK_PACKAGE, types)
        self.assertIn(KnowledgeDocType.ACCEPTANCE_CRITERIA, types)
        self.assertIn(KnowledgeDocType.COMMENT, types)

        # Verify provenance and hash
        for d in docs:
            self.assertEqual(d.project_id, "QAG3")
            self.assertEqual(d.metadata["native_id"], 101)
            self.assertEqual(d.metadata["lock_version"], 2)
            self.assertTrue(len(d.source_hash) == 64)

    def test_deterministic_hash_integrity(self):
        doc1 = classify_document(
            doc_type=KnowledgeDocType.ADR,
            project_id=self.allowed_project,
            source_id="adr-1",
            title="Same Title",
            content="Deterministic content hash check.",
        )
        doc2 = classify_document(
            doc_type=KnowledgeDocType.ADR,
            project_id=self.allowed_project,
            source_id="adr-1",
            title="Same Title",
            content="Deterministic content hash check.",
        )
        self.assertEqual(doc1.source_hash, doc2.source_hash)

    def test_classify_project_3_and_qldapm_local(self):
        doc_proj3 = classify_document(
            doc_type=KnowledgeDocType.ARCHITECTURE,
            project_id="3",
            source_id="docs/local.md",
            title="Local Arch",
            content="Local deployment architecture.",
        )
        self.assertEqual(doc_proj3.project_id, "3")

        doc_local = classify_document(
            doc_type=KnowledgeDocType.WORK_PACKAGE,
            project_id="qldapm-local",
            source_id="wp-301",
            title="Local WP",
            content="Local WP description.",
        )
        self.assertEqual(doc_local.project_id, "QLDAPM-LOCAL")

if __name__ == '__main__':
    unittest.main()
