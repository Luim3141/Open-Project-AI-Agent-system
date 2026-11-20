"""Two approved WP379 units; shared by Supervisor and host delivery adapter."""
UNIT='create-list-persistence-v1'
EXPANSION='crud-search-web-v1'
UNITS={
    UNIT:{'title':'Create/list tasks + SQLite persistence','acceptance_file':'test_create_list.py',
        'base_unit':None,'base_branch':'main','acceptance':{
            'AC1':'POST /tasks accepts nonblank title, returns201 with id,title,status=todo',
            'AC2':'GET /tasks returns stored tasks, stable id order',
            'AC3':'create_app(database_path) preserves tasks when reopened with same SQLite file',
            'AC4':'blank title is rejected422; SQL text is stored as data'}},
    EXPANSION:{'title':'Edit/delete/status/search and usable web interface','acceptance_file':'test_crud_web.py',
        'base_unit':UNIT,'base_branch':'codex/openclaw-'+UNIT,'acceptance':{
            'AC5':'PATCH /tasks/{id} edits title or status: todo,in_progress,done; persists after reopening',
            'AC6':'DELETE /tasks/{id} returns204; missing edit/delete returns404',
            'AC7':'GET /tasks?q=...&status=... filters by case-insensitive literal title substring and valid status; combined filters use AND; ordered ids',
            'AC8':'GET / returns self-contained HTML (inline CSS/JS) web UI: create/list/edit/delete/status/search/filter; viewport, main, labels, DOM textContent for task titles, keyboard controls and visible errors',
            'AC9':'Blank edit, empty PATCH, invalid status and malformed input return422; SQL text remains data; original AC1-4 regression passes'}}
}
