import hashlib
import unittest

from readable_spans import raw_citation, readable_span
from source_spans import extract_spans


class ReadableSpanTest(unittest.TestCase):
    def test_escaped_unicode_newline_negation_and_citation(self):
        source = r'{"text":"Kh\u00f4ng\\nph\u1ee5c h\u1ed3i; no restoration."}'
        # Double-escaped backslash is literal backslash+n, not a newline.
        span = extract_spans(source)[0]
        view = readable_span(source, span)
        self.assertEqual(view['readable'], r'Không\nphục hồi; no restoration.')
        quote = 'no restoration.'
        result = raw_citation(source, span, quote)
        self.assertEqual(source[result['start']:result['end']], quote)
        self.assertEqual(result['sha256'], hashlib.sha256(quote.encode()).hexdigest())

    def test_newline_is_whitespace_and_surrogate_pair_has_exact_mapping(self):
        source = r'{"text":"A\n\ud83d\ude80  B"}'
        span = extract_spans(source)[0]
        view = readable_span(source, span)
        self.assertEqual(view['readable'], 'A 🚀 B')
        result = raw_citation(source, span, '🚀 B')
        self.assertEqual(result['raw'], r'\ud83d\ude80  B')

    def test_plain_text_backslashes_html_entities_and_combining_marks_unchanged(self):
        source = 'Không &amp; a\u0301 ' + r'\n'
        span = extract_spans(source)[0]
        view = readable_span(source, span)
        self.assertEqual(view['readable'], source)

    def test_hash_tampering_stale_source_and_ambiguous_quote_fail_closed(self):
        source = 'same same'
        span = extract_spans(source)[0]
        with self.assertRaises(ValueError):
            readable_span(source + 'new', span)
        with self.assertRaises(ValueError):
            raw_citation(source, span, 'same')
        with self.assertRaises(ValueError):
            readable_span(source, {**span, 'sha256': '0' * 64})
        with self.assertRaises(ValueError):
            raw_citation('aaa', extract_spans('aaa')[0], 'aa')

    def test_secret_fields_are_not_added_by_normalization(self):
        source = r'{"password":{"text":"SECRET"},"text":"Allowed answer."}'
        views = [readable_span(source, span) for span in extract_spans(source)]
        self.assertEqual([view['readable'] for view in views], ['Allowed answer.'])

    def test_boolean_field_keeps_key_and_negation(self):
        source = '{"terminal_failure_preserved":false}'
        span = extract_spans(source)[0]
        self.assertEqual(readable_span(source, span)['readable'], '"terminal_failure_preserved":false')


if __name__ == '__main__':
    unittest.main()
