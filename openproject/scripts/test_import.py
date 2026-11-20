import unittest
from import_wbs import API, NoRedirect, description, source_index


class ImportChecks(unittest.TestCase):
    def test_duplicate_rejected(self):
        with self.assertRaises(RuntimeError):
            source_index([{"customField1": "A"}, {"customField1": "A"}], "customField1")

    def test_non_api_path_rejected(self):
        with self.assertRaises(ValueError):
            API("not-a-real-token").call("https://example.com/collect")

    def test_redirect_never_forwards_token(self):
        with self.assertRaises(RuntimeError):
            NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://example.com")

    def test_description_preserves_source(self):
        keys = ["Description", "Acceptance Criteria", "Checklist", "Source ID", "Reviewer Requirement", "Proposed Role",
                "Proposed Sprint", "Simulation Estimate Hours", "Simulation Points", "Depends On Source IDs",
                "Integration With Source IDs", "Labels", "Approval", "Proposed Priority"]
        row = dict.fromkeys(keys, "nội dung nguồn")
        result = description(row)
        self.assertIn(row["Acceptance Criteria"], result)
        self.assertIn("- [ ] nội dung nguồn", result)
        self.assertIn("MÔ PHỎNG", result)


if __name__ == "__main__":
    unittest.main()
