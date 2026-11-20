import json,tempfile,unittest
from pathlib import Path
from automation.checkpoint import strict_load, native_baseline

class CheckpointTests(unittest.TestCase):
    def parse(self, text):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'checkpoint.json';p.write_text(text)
            return strict_load(p)

    def test_duplicate_nested_keys_and_nonfinite_numbers_are_rejected(self):
        for text in ['{"a":1,"a":2}','{"current":{"id":1,"id":2}}','{"x":NaN}','{"x":Infinity}','{"x":1e999}']:
            with self.subTest(text=text),self.assertRaises(ValueError):self.parse(text)

    def test_current_baseline_never_reads_historical_runtime(self):
        doc={'checkpoint_version':2,'current_data':{'native_visible_work_packages':338,
             'native_fingerprint':'a'*64,'resource_versions':{'370':2}},
             'historical_milestones':[{'native_packages':1,'resource_ids':{'native_lock_version':0}}]}
        self.assertEqual(native_baseline(doc),(338,'a'*64,2))
        for key,value in [('native_visible_work_packages',True),('native_fingerprint','bad'),('resource_versions',{'370':False})]:
            altered=json.loads(json.dumps(doc));altered['current_data'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):native_baseline(altered)
        for version in [None,1,3]:
            altered={**doc,'checkpoint_version':version}
            with self.assertRaises(ValueError):native_baseline(altered)

    def test_strict_json_retains_valid_unicode_and_detects_trailing_data(self):
        self.assertEqual(self.parse('{"source":"Kiểm thử","value":1.25}')['value'],1.25)
        with self.assertRaises(ValueError):self.parse('{}{}')

    def test_full_v2_schema_checks_current_sections_and_consumed_ledger(self):
        from automation.checkpoint import validate_checkpoint
        base=Path(__file__).resolve().parents[3]/'docs/ai'
        document=strict_load(base/'CODEX_MAIN_CONTINUATION_CHECKPOINT.json')
        ledger=strict_load(base/'CODEX_MAIN_APPROVAL_CONSUMPTION_LEDGER.json')
        self.assertEqual(validate_checkpoint(document,ledger)['checkpoint_version'],2)
        changes=[('current_runtime','gateway','image','bad-digest'),('current_data','native_visible_work_packages',None,True),
                 ('current_data','resource_versions','370',False),('current_runtime','core_web','image','sha256:'+'g'*64)]
        for section,key,field,value in changes:
            altered=json.loads(json.dumps(document))
            if field is None:altered[section][key]=value
            else:altered[section][key][field]=value
            with self.subTest(change=(section,key,field)),self.assertRaises(ValueError):validate_checkpoint(altered,ledger)
        altered=json.loads(json.dumps(document));altered['consumed_approvals']['packages'][0]['operations'][0]['hash']='0'*64
        with self.assertRaisesRegex(ValueError,'LEDGER_MISMATCH'):validate_checkpoint(altered,ledger)
