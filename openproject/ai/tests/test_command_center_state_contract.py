"""Evaluate the actual ERB state expressions against Gateway-shaped fixtures; no browser."""
import json
from pathlib import Path
import subprocess
import unittest

TEMPLATE = Path(__file__).parents[1] / 'core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb'
CONTROLLER = Path(__file__).parents[1] / 'core/overlay/app/controllers/qldapm_ai_controller.rb'
RUBY = r'''
require 'json'
class Object; def present?; !nil? && self != ''; end; end
data=JSON.parse(STDIN.read)
b=binding
b.local_variable_set(:eng,data['eng'])
b.local_variable_set(:run,data['run'])
b.local_variable_set(:mode,data['mode'])
eval(data['worker_code'],b)
eval(data['run_code'],b)
puts JSON.generate({alive:b.local_variable_get(:worker_alive), status:b.local_variable_get(:status),
                    resumable:(b.local_variable_defined?(:can_resume) && b.local_variable_get(:can_resume)), active:b.local_variable_get(:is_active)})
'''


class CommandCenterStateContract(unittest.TestCase):
    def project(self, worker, queue, status, checkpoint, mode='OFF',eligible=False):
        source=TEMPLATE.read_text(encoding='utf-8')
        worker_code=source.split('  worker = ',1)[1].split('  plans = ',1)[0]
        worker_code='worker = '+worker_code
        run_code=source.split("qstate = run['queue_state']",1)[1].split('%>',1)[0]
        run_code="qstate = run['queue_state']"+run_code
        fixture={'eng':{'delivery_worker':worker},'run':{'queue_state':queue,'result':{'status':status},'checkpoint':checkpoint,'resume':{'eligible':eligible}},
                 'mode':mode,'worker_code':worker_code,'run_code':run_code}
        p=subprocess.run(['docker','exec','-i','qldapm-openproject-web-1','ruby','-e',RUBY],
                         input=json.dumps(fixture).encode(),capture_output=True,check=True,timeout=30)
        return json.loads(p.stdout)

    def test_stale_worker_does_not_show_alive(self):
        state=self.project({'state':'STALE','worker_id':'fixture'},'finished','blocked',{})
        self.assertFalse(state['alive'])

    def test_finished_failure_uses_actual_result_and_offers_safe_resume(self):
        state=self.project({'state':'ALIVE','worker_id':'fixture'},'finished','blocked',
                           {'resumable':True,'terminal_known':True,'version':3},eligible=True)
        self.assertTrue(state['alive'])
        self.assertEqual(state['status'],'blocked')
        self.assertTrue(state['resumable'])

    def test_unknown_outcome_never_offers_resume(self):
        state=self.project({'state':'ALIVE','worker_id':'fixture'},'finished','blocked',
                           {'resumable':False,'terminal_known':False,'version':3})
        self.assertFalse(state['resumable'])

    def test_paused_queued_run_offers_resume_and_cancel(self):
        state=self.project({'state':'ALIVE','worker_id':'fixture'},'queued','waiting',{},'PAUSED',eligible=True)
        self.assertTrue(state['active'])
        self.assertTrue(state['resumable'])

    def test_checkpoint_alone_cannot_bypass_canonical_resume_denial(self):
        state=self.project({'state':'ALIVE'},'finished','blocked',{'resumable':True,'terminal_known':True})
        self.assertFalse(state['resumable'])

    def test_cancel_message_distinguishes_request_from_completion(self):
        source=CONTROLLER.read_text(encoding='utf-8')
        code=source.split("when 'engineering_cancel'",1)[1].split("when 'engineering_resume'",1)[0]
        runner="require 'json';d=JSON.parse(STDIN.read);@result={'state'=>d['state']};eval(d['code']);puts JSON.generate(@result['message'])"
        def message(state):
            p=subprocess.run(['docker','exec','-i','qldapm-openproject-web-1','ruby','-e',runner],
                input=json.dumps({'state':state,'code':code}).encode(),capture_output=True,check=True,timeout=30)
            return json.loads(p.stdout)
        self.assertIn('yêu cầu',message('cancelling'))
        self.assertIn('Đã hủy',message('cancelled'))
        self.assertIn('đã kết thúc',message('finished'))

    def test_run_once_targets_only_ready_planned_unit_with_current_version(self):
        source=TEMPLATE.read_text(encoding='utf-8')
        code='backlog_items = '+source.split('backlog_items = ',1)[1].split('%>',1)[0]
        ruby="require 'json';class Object;def present?;!nil? && self!='';end;end;d=JSON.parse(STDIN.read);@engineering=d['eng'];mode='OFF';parent_id=379;parent_lock=4;b=binding;eval(d['code'],b);puts JSON.generate({unit:b.local_variable_get(:target_unit_name),lock:b.local_variable_get(:target_lock)})"
        def project(backlog,tasks):
            p=subprocess.run(['docker','exec','-i','qldapm-openproject-web-1','ruby','-e',ruby],
                input=json.dumps({'eng':{'backlog':backlog,'tasks':tasks},'code':code}).encode(),capture_output=True,check=True,timeout=30)
            return json.loads(p.stdout)
        self.assertEqual(project([{'unit':'done','state':'succeeded','native_id':389,'dependency_ready':True}],[]),{'unit':None,'lock':None})
        self.assertEqual(project([{'unit':'waiting','state':'PLANNED','native_id':390,'dependency_ready':False}],[]),{'unit':None,'lock':None})
        self.assertEqual(project([{'unit':'new','state':'PLANNED','native_id':390,'dependency_ready':True,'eligible':True}],[{'id':390,'lock_version':0}]),{'unit':'new','lock':0})
