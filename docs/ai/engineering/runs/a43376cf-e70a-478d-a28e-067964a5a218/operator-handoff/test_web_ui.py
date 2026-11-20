"""Exercise the actual served script with Node's VM; no browser or extra packages."""
import json
import os
import re
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient
from task_manager.app import create_app


def html(tmp_path):
    with TestClient(create_app(str(tmp_path / 'web.sqlite'))) as client:
        return client.get('/').text


def test_web_ui_html_structure(tmp_path):
    content=html(tmp_path)
    assert '<main>' in content
    assert 'role="alert"' in content and 'aria-live="polite"' in content
    assert 'aria-busy=' in content and 'id="retry-btn"' in content
    assert 'for="new-title"' in content


def test_actual_web_script_async_behaviors(tmp_path):
    node=os.environ.get('NODE_BINARY') or shutil.which('node')
    if not node:pytest.skip('Node needed for JavaScript-only unit checks')
    script=re.search(r'<script>(.*?)</script>',html(tmp_path),re.S).group(1)
    harness=r'''
const vm=require('node:vm'), assert=require('node:assert/strict');
const input=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
class Element {
  constructor(){this.value='';this.children=[];this.disabled=false;this.hidden=false;this.attrs={};this._text='';}
  set textContent(value){this._text=value;this.children=[];}
  get textContent(){return this._text+this.children.map(c=>c.textContent).join('');}
  appendChild(child){this.children.push(child);return child;}
  setAttribute(key,value){this.attrs[key]=value;}
}
const elements=new Map();
const document={getElementById(id){if(!elements.has(id))elements.set(id,new Element());return elements.get(id);},createElement(){return new Element();}};
const response=(data,status=200)=>({ok:status>=200&&status<300,status,json:async()=>data});
const context=vm.createContext({document,AbortController,URLSearchParams,fetch:async()=>response([]),prompt:()=>null});
const flush=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
  vm.runInContext(input.script,context);await flush();await flush();
  assert.equal(typeof context.requestJson,'function');
  assert.match(document.getElementById('list-status').textContent,/No tasks/);
  context.fetch=async()=>{throw Error('offline');};
  await context.fetchTasks();
  assert.match(document.getElementById('error-box').textContent,/Network/);
  assert.equal(document.getElementById('retry-btn').hidden,false);
  assert.equal(document.getElementById('task-list').attrs['aria-busy'],'false');
  context.fetch=async()=>response({detail:[{loc:['body','title'],msg:'field required'}]},422);
  await assert.rejects(context.requestJson('/tasks'),/title: field required/);
  context.fetch=async()=>({ok:false,status:500,json:async()=>{throw Error('html');}});
  await assert.rejects(context.requestJson('/tasks'),/HTTP 500/);
  context.fetch=async()=>({ok:true,status:204,json:async()=>{throw Error('must not parse');}});
  assert.equal(await context.requestJson('/tasks/1',{method:'DELETE'}),null);
  let pending=[];
  context.fetch=()=>new Promise(resolve=>pending.push(resolve));
  document.getElementById('search-q').value='old';const old=context.fetchTasks();
  document.getElementById('search-q').value='new';const newest=context.fetchTasks();
  pending[1](response([{id:2,title:'Newest',status:'todo'}]));await newest;
  pending[0](response([{id:1,title:'Obsolete',status:'todo'}]));await old;
  assert.match(document.getElementById('task-list').textContent,/Newest/);
  assert.doesNotMatch(document.getElementById('task-list').textContent,/Obsolete/);
  let posted=0,resolvePost;
  context.fetch=async(url,options={})=>{
    if(options.method==='POST'){posted++;return new Promise(resolve=>resolvePost=resolve);}
    return response([]);
  };
  document.getElementById('new-title').value='Saved once';
  const event={preventDefault(){}};
  const first=document.getElementById('create-form').onsubmit(event);
  const duplicate=document.getElementById('create-form').onsubmit(event);
  assert.equal(posted,1);assert.equal(document.getElementById('create-submit').disabled,true);
  resolvePost(response({id:3,title:'Saved once',status:'todo'},201));await first;await duplicate;
  assert.equal(document.getElementById('create-submit').disabled,false);
  assert.equal(document.getElementById('new-title').value,'');
  document.getElementById('new-title').value='Keep my input';
  context.fetch=async()=>{throw Error('offline');};
  await document.getElementById('create-form').onsubmit(event);
  assert.equal(document.getElementById('new-title').value,'Keep my input');
  assert.equal(document.getElementById('create-submit').disabled,false);
  assert.match(document.getElementById('error-box').textContent,/Network/);
  context.fetch=async()=>response([{id:4,title:'<img src=x onerror=evil()>',status:'todo'}]);
  await context.fetchTasks();
  assert.match(document.getElementById('task-list').textContent,/<img/);
  console.log('actual script: network/HTTP/validation/204/stale/double-submit/recovery/textContent PASS');
})().catch(error=>{console.error(error);process.exitCode=1;});
'''
    result=subprocess.run([node,'-e',harness],input=json.dumps({'script':script}),text=True,capture_output=True,timeout=20)
    assert result.returncode==0,result.stdout+result.stderr
    assert 'actual script:' in result.stdout
