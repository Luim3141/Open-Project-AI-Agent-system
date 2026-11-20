"""Source-preserving passages; no network or production corpus."""
import hashlib
import unittest

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from benchmark_phase2 import load_candidate
chunk_text = load_candidate().chunk_text


class SemanticPassageChunksTests(unittest.TestCase):
    def test_long_audit_document_keeps_complete_requirement_as_a_searchable_chunk(self):
        passage = 'Search Unicode case-insensitively using Python casefold for every task title.'
        content = 'Audit: ' + 'a12b34c56d78 ' * 65 + '\n' + passage + '\n' + 'Artifact: ' + 'e90f12 ' * 100
        chunks = chunk_text(content)
        self.assertIn(passage, [c['chunk_text'] for c in chunks])
        self.assertEqual([c['chunk_index'] for c in chunks], list(range(len(chunks))))
        for c in chunks:
            self.assertLessEqual(len(c['chunk_text']), 600)
            self.assertIn(c['chunk_text'], content)
            self.assertEqual(c['chunk_hash'], hashlib.sha256(f"{c['chunk_index']}:{c['chunk_text']}".encode()).hexdigest())

    def test_compact_json_keeps_requirement_value_without_neighboring_audit_fields(self):
        passage = 'Reject stale responses after a newer search request has finished.'
        content = '{"audit":"' + 'a12b34c56d78' * 70 + '","acceptance":["' + passage + '"],"trace":"' + 'b' * 700 + '"}'
        chunks = chunk_text(content)
        self.assertIn(passage, [c['chunk_text'] for c in chunks])
        self.assertEqual(chunks, chunk_text(content))

    def test_short_generic_fragment_is_not_promoted_out_of_its_context(self):
        fragment = '5.  Update task status.'
        content = 'Context ' * 100 + '\n' + fragment + '\n' + 'Audit ' * 100
        self.assertNotIn(fragment, [c['chunk_text'] for c in chunk_text(content)])


if __name__ == '__main__':
    unittest.main()
