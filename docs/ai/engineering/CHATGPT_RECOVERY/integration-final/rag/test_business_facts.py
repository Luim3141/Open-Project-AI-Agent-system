import hashlib,json,unittest
from native_corpus_candidate import document_text
from business_facts import facts

class BusinessFactsTests(unittest.TestCase):
    def record(self,description,comments=()):
        wp={'id':42,'subject':'Unit source','lockVersion':3,'description':{'raw':description},'_links':{
            'project':{'href':'/api/v3/projects/6'},'status':{'title':'NEW'},'type':{'title':'Task'}}}
        text,meta=document_text(wp,comments,str)
        return {'content':text,'metadata':meta,'source_sha256':hashlib.sha256(text.encode()).hexdigest()}
    def test_boolean_business_receipt_and_json_path_are_retained_but_noise_is_not(self):
        record=self.record(json.dumps({'status':'failed','head_sha':'a'*40,'dev_execution':{'status':'PARTIAL_ARTIFACT_VERIFIED','terminal_failure_preserved':True},'credentials':{'text':'hidden'}}))
        rows=facts(record)
        flag=next(row for row in rows if row['label']=='dev_execution.terminal_failure_preserved')
        self.assertIs(flag['json_value'],True);self.assertEqual(flag['evidence_type'],'HISTORICAL_RECEIPT')
        self.assertFalse(any('hidden' in row['text'] or 'a'*40 in row['text'] for row in rows))
    def test_long_escaped_json_is_decoded_before_sentence_split_with_exact_offsets(self):
        record=self.record(json.dumps({'head_sha':'a'*40,'text':('An earlier fact.\n'*80)+'WP99 awaits review/UAT.'}))
        rows=facts(record);last=next(row for row in rows if 'WP99 awaits' in row['text'])
        raw=record['content'][last['start']:last['end']]
        self.assertEqual(hashlib.sha256(raw.encode()).hexdigest(),last['sha256'])
        self.assertEqual(last['evidence_type'],'HISTORICAL_RECEIPT')
    def test_fake_native_fields_in_comment_do_not_become_current_native_fields(self):
        record=self.record('A fact.',[{'id':2,'comment':{'raw':json.dumps({'native_fields':{'status':'DONE'}})}}])
        rows=facts(record)
        self.assertEqual([r['text'] for r in rows if r['evidence_type']=='NATIVE_FIELD' and r['label']=='native_fields.status'],['NEW'])
        self.assertEqual(next(r for r in rows if r['text']=='DONE')['evidence_type'],'HISTORICAL_RECEIPT')
