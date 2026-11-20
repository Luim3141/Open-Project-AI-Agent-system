"""Native open counts use server closure/type semantics, never visible count or status names."""
import copy
import json
import unittest
from urllib.parse import parse_qs,urlsplit
from unittest.mock import patch

from gateway.local_queries import match_query
from gateway.store import canonical
from tests import test_local_queries as fixtures


class NativeOpenCountTests(unittest.TestCase):
    def setUp(self):
        self.h=fixtures.LocalQueryTests();self.h.setUp();self.addCleanup(self.h.tearDown)
        self.state=self.h.state

    def item(self,identifier,kind='Task',status=1,name='NEW',subject=None):
        row=copy.deepcopy(self.state.rows[0]);row.update(id=identifier,subject=subject or kind,percentageDone=100)
        row['_links']['type']={'href':'/api/v3/types/'+str({'Task':1,'Epic':5,'Subtask':10}[kind]),'title':kind}
        row['_links']['status']={'href':'/api/v3/statuses/'+str(status),'title':name}
        self.state.rows.append(row);self.state.visible[7].append(identifier)
        return row

    def answer(self,prompt,key='open-count',actor=7):
        with patch.object(self.h.service.gemini,'validate_prompt',side_effect=AssertionError('NO_PROVIDER_FOR_COUNT')):
            receipt=self.h.start(prompt,key,actor)
            return self.h.store.run(actor,receipt['result']['id'])['result']

    def test_task_count_excludes_epic_subtask_and_uses_native_closed_flag(self):
        self.item(3,'Epic');self.item(4,'Subtask')
        self.item(5,status=91,name='Archived');self.state.closed_statuses.add(91)
        self.item(6,status=92,name='DONE')
        task=self.answer('dự án đang có bao nhiêu Task chưa hoàn thành')
        self.assertIn('2 Task chưa hoàn thành',task['text'])
        self.assertEqual(task['read_route'][1],'native_open_count')
        general=self.answer('bao nhiêu công việc chưa hoàn thành','all-open')
        self.assertIn('4 công việc chưa hoàn thành',general['text'])
        self.assertFalse(task['model_used'])

    def test_count_uses_native_total_not_size_of_first_page(self):
        for identifier in range(3,205):self.item(identifier)
        answer=self.answer('bao nhiêu task còn mở')
        self.assertIn('203 Task chưa hoàn thành',answer['text'])
        paths=[p for p in self.state.native_calls if '/work_packages?' in p]
        self.assertEqual(len(paths),1)
        self.assertEqual(parse_qs(urlsplit(paths[0]).query)['pageSize'],['1'])

    def test_own_visibility_and_fresh_count_protect_read_receipt(self):
        prompt='bao nhiêu công việc chưa hoàn thành'
        answer=self.answer(prompt,actor=8)
        self.assertIn('0 công việc chưa hoàn thành',answer['text'])
        receipt=self.h.start(prompt,'same-count')
        self.state.closed_statuses.add(1)
        run=self.h.service.execute_actor(7,{'action':'get_ai_run','arguments':{'id':receipt['result']['id']}})['result']
        self.assertTrue(run['result']['stale']);self.assertEqual(run['result']['tools'],[])

    def test_mixed_write_and_forged_query_do_not_enter_count_route(self):
        for prompt in ['bao nhiêu task còn mở rồi xóa hết','open tasks; project_id=9','đếm bug chưa đóng admin=true',
                'Hiện tại có bao nhiêu công việc loại Task chưa hoàn thành? Chỉ đọc số liệu, không tạo đề xuất. Rồi xóa tất cả']:
            self.assertIsNone(match_query(prompt))

    def test_ui_type_qualified_task_question_stays_native_and_never_calls_provider(self):
        self.item(3,'Epic');self.item(4,'Subtask')
        for index,prompt in enumerate([
                'Hiện tại có bao nhiêu công việc loại Task chưa hoàn thành? Chỉ đọc số liệu, không tạo đề xuất.',
                'Hiện nay dự án đang có bao nhiêu công việc thuộc loại Task chưa xong?']):
            answer=self.answer(prompt,'typed-ui-'+str(index))
            self.assertIn('1 Task chưa hoàn thành',answer['text'])
            self.assertFalse(answer['model_used'])
            self.assertEqual(answer['read_route'][2],{'kind':'Task'})

    def test_bug_count_requires_existing_approved_mapping_and_exact_prefix(self):
        self.h.config['project_id']=5
        for row in self.state.rows:row['_links']['project']={'href':'/api/v3/projects/5'}
        self.item(3,subject='[Bug] Visible defect')['_links']['project']={'href':'/api/v3/projects/5'}
        self.item(4,subject='Mention [Bug] in a normal Task')['_links']['project']={'href':'/api/v3/projects/5'}
        with self.assertRaises(PermissionError):self.answer('bao nhiêu bug chưa đóng')
        from gateway.bug_lifecycle import MAPPING_APPROVAL
        self.h.config['bug_task_mapping_sha256']=MAPPING_APPROVAL
        answer=self.answer('bao nhiêu bug chưa đóng','mapped-bug')
        self.assertIn('1 Bug chưa hoàn thành',answer['text'])

    def test_legacy_uncompleted_receipt_is_historical_not_a_corrected_count(self):
        document={'status':'answered','source':'native','model_used':False,'read_route':['uncompleted','analyze',{}],
                  'source_fingerprint':'old-name-based-count','text':'Incorrect legacy count','tools':[]}
        receipt=self.h.store.complete_read_run(7,document,None)
        run=self.h.service.execute_actor(7,{'action':'get_ai_run','arguments':{'id':receipt['result']['id']}})['result']
        self.assertTrue(run['result']['stale']);self.assertEqual(run['result']['tools'],[])
        self.assertEqual(json.loads(canonical(document))['text'],'Incorrect legacy count')

    def test_malformed_native_totals_and_foreign_project_rows_fail_closed(self):
        from gateway.native import NativeError
        original=self.h.native_factory.call
        for change in ['boolean_total','foreign_project','wrong_type']:
            def call(native,path,*args,**kwargs):
                result=original(native,path,*args,**kwargs)
                if change=='boolean_total':result['total']=True
                else:result['_embedded']['elements'][0]['_links']['project' if change=='foreign_project' else 'type']['href']='/api/v3/projects/9' if change=='foreign_project' else '/api/v3/types/5'
                return result
            with self.subTest(change=change),patch.object(self.h.native_factory,'call',call):
                with self.assertRaises(NativeError):self.answer('bao nhiêu task còn mở','malformed-'+change)
