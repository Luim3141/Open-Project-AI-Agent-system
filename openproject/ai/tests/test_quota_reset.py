import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from gateway.store import Store, pacific_day


class PacificQuotaTests(unittest.TestCase):
    def test_dst_days_are_23_and_25_hours(self):
        for date, hours in [((2026, 3, 8), 23), ((2026, 11, 1), 25)]:
            now = datetime(*date, 12, tzinfo=ZoneInfo('America/Los_Angeles')).timestamp()
            start, end = pacific_day(now)
            self.assertEqual(end - start, hours * 3600)

    def test_exact_midnight_is_counted_and_reset_keeps_history(self):
        now = datetime(2026, 10, 16, tzinfo=ZoneInfo('America/Los_Angeles')).timestamp()
        start, end = pacific_day(now)
        limits = {'rpm': 10, 'tpm': 1000, 'rpd': 1}
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            with store.connect() as db:
                db.execute('INSERT INTO gemini_usage VALUES(?,?,?)', ('fixture', start - 1, 1))
            with patch('gateway.store.time.time', return_value=start):
                store.reserve_gemini('fixture', limits, 1)
            with patch('gateway.store.time.time', return_value=start + 61):
                with self.assertRaisesRegex(ValueError, 'RPD') as caught:
                    Store(directory).reserve_gemini('fixture', limits, 1)
                self.assertAlmostEqual(caught.exception.retry_at, end + 0.1)
            with patch('gateway.store.time.time', return_value=end):
                Store(directory).reserve_gemini('fixture', limits, 1)
            with store.connect() as db:
                self.assertEqual(db.execute('SELECT count(*) FROM gemini_usage').fetchone()[0], 3)


if __name__ == '__main__':
    unittest.main()
