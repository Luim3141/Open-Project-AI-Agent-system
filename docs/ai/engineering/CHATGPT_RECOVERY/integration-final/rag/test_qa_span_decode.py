import unittest
from qa_span_decode import decode_span


class DecodeTest(unittest.TestCase):
    def test_unicode_offsets_and_question_mask(self):
        result = decode_span('Đọc 14 ngày.', [(0, 0), (0, 3), (4, 6), (7, 11)], [None, 0, 1, 1], [0, 99, 8, 0], [0, 99, 0, 8])
        self.assertEqual(result['text'], '14 ngày')
        self.assertEqual((result['start'], result['end']), (4, 11))

    def test_null_and_tie_abstain(self):
        for answer_score in (1, 2):
            self.assertIsNone(decode_span('book', [(0, 0), (0, 4)], [None, 1], [2, answer_score], [2, answer_score]))

    def test_noncontiguous_or_overlong_not_returned(self):
        result = decode_span('a b', [(0, 0), (0, 1), (2, 3)], [None, 1, 1], [0, 9, 0], [0, 0, 9], max_answer_tokens=1)
        self.assertEqual(result['text'], 'a')

    def test_invalid_logits_fail_closed(self):
        with self.assertRaises(ValueError):
            decode_span('x', [(0, 0), (0, 1)], [None, 1], [0, float('nan')], [0, 1])


if __name__ == '__main__':
    unittest.main()
