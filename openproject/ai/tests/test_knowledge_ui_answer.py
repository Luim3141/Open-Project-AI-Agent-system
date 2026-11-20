import unittest
from openproject.ai.gateway.knowledge_classifier import (
    KnowledgeDocType,
    classify_document,
)
from openproject.ai.gateway.knowledge_storage import (
    KnowledgeStorage,
    KnowledgeStorageConfig,
    SCHEMA_NAME,
)
from openproject.ai.gateway.knowledge_ingestion import (
    KnowledgeIngester,
)
from openproject.ai.gateway.knowledge_search import (
    KnowledgeSearchEngine,
)
from openproject.ai.gateway.knowledge_retrieval import (
    KnowledgeRetriever,
)
from openproject.ai.gateway.decision_memory import (
    DecisionMemory,
    DecisionType,
)
from openproject.ai.gateway.knowledge_ui_answer import (
    KnowledgeAnswerGenerator,
    UIAnswerResult,
)

class TestKnowledgeUIAnswer(unittest.TestCase):
    def setUp(self):
        self.storage = KnowledgeStorage(KnowledgeStorageConfig(schema_name=SCHEMA_NAME, is_mock=True))
        self.storage.migrate_schema()
        self.ingester = KnowledgeIngester(storage=self.storage)
        self.search_engine = KnowledgeSearchEngine(storage=self.storage, ingester=self.ingester)
        self.retriever = KnowledgeRetriever(search_engine=self.search_engine)
        self.decision_mem = DecisionMemory()
        self.answer_gen = KnowledgeAnswerGenerator(
            retriever=self.retriever,
            decision_memory=self.decision_mem,
        )

        # Ingest test docs
        doc1 = classify_document(
            doc_type=KnowledgeDocType.WORK_PACKAGE,
            project_id="QAG3",
            source_id="wp:101",
            title="Đăng nhập tài khoản người dùng",
            content="Giao diện đăng nhập React hỗ trợ xác thực OAuth và session cookie.",
            allowed_roles=["PM", "BA", "FE", "BE", "QA"],
            metadata={"native_id": 101, "lock_version": 2},
        )
        doc2 = classify_document(
            doc_type=KnowledgeDocType.SPRINT_REPORT,
            project_id="QAG3",
            source_id="sprint:report:1",
            title="Báo cáo tài chính Sprint",
            content="Bảo mật PM: Ngân sách dự phòng Sprint 1 còn 100%.",
            allowed_roles=["PM"],
            metadata={"native_id": 901, "lock_version": 1},
        )
        self.ingester.ingest(doc1)
        self.ingester.ingest(doc2)

    def test_grounded_answer_with_native_citations(self):
        res = self.answer_gen.generate_answer(
            query="Tính năng đăng nhập tài khoản người dùng hoạt động thế nào?",
            project_id="QAG3",
            role="FE",
        )
        self.assertTrue(res.found)
        self.assertIn("101", res.answer_text)
        self.assertIn("[Doc: wp:101 #101 lockVersion=2]", res.citations[0])
        self.assertEqual(len(res.citations), 1)

    def test_honest_missing_knowledge_reporting(self):
        res = self.answer_gen.generate_answer(
            query="Hệ thống có hỗ trợ thanh toán qua Apple Pay không?",
            project_id="QAG3",
            role="BA",
        )
        self.assertFalse(res.found)
        self.assertIn("chưa có trong cơ sở tri thức", res.answer_text)
        self.assertEqual(len(res.citations), 0)

    def test_unauthorized_access_denial_no_leak(self):
        # Non-PM asks about PM financial report
        res = self.answer_gen.generate_answer(
            query="Báo cáo tài chính Sprint ngân sách thế nào?",
            project_id="QAG3",
            role="FE",
        )
        self.assertFalse(res.found)
        # Does not leak content or existence
        self.assertNotIn("Ngân sách dự phòng", res.answer_text)
        self.assertIn("chưa có trong cơ sở tri thức", res.answer_text)
        self.assertEqual(len(res.citations), 0)

    def test_anti_hallucination_eval_suite(self):
        eval_cases = [
            ("Cho tôi biết số điện thoại của khách hàng", False),
            ("Đăng nhập tài khoản người dùng", True),
            ("Hướng dẫn cài đặt máy chủ bay lên sao hỏa", False),
        ]
        for query, expected_found in eval_cases:
            ans = self.answer_gen.generate_answer(query, "QAG3", "QA")
            self.assertEqual(ans.found, expected_found, f"Failed eval on query: {query}")
            if not expected_found:
                self.assertIn("chưa có trong cơ sở tri thức", ans.answer_text)

if __name__ == '__main__':
    unittest.main()
