"""Gateway API seam with isolated SQLite/vector fixture; no Main source or filesystem root."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gateway.service import Service
from gateway.store import Store
from tests.test_rag_recovery import VectorFixture


class AllowlistedFileKnowledgeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        corpus = self.root/'corpus';corpus.mkdir()
        self.path = corpus/'contract.md'
        self.path.write_text('# Workflow contract\nLocal workflow citation with verified provenance.',encoding='utf-8')
        self.store = Store(self.root/'state')
        self.pm = self.store.issue_token(7,'PM','PM')
        self.ba = self.store.issue_token(8,'BA','BA')
        self.be = self.store.issue_token(9,'BE','BE')
        self.owner = self.store.issue_token(18,'AI_SYSTEM_OWNER','AI_SYSTEM_OWNER')
        self.source = {'project_id':5,'root':str(corpus),'path':str(self.path),
            'sha256':hashlib.sha256(self.path.read_bytes()).hexdigest(),'allowed_roles':['PM','BA']}
        class Native:
            def __init__(self,url,credential,project):self.role=credential
            def identity(self,actor):return {'user_id':actor,'role':self.role,
                'capabilities':['AI_SYSTEM_OWNER'] if actor==18 else []}
        self.service = Service(self.store,{'project_id':5,'users':{'7':'PM','8':'BA','9':'BE','18':'AI_SYSTEM_OWNER'},
            'gateway_mode':'native','openproject_url':'http://127.0.0.1:8088',
            'file_sources':{'workflow-contract':self.source}},self.root/'workspace',Native)
        self.vector = VectorFixture()
        self.addCleanup(patch.stopall)
        patch('gateway.vector_client.VectorClient',return_value=self.vector).start()

    def call(self,token,action,args,key=None):
        return self.service.execute(token,{'action':action,'arguments':args,'idempotency_key':key})['result']

    def test_real_document_ingestion_search_citation_and_readback_are_bound_to_server_source(self):
        result=self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'file-ingest-1')
        self.assertTrue(result['vector_indexed'])
        self.assertEqual(result['source_id'],'file:workflow-contract')
        search=self.call(self.ba,'knowledge_file_search',{'source_key':'workflow-contract','query':'workflow citation'})
        self.assertEqual(len(search['items']),1)
        citation=search['items'][0]
        self.assertEqual(citation['source_sha256'],self.source['sha256'])
        self.assertTrue(citation['citation'].startswith('file:workflow-contract#sha256='))
        read=self.call(self.ba,'knowledge_file_read',{'source_key':'workflow-contract','document_id':citation['document_id']})
        self.assertIn('verified provenance',read['content'])
        self.assertEqual(read['document_id'],result['document_id'])
        self.assertNotIn(str(self.root),str(search))

    def test_role_and_project_policy_apply_before_cached_receipts_or_file_reads(self):
        for token in (self.ba,self.be):
            with self.assertRaises(PermissionError):
                self.call(token,'knowledge_file_ingest',{'source_key':'workflow-contract'},'not-manager')
        with self.assertRaises(PermissionError):
            self.call(self.be,'knowledge_file_search',{'source_key':'workflow-contract','query':'workflow'})
        self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'cached-file')
        self.source['allowed_roles']=['BA']
        with self.assertRaises(PermissionError):
            self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'cached-file')
        self.source['project_id']=3
        with self.assertRaises(PermissionError):
            self.call(self.ba,'knowledge_file_search',{'source_key':'workflow-contract','query':'workflow'})

    def test_no_client_paths_forged_claims_or_unknown_sources(self):
        for extra in ({'path':str(self.path)},{'file_path':str(self.path)},{'content':'unsafe'},
                      {'actor_id':7},{'role':'PM'},{'project_id':5},{'approved':True}):
            with self.subTest(extra=extra),self.assertRaisesRegex(ValueError,'INVALID_ARGUMENTS'):
                self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract',**extra},'bad-input')
        with self.assertRaises(PermissionError):
            self.call(self.pm,'knowledge_file_search',{'source_key':'not-registered','query':'workflow'})
        self.source['path']=str(self.root/'outside.md')
        with self.assertRaisesRegex(PermissionError,'FILE_SOURCE_PATH_DENIED'):
            self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'outside')

    def test_changed_source_and_old_citation_are_not_returned_as_current(self):
        first=self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'revision-1')
        self.path.write_text('# Revised contract\nReplacement workflow citation.',encoding='utf-8')
        from gateway.native import NativeError
        with self.assertRaisesRegex(NativeError,'FILE_SOURCE_CHECKSUM_CHANGED'):
            self.call(self.ba,'knowledge_file_search',{'source_key':'workflow-contract','query':'workflow'})
        self.source['sha256']=hashlib.sha256(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(NativeError,'FILE_REVISION_CHANGED_USE_NEW_REQUEST_KEY'):
            self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'revision-1')
        second=self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'revision-2')
        self.assertNotEqual(first['document_id'],second['document_id'])
        with self.assertRaisesRegex(NativeError,'FILE_DOCUMENT_REVISION_CHANGED'):
            self.call(self.ba,'knowledge_file_read',{'source_key':'workflow-contract','document_id':first['document_id']})
        self.assertEqual({p['payload']['document_id'] for p in self.vector.points.values()},{second['document_id']})

    def test_vector_failure_retries_same_key_without_claiming_success(self):
        from gateway.native import NativeError
        self.vector.fail_upsert=True
        with self.assertRaisesRegex(NativeError,'FILE_VECTOR_INDEX_PENDING'):
            self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'vector-retry')
        self.vector.fail_upsert=False
        repaired=self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'vector-retry')
        self.assertTrue(repaired['vector_indexed'])
        self.assertEqual(self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'vector-retry'),repaired)

    def test_bounded_parser_and_dense_results_reject_unregistered_points(self):
        self.path.write_bytes(b'x'*262145)
        self.source['sha256']=hashlib.sha256(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError,'FILE_SIZE_LIMIT'):
            self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'oversized')
        self.path.write_text('Workflow citation safe document.',encoding='utf-8')
        self.source['sha256']=hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'bounded')
        import copy
        payload=copy.deepcopy(next(iter(self.vector.points.values()))['payload']);payload['document_id']='unmatched'
        self.vector.hits=[{'payload':payload,'score':0.99}]
        search=self.call(self.ba,'knowledge_file_search',{'source_key':'workflow-contract','query':'unrelated zebra'})
        self.assertEqual(search['items'],[])

    def test_owner_can_index_and_read_without_becoming_pm_or_overriding_source_identity(self):
        self.source['allowed_roles']=['BA']
        result=self.call(self.owner,'knowledge_file_ingest',{'source_key':'workflow-contract'},'owner-file')
        self.assertTrue(result['vector_indexed'])
        read=self.call(self.owner,'knowledge_file_read',{'source_key':'workflow-contract','document_id':result['document_id']})
        self.assertEqual(read['source_sha256'],self.source['sha256'])
        self.assertEqual(self.service.native_actor(18)[1]['role'],'AI_SYSTEM_OWNER')

    def test_docx_parser_and_archive_size_limit_are_enforced(self):
        import zipfile
        self.path=self.path.with_suffix('.docx');self.source['path']=str(self.path)
        with zipfile.ZipFile(self.path,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('word/document.xml','<document><p><t>Workflow citation DOCX contract.</t></p></document>')
        self.source['sha256']=hashlib.sha256(self.path.read_bytes()).hexdigest()
        first=self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'docx-file')
        self.assertTrue(first['vector_indexed'])
        with zipfile.ZipFile(self.path,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('word/document.xml',b'x'*8388609)
        self.source['sha256']=hashlib.sha256(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError,'FILE_ARCHIVE_SIZE_LIMIT'):
            self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'docx-bomb')

    def pdf(self, text='Workflow citation PDF contract.', pages=1, encrypted=False):
        from pypdf import PdfWriter
        from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
        self.path=self.path.with_suffix('.pdf');self.source['path']=str(self.path)
        writer=PdfWriter()
        for _ in range(pages):
            page=writer.add_blank_page(width=612,height=792)
            font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
            page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
            stream=DecodedStreamObject();stream.set_data(('BT /F1 12 Tf 72 720 Td ('+text+') Tj ET').encode())
            page[NameObject('/Contents')]=writer._add_object(stream)
        if encrypted:writer.encrypt('isolated-test')
        writer.write(self.path)
        self.source['sha256']=hashlib.sha256(self.path.read_bytes()).hexdigest()

    def test_pdf_pinned_source_ingests_all_pages_and_preserves_revision_acl(self):
        self.pdf(pages=2)
        receipt=self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'pdf-fixture')
        self.assertTrue(receipt['vector_indexed'])
        read=self.call(self.ba,'knowledge_file_read',{'source_key':'workflow-contract','document_id':receipt['document_id']})
        self.assertEqual(read['content'].count('Workflow citation PDF contract.'),2)
        self.assertEqual(read['source_sha256'],self.source['sha256'])
        with self.assertRaisesRegex(PermissionError,'FILE_SOURCE_ROLE_DENIED'):
            self.call(self.be,'knowledge_file_search',{'source_key':'workflow-contract','query':'PDF'})

    def test_pdf_corrupt_encrypted_empty_and_large_stream_fail_without_partial_ingest(self):
        for label,options in [('empty',{'text':''}),('encrypted',{'encrypted':True}),('stream',{'text':'x'*1048577})]:
            with self.subTest(label=label):
                self.pdf(**options)
                # Compress only the stream so the input fits the independent 256KiB source bound.
                if label=='stream':
                    from pypdf import PdfReader,PdfWriter
                    writer=PdfWriter(clone_from=PdfReader(self.path));writer.pages[0].compress_content_streams();writer.write(self.path)
                    self.source['sha256']=hashlib.sha256(self.path.read_bytes()).hexdigest()
                with self.assertRaisesRegex(ValueError,'PDF_'):
                    self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'pdf-'+label)
        self.path.write_bytes(b'%PDF-1.7\nmalformed');self.source['sha256']=hashlib.sha256(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError,'PDF_'):
            self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'pdf-corrupt')
        self.assertEqual(self.vector.points,{})

    def test_pdf_parser_timeout_is_reported_without_logging_parser_input(self):
        import subprocess
        from gateway.local_loaders import extract_pdf_text
        self.pdf()
        with patch('gateway.local_loaders.subprocess.run',side_effect=subprocess.TimeoutExpired('pdf',15)):
            with self.assertRaisesRegex(ValueError,'PDF_PARSE_TIMEOUT'):
                extract_pdf_text(self.path)

    def test_pdf_page_limit_rejects_whole_source_before_ingestion(self):
        self.pdf(pages=65)
        with self.assertRaisesRegex(ValueError,'PDF_PAGE_LIMIT'):
            self.call(self.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'pdf-page-limit')
        self.assertEqual(self.vector.points,{})


if __name__ == '__main__':unittest.main()
