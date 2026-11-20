"""Public source-phase drafts/reviews remain separate from Native proposal approval."""
import unittest
from types import SimpleNamespace
from starlette.testclient import TestClient
from gateway.app import create_app,openapi_document
from gateway.permissions import allowed
from gateway.agent_trace import current_run
from gateway.service import Command
from tests import test_native_phase as fixtures


class NativePhaseApiTests(unittest.TestCase):
    def setUp(self):
        self.h=fixtures.NativePhaseTests();self.h.setUp();self.addCleanup(self.h.doCleanups)
        self.client=TestClient(create_app(service=self.h.service),base_url='http://127.0.0.1:8090')
        self.addCleanup(self.client.close)

    def headers(self,actor=20):return {'Authorization':'Bearer '+self.h.tokens[actor]}

    def command(self,action,arguments,actor=20,key=None):
        payload={'action':action,'arguments':arguments}
        if key:payload['idempotency_key']=key
        return self.client.post('/api/v1/commands',json=payload,headers=self.headers(actor))

    def test_new_tools_preserve_six_role_ceilings_and_separate_review(self):
        for actor in [18,19,20,21,22,23]:
            result=self.command('phase_draft',{'native_id':39,'kind':'scope'},actor,'draft-'+str(actor))
            self.assertEqual(result.status_code,200 if actor in [18,19,20] else 403)
        for role in ['BA','BA-PM','BE','FE','QA']:
            self.assertFalse(allowed(role,'phase_transition_prepare','native'))
        self.assertNotIn('phase_review',Command.model_fields['action'].annotation.__args__)
        self.assertIn('/api/v1/native-phases/{id}/decision',openapi_document()['paths'])
        self.assertEqual(self.h.h.native.writes,[])

    def test_exact_human_rest_review_and_replay_409_without_native_write(self):
        draft=self.command('phase_draft',{'native_id':39,'kind':'scope'},key='draft-scope').json()['result']
        url='/api/v1/native-phases/'+draft['id']+'/decision'
        body={'decision':'accept','hash':draft['hash']}
        self.assertEqual(self.client.post(url,json=body,headers=self.headers(20)).status_code,403)
        self.assertEqual(self.client.post(url,json={**body,'actor_id':19},headers=self.headers(19)).status_code,422)
        self.assertEqual(self.client.post(url,json={**body,'hash':'0'*64},headers=self.headers(19)).status_code,409)
        accepted=self.client.post(url,json=body,headers=self.headers(19))
        self.assertEqual(accepted.status_code,200);self.assertEqual(accepted.json()['result']['review']['actor'],19)
        self.assertEqual(self.client.post(url,json=body,headers=self.headers(19)).status_code,409)
        self.assertEqual(self.h.h.native.writes,[])

    def test_invalid_auth_low_role_private_reads_and_forged_claims_denied(self):
        draft=self.h.draft()
        self.assertIn(self.client.post('/api/v1/commands',json={'action':'phase_get','arguments':{'id':draft['id']}}).status_code,[401,403])
        for actor in [21,22,23]:
            self.assertEqual(self.command('phase_get',{'id':draft['id']},actor).status_code,403)
        for claims in [{'actor':18},{'approved':True},{'owner':True}]:
            self.assertEqual(self.command('phase_draft',{'native_id':39,'kind':'scope',**claims},key='forged-'+str(claims)).status_code,422)
        with self.h.store.connect() as db:self.assertEqual(db.execute("SELECT count(*) FROM requests WHERE key LIKE 'forged-%'").fetchone()[0],0)

    def test_model_context_cannot_make_a_human_decision(self):
        draft=self.h.draft();token=current_run.set((self.h.store,SimpleNamespace(actor_id=19,project_id=5,run_id='isolated-model-context',trace_id='isolated-trace',task_id=None)))
        try:
            result=self.client.post('/api/v1/native-phases/'+draft['id']+'/decision',json={'decision':'accept','hash':draft['hash']},headers=self.headers(19))
            self.assertEqual(result.status_code,403)
        finally:current_run.reset(token)

    def test_inbox_is_fresh_authorized_and_draft_retry_refreshes_state(self):
        command={'native_id':39,'kind':'scope'}
        draft=self.command('phase_draft',command,key='same-draft').json()['result']
        self.h.review(draft)
        repeated=self.command('phase_draft',command,key='same-draft').json()['result']
        self.assertEqual(repeated['state'],'accepted')
        inbox=self.command('phase_list',{},19).json()['result']
        self.assertEqual(inbox['items'][0]['id'],draft['id'])
        self.assertNotIn('source',inbox['items'][0])
        self.h.h.native.rows[39]['lockVersion']+=1
        self.assertFalse(self.command('phase_get',{'id':draft['id']}).json()['result']['source_current'])

    def test_ba_reads_own_source_without_requesting_a_native_update_form(self):
        from gateway.native import NativeError
        draft=self.h.draft();original=self.h.h.native.call
        def call(native,path,method='GET',payload=None):
            if native.role in {'BA','BA-PM'} and path.endswith('/form'):
                raise NativeError(403,'NATIVE_EDIT_PERMISSION_REQUIRED')
            return original(native,path,method,payload)
        self.h.h.native.call=call
        response=self.command('phase_get',{'id':draft['id']},20)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['result']['status_options'],[])
        self.assertEqual(self.h.h.native.writes,[])

    def test_managers_read_stale_accepted_source_without_requesting_an_old_version_form(self):
        from gateway.native import NativeError
        draft=self.h.draft();self.h.review(draft)
        self.h.h.native.rows[39]['lockVersion']+=2
        original=self.h.h.native.call
        def call(native,path,method='GET',payload=None):
            if path.endswith('/form'):
                raise NativeError(409,'NATIVE_FORM_STALE_VERSION')
            return original(native,path,method,payload)
        self.h.h.native.call=call
        for actor in [18,19,20]:
            with self.subTest(actor=actor):
                response=self.command('phase_get',{'id':draft['id']},actor)
                self.assertEqual(response.status_code,200)
                result=response.json()['result']
                self.assertEqual(result['state'],'accepted')
                self.assertFalse(result['source_current'])
                self.assertEqual(result['status_options'],[])
                self.assertEqual(result['review']['actor'],19)
        from gateway.native_phase import packet
        with self.assertRaises(NativeError):packet(self.h.service,18,draft['id'])
        self.assertEqual(self.h.h.native.writes,[])


if __name__=='__main__':unittest.main()
