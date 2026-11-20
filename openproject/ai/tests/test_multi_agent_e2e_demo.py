"""End-to-End Multi-Agent Demonstration Tests (P05-11).
Flow:
1. Sprint Analysis with BA, QA, PM specialist agents
2. Reviewer Agent cross-verification & consistency audit
3. Proposal aggregation for schedule adjustment
4. Verification that NO mutation occurs without PM consent
5. Explicit PM approval with preview hash -> mutation applied & readback verified
"""
import copy
import tempfile
import unittest
from pathlib import Path

from gateway.e2e_demo import run_multi_agent_sprint_demo
from gateway.store import Store


class MultiAgentE2EDemoTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.store = Store(self.root)

        # Realistic sprint data fixture
        self.packages = {
            801: {
                "id": 801,
                "lockVersion": 2,
                "subject": "Xây dựng màn hình đăng ký thành viên",
                "description": {"raw": "Cần làm nhanh và giao diện đẹp để thu hút người dùng."},
                "dueDate": "2026-10-14",  # Overdue
                "_links": {
                    "type": {"title": "User Story"},
                    "status": {"href": "/api/v3/statuses/1", "title": "In Progress"},
                    "assignee": {"href": "/api/v3/users/9", "title": "FE Developer"},
                },
            },
            802: {
                "id": 802,
                "lockVersion": 3,
                "subject": "Lỗi 500 khi lưu phiên làm việc người dùng",
                "description": {"raw": "Server sập khi có 100 request đồng thời."},
                "dueDate": "2026-10-18",
                "_links": {
                    "type": {"title": "Bug"},
                    "status": {"href": "/api/v3/statuses/1", "title": "In Progress"},
                    "assignee": {"href": "/api/v3/users/8", "title": "BE Developer"},
                },
            },
        }

        packages = self.packages
        class MockNative:
            def __init__(self, url, token, project):
                self.project_id = project
            def package(self, identifier):
                if identifier not in packages:
                    raise ValueError("NOT_FOUND")
                return copy.deepcopy(packages[identifier])
            def packages(self):
                return [copy.deepcopy(p) for p in packages.values()]
            def call(self, path, method="GET", payload=None):
                if method == "PATCH":
                    pid = int(path.rsplit("/", 1)[1])
                    pkg = packages[pid]
                    if payload.get("lockVersion") != pkg["lockVersion"]:
                        raise ValueError("LOCK_VERSION_MISMATCH")
                    pkg["lockVersion"] += 1
                    if "dueDate" in payload:
                        pkg["dueDate"] = payload["dueDate"]
                    return copy.deepcopy(pkg)
                return {}

        self.native = MockNative("http://mock", "tok", 3)

    def tearDown(self):
        self.temporary.cleanup()

    def test_legacy_cross_actor_demo_cannot_bypass_authenticated_gateway(self):
        before=copy.deepcopy(self.packages)
        with self.assertRaisesRegex(PermissionError,'AUTHENTICATED_SUPERVISOR'):
            run_multi_agent_sprint_demo(self.packages,self.store,self.native)
        self.assertEqual(self.packages,before)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM proposals').fetchone()[0],0)

    def test_repeated_legacy_demo_never_creates_write_or_approval_callback(self):
        for _ in range(2):
            with self.assertRaises(PermissionError):
                run_multi_agent_sprint_demo(self.packages,self.store,self.native)
        self.assertEqual(self.packages[801]['lockVersion'],2)

if __name__=='__main__':unittest.main()
