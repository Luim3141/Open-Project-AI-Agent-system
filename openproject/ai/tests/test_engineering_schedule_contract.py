import unittest
from unittest.mock import patch
import test_engineering_reporting as fixtures
from gateway import engineering
from gateway.engineering_reporting import get_schedule,update_schedule,setup_reporting


class ScheduleContractTests(unittest.TestCase):
    def setUp(self):
        fixtures.EngineeringReportingTests.setUp(self)
        self.addCleanup(self.tmp.cleanup)
        self.service=engineering.scoped_service(self.service,6)
    def test_partial_edit_preserves_other_schedule_fields_and_rejects_bad_time(self):
        before=update_schedule(self.service,20,{'daily_minute':17,'weekly_day':4,'weekly_hour':13,'weekly_minute':23})
        changed=update_schedule(self.service,20,{'daily_hour':10})
        for key in ['daily_minute','weekly_day','weekly_hour','weekly_minute']:
            self.assertEqual(changed[key],before[key])
        for bad in [{'daily_hour':24},{'weekly_day':0},{'daily_minute':-1},{'weekly_enabled':'false'}]:
            with self.subTest(bad=bad),self.assertRaisesRegex(ValueError,'SCHEDULE_INVALID'):
                update_schedule(self.service,20,bad)
        self.assertEqual(get_schedule(self.service,20)['daily_hour'],10)

    def test_stale_editor_cannot_overwrite_another_saved_schedule(self):
        original=get_schedule(self.service,20)
        saved=update_schedule(self.service,20,{'daily_hour':10,'expected_updated':original['updated']})
        with self.assertRaisesRegex(ValueError,'SCHEDULE_CONFLICT'):
            update_schedule(self.service,20,{'weekly_hour':12,'expected_updated':original['updated']})
        current=get_schedule(self.service,20)
        self.assertEqual(current['updated'],saved['updated'])
        self.assertEqual(current['weekly_hour'],original['weekly_hour'])

    def test_invalid_timezone_is_rejected_without_silent_fallback(self):
        with self.assertRaisesRegex(ValueError,'SCHEDULE_INVALID'):
            update_schedule(self.service,20,{'timezone':'invalid/timezone'})

    def test_initialized_reporting_reads_do_not_reacquire_schema_writer(self):
        setup_reporting(self.store)
        with patch.object(self.store,'connect',side_effect=AssertionError('unnecessary schema connection')):
            setup_reporting(self.store)

    def test_service_api_preserves_schedule_version_and_deduplicates_save(self):
        original=get_schedule(self.service,20)
        command={'action':'engineering_report_schedule_update','arguments':{'daily_minute':17,'expected_updated':original['updated'],'timezone':original['timezone']},'idempotency_key':'schedule-api-save'}
        saved=self.service.execute_actor(20,command)
        self.assertEqual(saved['result']['daily_minute'],17)
        self.assertEqual(self.service.execute_actor(20,command),saved)
        self.assertEqual(get_schedule(self.service,20)['updated'],saved['result']['updated'])
        with self.assertRaisesRegex(ValueError,'SCHEDULE_CONFLICT'):
            self.service.execute_actor(20,{**command,'idempotency_key':'schedule-api-stale','arguments':{**command['arguments'],'weekly_hour':11}})

    def test_edit_between_snapshot_and_commit_cannot_be_overwritten(self):
        original=get_schedule(self.service,20)
        def concurrent_edit(*args):
            with self.store.connect() as db:
                db.execute('UPDATE engineering_report_schedules SET daily_hour=11,updated=? WHERE project=6',(original['updated']+1,))
            return original
        with patch('gateway.engineering_reporting.get_schedule',side_effect=concurrent_edit):
            with self.assertRaisesRegex(ValueError,'SCHEDULE_CONFLICT'):
                update_schedule(self.service,20,{'daily_hour':10,'expected_updated':original['updated']})
        self.assertEqual(get_schedule(self.service,20)['daily_hour'],11)
