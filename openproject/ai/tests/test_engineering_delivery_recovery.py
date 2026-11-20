"""Full delivery journal + real temporary Gateway Store; all external leaves are fixtures.

No WSL, git executable, GitHub, Native HTTP or provider is called. Synthetic review,
QA and diff receipts exercise control flow; they are not live OpenClaw evidence.
"""
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from automation import engineering_worker as worker
from gateway import engineering, engineering_lifecycle as lifecycle
from gateway.store import Store


class NativeFixture:
    def call(self, path):
        if path != '/api/v3/projects/6':
            raise AssertionError(path)
        return {'identifier': 'ai-dev-demo', 'active': True}

    def package(self, identifier):
        return {'id': identifier, 'lockVersion': 0, 'subject': 'Fixture task',
                'description': {'raw': 'Synthetic delivery acceptance'}}


class DeliveryRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(Path(self.tmp.name)/'store')
        self.native = NativeFixture()
        self.service = SimpleNamespace(store=self.store,
            config={'project_id': 6, 'engineering': {'enabled': True}},
            native_actor=lambda actor: (self.native, {'user_id': actor, 'role': 'PM'}))
        run_id = engineering.admit(self.service, 20,
            {'native_id': 379, 'lock_version': 0, 'unit': engineering.UNIT}, 'delivery-fixture')['id']
        self.claim = engineering.claim(self.service, 20)
        self.assertEqual(self.claim['id'], run_id)
        self.folder = Path(self.tmp.name)/'artifacts'/run_id
        self.calls = []
        self.diff = b''
        self.head = 'a'*40
        self.reviewer_fails = False
        self.qa_fails = False
        self.pause_on = None
        self.partial_rework_pause = False
        self.unknown_on = None
        stack = ExitStack()
        self.addCleanup(stack.close)
        for name, value in {
            'EVIDENCE': self.folder.parent, 'CURRENT_JOURNAL': None,
            'LINUX': '/fixture', 'BRANCH': 'fixture', 'ACCEPTANCE': 'fixture.py',
            'BASE_BRANCH': 'main', 'operator': self.operator, 'wsl': self.wsl,
            'command': self.command, 'prepare': self.prepare, 'inference': self.inference,
            'test_tree': self.acceptance_fixture, 'publish_commit': self.publish_commit,
            'gate': lambda: self.calls.append(('gate',)),
            'checkpoint': lambda *args: self.calls.append(('host-checkpoint', *args))
        }.items():
            stack.enter_context(patch.object(worker, name, value))

    def operator(self, op, **args):
        self.calls.append((op, args))
        run_id = self.claim['id']
        if op == 'signal':
            return lifecycle.signal(self.store, 20, run_id)
        if op == 'checkpoint':
            return lifecycle.save(self.service, 20, run_id, args['document'])
        if op == 'finish':
            return engineering.finish(self.service, 20, run_id, args['result'])
        if op == 'context':
            return {'plan': {'acceptance': {'AC1': 'fixture acceptance'}}, 'knowledge': []}
        if op == 'publish_native':
            return {'child_id': 380, 'project_id': 6}
        if op == 'knowledge':
            return {'retrieval': {'items': [{'native_id': 380, 'citation': 'fixture-only'}]}}
        if op in {'progress', 'delivery_note'}:
            return {}
        raise AssertionError(op)

    def prepare(self, base):
        self.calls.append(('prepare', base))
        return self.head

    def wsl(self, argv, **kwargs):
        self.calls.append(('wsl', argv))
        if argv == ['/usr/local/bin/openclaw','gateway','stop','--force']:
            output = b''
        elif '--name-only' in argv:
            output = b'task_manager/app.py\n'
        elif 'diff' in argv:
            output = self.diff
        elif 'rev-parse' in argv:
            output = self.head.encode()
        elif 'commit' in argv:
            self.head = 'b'*40
            output = b''
        elif 'add' in argv:
            output = b''
        else:
            raise AssertionError(argv)
        return subprocess.CompletedProcess(argv, 0, output, b'')

    def command(self, argv, **kwargs):
        self.calls.append(('gh', argv))
        if argv[1:3] == ['pr', 'list']:
            value = [{'url': 'https://github.com/Luim3141/mini-task-manager/pull/999'}]
        elif argv[1:3] == ['pr', 'view']:
            value = {'headRefOid': self.head, 'headRefName': worker.BRANCH,
                     'baseRefName': worker.BASE_BRANCH, 'state': 'OPEN',
                     'url': 'https://github.com/Luim3141/mini-task-manager/pull/999'}
        else:
            raise AssertionError(argv)
        return subprocess.CompletedProcess(argv, 0, json.dumps(value).encode(), b'')

    def inference(self, run_id, folder, role, step, message, **kwargs):
        self.calls.append(('inference', role, step))
        if step == self.unknown_on:
            worker.CURRENT_JOURNAL.session_id = 'fixture-unknown-session'
            worker.CURRENT_JOURNAL.terminal_known = False
            raise RuntimeError('OPENCLAW_OUTCOME_UNKNOWN')
        if step == self.pause_on:
            self.pause_on = None
            if self.partial_rework_pause:
                self.diff += b'+known fenced partial rework\n'
            raise RuntimeError('ENGINEERING_PAUSED_CHECKPOINT_REQUIRED')
        if role == 'dev':
            self.diff = ('diff --git a/task_manager/app.py b/task_manager/app.py\n+'+step+'\n').encode()
            value = {'fixture': step}
        elif role == 'reviewer':
            failed = self.reviewer_fails and step == 'review-0'
            value = {'verdict': 'FAIL' if failed else 'PASS',
                     'revision': hashlib.sha256(self.diff).hexdigest(),
                     'findings': [{'file': 'task_manager/app.py', 'line': 1,
                                   'reason': 'synthetic missing behavior'}] if failed else []}
        else:
            failed = self.qa_fails and step == 'qa-0'
            value = {'status': 'FAIL' if failed else 'PASS', 'exit_code': 1 if failed else 0,
                     'command': 'fixture acceptance', 'failures': ['synthetic failure'] if failed else []}
        return {'result': {'payloads': [{'text': json.dumps(value)}]}}

    def acceptance_fixture(self, folder, name):
        self.calls.append(('acceptance', name))
        (folder/(name+'.log')).write_text('Synthetic acceptance: PASS', encoding='utf-8')
        return {'exit_code': 0, 'command': 'fixture acceptance', 'artifact': name+'.log'}

    def publish_commit(self, head, folder):
        self.calls.append(('publish', head))

    def journal(self):
        return json.loads((self.folder/'delivery-steps.json').read_text(encoding='utf-8'))

    def resume(self):
        saved = lifecycle.load(self.store, self.claim['id'])
        lifecycle.resume(self.service, 20, self.claim['id'], saved['version'])
        self.claim = engineering.claim(self.service, 20)
        return worker.execute(self.claim)

    def assert_success(self, result):
        self.assertEqual(result['status'], 'succeeded', result)
        self.assertIsNone(worker.CURRENT_JOURNAL)
        self.assertEqual(result['head_sha'], 'b'*40)
        self.assertEqual(self.store.run(20, self.claim['id'])['result']['status'], 'succeeded')
        self.assertEqual(self.journal()['steps']['knowledge']['state'], 'done')

    def test_reviewer_failure_reworks_then_rechecks_new_revision_before_publication(self):
        self.reviewer_fails = True
        result = worker.execute(self.claim)
        self.assert_success(result)
        stages = [c[2] for c in self.calls if c[0] == 'inference']
        self.assertEqual(stages, ['dev-0', 'review-0', 'rework-0', 'review-1', 'qa-1'])
        self.assertEqual(result['review_evidence']['revision'], hashlib.sha256(self.diff).hexdigest())
        self.assertIn('synthetic missing behavior', self.journal()['steps']['review-0']['value']['result']['payloads'][0]['text'])

    def test_qa_failure_reworks_and_runs_independent_review_and_qa_again(self):
        self.qa_fails = True
        result = worker.execute(self.claim)
        self.assert_success(result)
        self.assertEqual([c[2] for c in self.calls if c[0] == 'inference'],
                         ['dev-0', 'review-0', 'qa-0', 'rework-0', 'review-1', 'qa-1'])
        self.assertEqual([c[1] for c in self.calls if c[0] == 'acceptance'], ['acceptance-0', 'acceptance-1'])

    def test_unknown_provider_outcome_saves_checkpoint_and_gateway_denies_replay(self):
        self.unknown_on = 'review-0'
        result = worker.execute(self.claim)
        self.assertEqual(result['error'], 'OPENCLAW_OUTCOME_UNKNOWN')
        saved = lifecycle.load(self.store, self.claim['id'])
        self.assertFalse(saved['terminal_known'])
        self.assertFalse(saved['resumable'])
        self.assertEqual(saved['session_id'], 'fixture-unknown-session')
        self.assertEqual(self.journal()['steps']['review-0']['state'], 'started')
        before = list(self.calls)
        with self.assertRaisesRegex(ValueError, 'ENGINEERING_RECONCILIATION_REQUIRED'):
            lifecycle.resume(self.service, 20, self.claim['id'], saved['version'])
        self.assertIsNone(engineering.claim(self.service, 20))
        self.assertEqual(self.calls, before)
        self.assertFalse(any(c[0] in {'publish', 'publish_native', 'gh'} for c in self.calls))

    def test_resume_keeps_completed_context_prepare_and_dev_artifacts(self):
        self.pause_on = 'review-0'
        self.assertEqual(worker.execute(self.claim)['status'], 'paused')
        before = self.journal()['steps']['dev-0']
        self.assert_success(self.resume())
        self.assertEqual(self.journal()['steps']['dev-0'], before)
        self.assertEqual(len([c for c in self.calls if c[0] == 'context']), 1)
        self.assertEqual(len([c for c in self.calls if c[:3] == ('inference', 'dev', 'dev-0')]), 1)
        self.assertEqual(len([c for c in self.calls if c[0] == 'prepare']), 2)

    def test_resume_after_rework_preserves_done_stages_and_reviews_current_revision(self):
        self.reviewer_fails = True
        self.pause_on = 'qa-1'
        self.assertEqual(worker.execute(self.claim)['status'], 'paused')
        completed = {k: v for k, v in self.journal()['steps'].items() if v['state'] == 'done'}
        self.assert_success(self.resume())
        for name, receipt in completed.items():
            self.assertEqual(self.journal()['steps'][name], receipt)
        self.assertEqual(len([c for c in self.calls if c[:3] == ('inference', 'dev', 'rework-0')]), 1)

    def test_known_partial_rework_resumes_same_step_before_new_review(self):
        self.reviewer_fails = True
        self.pause_on = 'rework-0'
        self.partial_rework_pause = True
        self.assertEqual(worker.execute(self.claim)['status'], 'paused')
        saved = lifecycle.load(self.store, self.claim['id'])
        self.assertTrue(saved['terminal_known'])
        self.assertTrue(saved['resumable'])
        self.assertEqual(self.journal()['steps']['rework-0']['state'], 'started')
        self.assertEqual(saved['revision'], hashlib.sha256(self.diff).hexdigest())
        failed_review = self.journal()['steps']['review-0']
        original_candidate = (self.folder/'candidate-0.diff').read_bytes()
        self.assertNotEqual(hashlib.sha256(original_candidate).hexdigest(), saved['revision'])
        self.assert_success(self.resume())
        self.assertEqual(self.journal()['steps']['review-0'], failed_review)
        self.assertEqual((self.folder/'candidate-0.diff').read_bytes(), original_candidate)
        self.assertEqual([c[2] for c in self.calls if c[0] == 'inference'],
                         ['dev-0', 'review-0', 'rework-0', 'rework-0', 'review-1', 'qa-1'])

    def test_changed_tree_after_pause_blocks_before_provider_or_publication(self):
        self.pause_on = 'review-0'
        self.assertEqual(worker.execute(self.claim)['status'], 'paused')
        before = [c for c in self.calls if c[0] == 'inference']
        self.diff += b'+external edit\n'
        result = self.resume()
        self.assertEqual(result['error'], 'ENGINEERING_CHECKPOINT_TREE_CHANGED')
        self.assertEqual([c for c in self.calls if c[0] == 'inference'], before)
        self.assertFalse(lifecycle.load(self.store, self.claim['id'])['resumable'])
        self.assertFalse(any(c[0] in {'publish', 'publish_native', 'gh'} for c in self.calls))

    def test_resume_prepare_timeout_is_fenced_and_not_replayable(self):
        self.pause_on = 'review-0'
        self.assertEqual(worker.execute(self.claim)['status'], 'paused')
        with patch.object(worker, 'prepare', side_effect=subprocess.TimeoutExpired('fixture-secret', 1)):
            result = self.resume()
        checkpoint = lifecycle.load(self.store, self.claim['id'])
        self.assertEqual(result['error'], 'ENGINEERING_PREPARE_OUTCOME_UNKNOWN')
        self.assertFalse(checkpoint['terminal_known'])
        self.assertFalse(checkpoint['resumable'])
        diagnostic = json.loads((self.folder/'failure-diagnostic.json').read_text(encoding='utf-8'))
        self.assertEqual(diagnostic['exception_type'], 'TimeoutExpired')
        self.assertNotIn('fixture-secret', json.dumps(diagnostic))
        with self.assertRaisesRegex(ValueError, 'ENGINEERING_RECONCILIATION_REQUIRED'):
            lifecycle.resume(self.service, 20, self.claim['id'], checkpoint['version'])
        self.assertFalse(any(c[0] in {'publish', 'publish_native', 'gh'} for c in self.calls))

    def test_resume_interrupted_prepare_executes_once_not_twice(self):
        attempts = []
        def prepare(base):
            attempts.append(base)
            if len(attempts) == 1:
                raise RuntimeError('ENGINEERING_PAUSED_CHECKPOINT_REQUIRED')
            return self.head
        with patch.object(worker, 'prepare', side_effect=prepare):
            self.assertEqual(worker.execute(self.claim)['status'], 'paused')
            self.assert_success(self.resume())
        self.assertEqual(len(attempts), 2)

    def test_push_timeout_blocks_replay_until_remote_reconciliation(self):
        with patch.object(worker, 'publish_commit', side_effect=subprocess.TimeoutExpired('fixture-push', 1)):
            result = worker.execute(self.claim)
        checkpoint = lifecycle.load(self.store, self.claim['id'])
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(checkpoint['stage'], 'push')
        self.assertFalse(checkpoint['terminal_known'])
        self.assertFalse(checkpoint['resumable'])
        with self.assertRaisesRegex(ValueError, 'ENGINEERING_RECONCILIATION_REQUIRED'):
            lifecycle.resume(self.service, 20, self.claim['id'], checkpoint['version'])
        self.assertFalse(any(c[0] in {'publish_native', 'gh'} for c in self.calls))

    def test_known_knowledge_failure_resumes_without_duplicate_publication(self):
        failed = []
        def operator(op, **kwargs):
            if op == 'knowledge' and not failed:
                failed.append(True)
                raise RuntimeError('KNOWLEDGE_UNAVAILABLE')
            return self.operator(op, **kwargs)
        with patch.object(worker, 'operator', side_effect=operator):
            self.assertEqual(worker.execute(self.claim)['error'], 'KNOWLEDGE_UNAVAILABLE')
            self.assert_success(self.resume())
        self.assertEqual(len([c for c in self.calls if c[0] == 'publish']), 1)
        self.assertEqual(len([c for c in self.calls if c[0] == 'publish_native']), 1)
        self.assertEqual(len([c for c in self.calls if c[0] == 'gh' and c[1][1:3] == ['pr','list']]), 1)


if __name__ == '__main__':
    unittest.main()
