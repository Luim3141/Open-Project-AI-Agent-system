"""REC-018: durable recovery across real HTTP boundaries and isolated SQLite only."""
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

from gateway import engineering_github_sync as sync
from gateway.native import Native
from gateway.store import Store


class GitHubJournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.service = SimpleNamespace(store=Store(Path(self.tmp.name)))
        self.activities, self.posts = [], 0
        self.post_mode, self.read_mode = 'ok', 'ok'
        self.entered, self.release = threading.Event(), threading.Event()
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def send_json(self, value, status=200):
                body = json.dumps(value).encode()
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if '/activities' in self.path:
                    if owner.read_mode == 'fail':
                        return self.send_json({'message': 'denied'}, 403)
                    # Put the marker on a second page to enforce complete readback.
                    elements = owner.activities if 'offset=2' in self.path else [{'comment': {'raw': 'other'}}]
                    return self.send_json({'total': 1 + len(owner.activities), '_embedded': {'elements': elements}})
                if '/pulls?' in self.path:
                    if owner.read_mode in ('429', '403'):
                        return self.send_json({'message': 'fixture failure'}, int(owner.read_mode))
                    return self.send_json([])
                return self.send_json({'id': 380, '_links': {
                    'project': {'href': '/api/v3/projects/6'},
                    'parent': {'href': '/api/v3/work_packages/379'}}})

            def do_POST(self):
                owner.posts += 1
                document = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                if owner.post_mode == 'reject':
                    return self.send_json({'message': 'forbidden'}, 403)
                if owner.post_mode == 'server_error':
                    return self.send_json({'message': 'unknown server outcome'}, 503)
                owner.activities.append(document)
                owner.entered.set()
                if owner.post_mode == 'block':
                    owner.release.wait(5)
                if owner.post_mode == 'disconnect':
                    self.connection.shutdown(socket.SHUT_RDWR)
                    self.connection.close()
                    return
                self.send_json({'id': len(owner.activities) + 100}, 201)

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base = f'http://127.0.0.1:{self.server.server_port}'
        self.pr = {'number': 1, 'state': 'closed', 'is_merged': True, 'merge_target': 'MAIN',
                   'head_sha': 'a' * 40, 'base_ref': 'main',
                   'html_url': 'https://github.com/Luim3141/mini-task-manager/pull/1'}
        self.fetch = patch.object(sync, 'fetch_pull_requests', return_value=[self.pr])
        self.fetch.start()
        self.addCleanup(self.fetch.stop)
        sync._SYNC_CACHE.clear()

    def run_sync(self):
        return sync.reconcile_github_with_openproject(self.service, Native(self.base, 'fixture', 6))

    def test_crash_after_post_before_persist_recovers_by_paginated_marker(self):
        finish = sync._journal_finish
        def crash_after_post(service, key, state, error=None):
            if state == 'DONE':
                raise SystemExit('crash after accepted POST')
            return finish(service, key, state, error)
        with patch.object(sync, '_journal_finish', side_effect=crash_after_post):
            with self.assertRaises(SystemExit):
                self.run_sync()
        self.assertEqual(self.posts, 1)
        sync._SYNC_CACHE.clear()
        self.service = SimpleNamespace(store=Store(Path(self.tmp.name)))
        receipt = self.run_sync()
        self.assertEqual(receipt['status'], 'SUCCESS')
        self.assertEqual(receipt['items'][0]['status'], 'RECONCILED')
        self.assertFalse(receipt['changed'])
        self.assertEqual(self.posts, 1)
        self.assertEqual(self.run_sync()['items'][0]['status'], 'UNCHANGED')

    def test_timeout_after_native_commit_reconciles_without_repost(self):
        self.post_mode = 'disconnect'
        first = self.run_sync()
        self.assertEqual(first['items'][0]['status'], 'UNKNOWN')
        self.assertEqual(first['status'], 'SYNC_FAILED')
        self.assertEqual(self.run_sync()['items'][0]['status'], 'RECONCILED')
        self.assertEqual(self.posts, 1)

    def test_unknown_without_marker_never_reposts(self):
        self.post_mode = 'server_error'
        self.assertEqual(self.run_sync()['items'][0]['status'], 'UNKNOWN')
        self.post_mode = 'ok'
        self.assertEqual(self.run_sync()['items'][0]['status'], 'UNKNOWN')
        self.assertEqual(self.posts, 1)

    def test_two_concurrent_requests_only_one_post(self):
        self.post_mode = 'block'
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(self.run_sync)
            self.assertTrue(self.entered.wait(5))
            second = pool.submit(self.run_sync).result(timeout=5)
            self.release.set()
            result = first.result(timeout=5)
        self.assertEqual(self.posts, 1)
        self.assertEqual(len(self.activities), 1)
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertIn(second['items'][0]['status'], ('UNKNOWN', 'RECONCILED', 'UNCHANGED'))

    def test_known_rejection_allows_retry(self):
        self.post_mode = 'reject'
        self.assertEqual(self.run_sync()['items'][0]['status'], 'FAILED')
        self.post_mode = 'ok'
        self.assertTrue(self.run_sync()['changed'])
        self.assertEqual(self.posts, 2)
        self.assertEqual(len(self.activities), 1)

    def test_missing_durable_store_fails_closed(self):
        self.service.store = None
        self.assertEqual(self.run_sync()['status'], 'SYNC_FAILED')
        self.assertEqual(self.posts, 0)

    def test_existing_legacy_sync_note_is_adopted_without_duplicate(self):
        comment = 'Verified legacy GitHub sync note with exact revision and state'
        self.activities.append({'comment': {'raw': comment}})
        result = sync._sync_activity(self.service, Native(self.base, 'fixture', 6), 380, 'legacy-operation', comment)
        self.assertEqual(result, 'RECONCILED')
        self.assertEqual(self.posts, 0)

    def test_preflight_read_failure_does_not_post_and_can_retry(self):
        self.read_mode = 'fail'
        self.assertEqual(self.run_sync()['status'], 'SYNC_FAILED')
        self.assertEqual(self.posts, 0)
        self.read_mode = 'ok'
        self.assertTrue(self.run_sync()['changed'])

    def test_main_and_feature_merge_only_create_activities(self):
        self.run_sync()
        self.pr.update(base_ref='feature', merge_target='FEATURE_BRANCH (feature)')
        self.run_sync()
        self.assertEqual(self.posts, 2)
        self.assertIn('CHƯA VÀO MAIN', self.activities[-1]['comment']['raw'])
        self.assertNotIn('DEPLOYED', json.dumps(self.activities))

    def test_github_empty_403_429_and_timeout_do_not_return_stale_success(self):
        self.fetch.stop()
        original_open = urllib.request.urlopen
        def local_open(request, **kwargs):
            url = self.base + '/pulls?' + request.full_url.split('?', 1)[1]
            return original_open(url, **kwargs)
        with patch('urllib.request.urlopen', side_effect=local_open):
            self.assertEqual(sync.fetch_pull_requests(token='', force=True), [])
            for status in ('403', '429'):
                self.read_mode = status
                self.assertEqual(self.run_sync()['status'], 'SYNC_FAILED')
        with patch('urllib.request.urlopen', side_effect=TimeoutError('fixture timeout')):
            self.assertEqual(self.run_sync()['status'], 'SYNC_FAILED')
        self.assertEqual(self.posts, 0)


if __name__ == '__main__':
    unittest.main()
