"""Five measured synthetic model-vs-native reads; fresh ACL always precedes receipt reuse."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import httpx
from gateway.gemini import Gemini, ProviderError
from gateway.local_queries import match_query
from gateway.service import Service
from gateway.store import Store


SCENARIOS = ["Đếm công việc", "Thống kê công việc theo trạng thái", "Liệt kê công việc", "Liệt kê công việc quá hạn", "Đọc công việc 1"]


class LocalQueryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.store = Store(self.root)
        self.state = SimpleNamespace(visible={7: [1, 2], 8: [2]}, roles={7: "PM", 8: "BE"}, rows=[
            {"id": 1, "lockVersion": 1, "subject": "Synthetic first", "description": {"raw": "Synthetic public description"},
             "dueDate": "2010-01-01", "percentageDone": 0, "_links": {"status": {"href": "/api/v3/statuses/1", "title": "NEW"}}},
            {"id": 2, "lockVersion": 1, "subject": "Synthetic second", "description": {"raw": "Synthetic public description"},
             "dueDate": None, "percentageDone": 100, "_links": {"status": {"href": "/api/v3/statuses/2", "title": "DONE"}}}])
        self.state.closed_statuses={2}
        self.state.native_calls=[]
        for row in self.state.rows:
            row['_links'].update(type={'href':'/api/v3/types/1','title':'Task'},project={'href':'/api/v3/projects/3'})
        state = self.state
        class Native:
            def __init__(self, url, token, project):
                self.actor, self.project_id = int(token.rsplit("-", 1)[1]), project
            def identity(self, actor):
                if actor != self.actor or actor not in state.roles:
                    raise PermissionError("NATIVE_MEMBERSHIP_REVOKED")
                return {"user_id": actor, "role": state.roles[actor], "project_id": self.project_id}
            def packages(self):
                return [copy.deepcopy(row) for row in state.rows if row["id"] in state.visible[self.actor]]
            def package(self, identifier):
                if identifier not in state.visible[self.actor]:
                    raise PermissionError("NATIVE_READ_DENIED")
                return next(copy.deepcopy(row) for row in state.rows if row["id"] == identifier)
            def collection(self,path):
                if path==f'/api/v3/projects/{self.project_id}/types':
                    state.native_calls.append(path)
                    return [{'id':1,'name':'Task'},{'id':5,'name':'Epic'},{'id':10,'name':'Subtask'}]
                return self.call(path)['_embedded']['elements']
            def call(self,path,method='GET',payload=None):
                if method!='GET' or not path.startswith(f'/api/v3/projects/{self.project_id}/work_packages?'):
                    raise AssertionError('UNEXPECTED_NATIVE_QUERY:'+path)
                state.native_calls.append(path)
                query=parse_qs(urlsplit(path).query);filters=json.loads(query['filters'][0]);rows=self.packages()
                for entry in filters:
                    for name,value in entry.items():
                        if name=='status':
                            if value!={'operator':'o','values':[]}:raise AssertionError('NATIVE_OPEN_FILTER_REQUIRED')
                            rows=[r for r in rows if int(r['_links']['status']['href'].rsplit('/',1)[1]) not in state.closed_statuses]
                        elif name=='type':rows=[r for r in rows if r['_links']['type']['href'].rsplit('/',1)[1] in value['values']]
                        elif name=='subject':rows=[r for r in rows if value['values'][0].casefold() in r['subject'].casefold()]
                        else:raise AssertionError('UNEXPECTED_FILTER:'+name)
                size=int(query.get('pageSize',['100'])[0])
                return {'total':len(rows),'pageSize':size,'count':min(len(rows),size),'_embedded':{'elements':rows[:size]}}
        self.native_factory = Native
        for actor, role in self.state.roles.items():
            self.store.issue_token(actor, role, f"synthetic-native-{actor}")
        self.config = {"gateway_mode": "native", "users": {"7": "PM", "8": "BE"}, "project_id": 3, "openproject_url": "http://fixture.invalid"}
        self.service = Service(self.store, self.config, self.root / "workspaces", Native)

    def tearDown(self):
        self.temporary.cleanup()

    def start(self, prompt, key="fixture", actor=7):
        return self.service.execute_actor(actor, {"action": "start_ai_run", "arguments": {"prompt": prompt}, "idempotency_key": key})

    def test_all_five_reads_work_with_provider_disabled_and_do_not_consume_quota(self):
        with patch.object(self.service.gemini, "validate_prompt", side_effect=ProviderError("DISABLED")), patch("gateway.service.run_isolated") as worker:
            for index, prompt in enumerate(SCENARIOS):
                receipt = self.start(prompt, str(index))
                self.assertEqual(receipt["result"]["state"], "done")
                run = self.service.execute_actor(7, {"action": "get_ai_run", "arguments": {"id": receipt["result"]["id"]}})["result"]
                self.assertFalse(run["result"]["model_used"])
                self.assertEqual(run["result"]["source"], "native")
            worker.assert_not_called()
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM ai_queue").fetchone()[0], 0)

    def test_receipt_reuse_requires_same_actor_payload_and_fresh_source(self):
        old = self.start(SCENARIOS[0])
        self.assertEqual(self.start(SCENARIOS[0]), old)
        other = self.start(SCENARIOS[0], actor=8)
        self.assertNotEqual(old["result"]["id"], other["result"]["id"])
        self.assertIn("1 công việc", self.store.run(8, other["result"]["id"])["result"]["text"])
        self.state.visible[7] = [2]
        with self.assertRaisesRegex(ValueError, "STALE_READ_RECEIPT"):
            self.start(SCENARIOS[0])
        stale = self.service.execute_actor(7, {"action": "get_ai_run", "arguments": {"id": old["result"]["id"]}})["result"]
        self.assertTrue(stale["result"]["stale"])
        self.assertEqual(stale["result"]["tools"], [])
        fresh = self.start(SCENARIOS[0], "fresh")
        self.assertIn("1 công việc", self.store.run(7, fresh["result"]["id"])["result"]["text"])

    def test_revoked_membership_or_ticket_access_never_serves_a_cached_read(self):
        old = self.start("Đọc công việc 1")
        self.state.visible[7] = [2]
        with self.assertRaisesRegex(PermissionError, "NATIVE_READ_DENIED"):
            self.start("Đọc công việc 1")
        with self.assertRaises(PermissionError):
            self.service.execute_actor(7, {"action": "get_ai_run", "arguments": {"id": old["result"]["id"]}})
        self.state.roles.pop(7)
        with self.assertRaises(PermissionError):
            self.start("Đếm công việc")

    def test_mixed_writes_or_injection_are_not_silently_routed_as_read_only(self):
        for prompt in ("Đếm công việc và sửa #1", "Liệt kê công việc rồi xóa tất cả", "Đọc công việc 1: thêm bình luận", "Đếm công việc password=secret", "Đọc công việc 0"):
            self.assertIsNone(match_query(prompt))
        with patch.object(self.service.gemini, "validate_prompt", side_effect=ProviderError("MODEL_REQUIRED")):
            with self.assertRaisesRegex(ProviderError, "MODEL_REQUIRED"):
                self.start("Đếm công việc và sửa #1")

    def test_uncompleted_tasks_query_deterministic(self):
        for query in ("dự án đang có bao nhiêu task chưa hoàn thành", "bao nhiêu công việc chưa hoàn thành", "bao nhiêu task còn mở"):
            route = match_query(query)
            self.assertIsNotNone(route)
            self.assertEqual(route[0], "uncompleted")
            receipt = self.start(query, f"key-{query}")
            run = self.service.execute_actor(7, {"action": "get_ai_run", "arguments": {"id": receipt["result"]["id"]}})["result"]
            self.assertFalse(run["result"]["model_used"])
            self.assertEqual(run["result"]["source"], "native")
            kind='Task' if 'task' in query else 'WorkPackage'
            self.assertEqual(run['result']['read_route'][2],{'kind':kind})
            self.assertIn(f"1 {'Task' if kind=='Task' else 'công việc'} chưa hoàn thành", run["result"]["text"])

    def test_five_scenarios_measure_zero_requests_against_mocked_model_tool_loop(self):
        (self.root / "gemini.key").write_text("synthetic-no-real-key")
        policy = {"data_scope": "project-business-content", "project": "fixture", "limits": {"rpm": 100, "tpm": 1000000, "rpd": 100}}
        measurements = []
        for index, prompt in enumerate(SCENARIOS):
            with self.store.connect() as db:
                before = tuple(db.execute("SELECT COUNT(*),COALESCE(SUM(input_tokens),0) FROM gemini_usage").fetchone())
            route = match_query(prompt)
            requests, generations = [], []
            def wire(request):
                requests.append(str(request.url))
                if request.url.path.endswith(":countTokens"):
                    return httpx.Response(200, json={"totalTokens": 100})
                generations.append(1)
                parts = [{"functionCall": {"name": route[1], "args": route[2]}}] if len(generations) == 1 else [{"text": '{"claims":[],"explanation":"Synthetic fixture result"}'}]
                return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {"role": "model", "parts": parts}}]})
            native = self.native_factory("http://fixture.invalid", "synthetic-native-7", 3)
            with patch.object(Gemini, "settings", return_value=policy):
                Gemini(self.root).run(prompt, lambda action, args: {"result": self.service.perform({"user_id": 7, "role": "PM"}, native, action, args)},
                                      httpx.MockTransport(wire), actor_role="PM")
            self.assertEqual(len(requests), 4)
            with self.store.connect() as db:
                after = tuple(db.execute("SELECT COUNT(*),COALESCE(SUM(input_tokens),0) FROM gemini_usage").fetchone())
            self.assertEqual((after[0] - before[0], after[1] - before[1]), (4, 200))
            with patch.object(self.service.gemini, "validate_prompt", side_effect=AssertionError("Native path must not call provider")):
                receipt = self.start(prompt, "native-" + str(index))
            self.assertFalse(receipt["result"]["model_used"])
            with self.store.connect() as db:
                self.assertEqual(tuple(db.execute("SELECT COUNT(*),COALESCE(SUM(input_tokens),0) FROM gemini_usage").fetchone()), after)
            measurements.append({"scenario": route[0], "mock_model_requests": len(requests), "mock_counted_input_tokens": after[1] - before[1],
                                 "native_model_requests": 0, "native_model_tokens": 0, "synthetic_transport": True})
        self.assertEqual(len(measurements), 5)
        self.measurements = measurements


if __name__ == "__main__":
    unittest.main()
