import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from source_spans import extract_spans
from evidence_validation import EvidenceError, validate_response, capture_response, parse_with_reformat,repair_span_reference


class EvidenceValidationTests(unittest.TestCase):
    def fixture(self, source='Không phục hồi lịch sử cũ. Source current.'):
        spans=extract_spans(source);span=spans[0];doc='a'*64
        item={'id':0,'native_id':392,'document_id':doc,'start':span['start'],'end':span['end'],
              'source_sha256':span['source_sha256'],'span_sha256':span['sha256']}
        packet={'case':{'id':'diagnostic:vi'},'spans':[item]}
        response={'matches':[{'native_id':392,'span_id':0,'answer':'Không phục hồi lịch sử cũ.', 'quote':span['raw']}]}
        return packet,{doc:source},{(doc,span['start'],span['end']):span},response

    def rule(self, expected, raw, packet, sources, spans, **kwargs):
        with self.assertRaises(EvidenceError) as raised:validate_response(raw,packet,sources,spans,**kwargs)
        self.assertEqual(raised.exception.rule,expected)
        self.assertNotIn('quote',raised.exception.context)
        return raised.exception

    def test_valid_identity_is_not_semantic_support_and_quote_has_exact_offsets(self):
        packet,sources,spans,response=self.fixture();rows=validate_response(json.dumps(response),packet,sources,spans)
        self.assertEqual(rows[0]['support'],'UNVERIFIED')
        c=rows[0]['citation'];source=sources['a'*64]
        self.assertEqual(source[c['start']:c['end']],response['matches'][0]['quote'])
        self.assertEqual(hashlib.sha256(source[c['start']:c['end']].encode()).hexdigest(),c['sha256'])

    def test_format_failures_are_distinct_and_boolean_ids_are_refused(self):
        p,s,v,r=self.fixture()
        self.rule('MALFORMED_JSON','{"matches":',p,s,v)
        self.rule('DUPLICATE_JSON_KEY','{"matches":[],"matches":[]}',p,s,v)
        self.rule('RESPONSE_SHAPE_INVALID','{"matches":{}}',p,s,v)
        r['matches'][0]['span_id']=True;self.rule('MATCH_SHAPE_INVALID',json.dumps(r),p,s,v)

    def test_missing_and_overlapping_ambiguous_quotes_have_different_rules(self):
        p,s,v,r=self.fixture();r['matches'][0]['quote']='Nội dung không tồn tại'
        e=self.rule('QUOTE_NOT_FOUND',json.dumps(r),p,s,v);self.assertEqual(e.category,'QUOTE')
        p,s,v,r=self.fixture('aaa');r['matches'][0]['quote']='aa';self.rule('QUOTE_AMBIGUOUS',json.dumps(r),p,s,v)

    def test_source_identity_hash_span_offset_and_hash_fail_independently(self):
        p,s,v,r=self.fixture();r['matches'][0]['native_id']=5;self.rule('NATIVE_SOURCE_MISMATCH',json.dumps(r),p,s,v)
        p,s,v,r=self.fixture();self.rule('SOURCE_NOT_FOUND',json.dumps(r),p,{},v)
        s['a'*64]+=' mới';self.rule('SOURCE_HASH_MISMATCH',json.dumps(r),p,s,v)
        p,s,v,r=self.fixture();p['spans'][0]['end']=9999;self.rule('SPAN_OFFSETS_INVALID',json.dumps(r),p,s,v)
        p,s,v,r=self.fixture();p['spans'][0]['span_sha256']='b'*64;self.rule('SPAN_HASH_MISMATCH',json.dumps(r),p,s,v)

    def test_exact_quote_with_wrong_answer_is_rejected_by_separate_support_check(self):
        p,s,v,r=self.fixture();r['matches'][0]['answer']='Có phục hồi toàn bộ lịch sử.'
        self.rule('UNSUPPORTED_ANSWER',json.dumps(r),p,s,v,support_check=lambda row:False)

    def test_wrong_span_can_only_be_repaired_to_unique_exact_quote_in_same_source(self):
        p,s,v,r=self.fixture('Metadata only. Không phục hồi Native history.')
        doc='a'*64;other=extract_spans(s[doc])[1]
        p['spans'].append({'id':1,'native_id':392,'document_id':doc,'start':other['start'],'end':other['end'],'source_sha256':other['source_sha256'],'span_sha256':other['sha256']});v[(doc,other['start'],other['end'])]=other
        r['matches'][0]['quote']=other['raw'];raw=json.dumps(r)
        e=self.rule('SPAN_REFERENCE_MISMATCH',raw,p,s,v);self.assertEqual(e.context['candidate_span_ids'],[1])
        repaired,audit=repair_span_reference(raw,p,s,v);rows=validate_response(repaired,p,s,v)
        self.assertEqual(rows[0]['match']['span_id'],1);self.assertEqual(rows[0]['support'],'UNVERIFIED')
        self.assertEqual(audit[0]['from_span_id'],0);self.assertEqual(audit[0]['to_span_id'],1)
        self.rule('UNSUPPORTED_ANSWER',repaired,p,s,v,support_check=lambda row:False)

    def test_repair_never_moves_quote_across_source_or_chooses_ambiguous_span(self):
        p,s,v,r=self.fixture('No target quote.');doc='b'*64;source='Other secret source.';other=extract_spans(source)[0]
        s[doc]=source;v[(doc,other['start'],other['end'])]=other;p['spans'].append({'id':1,'native_id':5,'document_id':doc,'start':other['start'],'end':other['end'],'source_sha256':other['source_sha256'],'span_sha256':other['sha256']});r['matches'][0]['quote']=source
        self.rule('QUOTE_SOURCE_MISMATCH',json.dumps(r),p,s,v)
        with self.assertRaises(EvidenceError):repair_span_reference(json.dumps(r),p,s,v)

    def test_repair_refuses_duplicate_quote_spans_and_changed_source_hash(self):
        p,s,v,r=self.fixture('Lead only. Repeated proof. Repeated proof.')
        doc='a'*64
        for index,span in enumerate(extract_spans(s[doc])[1:],1):
            p['spans'].append({'id':index,'native_id':392,'document_id':doc,'start':span['start'],'end':span['end'],
                'source_sha256':span['source_sha256'],'span_sha256':span['sha256']});v[(doc,span['start'],span['end'])]=span
        r['matches'][0]['quote']='Repeated proof.';raw=json.dumps(r)
        self.rule('QUOTE_AMBIGUOUS_ACROSS_SPANS',raw,p,s,v)
        with self.assertRaises(EvidenceError):repair_span_reference(raw,p,s,v)
        p['spans']=p['spans'][:2];p['spans'][1]['span_sha256']='c'*64
        self.rule('QUOTE_NOT_FOUND',raw,p,s,v)

    def test_capture_is_bounded_redacted_and_keeps_original_hash(self):
        response={'message':{'content':json.dumps({'matches':[],'api_key':'not-for-output','quote':'Bearer abcdefghijklmnop ghp_'+'x'*30})}}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'reply.json';meta=capture_response(response,path)
            saved=path.read_text();self.assertNotIn('not-for-output',saved);self.assertNotIn('abcdefghijklmnop',saved);self.assertNotIn('x'*30,saved)
            self.assertEqual(meta['response_sha256'],hashlib.sha256(json.dumps(response,ensure_ascii=False,sort_keys=True).encode()).hexdigest())
            self.assertLessEqual(path.stat().st_size,20000)
            with self.assertRaises(FileExistsError):capture_response(response,path)
            large=Path(directory)/'large.json';capture_response({'text':'\\'*15000},large)
            self.assertLessEqual(large.stat().st_size,20000)

    def test_only_format_failure_may_be_reformatted_once(self):
        p,s,v,r=self.fixture();calls=[];validator=lambda raw:validate_response(raw,p,s,v)
        fixed=parse_with_reformat('{',validator,lambda raw:(calls.append(raw),json.dumps(r))[1]);self.assertEqual(len(calls),1);self.assertEqual(len(fixed),1)
        r['matches'][0]['quote']='Absent';calls=[]
        with self.assertRaises(EvidenceError):parse_with_reformat(json.dumps(r),validator,lambda raw:calls.append(raw))
        self.assertEqual(calls,[])
        calls=[]
        with self.assertRaises(EvidenceError):parse_with_reformat('{',validator,lambda raw:(calls.append(raw),'{')[1])
        self.assertEqual(len(calls),1)
