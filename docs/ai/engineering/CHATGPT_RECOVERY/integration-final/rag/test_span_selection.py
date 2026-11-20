import unittest
from span_selection import select_spans


class SpanSelectionTests(unittest.TestCase):
    def test_small_document_keeps_all_evidence_and_source_order(self):
        spans=[{'start':i*10,'end':i*10+5,'raw':f'item {i}'} for i in range(8)]
        self.assertEqual(select_spans('unknown terms',spans),spans)

    def test_long_document_selects_edges_and_lexical_coverage_bounded(self):
        spans=[{'start':i*10,'end':i*10+5,'raw':f'content {i}'} for i in range(15)]
        spans[7]['raw']='rare volcano result'
        selected=select_spans('what volcano result?',spans)
        self.assertLessEqual(len(selected),8)
        self.assertIn(spans[0],selected);self.assertIn(spans[-1],selected);self.assertIn(spans[7],selected)
        self.assertEqual(len({s['start'] for s in selected}),len(selected))

    def test_selection_does_not_discard_negation_in_raw_span(self):
        spans=[{'start':0,'end':32,'raw':'Không khôi phục dữ liệu đã xoá.'}]
        self.assertEqual(select_spans('có khôi phục không?',spans)[0]['raw'],spans[0]['raw'])


if __name__=='__main__':unittest.main()
