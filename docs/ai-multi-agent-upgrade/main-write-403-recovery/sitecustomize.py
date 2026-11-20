"""Test-only provider stub, mounted only in the private isolated clone; never in an image."""
import os
if os.environ.get('QLDAPM_OFFLINE_WRITE_UAT') == '1':
    import json
    from pathlib import Path
    from gateway.gemini import Gemini
    from gateway.live_agents import LiveConfig
    from gateway.presentation import execution_report, requested_ids
    assert Path('/state/isolated-write-fixture.json').is_file()
    assert not Path('/state/gemini.key').exists(), 'REAL_KEY_FORBIDDEN_IN_OFFLINE_FIXTURE'
    policy = {'enabled':True, 'project':'synthetic-offline-write', 'model':'OFFLINE_TEST_DOUBLE',
              'data_scope':'project-business-content','limits':{'rpm':1000,'tpm':1000000,'rpd':1000}}
    Gemini.settings = lambda self, **kwargs: policy
    Gemini.validate_prompt = lambda self, prompt: policy
    Gemini.multi_agent_settings = lambda self: LiveConfig(enabled=True)
    def no_network(*args, **kwargs): raise AssertionError('GOOGLE_FORBIDDEN_IN_OFFLINE_FIXTURE')
    Gemini.sdk_client = no_network
    def run(self, prompt, execute, **kwargs):
        fixture = json.loads(Path('/state/isolated-write-fixture.json').read_text())
        ids = requested_ids(prompt)
        assert len(ids) == 1 and ids[0] == fixture['parent_id'], 'ONLY_OWNED_PARENT_ALLOWED'
        calls = []
        for action, arguments in [('get_work_package', {'id':ids[0]}), ('create_work_package', {
                'subject':'test', 'type_id':fixture['type_id'], 'parent_id':ids[0], 'assignee_id':23})]:
            value = execute(action, arguments)
            calls.append({'action':action, 'arguments':arguments, 'result':Gemini.business_result(action, value)})
            if kwargs.get('progress'): kwargs['progress']({'tools':calls, **execution_report(calls)})
        return {**execution_report(calls, 'OFFLINE TEST DOUBLE — Native tools are real; no model call.'),
                'tools':calls,'model_used':False,'execution_mode':'MOCK_PROVIDER_NATIVE_REAL','usage':[]}
    Gemini.run = run
