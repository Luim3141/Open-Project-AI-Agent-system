import json
import time
import unittest
import uuid
from unittest.mock import patch

from starlette.testclient import TestClient
from gateway.agent_models import AgentTask, AgentRun
from gateway.agent_trace import bind_run, reset_run, trace_event
from gateway.app import create_app, openapi_document
from gateway.service import MUTATIONS
from tests import test_local_queries as fixture


class AgentAPITests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.LocalQueryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.store, self.service = self.fixture.store, self.fixture.service
        self.service.config["hosts"] = ["testserver"]
        self.tokens = {actor: self.store.issue_token(actor, role, f"synthetic-native-{actor}") for actor, role in self.fixture.state.roles.items()}
        self.dispatch = patch.object(self.service, "start_dispatcher")
        self.dispatch.start()
        self.addCleanup(self.dispatch.stop)
        self.client = TestClient(create_app(self.fixture.root, self.service))
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def headers(self, actor=7):
        return {"Authorization": "Bearer " + self.tokens[actor]}

    def seed(self, actor=7, project=3, bound=False):
        now = time.time()
        task = AgentTask(task_id=str(uuid.uuid4()), actor_id=actor, project_id=project, conversation_id=str(uuid.uuid4()),
            agent="ba", instruction="PRIVATE_TASK_INSTRUCTION_NOT_PUBLIC", created_at=now, expires_at=now + 600)
        self.store.create_agent_task(actor, project, task)
        if bound:
            response = self.store.enqueue_run(actor, {"prompt": task.instruction, "allow_routine_writes": False,
                "write_scope_ids": [], "policy_sha256": "a" * 64}, kind="agent", agent_task=task)
            return response["result"]["id"]
        run = AgentRun(run_id=str(uuid.uuid4()), task_id=task.task_id, actor_id=actor, project_id=project,
            trace_id=str(uuid.uuid4()), created_at=now, updated_at=now)
        self.store.create_agent_run(actor, project, run)
        return run.run_id

    def test_owned_metadata_paginates_without_other_actor_project_or_content(self):
        owned = [self.seed() for _ in range(3)]
        other = self.seed(8)
        wrong_project = self.seed(project=4)
        first = self.client.get("/api/v1/agent-runs?limit=2", headers=self.headers()).json()["result"]
        self.assertEqual(first["total"], 3)
        self.assertEqual([row["run_id"] for row in first["items"]], list(reversed(owned))[:2])
        self.assertEqual(first["next_offset"], 2)
        last = self.client.get("/api/v1/agent-runs?limit=2&offset=2", headers=self.headers()).json()["result"]
        self.assertEqual(last["items"][0]["run_id"], owned[0])
        self.assertIsNone(last["next_offset"])
        encoded = json.dumps([first, last])
        for private in (other, wrong_project, "PRIVATE_TASK_INSTRUCTION_NOT_PUBLIC", "synthetic-native-"):
            self.assertNotIn(private, encoded)
        self.assertNotIn("result", first["items"][0])

    def test_failed_progress_is_read_only_and_links_only_owned_canonical_receipt(self):
        identifier = self.seed(bound=True)
        self.store.claim_run()
        self.store.finish_run(7, identifier, {"status": "failed", "text": "PRIVATE_RESULT_NOT_PUBLIC", "tools": []}, "failed_or_unknown")
        progress = self.client.get("/api/v1/agent-runs/" + identifier, headers=self.headers()).json()["result"]
        self.assertEqual(progress["state"], "FAILED")
        self.assertEqual(progress["receipt_id"], identifier)
        self.assertFalse(progress["can_replay"])
        self.assertTrue(progress["reconcile_required"])
        self.assertTrue(progress["new_request_required"])
        self.assertNotIn("PRIVATE_RESULT_NOT_PUBLIC", json.dumps(progress))
        before = self.store.agent_run(7, 3, identifier)
        for path in ("/api/v1/agent-runs", "/api/v1/agent-runs/" + identifier + "/retry", "/api/v1/agent-runs/" + identifier + "/reconcile"):
            response = self.client.post(path, headers=self.headers(), json={})
            self.assertIn(response.status_code, {404, 405})
        self.assertEqual(self.store.agent_run(7, 3, identifier), before)
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM ai_queue WHERE state='queued'").fetchone()[0], 0)

    def test_trace_pages_contain_only_owned_scoped_code_metadata(self):
        identifier = self.seed(bound=True)
        self.store.claim_run()
        token = bind_run(self.store, 7, 3, identifier)
        try:
            trace_event("worker", "start")
            trace_event("native", "GET")
        finally:
            reset_run(token)
        self.store.finish_run(7, identifier, {"status": "answered", "text": "PRIVATE_RESULT_NOT_PUBLIC", "tools": []}, "done")
        first = self.client.get(f"/api/v1/agent-runs/{identifier}/trace?limit=2", headers=self.headers()).json()["result"]
        second = self.client.get(f"/api/v1/agent-runs/{identifier}/trace?limit=2&offset=2", headers=self.headers()).json()["result"]
        self.assertEqual(first["next_offset"], 2)
        self.assertFalse({r["event_id"] for r in first["items"]} & {r["event_id"] for r in second["items"]})
        self.assertTrue(all(r["actor_id"] == 7 and r["project_id"] == 3 and r["run_id"] == identifier for r in first["items"] + second["items"]))
        self.assertNotIn("PRIVATE_", json.dumps([first, second]))

    def test_anonymous_cross_actor_and_changed_native_role_fail_closed(self):
        identifier = self.seed()
        other = self.seed(8)
        for path in ("/api/v1/agent-runs", "/api/v1/agent-runs/" + identifier, "/api/v1/agent-runs/" + identifier + "/trace"):
            self.assertEqual(self.client.get(path).status_code, 401)
        for actor, target in ((8, identifier), (7, other)):
            for suffix in ("", "/trace"):
                self.assertEqual(self.client.get("/api/v1/agent-runs/" + target + suffix, headers=self.headers(actor)).status_code, 403)
        self.fixture.state.roles[7] = "BE"
        self.assertEqual(self.client.get("/api/v1/agent-runs", headers=self.headers()).status_code, 403)

    def test_page_and_id_validation_rejects_coercion_and_extra_scope(self):
        for query in ("limit=0", "limit=51", "offset=-1", "offset=2147483648", "limit=true", "limit=1.5", "actor=8", "project_id=4"):
            with self.subTest(query=query):
                self.assertEqual(self.client.get("/api/v1/agent-runs?" + query, headers=self.headers()).status_code, 422)
        for page in ({"limit": True}, {"offset": 1.5}):
            self.assertEqual(self.client.post("/api/v1/commands", headers=self.headers(), json={"action": "list_agent_runs", "arguments": page}).status_code, 422)
        self.assertEqual(self.client.get("/api/v1/agent-runs/invalid", headers=self.headers()).status_code, 422)
        self.assertEqual(self.client.post("/api/v1/commands", headers=self.headers(), json={"action": "get_agent_run", "arguments": {"id": {"actor": 8}}}).status_code, 422)

    def test_openapi_refs_and_mcp_readonly_tools_match_actual_contract(self):
        document = openapi_document()
        def check_refs(value):
            if isinstance(value, dict):
                if "$ref" in value:
                    node = document
                    for part in value["$ref"].removeprefix("#/").split("/"):
                        node = node[part]
                for nested in value.values():
                    check_refs(nested)
            elif isinstance(value, list):
                for nested in value:
                    check_refs(nested)
        check_refs(document)
        headers = {**self.headers(), "Accept": "application/json, text/event-stream"}
        tools = self.client.post("/mcp", headers=headers, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).json()["result"]["tools"]
        names = {tool["name"]: tool for tool in tools}
        for name in ("list_agent_runs", "get_agent_run", "get_agent_trace"):
            self.assertNotIn(name, MUTATIONS)
            self.assertTrue(names[name]["annotations"]["readOnlyHint"])
        identifier = self.seed()
        response = self.client.post("/mcp", headers=headers, json={"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "get_agent_run", "arguments": {"arguments": {"id": identifier}}}})
        self.assertFalse(response.json()["result"].get("isError", False))
        self.assertIn(identifier, response.text)
        self.assertNotIn("PRIVATE_", response.text)


if __name__ == "__main__":
    unittest.main()
