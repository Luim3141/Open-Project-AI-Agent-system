import json,unittest
from native_corpus_candidate import document_text
from business_spans import business_spans

class NativeCorpusCandidateTests(unittest.TestCase):
    def fixture(self):
        return {'id':42,'subject':'Source','lockVersion':3,'description':{'raw':'Full description.'},
                '_links':{'project':{'href':'/api/v3/projects/6'},'status':{'title':'NEW'},'type':{'title':'Task'}}}
    def test_whole_long_json_journal_remains_parseable_and_later_receipts_visible(self):
        long=json.dumps({'text':'A'*900,'summary':'Verified SQLite receipt.'})
        text,meta=document_text(self.fixture(),[{'id':1,'comment':{'raw':long}},{'id':2,'comment':{'raw':'Second receipt.'}}],str)
        self.assertIn(long,text);self.assertEqual(meta['activity_ids'],[1,2]);self.assertFalse(meta['partial_json_truncation'])
        self.assertTrue(any('Verified SQLite' in s['text'] for s in business_spans(text)))
    def test_oversized_journal_is_explicitly_omitted_whole_without_hiding_smaller_receipt(self):
        text,meta=document_text(self.fixture(),[{'id':1,'comment':{'raw':'Small receipt.'}},{'id':2,'comment':{'raw':'x'*5000}}],str,max_chars=500)
        self.assertLessEqual(len(text),500);self.assertEqual(meta['omitted_activity_ids'],[2]);self.assertEqual(meta['activity_ids'],[1])
        self.assertIn('Small receipt.',text)
    def test_large_description_and_wrong_project_fail_closed(self):
        wp=self.fixture();wp['description']['raw']='x'*1000
        with self.assertRaises(ValueError):document_text(wp,[],str,max_chars=200)
        wp=self.fixture();wp['_links']['project']['href']='/api/v3/projects/5'
        with self.assertRaises(PermissionError):document_text(wp,[],str)
    def test_native_current_field_is_separate_from_untrusted_comment_status(self):
        text,meta=document_text(self.fixture(),[{'id':1,'comment':{'raw':'Status is DONE (untrusted claim).'}}],str)
        self.assertEqual(meta['native_fields']['status'],'NEW')
        spans=business_spans(text)
        self.assertTrue(any(s.get('json_path')==['native_fields','status'] and s['text']=='NEW' for s in spans))
