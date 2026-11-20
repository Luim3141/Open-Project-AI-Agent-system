import json
import unittest
from pydantic import ValidationError

from gateway.agent_models import AgentTask, AgentRun, AgentResult, MAX_AGENT_BYTES


TASK = "00000000-0000-4000-8000-000000000001"
RUN = "00000000-0000-4000-8000-000000000002"
TRACE = "00000000-0000-4000-8000-000000000003"
SCOPE = dict(run_id=RUN, task_id=TASK, actor_id=7, project_id=1, trace_id=TRACE)


class AgentModelTests(unittest.TestCase):
    def task(self, **changes):
        return dict(task_id=TASK, actor_id=7, project_id=1, conversation_id=TRACE,
                    agent="ba", instruction="Đọc công việc và chỉ ra AC còn thiếu",
                    references=[dict(work_package_id=42, lock_version=3)],
                    created_at=100.0, expires_at=200.0, **changes)

    def test_all_contracts_roundtrip_version_and_json_schema(self):
        task = AgentTask(**self.task())
        result = AgentResult(**SCOPE, state="COMPLETED", summary="Đã đọc dữ liệu native", receipt_ids=[TASK])
        run = AgentRun(**SCOPE, state="COMPLETED", created_at=100.0, updated_at=101.0, result=result)
        for document in (task, result, run):
            with self.subTest(contract=type(document).__name__):
                self.assertEqual(type(document).from_json(document.model_dump_json()), document)
                schema = type(document).model_json_schema()
                self.assertFalse(schema["additionalProperties"])
                self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
                self.assertEqual(schema["x-max-serialized-bytes"], MAX_AGENT_BYTES)

    def test_rejects_versions_coercion_unknown_authority_and_bad_ids(self):
        for change in ({"schema_version": 2}, {"schema_version": True}, {"schema_version": "1"},
                       {"actor_id": True}, {"actor_id": "7"}, {"project_id": 0},
                       {"task_id": "../../state/gemini.key"}, {"instruction": "   "},
                       {"agent": "shell"}, {"role": "PM"}, {"confirmed": True},
                       {"allow_routine_writes": True}, {"api_key": "synthetic-forbidden"},
                       {"references": [{"work_package_id": 42, "lock_version": 3, "command": "execute"}]}):
            with self.subTest(change=change), self.assertRaises(ValidationError):
                AgentTask(**{**self.task(), **change})

    def test_invalid_json_and_raw_byte_bound(self):
        for invalid in ("{", "[]", "null", '{"schema_version": NaN}', 42):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                AgentTask.from_json(invalid)
        with self.assertRaisesRegex(ValueError, "AGENT_PAYLOAD_TOO_LARGE"):
            AgentTask.from_json(" " * (MAX_AGENT_BYTES + 1))

    def test_both_character_and_utf8_document_bounds(self):
        for changes in ({"instruction": "x" * 8001}, {"references": [{"work_package_id": 1, "lock_version": 0}] * 51}):
            with self.assertRaises(ValidationError):
                AgentTask(**{**self.task(), **changes})
        with self.assertRaisesRegex(ValueError, "AGENT_PAYLOAD_TOO_LARGE"):
            AgentResult(**SCOPE, state="FAILED", summary="😀" * 9000)
        self.assertEqual(AgentTask.from_json(json.dumps(self.task(), ensure_ascii=False)).actor_id, 7)

    def test_expiry_finite_time_and_nested_result_scope(self):
        for change in ({"expires_at": 100.0}, {"expires_at": float("inf")}, {"created_at": -1.0}):
            with self.assertRaises(ValidationError):
                AgentTask(**{**self.task(), **change})
        result = AgentResult(**SCOPE, state="COMPLETED", summary="Native receipt")
        with self.assertRaisesRegex(ValueError, "TERMINAL_RESULT_REQUIRED"):
            AgentRun(**SCOPE, state="COMPLETED", created_at=100.0, updated_at=101.0)
        for change in ({"actor_id": 8}, {"project_id": 2}, {"trace_id": TASK}, {"state": "RUNNING"}, {"updated_at": 99.0}):
            with self.subTest(change=change), self.assertRaises(ValidationError):
                AgentRun(**{**SCOPE, "state": "COMPLETED", "created_at": 100.0, "updated_at": 101.0, "result": result, **change})


if __name__ == "__main__":
    unittest.main()
