"""Offline report-reader template contract; no browser or live service."""
from pathlib import Path
import re
import unittest


class EngineeringReportTemplateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = (Path(__file__).parents[1] / 'core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb').read_text(encoding='utf-8')

    def test_report_json_cannot_close_its_script_element(self):
        block = re.search(r'<script type="application/json" id="rep-narrative-.*?</script>', self.template, re.S).group()
        self.assertIn('json_escape(', block)

    def test_report_cards_use_recorded_metrics_or_explicit_missing_data(self):
        block = self.template.split('<div class="qcc-report-metrics">', 1)[1].split('</div>\n                  <% if', 1)[0]
        self.assertNotRegex(block, r'\|\| (?:5|12)\b')
        self.assertIn("rep.dig('metrics', 'github', 'total_prs')", block)
        self.assertIn('Chưa có dữ liệu', block)

    def test_reader_uses_authenticated_sanitized_document_and_raw_mode(self):
        reader = (Path(__file__).parents[1] / 'core/overlay/app/views/qldapm_ai/_engineering_report_reader.html.erb').read_text(encoding='utf-8')
        self.assertIn('qccReportReader.handleClick(e)', self.template)
        self.assertIn("reader.rendering !== 'COMMONMARK_SANITIZED'", reader)
        self.assertIn("node('qcc-report-raw').textContent = reader.raw_markdown", reader)
        self.assertIn('encodeURIComponent(id)', reader)

    def test_mission_and_run_cards_do_not_invent_acceptance_or_native_versions(self):
        for claim in ['21/21 passed (100%)', 'Task #384 delivered · PR #5 OPEN',
                      '341 Work Packages bất biến 100%', 'Local AI Review: <strong>PASSED</strong>']:
            self.assertFalse(claim in self.template, claim)
        self.assertFalse("parent['lock_version'] || 4" in self.template)


if __name__ == '__main__':
    unittest.main()
