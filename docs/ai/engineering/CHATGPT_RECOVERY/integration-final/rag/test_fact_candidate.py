import unittest
import test_business_candidate
from fact_candidate import FactCandidate


class FactCandidateTests(test_business_candidate.BusinessCandidateTests):
    def engine(self, records, **kwargs):
        return FactCandidate(records, project_id=6, source_actor=20, role='PM', current_sources={
            r['metadata']['native_id']: {'lock_version': 3, 'document_id': r['document_id']} for r in records}, **kwargs)

    def test_receipt_boolean_and_label_enter_retrieval_and_context(self):
        record=self.record(description='{"dev_execution":{"terminal_failure_preserved":true,"status":"PARTIAL_ARTIFACT_VERIFIED"}}')
        engine=self.engine([record]);packet=engine.packet('terminal failure preserved partial artifact')
        self.assertEqual(packet['retrieved_native_ids'], [42])
        flag=next(f for f in packet['facts'] if f['label']=='dev_execution.terminal_failure_preserved')
        result=engine.render(packet, {'fact_ids':[flag['id']]})
        self.assertIn('HISTORICAL_RECEIPT',result['answer'])
        self.assertIn('terminal_failure_preserved',result['answer'])
        self.assertIn('true',result['answer'])
        self.assertEqual(result['citations'][0]['native_id'],42)

    def test_selector_cannot_generate_text_or_cross_packet_ids(self):
        engine=self.engine([self.record()]);packet=engine.packet('SQLite')
        for selected in ({'fact_ids':[99999]}, {'fact_ids':[True]}, {'fact_ids':[], 'answer':'invented'}, {'fact_ids':[0,0]}):
            with self.assertRaises(ValueError):engine.render(packet,selected)
        self.assertIsNone(engine.render(packet,{'fact_ids':[]})['answer'])

    def test_reference_lookup_targets_live_replacement_without_resurrecting_deleted_id(self):
        record=self.record(identifier=43,title='Replacement entry',description='Replacement for WP42; NEW record, not restoration of Native history.')
        packet=self.engine([record]).packet('Does the replacement for WP42 restore Native history?')
        self.assertEqual(packet['retrieved_native_ids'],[43])

    def test_semantic_fact_ranking_preserves_identity_and_bounds_context(self):
        engine=self.engine([self.record(description='{"dev_execution":{"terminal_failure_preserved":true,"status":"PARTIAL_ARTIFACT_VERIFIED"}}')])
        doc=next(iter(engine.records));span=next(s for s in engine.spans[doc] if s['label']=='dev_execution.terminal_failure_preserved')
        hit={'score':.9,'payload':engine.fact_payload(doc,span)}
        packet=engine.semantic_packet('Lỗi cũ có được giữ lại không?',[],[{'score':1,'payload':{**hit['payload'],'actor_id':21}},hit])
        self.assertEqual(len(packet['facts']),1)
        self.assertEqual(packet['facts'][0]['label'],'dev_execution.terminal_failure_preserved')
        self.assertLessEqual(packet['context_chars'],2200)


if __name__=='__main__':unittest.main()
