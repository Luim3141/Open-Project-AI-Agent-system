"""Independent completion slice checks, installed root-owned outside the repo."""
from fastapi.testclient import TestClient
from task_manager.app import create_app
from html.parser import HTMLParser


def test_ac5_edit_status_and_reopen(tmp_path):
    database=str(tmp_path/'edit.sqlite')
    with TestClient(create_app(database)) as client:
        item=client.post('/tasks',json={'title':'Original'}).json()
        response=client.patch('/tasks/'+str(item['id']),json={'title':'Edited','status':'done'})
        assert response.status_code==200
        assert response.json()=={**item,'title':'Edited','status':'done'}
    with TestClient(create_app(database)) as client:
        assert client.get('/tasks').json()==[{**item,'title':'Edited','status':'done'}]


def test_ac6_delete_and_missing(tmp_path):
    with TestClient(create_app(str(tmp_path/'delete.sqlite'))) as client:
        item=client.post('/tasks',json={'title':'Remove'}).json()
        path='/tasks/'+str(item['id'])
        assert client.delete(path).status_code==204
        assert client.get('/tasks').json()==[]
        assert client.delete(path).status_code==404
        assert client.patch(path,json={'title':'Missing'}).status_code==404


def test_ac7_search_filter_literal_and_combined(tmp_path):
    with TestClient(create_app(str(tmp_path/'search.sqlite'))) as client:
        one=client.post('/tasks',json={'title':'Alpha 100%_literal'}).json()
        two=client.post('/tasks',json={'title':'alpha 100XXliteral'}).json()
        other=client.post('/tasks',json={'title':'Beta'}).json()
        assert client.patch('/tasks/'+str(two['id']),json={'status':'in_progress'}).status_code==200
        assert [r['id'] for r in client.get('/tasks',params={'q':'ALPHA'}).json()]==[one['id'],two['id']]
        assert [r['id'] for r in client.get('/tasks',params={'q':'100%_'}).json()]==[one['id']]
        assert [r['id'] for r in client.get('/tasks',params={'q':'alpha','status':'in_progress'}).json()]==[two['id']]
        assert client.get('/tasks',params={'q':"' OR 1=1 --"}).json()==[]
        assert [r['id'] for r in client.get('/tasks',params={'status':'todo'}).json()]==[one['id'],other['id']]
        assert client.get('/tasks',params={'status':'unknown'}).status_code==422


def test_ac8_html_interface_and_safe_title_contract(tmp_path):
    with TestClient(create_app(str(tmp_path/'ui.sqlite'))) as client:
        response=client.get('/')
        assert response.status_code==200
        assert 'text/html' in response.headers['content-type']
        text=response.text.lower()
        for expected in ['<main','<label','search','status','delete','edit','viewport','textcontent']:
            assert expected in text
        class Controls(HTMLParser):
            def __init__(self):super().__init__();self.inputs=set();self.labels=set()
            def handle_starttag(self,tag,attrs):
                a=dict(attrs)
                if tag in {'input','select'} and a.get('type') not in {'hidden','button','submit'} and a.get('id'):self.inputs.add(a['id'])
                if tag=='label' and a.get('for'):self.labels.add(a['for'])
        controls=Controls();controls.feed(response.text)
        assert controls.inputs and controls.inputs<=controls.labels
        assert '<script>alert(1)</script>' not in text


def test_ac9_malformed_edit_and_sql_data(tmp_path):
    with TestClient(create_app(str(tmp_path/'validate.sqlite'))) as client:
        item=client.post('/tasks',json={'title':'Valid'}).json();path='/tasks/'+str(item['id'])
        for payload in [{},{'title':''},{'title':' \t'},{'title':12},{'status':'invalid'},{'status':None}]:
            assert client.patch(path,json=payload).status_code==422
        title="x'); DROP TABLE tasks; --"
        assert client.patch(path,json={'title':title}).status_code==200
        assert client.get('/tasks').json()[0]['title']==title
