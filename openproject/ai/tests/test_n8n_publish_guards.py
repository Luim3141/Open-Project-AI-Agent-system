import unittest

from automation.n8n_publish_guards import verify_idle,verify_runtime


class PublishGuardTests(unittest.TestCase):
    def test_runtime_must_match_all_qualified_files(self):
        expected={'app.py':'a'*64,'service.py':'b'*64}
        verify_runtime(expected,dict(expected))
        for current in ({'app.py':'a'*64},{'app.py':'a'*64,'service.py':'c'*64},{}):
            with self.subTest(current=current),self.assertRaisesRegex(ValueError,'GATEWAY_RUNTIME_NOT_QUALIFIED'):
                verify_runtime(expected,current)

    def test_inflight_or_invalid_count_blocks_before_and_after_stop(self):
        verify_idle({'unfinished':0})
        for value in (1,-1,None,True,'0'):
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,'N8N_NOT_IDLE'):
                verify_idle({'unfinished':value})

