import hashlib,json,unittest
from business_spans import business_spans

class BusinessSpansTests(unittest.TestCase):
    def test_assignment_fields_are_kept_copied_parent_and_secrets_are_not(self):
        source='Unit title\n'+json.dumps({'assignment':{'objective':'Count SQLite tasks.','acceptance':['Returns integer.']},
            'functional_specification':{'acceptance':'Unrelated parent CSV feature.'},'credentials':{'objective':'Private value'}},ensure_ascii=False)
        spans=business_spans(source);text=' '.join(s['text'] for s in spans)
        self.assertIn('Count SQLite',text);self.assertIn('Returns integer',text)
        self.assertNotIn('CSV',text);self.assertNotIn('Private',text)
        self.assertTrue(any(s['evidence_type']=='REQUIREMENT' for s in spans))
        for s in spans:
            self.assertEqual(source[s['start']:s['end']],s['raw']);self.assertEqual(hashlib.sha256(s['raw'].encode()).hexdigest(),s['sha256'])

    def test_incomplete_comment_cannot_hide_later_receipt_or_expose_partial_json(self):
        source='Actual description.\nBình luận #4: {"text":"partial\nBình luận #5: '+json.dumps({'text':'Verified later result.'})
        spans=business_spans(source);text=' '.join(s['text'] for s in spans)
        self.assertIn('Actual description',text);self.assertIn('Verified later result',text);self.assertNotIn('partial',text)
        self.assertEqual(next(s for s in spans if 'Verified' in s['text'])['evidence_type'],'HISTORICAL_RECEIPT')

    def test_escaped_offsets_and_repeated_values_are_preserved_without_duplicate(self):
        source='Title\nBình luận #1: '+json.dumps({'text':'Không phục hồi lịch sử.','summary':'Không phục hồi lịch sử.'})
        spans=business_spans(source)
        self.assertTrue(any('Không phục hồi' in s['text'] for s in spans))
        self.assertTrue(all(s['source_sha256']==hashlib.sha256(source.encode()).hexdigest() for s in spans))
