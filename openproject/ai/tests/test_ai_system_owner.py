"""Offline Owner18 qualification; no Main data, credentials, model or network writes."""
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock

from gateway import daily_brief
from gateway.native import Native
from gateway.permissions import allowed
from gateway.service import Service
from gateway.store import Store

OWNER = "AI_SYSTEM_OWNER"


class OwnerIdentityTests(unittest.TestCase):
    def native(self, **changes):
        native = Native("http://127.0.0.1:8088", "fixture-owner-key", changes.pop("project_id", 5))
        user = {"id": 18, "login": "op-owner", "admin": True, "status": "active", **changes}
        proof = {"actor": 18, "project_id": 5, "role": OWNER, "capabilities": [OWNER]}
        native.call = Mock(side_effect=lambda path: user if path.endswith("/users/me") else
                           {"identifier": "qldapm-local"} if "/projects/" in path else proof)
        native.collection = Mock(return_value=[])
        return native

    def test_owner_requires_fresh_native_identity_and_server_capability(self):
        native = self.native()
        self.assertEqual(native.identity(18)["role"], OWNER)
        native.call.assert_any_call("/api/v3/qldapm/permissions")
        native.collection.assert_not_called()

    def test_other_admin_wrong_login_inactive_or_other_project_does_not_inherit(self):
        for changes in ({"id": 17}, {"login": "other-owner"}, {"admin": False},
                        {"status": "locked"}, {"project_id": 3}):
            with self.subTest(changes=changes), self.assertRaises(PermissionError):
                self.native(**changes).identity(18)

    def test_six_role_capabilities_preserve_existing_ceilings(self):
        for role in (OWNER, "PM", "BA", "BE", "FE", "QA"):
            self.assertTrue(allowed(role, "knowledge_search", "native"))
            self.assertEqual(allowed(role, "update_work_package", "native"), role in {OWNER, "PM"})
            self.assertEqual(allowed(role, "owner_inspect", "native"), role == OWNER)
            self.assertFalse(allowed(role, "write_code", "native"))

    def test_owner_registration_does_not_expand_fixed_business_daily_targets(self):
        service = Mock()
        service.config = {"project_id": 5, "users": {"18": OWNER, "19": "PM", "20": "BA", "21": "BE", "22": "FE", "23": "QA"}}
        service.store.begin_automation.return_value = ({"state": "READY"}, False)
        issued = time.time()
        command = {"issued_at": issued, "request_key": "daily:" + daily_brief.day(issued)}
        self.assertEqual(daily_brief.collect(service, command), {"state": "READY"})
        service.store.begin_automation.assert_called_once_with(command, project=5, targets=5)


class NativeFixture:
    def __init__(self, base, credential, project):
        self.role = credential

    def identity(self, actor):
        return {"user_id": actor, "project_id": 5, "role": self.role, "capabilities": [OWNER] if self.role == OWNER else []}

    def package(self, identifier):
        return {"id": identifier, "lockVersion": 1, "subject": "Offline test resource", "_links": {}}


class OwnerApprovalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.store = Store(self.root)
        self.tokens = {actor: self.store.issue_token(actor, role, role) for actor, role in
                       ((18, OWNER), (19, "PM"), (20, "BA"), (21, "BE"), (22, "FE"), (23, "QA"))}
        self.service = Service(self.store, {"users": {"18": OWNER, "19": "PM", "20": "BA", "21": "BE", "22": "FE", "23": "QA"},
            "project_id": 5, "gateway_mode": "native", "openproject_url": "http://127.0.0.1:8088"}, self.root / "workspaces", NativeFixture)
        self.writes = []

    def test_owner_rag_scope_keeps_native_visibility_version_and_actor_roles(self):
        from unittest.mock import patch
        from gateway.knowledge_classifier import KnowledgeDocType, classify_document
        from gateway.knowledge_storage import KnowledgeStorage, KnowledgeStorageConfig
        from gateway.knowledge_ingestion import KnowledgeIngester
        from test_rag_recovery import VectorFixture
        storage = KnowledgeStorage(KnowledgeStorageConfig(db_path=str(self.root / 'knowledge.sqlite')))
        vector = VectorFixture()
        ingester = KnowledgeIngester(storage, vector)
        for native_id, version, source, metadata in (
                (370, 1, 'op:wp:370', {}), (371, 1, 'actor:20:wp:371', {'actor_id': 20}),
                (372, 1, 'actor:20:wp:372', {'actor_id': 20}),
                (373, 0, 'op:wp:373', {}), (374, 1, 'test:wp:374', {})):
            ingester.ingest(classify_document(KnowledgeDocType.WORK_PACKAGE, '5', source, 'Owner authorization fixture',
                'Owner authorization acceptance requirements.', allowed_roles=['BA'],
                metadata={**metadata, 'native_id': native_id, 'lock_version': version}))
        vector.hits = [{'payload': p['payload'], 'score': .9} for p in vector.points.values()]
        native = Mock()
        native.packages.return_value = [{'id': i, 'lockVersion': 1} for i in (370, 371, 373, 374)]
        native.package.side_effect = lambda i: {'id': i, 'lockVersion': 1}
        with patch('gateway.vector_client.VectorClient', return_value=vector):
            result = self.service.knowledge({'user_id': 18, 'role': OWNER}, native, 'knowledge_search', {'query': 'authorization'})
            self.assertEqual({h['native_id'] for h in result['items']}, {370, 371})
            ordinary = self.service.knowledge({'user_id': 19, 'role': 'PM'}, native, 'knowledge_search', {'query': 'authorization'})
            self.assertEqual(ordinary['items'], [])

    def test_owner_dense_filter_requires_trusted_document_ids(self):
        from gateway.vector_client import VectorClient
        vector = object.__new__(VectorClient)
        vector.enabled = True
        vector.qdrant_url = 'http://fixture.invalid'
        vector.collection_name = 'fixture'
        vector._http = Mock()
        vector._http.post.return_value.status_code = 200
        vector._http.post.return_value.json.return_value = {'result': []}
        with self.assertRaises(PermissionError):
            vector.search_dense([.1] * 1024, '5', OWNER)
        vector._http.post.assert_not_called()
        vector.search_dense([.1] * 1024, '5', OWNER, document_ids=['a' * 64])
        filters = vector._http.post.call_args.kwargs['json']['filter']['must']
        self.assertEqual({f['key'] for f in filters}, {'project_id', 'document_id'})

    def propose(self, actor):
        return self.service.execute(self.tokens[actor], {"action": "update_work_package",
            "arguments": {"id": 370, "lock_version": 1, "changes": {"subject": "Offline proposed change"}},
            "idempotency_key": "owner-regression-" + str(actor)})["result"]

    def test_owner_own_exact_approval_once_and_pm_behavior_preserved(self):
        for actor in (18, 19):
            proposal = self.propose(actor)
            self.assertEqual(proposal["state"], "pending")
            self.assertEqual(proposal["command"]["auto_execute"], False)
            self.service.perform = lambda who, native, action, args, key: self.writes.append(who["user_id"]) or {"id": 370, "lockVersion": 2}
            with self.assertRaises(ValueError):
                self.service.confirm(actor, proposal["id"], "0" * 64)
            self.service.confirm(actor, proposal["id"], proposal["hash"])
            with self.assertRaises(ValueError):
                self.service.confirm(actor, proposal["id"], proposal["hash"])
        self.assertEqual(self.writes, [18, 19])

    def test_owner_oversight_is_read_only_audited_and_does_not_impersonate_pm(self):
        proposal = self.propose(19)
        with self.assertRaises((PermissionError, ValueError)):
            self.service.execute(self.tokens[18], {"action": "get_proposal", "arguments": {"id": proposal["id"]}})
        result = self.service.execute(self.tokens[18], {"action": "owner_inspect",
            "arguments": {"kind": "proposal", "subject_actor": 19, "id": proposal["id"]}})["result"]
        self.assertEqual(result["viewer_actor"], 18)
        self.assertEqual(result["subject_actor"], 19)
        self.assertFalse(result["can_execute_as_subject"])
        self.assertEqual(result["data"]["hash"], proposal["hash"])
        with self.assertRaises((PermissionError, ValueError)):
            self.service.confirm(18, proposal["id"], proposal["hash"])
        self.assertEqual(self.store.proposal(19, proposal["id"])["state"], "pending")
        with self.store.connect() as db:
            self.assertTrue(db.execute("SELECT count(*) FROM audit WHERE actor=18 AND action='owner_oversight'").fetchone()[0])

    def test_nonowners_cannot_forge_owner_or_inspect_another_actor(self):
        for actor in (19, 20, 21, 22, 23):
            with self.assertRaises(PermissionError):
                self.service.execute(self.tokens[actor], {"action": "owner_inspect", "arguments": {"kind": "history", "subject_actor": 18}})
        for actor in (20, 21, 22, 23):
            with self.assertRaises(PermissionError):
                self.service.confirm(actor, "not-a-proposal", "0" * 64)


if __name__ == "__main__":
    unittest.main()
