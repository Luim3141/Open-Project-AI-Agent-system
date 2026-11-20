"""Custom field definition pagination; mock only, no Jira mutations."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import jira_admin_mcp as admin


def field(number, name="QAG3 Change reason"):
    return {"id": f"customfield_{number}", "name": name, "schema": {"type": "string"}}


class GateFieldTests(unittest.TestCase):
    def run_pages(self, pages):
        with patch.object(admin, "preflight", return_value={}), patch.object(
                admin, "request", side_effect=pages) as request:
            result = admin.inspect_gate_fields()
            for call in request.call_args_list:
                self.assertEqual(call.args, ("GET", "/field/search"))
                self.assertEqual(call.kwargs["params"]["query"], "QAG3")
            return result

    def test_all_pages_and_prefix_only(self):
        result = self.run_pages([
            {"startAt": 0, "total": 2, "isLast": False, "values": [field(1)]},
            {"startAt": 1, "total": 2, "isLast": True, "values": [field(2, "Other field")]},
        ])
        self.assertTrue(result["readComplete"])
        self.assertEqual(result["fields"], [field(1)])
        self.assertEqual(result["matchedCatalogCount"], 2)

    def test_empty_complete_not_unknown(self):
        self.assertEqual(self.run_pages([
            {"startAt": 0, "total": 0, "isLast": True, "values": []}
        ])["fields"], [])

    def test_changed_total_not_complete(self):
        with self.assertRaisesRegex(ValueError, "CHANGED_DURING_READ"):
            self.run_pages([
                {"startAt": 0, "total": 2, "isLast": False, "values": [field(1)]},
                {"startAt": 1, "total": 3, "isLast": True, "values": [field(2), field(3)]},
            ])

    def test_invalid_pages_fail_closed(self):
        for page in [
            {"startAt": 0, "total": 1, "values": [field(1)]},
            {"startAt": 0, "total": 2, "isLast": True, "values": [field(1)]},
            {"startAt": 0, "total": 1, "isLast": False, "values": []},
            {"startAt": 0, "total": 2, "isLast": True, "values": [field(1), field(1)]},
            {"startAt": 0, "total": 1, "isLast": True, "values": [{"id": "bad"}]},
        ]:
            with self.subTest(page=page), self.assertRaises(ValueError): self.run_pages([page])


if __name__ == "__main__": unittest.main()
