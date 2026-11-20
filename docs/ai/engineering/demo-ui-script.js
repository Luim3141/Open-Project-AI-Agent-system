
        async function fetchTasks() {
            const q = document.getElementById('search-q').value;
            const status = document.getElementById('filter-status').value;
            let url = '/tasks?';
            if (q) url += `q=${encodeURIComponent(q)}&`;
            if (status) url += `status=${encodeURIComponent(status)}`;
            
            const res = await fetch(url);
            const tasks = await res.json();
            const listEl = document.getElementById('task-list');
            listEl.innerHTML = '';
            tasks.forEach(task => {
                const div = document.createElement('div');
                div.className = 'task-item';
                
                const label = document.createElement('label');
                label.className = 'task-title';
                label.textContent = task.title + ' (' + task.status + ')';
                div.appendChild(label);

                const actions = document.createElement('div');
                actions.className = 'task-actions';

                const statusSelect = document.createElement('select');
                statusSelect.setAttribute('aria-label', 'Task Status');
                ['todo', 'in_progress', 'done'].forEach(st => {
                    const opt = document.createElement('option');
                    opt.value = st;
                    opt.textContent = st;
                    if (st === task.status) opt.selected = true;
                    statusSelect.appendChild(opt);
                });
                statusSelect.onchange = async () => {
                    const r = await fetch(`/tasks/${task.id}`, {
                        method: 'PATCH',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({status: statusSelect.value})
                    });
                    if (!r.ok) showError('Failed to update status');
                    else fetchTasks();
                };
                actions.appendChild(statusSelect);

                const editBtn = document.createElement('button');
                editBtn.textContent = 'Edit';
                editBtn.onclick = async () => {
                    const newTitle = prompt('Edit task title:', task.title);
                    if (newTitle !== null) {
                        const r = await fetch(`/tasks/${task.id}`, {
                            method: 'PATCH',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({title: newTitle})
                        });
                        if (!r.ok) {
                            const err = await r.json();
                            showError(err.detail || 'Failed to edit');
                        } else {
                            fetchTasks();
                        }
                    }
                };
                actions.appendChild(editBtn);

                const delBtn = document.createElement('button');
                delBtn.textContent = 'Delete';
                delBtn.onclick = async () => {
                    const r = await fetch(`/tasks/${task.id}`, {method: 'DELETE'});
                    if (!r.ok) showError('Failed to delete');
                    else fetchTasks();
                };
                actions.appendChild(delBtn);

                div.appendChild(actions);
                listEl.appendChild(div);
            });
        }

        function showError(msg) {
            document.getElementById('error-box').textContent = msg;
        }

        document.getElementById('create-form').onsubmit = async (e) => {
            e.preventDefault();
            showError('');
            const title = document.getElementById('new-title').value;
            const r = await fetch('/tasks', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({title})
            });
            if (!r.ok) {
                const err = await r.json();
                showError(err.detail || 'Failed to create');
            } else {
                document.getElementById('new-title').value = '';
                fetchTasks();
            }
        };

        document.getElementById('search-btn').onclick = fetchTasks;
        fetchTasks();
    