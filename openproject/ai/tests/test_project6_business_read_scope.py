import copy
import unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch

from gateway import bug_lifecycle,native_wbs


class Project6BusinessScopeTests(unittest.TestCase):
    def service(self,project=6,scoped=True):
        return SimpleNamespace(mode='native',config={'project_id':project,'_engineering_scope':scoped,
            'engineering':{'enabled':True}},keys=lambda *a:None)

    def test_triage_permission_does_not_grant_native_bug_proposal_authority(self):
        service=self.service()
        bug_lifecycle.mapping(service,read_only=True)
        with self.assertRaisesRegex(PermissionError,'BUG_MAPPING_NOT_APPROVED'):
            bug_lifecycle.mapping(service)
        for service in (self.service(7),self.service(6,False)):
            with self.assertRaises(PermissionError):bug_lifecycle.mapping(service,read_only=True)

    def test_project6_only_draft_get_not_adopt_or_materialize(self):
        service=self.service();who={'user_id':20};native=Mock()
        with patch.object(native_wbs,'specification',return_value={'validated':True}),patch.object(native_wbs,'save',return_value={'id':'draft'}) as save:
            self.assertEqual(native_wbs.perform(service,who,native,'wbs_draft',{},'key'),{'id':'draft'})
            save.assert_called_once_with(service,20,'draft',{'validated':True},'key')
        for action in ('wbs_adopt','wbs_next','wbs_from_ba'):
            with self.subTest(action=action),self.assertRaises(PermissionError):
                native_wbs.perform(service,who,native,action,{},'key')
        native.call.assert_not_called()

    def test_unscoped_or_other_project_cannot_reuse_project6_draft_capability(self):
        for service in (self.service(7),self.service(6,False)):
            with self.assertRaises(PermissionError):
                native_wbs.perform(service,{'user_id':20},Mock(),'wbs_draft',{},'key')
