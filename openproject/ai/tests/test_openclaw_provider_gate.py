import unittest
from automation.openclaw_provider_gate import admit,MODEL


class GateTests(unittest.TestCase):
    def test_off_expired_wrong_model_and_large_body_never_admit(self):
        for d,m,size in [({'active':False,'deadline':200,'remaining':1},MODEL,10),
                         ({'active':True,'deadline':100,'remaining':1},MODEL,10),
                         ({'active':True,'deadline':200,'remaining':1},'other-model',10),
                         ({'active':True,'deadline':200,'remaining':1},MODEL,262145)]:
            with self.assertRaises(PermissionError):admit(d,m,size,100)
            self.assertEqual(d['remaining'],1)

    def test_request_allowance_is_consumed_once_and_cannot_go_negative(self):
        d={'active':True,'deadline':200,'remaining':1}
        admit(d,MODEL,100,100)
        with self.assertRaises(PermissionError):admit(d,MODEL,100,100)
        self.assertEqual(d['remaining'],0)
