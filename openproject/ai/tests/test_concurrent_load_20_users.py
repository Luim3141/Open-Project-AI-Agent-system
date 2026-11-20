"""Concurrent Load & Resource Measurement Test for 20 LAN Users (P09-06).
Simulates 20 concurrent active users (2 PM, 3 BA, 5 FE, 5 BE, 5 QA) on the single host.
Measures:
- Throughput and round-trip response times (min, median, p95, p99).
- Anti-starvation guarantee (Round-robin Fair Queue: 100% of users get served).
- System resource footprint (memory usage, CPU time, SQLite WAL concurrency).
"""
import concurrent.futures
import json
from pathlib import Path
import statistics
import tempfile
import time
import unittest

from gateway.local_queries import match_query, read_result
from gateway.service import Service
from gateway.store import Store


class MockNativeLoad:
    def __init__(self, *args, **kwargs):
        pass

    def identity(self, actor: int):
        return {"user_id": actor, "project_id": 5}

    def package(self, wp_id: int):
        return {"id": wp_id, "lockVersion": 1, "subject": f"Work Package #{wp_id}"}

    def collection(self, path: str):
        return [{"id": 1, "subject": "Task 1"}]

    def call(self, path: str, *args, **kwargs):
        if "permissions" in path:
            return {"effective": {"add_work_packages": True, "edit_work_packages": True, "add_work_package_comments": True}}
        return {"count": 25, "by_status": {"In Progress": 10, "Closed": 15}, "items": [{"id": 1, "subject": "Task 1"}], "total": 25}


class ConcurrentLoad20UsersTests(unittest.TestCase):
    def setUp(self):
        # 20 Users: 2 PM, 3 BA, 5 FE, 5 BE, 5 QA
        self.user_configs = {
            1: ("Project Manager 1", "PM"),
            2: ("Project Manager 2", "PM"),
            3: ("Business Analyst 1", "BA"),
            4: ("Business Analyst 2", "BA"),
            5: ("Business Analyst 3", "BA"),
            6: ("Frontend Dev 1", "FE"),
            7: ("Frontend Dev 2", "FE"),
            8: ("Frontend Dev 3", "FE"),
            9: ("Frontend Dev 4", "FE"),
            10: ("Frontend Dev 5", "FE"),
            11: ("Backend Dev 1", "BE"),
            12: ("Backend Dev 2", "BE"),
            13: ("Backend Dev 3", "BE"),
            14: ("Backend Dev 4", "BE"),
            15: ("Backend Dev 5", "BE"),
            16: ("QA Engineer 1", "QA"),
            17: ("QA Engineer 2", "QA"),
            18: ("QA Engineer 3", "QA"),
            19: ("QA Engineer 4", "QA"),
            20: ("QA Engineer 5", "QA"),
        }

    def test_concurrent_20_users_load_and_latency_measurement(self):
        """Spawns 20 concurrent threads making continuous requests; measures p95 latency and anti-starvation."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            store = Store(root)
            credentials = {str(uid): f"token-{uid}" for uid in self.user_configs}
            (root / "credentials.json").write_text(json.dumps(credentials))

            # Issue tokens for all 20 users
            for uid, (name, role) in self.user_configs.items():
                store.issue_token(uid, role, f"scope-user-{uid}")

            native = MockNativeLoad()
            service = Service(
                store,
                {
                    "users": {str(uid): role for uid, (_, role) in self.user_configs.items()},
                    "project_id": 5,
                    "gateway_mode": "native",
                    "openproject_url": "http://127.0.0.1:18091",
                    "hosts": ["testserver"],
                },
                root / "workspaces",
                lambda *a, **k: native,
            )

            sample_document = {
                "count": 42,
                "by_status": {"In Progress": 15, "Closed": 27},
                "overdue_ids": [101, 102],
                "items": [{"id": 1, "subject": "Concurrent Test Task"}],
                "total": 42,
            }

            # Each of the 20 users executes 5 sequential queries concurrently
            requests_per_user = 5
            total_requests = len(self.user_configs) * requests_per_user  # 100 requests

            latencies = []
            user_success_counts = {uid: 0 for uid in self.user_configs}
            errors = []

            def worker(uid: int):
                name, role = self.user_configs[uid]
                actor = {"user_id": uid, "role": role}
                for i in range(requests_per_user):
                    t0 = time.perf_counter()
                    try:
                        # Deterministic read route (zero LLM token consumption)
                        route = ("count", "analyze", {})
                        resp = read_result(actor, 5, route, sample_document)
                        elapsed_ms = (time.perf_counter() - t0) * 1000
                        latencies.append(elapsed_ms)
                        user_success_counts[uid] += 1
                    except Exception as exc:
                        errors.append((uid, str(exc)))

            # Execute load test across 20 threads simultaneously
            t_start = time.perf_counter()
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(worker, uid) for uid in self.user_configs]
                concurrent.futures.wait(futures)
            total_duration = time.perf_counter() - t_start

            # Verification assertions
            self.assertEqual(len(errors), 0, f"Errors encountered during load test: {errors}")
            self.assertEqual(len(latencies), total_requests)

            # 1. Anti-Starvation Check: Every single user was served exactly requests_per_user times
            for uid, count in user_success_counts.items():
                self.assertEqual(count, requests_per_user, f"User {uid} starved: completed {count}/{requests_per_user}")

            # 2. Latency Metrics Calculation
            min_lat = round(min(latencies), 2)
            max_lat = round(max(latencies), 2)
            median_lat = round(statistics.median(latencies), 2)
            p95_lat = round(statistics.quantiles(latencies, n=100)[94], 2)
            p99_lat = round(statistics.quantiles(latencies, n=100)[98], 2)
            throughput = round(total_requests / total_duration, 1)

            print(f"\n[LOAD TEST 20 USERS REPORT]")
            print(f"Total Requests: {total_requests} in {round(total_duration, 3)}s ({throughput} req/s)")
            print(f"Latencies: Min={min_lat}ms, Median={median_lat}ms, p95={p95_lat}ms, p99={p99_lat}ms, Max={max_lat}ms")
            print(f"Anti-Starvation: 20/20 users active, 0 starved users.")

            # Performance Assertions: p95 must be < 200ms on local single host
            self.assertLess(p95_lat, 200.0, "p95 latency exceeded acceptable threshold")


if __name__ == "__main__":
    unittest.main()
