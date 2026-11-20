"""Operator producer orchestration, with isolated fixtures and no Docker or Main calls."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from automation import wbs_application_qualification as producer
from tests import test_application_qa_proof as proof_fixtures


class ApplicationQualificationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        runtime = self.root / 'runtime'
        (runtime / 'gateway').mkdir(parents=True)
        (runtime / 'gateway/config.json').write_text(json.dumps({'project_id': 5, 'gateway_mode': 'native'}))
        (runtime / 'gateway/credentials.json').write_text(json.dumps({'18': 'synthetic-owner-credential'}))
        (runtime / 'gateway/ui.key').write_bytes(b'synthetic-proof-key-not-a-runtime-key')
        fixture = proof_fixtures.ApplicationQaProofTests('test_exact_current_source_and_build_proof_is_not_a_human_review')
        fixture.setUp()
        self.item, self.hashes = fixture.item, fixture.sources
        self.records = [{'id': 'test_native_wbs_analysis.NativeWbsAnalysisTests.case_' + str(i), 'outcome': 'PASSED'} for i in range(13)]
        self.records += [{'id': 'test_wbs_scheduled_parent_effects.ScheduledParentEffectsTests.' + name, 'outcome': 'PASSED'} for name in [
            'test_exact_native_two_save_first_child_and_later_child_chain',
            'test_business_edit_unknown_child_extra_version_and_bad_calendar_are_not_parent_effects',
            'test_expanded_parent_changes_do_not_change_the_verified_work_package']]
        self.native_result = {'status': 'PASS_RETAINED_BA_TO_ISOLATED_NATIVE_WBS_RELATION_SCHEDULE_RAG_RECOVERY',
            'native_readback': {k: {} for k in ['epic', 'task-a', 'sub-a', 'task-b']},
            'raw_ba_output_unchanged': True, 'lost_node_response_reconciled_one_create': True}
        self.manifest = {'containers': {
            'qldapm-ai-gateway-1': {'image': 'sha256:' + '3' * 64},
            'qldapm-openproject-web-1': {'image': 'sha256:' + '4' * 64}}}
        self.patches = [patch.object(producer, 'RUNTIME', runtime), patch.object(producer, 'private_path', side_effect=Path),
            patch.object(producer, 'capture', return_value=self.manifest), patch.object(producer, 'work_state', return_value={'active': 0}),
            patch.object(producer, 'owner_source', side_effect=lambda *a: {'identity': {'user_id': 18, 'role': 'AI_SYSTEM_OWNER'}, 'item': copy.deepcopy(self.item)}), patch.object(producer, 'sources', return_value=self.hashes),
            patch.object(producer, 'verify'), patch.object(producer, 'units', side_effect=lambda *a: {'run': 16, 'records': self.records})]
        for context in self.patches:
            context.start()
            self.addCleanup(context.stop)

    def test_failed_regression_never_runs_native_clone_or_writes_pass_proof(self):
        self.records[0]['outcome'] = 'FAILED'
        output = self.root / 'failed'
        with patch.object(producer, 'native_wbs') as native:
            with self.assertRaisesRegex(RuntimeError, 'REGRESSION_FAILED_NO_PASS'):
                producer.qualify(output)
            native.assert_not_called()
        self.assertFalse((output / 'proof.json').exists())
        self.assertTrue((output / 'blocked.json').exists())

    def test_source_drift_prevents_signing_after_successful_isolated_tests(self):
        output = self.root / 'changed'
        def changed(*args):
            self.item['lockVersion'] += 1
            return self.native_result
        with patch.object(producer, 'native_wbs', side_effect=changed):
            with self.assertRaisesRegex(RuntimeError, 'SOURCE_BUILD_OR_KEY_CHANGED'):
                producer.qualify(output)
        self.assertFalse((output / 'proof.json').exists())

    def test_success_is_only_a_private_signed_artifact_without_import_or_review(self):
        output = self.root / 'passed'
        with patch.object(producer, 'native_wbs', return_value=self.native_result):
            result = producer.qualify(output)
        self.assertEqual(result['status'], 'QUALIFIED_PRIVATE_ARTIFACT_NOT_IMPORTED_OR_HUMAN_REVIEWED')
        self.assertEqual(result['main_native_writes'], 0)
        bundle = json.loads((output / 'proof.json').read_text())
        body = producer.validate(bundle, b'synthetic-proof-key-not-a-runtime-key', self.item, self.hashes)
        self.assertEqual(body['verdict'], 'PASSED')
        self.assertNotIn('approved', body)


if __name__ == '__main__':
    unittest.main()
