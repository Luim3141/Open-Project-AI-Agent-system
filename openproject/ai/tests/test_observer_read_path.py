import json,sqlite3,unittest
from unittest.mock import patch
from gateway.agent_observer import execute
from tests.test_agent_observer import ObserverServiceTests

class ReadPathTests(ObserverServiceTests):
    def test_equal_event_timestamps_use_sequence_and_keep_source_order_when_missing(self):
        from gateway.agent_observer import project_task
        from tests.test_agent_observer import ObserverProjectionTests
        fixture=ObserverProjectionTests();monitor=fixture.monitor()
        original=monitor['events'][0]
        monitor['events']=[{**original,'event_id':'tie-b','sequence':2},{**original,'event_id':'tie-a','sequence':1}]
        result=project_task(fixture.package(),6,[monitor],now=1010)
        self.assertEqual([e['event_id'] for e in result['events']],['tie-a','tie-b'])
        for event in monitor['events']:event.pop('sequence',None)
        result=project_task(fixture.package(),6,[monitor],now=1010)
        self.assertEqual([e['event_id'] for e in result['events']],['tie-b','tie-a'])
    def test_run_timestamp_ties_and_missing_timestamps_use_record_order(self):
        from gateway.agent_observer import _rows
        import uuid
        for stamp in [1000,None]:
            identifiers=[str(uuid.uuid4()),str(uuid.uuid4())]
            with self.service.store.connect() as db:
                row=dict(db.execute('SELECT * FROM agent_runs LIMIT 1').fetchone())
                for identifier in identifiers:
                    clone=dict(row);clone['id']=identifier;document=json.loads(clone['document']);document['run_id']=identifier
                    if stamp is None:document.pop('created_at',None)
                    else:document['created_at']=stamp
                    clone['document']=json.dumps(document)
                    db.execute('INSERT INTO agent_runs('+','.join(clone)+') VALUES('+','.join('?' for _ in clone)+')',tuple(clone.values()))
            actual=[r['id'] for r in _rows(self.service,self.who['user_id']) if r['id'] in identifiers]
            self.assertEqual(actual,list(reversed(identifiers)))
    def test_ui_deadline_does_not_shorten_existing_full_bot_contract(self):
        from gateway.observer_reads import read_scope
        budgets=[]
        def scoped(*args,**kwargs):
            budgets.append(kwargs.get('timeout'));return read_scope(*args,**kwargs)
        with patch('gateway.observer_reads.read_scope',side_effect=scoped):
            execute(self.service,self.who,self.native,'observer_task_progress',{'task_id':1,'view':'graph'})
            execute(self.service,self.who,self.native,'observer_active',{'limit':5})
        self.assertEqual(budgets,[8,60])
    def test_legacy_full_list_shares_request_metadata_reader(self):
        from gateway.observer_reads import ReadNative
        original=__import__('gateway.agent_observer',fromlist=['task_progress']).task_progress
        readers=[]
        def task(*args,**kwargs):
            readers.append(kwargs['native']);return original(*args,**kwargs)
        with patch('gateway.agent_observer.task_progress',side_effect=task):execute(self.service,self.who,self.native,'observer_active',{'limit':5})
        self.assertTrue(readers);self.assertTrue(all(isinstance(r,ReadNative) for r in readers));self.assertEqual(len({id(r) for r in readers}),1)
    def test_light_list_does_not_hydrate_task_or_probe_integrations(self):
        with patch('gateway.agent_observer.recorded_monitor',side_effect=AssertionError('heavy monitor')),\
             patch('gateway.agent_observer.system_snapshot',side_effect=AssertionError('health probes')):
            result=execute(self.service,self.who,self.native,'observer_active',{'view':'list','limit':5})
        self.assertEqual(result['items'][0]['task_id'],1)
        self.assertNotIn('artifacts',result['items'][0]);self.assertNotIn('events',result['items'][0])
        self.assertEqual(result['items'][0]['run_count'],1)

    def test_graph_summary_has_actual_edges_and_no_raw_artifacts(self):
        result=execute(self.service,self.who,self.native,'observer_task_progress',{'task_id':1,'view':'graph'})
        self.assertEqual(result['task_id'],1)
        self.assertIn('flow_edges',result)
        self.assertEqual(result['events'],[]);self.assertEqual(result['artifacts'],[])
        self.assertIn('detail_counts',result)
        self.assertLess(len(json.dumps(result)),16000)

    def test_read_scope_reuses_one_connection_and_denies_writes(self):
        from gateway.observer_reads import read_scope
        original=self.service.store
        with read_scope(self.service) as scoped:
            with scoped.store.connect() as first:
                with scoped.store.connect() as second:self.assertIs(first,second)
                with self.assertRaises(sqlite3.OperationalError):first.execute("DELETE FROM agent_runs")
        self.assertIs(self.service.store,original)

    def test_explicit_native_owner_excludes_parent_reference_from_runs(self):
        with self.service.store.connect() as db:
            row=db.execute('SELECT id,payload FROM ai_queue LIMIT 1').fetchone()
            if row is None:
                identifier=db.execute('SELECT id FROM agent_runs LIMIT 1').fetchone()[0]
                db.execute("INSERT INTO ai_queue(id,actor,payload,state,created) VALUES(?,?,'{}','finished',0)",(identifier,self.who['user_id']))
                row=db.execute('SELECT id,payload FROM ai_queue WHERE id=?',(identifier,)).fetchone()
            data=json.loads(row['payload']);data['native_id']=2;db.execute('UPDATE ai_queue SET payload=? WHERE id=?',(json.dumps(data),row['id']))
        from gateway.agent_observer import _rows
        self.assertEqual(_rows(self.service,self.who['user_id'],task_id=1),[])

    def test_malformed_legacy_run_is_unknown_instead_of_failing_other_data(self):
        with self.service.store.connect() as db:db.execute("UPDATE agent_runs SET document='malformed'")
        result=execute(self.service,self.who,self.native,'observer_task_progress',{'task_id':1,'view':'graph'})
        self.assertEqual(result['workflow_status'],'UNKNOWN');self.assertTrue(result['source_conflicts'])

    def test_details_are_paginated_and_task_scoped(self):
        result=execute(self.service,self.who,self.native,'observer_task_progress',{'task_id':1,'view':'details','section':'runs','limit':1})
        self.assertEqual(len(result['items']),1);self.assertEqual(result['task_id'],1)
        with self.assertRaises(PermissionError):execute(self.service,self.who,self.native,'observer_task_progress',{'task_id':999,'view':'details','section':'runs'})

    def test_metadata_miss_and_cross_project_are_fail_closed(self):
        from gateway.observer_reads import ReadNative
        class Fake:
            project_id=6
            def observer_packages(self,ids):return {'project_id':6,'items':[]}
            def package(self,identifier):raise AssertionError('permission bypass fallback')
        reader=ReadNative(Fake());reader.prime([397])
        with self.assertRaises(PermissionError):reader.package(397)
        with patch.object(Fake,'observer_packages',return_value={'project_id':5,'items':[]}):
            with self.assertRaises(ValueError):ReadNative(Fake()).prime([397])

    def test_new_views_reject_invalid_section_limits_and_offsets(self):
        for args in [{'task_id':1,'view':'bogus'},{'task_id':1,'view':'details','section':'secret'},
                     {'task_id':1,'view':'details','section':'events','limit':51},
                     {'task_id':1,'view':'details','section':'events','offset':-1}]:
            with self.assertRaises(ValueError):execute(self.service,self.who,self.native,'observer_task_progress',args)

if __name__=='__main__':unittest.main()
