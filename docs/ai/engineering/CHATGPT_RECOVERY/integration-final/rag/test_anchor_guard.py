import unittest
from anchor_guard import missing_identifiers


class IdentifierGuardTests(unittest.TestCase):
    def test_technical_identifier_absent_from_authorized_scope_abstains(self):
        self.assertEqual(missing_identifiers('How is caching done with Redis?', ['Uses a local cache.']), ['Redis'])
        self.assertEqual(missing_identifiers('What does GET /v2/orders/{id} return?', ['GET /v2/users/{id} returns a user.']), ['/v2/orders/{id}'])
        self.assertEqual(missing_identifiers('Is max_retries set?', ['The max_retries setting is four.']), [])

    def test_common_sentence_start_and_unicode_do_not_become_identifiers(self):
        self.assertEqual(missing_identifiers('Which action can update a task?', ['An action can update a task.']), [])
        self.assertEqual(missing_identifiers('Tìm việc theo trạng thái.', ['Tìm việc theo trạng thái.']), [])

    def test_identifier_match_respects_token_boundaries_and_case(self):
        self.assertEqual(missing_identifiers('Can we use ABC?', ['ABCD is available.']), ['ABC'])
        self.assertEqual(missing_identifiers('Can we use ABC?', ['The abc integration is available.']), [])


if __name__ == '__main__':
    unittest.main()
