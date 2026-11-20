const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const yaml = require('../../tools/forge-cli/node_modules/@forge/cli/node_modules/yaml');
const current = yaml.parse(fs.readFileSync(`${__dirname}/manifest.yml`, 'utf8'));
const before = yaml.parse(fs.readFileSync(`${__dirname}/manifest.before-qa-split-2026-10-12.yml`, 'utf8'));
assert.deepEqual(current.modules['jira:workflowValidator'].slice(0, 10).filter(m => !['qag3-qa-current','qag3-subtask-acceptance'].includes(m.key)), before.modules['jira:workflowValidator'].filter(m => !['qag3-qa-current','qag3-subtask-acceptance'].includes(m.key)));
assert.equal(current.modules.function, undefined); assert.equal(current.permissions, undefined);
const gate = current.modules['jira:workflowValidator'].find(module => module.key === 'qag3-qa-freshness');
assert(gate);
const signed = {id:'42', created:42, items:[{fieldId:'status', from:'10018',to:'10012'},{fieldId:'customfield_10045'}]};
function allowed(history, type=10011, status=10012, project={id:10002,key:'QAG3'}, pending={}) {
  let reads=0;
  const issue={key:project.key+'-332',project,issueType:{id:type},...pending};
  const originalIssue={status:{id:status}, getNewestChangelog(field, filter={}) {
    reads++;
    if (!Array.isArray(history)) throw Error('history unavailable');
    return history.find(change => change.items.some(item => item.fieldId === field && Object.entries(filter).every(([key,value]) => item[key] === value))) ?? null;
  }};
  let value=false;
  try {value=vm.runInNewContext(gate.expression,{issue,originalIssue},{timeout:100})===true;} catch {}
  if(type===10010) assert.equal(reads,1); // Subtask branch probes QA status for the current checklist; acceptance owns provenance.
  else assert(reads > 0 && reads <= 6);
  return value;
}
assert(allowed([signed]));
assert(!allowed([])); assert(!allowed(null));
for(const fieldId of ['summary','description','parent','assignee','customfield_10045']) {
  const edit={id:'43',created:43,items:[{fieldId}]};
  assert(!allowed([edit,signed]));
  assert(allowed([signed,{...edit,id:'41',created:41}]));
  assert(!allowed([{...edit,created:42},signed]));
}
for(const to of ['3','10018','10009']) assert(!allowed([{id:'43',created:43,items:[{fieldId:'status',from:'10012',to}]},signed]));
const approved={id:'43',created:43,items:[{fieldId:'status',from:'10012',to:'10019'}]};
assert(allowed([approved,signed],10011,10019)); assert(!allowed([approved,signed],10010,10019));
assert(!allowed([signed],10000)); assert(!allowed([signed],10011,3));
assert(!allowed([signed],10011,10012,{id:10001,key:'KAN'}));
assert(!allowed([signed],10011,10012,{id:10002,key:'SAM1'}));
assert(!allowed([signed],10011,10012,undefined,{parent:{id:99}}));
assert(!allowed([signed],10011,10012,undefined,{assignee:{accountId:'changed'}}));
assert(allowed([signed,...Array.from({length:1000},(_,i)=>({id:String(i),created:0,items:[{fieldId:'priority'}]}))]));
console.log('PASS: eight other original baseline modules unchanged; Task freshness stale/edit/rework/empty/cross-project/long-history cases; Subtask conjunction covered separately; no new scopes/functions. Not Jira E2E.');
