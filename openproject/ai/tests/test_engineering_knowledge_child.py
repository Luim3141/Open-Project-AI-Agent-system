import json
import time
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch

from gateway.engineering_operator import operation


class ChildKnowledgeTest(unittest.TestCase):
    def test_knowledge_verifies_citation_for_requested_child(self):
        class DB:
            def execute(self, *args):
                return SimpleNamespace(fetchone=lambda: {'state': 'executing','lease_until':time.time()+60, 'payload': json.dumps({'engine':'openclaw','deadline':time.time()+60,'worker_id':'fixture','claim_token':'current'})})
        @contextmanager
        def connect(): yield DB()
        native=SimpleNamespace(package=lambda identifier: {'id':identifier,'subject':'Retrieve task by numeric identifier','lockVersion':2})
        calls=[]
        def knowledge(who, client, action, args):
            calls.append(args)
            return {'items':[{'native_id':387,'lock_version':2,'citation':'/work_packages/387'}]}
        service=SimpleNamespace(
            store=SimpleNamespace(agent_run=lambda *a: {},connect=connect),
            execute_actor=lambda *a: {'result':{'vector_indexed':True}},
            sync_canonical_native=lambda *a: {'vector_indexed':True},
            knowledge=knowledge)
        with patch('gateway.engineering.authorized',return_value=(native,{})), patch('gateway.engineering_lifecycle.signal',return_value={'mode':'RUN_ONCE'}):
            result=operation(service,'knowledge',{'run_id':'fixture','child_id':387,'worker_id':'fixture','claim_token':'current'})
        self.assertEqual(calls[0]['native_ids'],[387])
        self.assertEqual(calls[0]['query'],'Retrieve task by numeric identifier')
        self.assertEqual(result['retrieval']['items'][0]['native_id'],387)

    def test_parent_only_result_is_not_child_proof(self):
        class DB:
            def execute(self, *args):
                return SimpleNamespace(fetchone=lambda: {'state':'executing','lease_until':time.time()+60,'payload':json.dumps({'engine':'openclaw','deadline':time.time()+60,'worker_id':'fixture','claim_token':'current'})})
        @contextmanager
        def connect(): yield DB()
        native=SimpleNamespace(package=lambda identifier: {'id':identifier,'subject':'Task title','lockVersion':2})
        service=SimpleNamespace(store=SimpleNamespace(agent_run=lambda *a: {},connect=connect),
            execute_actor=lambda *a: {'result':{'vector_indexed':True}},
            sync_canonical_native=lambda *a: {'vector_indexed':True},
            knowledge=lambda *a: {'items':[{'native_id':379,'lock_version':4,'citation':'/work_packages/379'}]})
        with patch('gateway.engineering.authorized',return_value=(native,{})), patch('gateway.engineering_lifecycle.signal',return_value={'mode':'RUN_ONCE'}):
            with self.assertRaisesRegex(ValueError,'ENGINEERING_KNOWLEDGE_CHILD_NOT_VERIFIED'):
                operation(service,'knowledge',{'run_id':'fixture','child_id':387,'worker_id':'fixture','claim_token':'current'})
