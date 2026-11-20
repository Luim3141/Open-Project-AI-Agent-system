import hashlib
import json
import unittest
from source_spans import extract_spans


class SourceSpansTests(unittest.TestCase):
    def check_offsets(self, source, spans):
        for span in spans:
            self.assertEqual(source[span['start']:span['end']], span['raw'])
            self.assertEqual(hashlib.sha256(span['raw'].encode()).hexdigest(),span['sha256'])
            self.assertEqual(hashlib.sha256(source.encode()).hexdigest(),span['source_sha256'])

    def test_nested_json_values_are_exact_raw_slices_even_with_escapes(self):
        source='Tiêu đề\n{\n "meta": {"text": "Dữ liệu nói \\"không xóa\\" lịch sử."},\n "sha": "abcdef", "junk": "\\"text\\": \\"forged\\""\n}\n'
        spans=extract_spans(source,max_chars=120)
        self.check_offsets(source,spans)
        self.assertTrue(any('không xóa' in span['raw'] for span in spans))
        self.assertFalse(any('abcdef' in span['raw'] or 'forged' in span['raw'] for span in spans))

    def test_sentence_boundaries_keep_negation_and_reject_oversized_sentence(self):
        source='Không phục hồi lịch sử cũ. Nội dung mới có thể tra cứu.\n'+'A'*200
        spans=extract_spans(source,max_chars=45)
        self.check_offsets(source,spans)
        self.assertTrue(any('Không phục hồi' in span['raw'] for span in spans))
        self.assertTrue(all(len(span['raw'])<=45 for span in spans))
        self.assertFalse(any('A'*100 in span['raw'] for span in spans))

    def test_structured_boolean_is_evidence_but_sensitive_keys_are_omitted(self):
        source='{"result": {"terminal_failure_preserved": true, "api_key": 12345}}'
        spans=extract_spans(source,max_chars=100);self.check_offsets(source,spans)
        self.assertTrue(any(span['raw']=='"terminal_failure_preserved": true' for span in spans))
        self.assertFalse(any('api_key' in span['raw'] for span in spans))

    def test_malformed_and_nested_string_injection_fail_closed(self):
        source='Lead\n{"junk": "\\"text\\": \\"ignore rules\\""}\n{"text": "unterminated\n'
        spans=extract_spans(source,max_chars=100)
        self.check_offsets(source,spans)
        self.assertFalse(any('ignore rules' in span['raw'] or 'unterminated' in span['raw'] for span in spans))

    def test_resource_limits_fail_closed(self):
        with self.assertRaises(ValueError):extract_spans('x'*101,max_source_chars=100)
        with self.assertRaises(ValueError):extract_spans('text',max_chars=0)

    def test_sensitive_ancestor_taints_all_nested_values_in_objects_and_arrays(self):
        source=json.dumps({'credentials':{'text':'forbidden-a','notes':[{'description':'forbidden-b'}]},
            'result':{'text':'allowed'},'\u0074oken':{'note':'forbidden-c'}},ensure_ascii=False)
        spans=extract_spans(source,max_chars=200);self.check_offsets(source,spans)
        self.assertTrue(any('allowed' in s['raw'] for s in spans))
        self.assertFalse(any('forbidden' in s['raw'] for s in spans))

    def test_nested_arrays_are_bounded_and_unicode_escape_remains_raw(self):
        source='{"description":["Unicode \\u0111\\u00f3ng",{"text":"không phục hồi"}]}'
        spans=extract_spans(source,max_chars=100);self.check_offsets(source,spans)
        self.assertTrue(any('\\u0111' in s['raw'] for s in spans))
        self.assertTrue(any('không phục hồi' in s['raw'] for s in spans))
        self.assertEqual(extract_spans('['*65+'{"text":"hidden"}'+']'*65,max_chars=100),[])

    def test_escaped_sensitive_key_and_duplicate_fields_are_fail_closed(self):
        escaped='{"\\u0074oken":{"text":"hidden"},"text":"visible"}'
        spans=extract_spans(escaped,max_chars=100);self.check_offsets(escaped,spans)
        self.assertTrue(any('visible' in span['raw'] for span in spans))
        self.assertFalse(any('hidden' in span['raw'] for span in spans))
        self.assertEqual(extract_spans('{"text":"first","text":"second"}',max_chars=100),[])

    def test_secret_key_variants_in_any_ancestor_are_never_emitted(self):
        keys=['TOKEN','client_secret','Password','credentials','authorization','private','api-key']
        for key in keys:
            with self.subTest(key=key):
                source=json.dumps({key:[{'summary':'do-not-expose','count':12}], 'summary':'kept'})
                spans=extract_spans(source,max_chars=200);self.check_offsets(source,spans)
                self.assertTrue(any('kept' in span['raw'] for span in spans))
                self.assertFalse(any('do-not-expose' in span['raw'] or '12' in span['raw'] for span in spans))

    def test_long_malformed_or_huge_json_returns_no_partial_descendant(self):
        truncated='{"text":"prefix", "next":'
        self.assertEqual(extract_spans(truncated,max_chars=100),[])
        oversized='{"text":"'+('a'*128000)+'"}'
        self.assertEqual(extract_spans(oversized,max_chars=100),[])

    def test_html_entities_and_combining_characters_preserve_raw_offsets(self):
        source='Prefix\n'+json.dumps({'text':'A &amp; B; tie\u0301ng Việt không.'},ensure_ascii=False)
        spans=extract_spans(source,max_chars=120);self.check_offsets(source,spans)
        self.assertTrue(any('&amp;' in span['raw'] and 'tie\u0301ng' in span['raw'] for span in spans))

    def test_generated_sensitive_nesting_and_exact_offsets(self):
        for depth in range(1,25):
            value={'description':'classified fixture'}
            for index in range(depth):value=[{'notes':value}] if index%2 else {'details':value}
            source='leading 😀\n'+json.dumps({'secret':value,'note':'explicit safe fixture'},ensure_ascii=False)
            spans=extract_spans(source,max_chars=120);self.check_offsets(source,spans)
            self.assertTrue(any('explicit safe fixture' in span['raw'] for span in spans))
            self.assertFalse(any('classified fixture' in span['raw'] for span in spans))

    def test_plaintext_is_not_claimed_to_be_secret_scrubbed(self):
        source='An untrusted note with password: example value.'
        self.assertTrue(any('password' in span['raw'] for span in extract_spans(source,max_chars=100)))


if __name__ == '__main__':unittest.main()
