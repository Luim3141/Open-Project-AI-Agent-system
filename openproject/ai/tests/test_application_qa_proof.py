"""Fixed WBS application proof protocol; no network, Native write or human decisions."""
import copy
import hashlib
import hmac
import json
import tempfile
import time
import unittest
import uuid
from pathlib import Path

from gateway.store import canonical
from gateway.native_qa_runs import snapshot
from gateway.application_qa_proof import DOMAIN, PRODUCER, GATEWAY_SOURCES, CORE_SOURCES, CODE_SHA256, validate, criteria


class ApplicationQaProofTests(unittest.TestCase):
    def setUp(self):
        self.key=b'synthetic-proof-key-not-a-runtime-key'
        self.criteria=json.loads((Path(__file__).parent/'fixtures/wbs_bug371_criteria.json').read_text(encoding='utf-8'))
        self.item={'id':371,'lockVersion':4,'subject':'[Bug] [CODEX TEST] WBS fix',
            'description':{'raw':'\n'.join(k+': '+v for k,v in self.criteria.items())},
            '_links':{'project':{'href':'/api/v3/projects/5'},'type':{'href':'/api/v3/types/1'},
                'status':{'href':'/api/v3/statuses/2'},'assignee':{'href':'/api/v3/users/21'}}}
        self.sources={'gateway':{p:'1'*64 for p in GATEWAY_SOURCES},'core':{p:'2'*64 for p in CORE_SOURCES}}
        self.body={'version':1,'id':str(uuid.uuid4()),'actor':18,'project_id':5,'producer':PRODUCER,'producer_sha256':CODE_SHA256,
            'source':snapshot(self.item),'criteria':self.criteria,'sources':self.sources,
            'build':{'gateway':'sha256:'+'3'*64,'core':'sha256:'+'4'*64},
            'started_at':time.time()-10,'finished_at':time.time()-1,
            'tests':[{'criterion_id':c,'reference':'wbs-application:'+c,'expected':'Pinned application assertion passes',
                'actual':'Actual isolated test completed','outcome':'PASSED','proof_sha256':'5'*64} for c in self.criteria],
            'verdict':'PASSED','qualification':'ISOLATED_APPLICATION_AND_NATIVE; synthetic embeddings and isolated decisions; not human QA approval'}
    def bundle(self,body=None):
        text=canonical(self.body if body is None else body)
        return {'document':text,'signature':hmac.new(self.key,DOMAIN+text.encode(),hashlib.sha256).hexdigest()}
    def check(self,bundle=None,item=None,sources=None):
        return validate(self.bundle() if bundle is None else bundle,self.key,self.item if item is None else item,
            self.sources if sources is None else sources)
    def test_exact_current_source_and_build_proof_is_not_a_human_review(self):
        got=self.check();self.assertEqual(got,self.body);self.assertNotIn('approved',got)
        self.assertEqual(criteria(self.item),self.criteria)
    def test_tampered_signature_payload_and_noncanonical_json_are_rejected(self):
        b=self.bundle();b['signature']='0'*64
        with self.assertRaisesRegex(ValueError,'SIGNATURE'):self.check(b)
        b=self.bundle();b['document']+=' '
        b['signature']=hmac.new(self.key,DOMAIN+b['document'].encode(),hashlib.sha256).hexdigest()
        with self.assertRaisesRegex(ValueError,'CANONICAL'):self.check(b)
    def test_native_version_description_and_project_drift_fail_closed(self):
        for change in [{'lockVersion':5},{'description':{'raw':self.item['description']['raw']+' changed'}},
                {'_links':{**self.item['_links'],'project':{'href':'/api/v3/projects/1'}}}]:
            item={**self.item,**change}
            with self.assertRaises(ValueError):self.check(item=item)
    def test_source_code_drift_and_unknown_source_paths_are_rejected(self):
        current=copy.deepcopy(self.sources);current['gateway'][GATEWAY_SOURCES[0]]='6'*64
        with self.assertRaisesRegex(ValueError,'CODE_CHANGED'):self.check(sources=current)
        body=copy.deepcopy(self.body);body['sources']['core']['../../private']='7'*64
        with self.assertRaisesRegex(ValueError,'SOURCE'):self.check(self.bundle(body))
    def test_wrong_actor_producer_and_claimed_approval_are_never_authority(self):
        for change in [{'actor':19},{'producer':'caller-verified-pass'},{'approved':True},{'owner':True}]:
            with self.assertRaises(ValueError):self.check(self.bundle({**self.body,**change}))
    def test_missing_duplicate_or_fabricated_criteria_and_test_references_fail(self):
        for mutate in [lambda b:b['tests'].pop(),lambda b:b['tests'].append(copy.deepcopy(b['tests'][0])),
                lambda b:b['criteria'].update(AC5='Unverified extra assertion')]:
            body=copy.deepcopy(self.body);mutate(body)
            with self.assertRaises(ValueError):self.check(self.bundle(body))
    def test_failed_tests_remain_failed_and_retest_uses_a_new_proof(self):
        body=copy.deepcopy(self.body);body['tests'][0]['outcome']='FAILED'
        with self.assertRaisesRegex(ValueError,'VERDICT'):self.check(self.bundle(body))
        body['verdict']='FAILED';self.assertEqual(self.check(self.bundle(body))['verdict'],'FAILED')
        body=copy.deepcopy(self.body);body['id']=str(uuid.uuid4());self.assertNotEqual(self.check(self.bundle(body))['id'],self.body['id'])
    def test_malformed_test_types_and_utf8_byte_limits_fail_closed(self):
        for field, value in [('criterion_id', []), ('outcome', {}), ('actual', 'ệ'*2000)]:
            body=copy.deepcopy(self.body);body['tests'][0][field]=value
            with self.assertRaises(ValueError):self.check(self.bundle(body))

    def test_invalid_timestamp_hash_and_oversized_proof_are_rejected(self):
        for change in [{'finished_at':time.time()+1000},{'started_at':float('nan')},{'build':{'gateway':'mutable:latest','core':'sha256:'+'4'*64}}]:
            with self.assertRaises(ValueError):self.check(self.bundle({**self.body,**change}))
        body=copy.deepcopy(self.body);body['tests'][0]['actual']='x'*1048576
        with self.assertRaises(ValueError):self.check(self.bundle(body))

if __name__=='__main__':unittest.main()
