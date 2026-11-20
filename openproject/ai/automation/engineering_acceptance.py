"""Independent AC suite, deployed root-owned outside the writable repository."""
from fastapi.testclient import TestClient
from task_manager.app import create_app


def test_ac1_create_and_ac2_stable_list(tmp_path):
    with TestClient(create_app(str(tmp_path/'tasks.sqlite'))) as client:
        assert client.get('/tasks').json()==[]
        first=client.post('/tasks',json={'title':'First'})
        assert first.status_code==201
        item=first.json()
        assert type(item['id']) is int and item['id']>0
        assert item['title']=='First' and item['status']=='todo'
        second=client.post('/tasks',json={'title':'Second'})
        assert second.status_code==201
        assert client.get('/tasks').json()==[item,second.json()]


def test_ac3_persistence_across_app_reopen(tmp_path):
    database=str(tmp_path/'persist.sqlite')
    with TestClient(create_app(database)) as client:
        item=client.post('/tasks',json={'title':'Durable'}).json()
    with TestClient(create_app(database)) as client:
        assert client.get('/tasks').json()==[item]


def test_ac4_validation_and_sql_as_data(tmp_path):
    with TestClient(create_app(str(tmp_path/'safe.sqlite'))) as client:
        for value in ['', '   ', '\t\n']:
            assert client.post('/tasks',json={'title':value}).status_code==422
        for payload in [{},{'title':None},{'title':17}]:
            assert client.post('/tasks',json=payload).status_code==422
        title="x'); DROP TABLE tasks; --"
        assert client.post('/tasks',json={'title':title}).status_code==201
        assert client.get('/tasks').json()[0]['title']==title
