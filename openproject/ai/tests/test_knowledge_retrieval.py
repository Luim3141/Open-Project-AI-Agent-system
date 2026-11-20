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
    RetrievedContext,
)

class TestKnowledgeRetrieval(unittest.TestCase):
    def setUp(self):
        self.storage = KnowledgeStorage(KnowledgeStorageConfig(schema_name=SCHEMA_NAME, is_mock=True))
        self.storage.migrate_schema()
        self.ingester = KnowledgeIngester(storage=self.storage)
        self.search_engine = KnowledgeSearchEngine(storage=self.storage, ingester=self.ingester)
        self.retriever = KnowledgeRetriever(search_engine=self.search_engine)

        # Ingest 10 diverse test documents across roles and projects
        docs = [
            # 1. Architecture doc
            classify_document(
                doc_type=KnowledgeDocType.ARCHITECTURE,
                project_id="QAG3",
                source_id="docs/architecture.md",
                title="System Architecture TO-BE",
                content="Architecture specifies 5 LAN users with Docker, Python gateway, PostgreSQL.",
                allowed_roles=["PM", "BA", "FE", "BE", "QA"],
            ),
            # 2. ADR doc
            classify_document(
                doc_type=KnowledgeDocType.ADR,
                project_id="QAG3",
                source_id="docs/adr/0003-orchestration.md",
                title="ADR 0003: State Machine",
                content="Decision to use internal typed state machine instead of heavy external frameworks.",
                allowed_roles=["PM", "BA", "FE", "BE", "QA"],
            ),
            # 3. Work Package 101: Login UI
            classify_document(
                doc_type=KnowledgeDocType.WORK_PACKAGE,
                project_id="QAG3",
                source_id="wp:101",
                title="Frontend Login Interface",
                content="Build accessible responsive login screen in React.",
                allowed_roles=["PM", "BA", "FE", "QA"],
                metadata={"native_id": 101, "lock_version": 2},
            ),
            # 4. Acceptance Criteria for WP 101
            classify_document(
                doc_type=KnowledgeDocType.ACCEPTANCE_CRITERIA,
                project_id="QAG3",
                source_id="wp:101:ac",
                title="AC: Login Authentication",
                content="Given valid email and password, When click submit, Then redirect to dashboard.",
                allowed_roles=["PM", "BA", "FE", "QA"],
                metadata={"native_id": 101, "lock_version": 2},
            ),
            # 5. Work Package 102: Backend API
            classify_document(
                doc_type=KnowledgeDocType.WORK_PACKAGE,
                project_id="QAG3",
                source_id="wp:102",
                title="Backend Auth REST API",
                content="Implement POST /api/v1/auth/token endpoint with rate limiting.",
                allowed_roles=["PM", "BE", "QA"],
                metadata={"native_id": 102, "lock_version": 4},
            ),
            # 6. QA Comment on WP 102
            classify_document(
                doc_type=KnowledgeDocType.COMMENT,
                project_id="QAG3",
                source_id="wp:102:comment:1",
                title="QA Test Note for Auth API",
                content="Verified 429 status code on rate limit exceeded with 10 attempts.",
                allowed_roles=["PM", "BE", "QA"],
                metadata={"native_id": 102, "lock_version": 4},
            ),
            # 7. PM-only Sprint Report
            classify_document(
                doc_type=KnowledgeDocType.SPRINT_REPORT,
                project_id="QAG3",
                source_id="sprint:report:1",
                title="Sprint 1 Risk and Performance Report",
                content="Confidential: Sprint workload capacity buffer and resource allocation.",
                allowed_roles=["PM"],
                metadata={"native_id": 901, "lock_version": 1},
            ),
            # 8. User Story draft from BA
            classify_document(
                doc_type=KnowledgeDocType.WORK_PACKAGE,
                project_id="QAG3",
                source_id="wp:103",
                title="User Story Export CSV",
                content="As a Project Manager, I want to export sprint reports to CSV.",
                allowed_roles=["PM", "BA"],
                metadata={"native_id": 103, "lock_version": 1},
            ),
            # 9. Disallowed Project Doc
            classify_document(
                doc_type=KnowledgeDocType.WORK_PACKAGE,
                project_id="DEMO",
                source_id="wp:501",
                title="Demo Task Outside QAG3",
                content="Demo project details should not leak.",
                allowed_roles=["PM", "BA", "FE", "BE", "QA"],
            ),
            # 10. Temporary doc to be deindexed
            classify_document(
                doc_type=KnowledgeDocType.COMMENT,
                project_id="QAG3",
                source_id="wp:999:temp",
                title="Temporary comment",
                content="Temporary remark to test deindexing.",
                allowed_roles=["PM", "FE"],
            )
        ]
        for d in docs:
            self.ingester.ingest(d)

    # 10 Golden Retrieval Test Cases

    def test_case_01_pm_sprint_risks(self):
        ctx = self.retriever.retrieve_context(query="Sprint Risk and Performance", project_id="QAG3", role="PM")
        self.assertGreater(len(ctx.results), 0)
        self.assertTrue(any("sprint:report:1" in r.source_id for r in ctx.results))
        self.assertIn("[Doc: sprint:report:1", ctx.formatted_prompt_context)

    def test_case_02_ba_user_story_ac(self):
        ctx = self.retriever.retrieve_context(query="Login Authentication Given When Then", project_id="QAG3", role="BA")
        self.assertGreater(len(ctx.results), 0)
        ac_matches = [r for r in ctx.results if r.doc_type == KnowledgeDocType.ACCEPTANCE_CRITERIA]
        self.assertGreaterEqual(len(ac_matches), 1)

    def test_case_03_fe_ui_specs(self):
        ctx = self.retriever.retrieve_context(query="Frontend Login Interface React", project_id="QAG3", role="FE")
        self.assertGreater(len(ctx.results), 0)
        self.assertEqual(ctx.results[0].source_id, "wp:101")
        self.assertEqual(ctx.results[0].native_id, 101)

    def test_case_04_be_rest_api_contract(self):
        ctx = self.retriever.retrieve_context(query="Backend Auth REST API endpoint", project_id="QAG3", role="BE")
        self.assertGreater(len(ctx.results), 0)
        self.assertEqual(ctx.results[0].source_id, "wp:102")
        self.assertEqual(ctx.results[0].native_id, 102)

    def test_case_05_qa_test_coverage_comments(self):
        ctx = self.retriever.retrieve_context(query="Verified 429 status code rate limit", project_id="QAG3", role="QA")
        self.assertGreater(len(ctx.results), 0)
        self.assertEqual(ctx.results[0].source_id, "wp:102:comment:1")

    def test_case_06_non_pm_fail_closed_on_pm_report(self):
        # FE querying PM confidential report must fail closed (0 results)
        ctx = self.retriever.retrieve_context(query="Sprint Risk and Performance Report", project_id="QAG3", role="FE")
        pm_results = [r for r in ctx.results if r.source_id == "sprint:report:1"]
        self.assertEqual(len(pm_results), 0)
        self.assertNotIn("sprint:report:1", ctx.formatted_prompt_context)

    def test_case_07_cross_project_isolation_fail_closed(self):
        # Querying for DEMO project task from QAG3 scope returns 0 results
        ctx = self.retriever.retrieve_context(query="Demo Task Outside QAG3", project_id="QAG3", role="PM")
        self.assertEqual(len(ctx.results), 0)

    def test_case_08_deindexed_source_fail_closed(self):
        # Deindex wp:999:temp
        self.ingester.deindex_source("wp:999:temp")
        ctx = self.retriever.retrieve_context(query="Temporary remark deindexing", project_id="QAG3", role="PM")
        self.assertEqual(len(ctx.results), 0)
        self.assertNotIn("wp:999:temp", [r.source_id for r in ctx.results])

    def test_case_09_empty_or_nonsense_query(self):
        ctx = self.retriever.retrieve_context(query="XYZ999UnknownKeywordNone", project_id="QAG3", role="PM")
        self.assertEqual(len(ctx.results), 0)
        self.assertEqual(ctx.formatted_prompt_context, "")

    def test_case_10_prompt_formatting_with_citations(self):
        ctx = self.retriever.retrieve_context(query="System Architecture Docker Python", project_id="QAG3", role="BE")
        self.assertGreater(len(ctx.results), 0)
        # Check formatted citations
        self.assertIn("### Relevant Internal Knowledge Context", ctx.formatted_prompt_context)
        self.assertIn("[Doc: docs/architecture.md", ctx.formatted_prompt_context)

if __name__ == '__main__':
    unittest.main()
