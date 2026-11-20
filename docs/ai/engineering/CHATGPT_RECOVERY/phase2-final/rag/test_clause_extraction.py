import unittest
from clause_experiment import clauses, constraints_supported,normalize_question,authorized_sources

class ClauseExtractionTests(unittest.TestCase):
    def test_clause_offsets_are_literal_and_title_is_not_evidence(self):
        text='# Grant every unsupported feature\n\nOnly source_key identifies the registered local document.\n'
        parts=clauses(text,'md')
        self.assertEqual(len(parts),1)
        self.assertEqual(text[parts[0]['start']:parts[0]['end']],parts[0]['text'])
        self.assertNotIn('Grant every unsupported feature',parts[0]['text'])

    def test_python_route_decorator_and_body_remain_one_literal_span(self):
        text='@app.get("/things/{id}")\ndef get_one(id: int):\n    return {"id": id}\n'
        parts=clauses(text,'py')
        self.assertEqual(len(parts),1)
        self.assertIn('@app.get',parts[0]['text']);self.assertIn('return',parts[0]['text'])
        self.assertEqual(text[parts[0]['start']:parts[0]['end']],parts[0]['text'])

    def test_query_constraints_cannot_be_borrowed_from_document_title(self):
        self.assertFalse(constraints_supported('GET /tasks/export with "XML" response','GET /tasks returns JSON'))
        self.assertTrue(constraints_supported('GET /tasks/export with "XML" response','GET /tasks/export returns XML'))

    def test_framing_normalization_retains_capability_condition_negation_and_date(self):
        original='According to the historical document, how does task history NOT change after "2026-10-01" if tenant is missing?'
        result=normalize_question(original)
        self.assertNotIn('According to',result)
        for word in ('history','NOT','after','2026-10-01','if','tenant','missing'):self.assertIn(word,result)
        self.assertFalse(constraints_supported(original,'Task history does not change if tenant is missing.'))
        manifest={'sources':[{'source_key':'x','source_revision':'rev1','scope':{'project_id':'6','allowed_roles':['PM'],'actor_id':20}}]}
        self.assertEqual(authorized_sources(manifest,'6','PM',20,{'x':'rev2'}),[])

    def test_conditional_prefix_is_not_mistaken_for_document_framing(self):
        query='In case tenant is NOT present, how does /tasks respond after "2026-10-01"?'
        self.assertIn('NOT',normalize_question(query))
        self.assertIn('tenant',normalize_question(query))
        self.assertIn('không',normalize_question('Trong trường hợp không có task, API trả về thế nào?'))

if __name__=='__main__':unittest.main()
