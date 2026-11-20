import copy
import tempfile
import unittest
from pathlib import Path

from automation.telegram_n8n_install import install


class InstallerTests(unittest.TestCase):
    def test_new_workflow_is_published_without_updating_existing_objects(self):
        class API:
            calls=[]
            workflow=None
            def request(self,method,path,body=None):
                self.calls.append((method,path))
                if method=='GET' and path=='/rest/workflows':return [{'id':'old','name':'WF01','active':True}]
                if method=='GET' and path=='/rest/credentials':return [{'id':'oldkey','name':'Existing','type':'httpHeaderAuth'}]
                if method=='POST' and path=='/rest/credentials':return {'id':'new'+str(len(self.calls))}
                if method=='POST' and path=='/rest/workflows':
                    self.workflow={**copy.deepcopy(body),'id':'newflow','versionId':'v1','active':False}
                    self.workflow['nodes'][2]['webhookId']='server-generated-outgoing-metadata'
                    return self.workflow
                if path.endswith('/activate'):self.workflow['active']=True;return self.workflow
                if path=='/rest/workflows/newflow':return self.workflow
                raise AssertionError((method,path))
        with tempfile.TemporaryDirectory() as folder:
            api=API();receipt=Path(folder)/'receipt.json'
            result=install(api,'123:bot-secret','k'*64,receipt)
            self.assertEqual(result['status'],'PUBLISHED')
            self.assertFalse(any('/old' in path for _,path in api.calls))
            self.assertNotIn('bot-secret',receipt.read_text())

    def test_existing_name_or_partial_install_is_never_overwritten(self):
        class API:
            def request(self,method,path,body=None):
                self.assert_read=method=='GET'
                if not self.assert_read:raise AssertionError('mutation')
                return [{'name':'QLDAPM — Telegram Agent Notifications'}] if path.endswith('workflows') else []
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError,'EXISTING'):
                install(API(),'123:token','k'*64,Path(folder)/'receipt.json')
