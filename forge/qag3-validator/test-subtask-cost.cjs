const assert = require('node:assert/strict');
const fs = require('node:fs');
const yaml = require('../../tools/forge-cli/node_modules/@forge/cli/node_modules/yaml');
const before = yaml.parse(fs.readFileSync(`${__dirname}/manifest.before-subtask-cost-2026-10-13.yml`, 'utf8'));
const candidate = yaml.parse(fs.readFileSync(`${__dirname}/manifest.subtask-history-candidate.yml`, 'utf8'));
const changed = ['qag3-subtask-acceptance','qag3-qa-freshness'];
assert.equal(candidate.modules['jira:workflowValidator'].length,11);
assert.deepEqual(candidate.modules['jira:workflowValidator'].filter(m=>!changed.includes(m.key)),
  before.modules['jira:workflowValidator'].filter(m=>!changed.includes(m.key)));
assert.deepEqual(candidate.app,before.app);
assert.equal(candidate.permissions,undefined);
assert.equal(candidate.modules.function,undefined);
// Task branch is byte-for-byte the deployed expression inside its function wrapper.
const oldTask = before.modules['jira:workflowValidator'].find(m=>m.key==='qag3-qa-freshness').expression;
const split = oldTask.lastIndexOf('; ');
const body = oldTask.slice(0,split)+'; return '+oldTask.slice(split+2)+';';
const newGate = candidate.modules['jira:workflowValidator'].find(m=>m.key==='qag3-qa-freshness').expression;
assert(newGate.includes('let taskGate = ignored => {'+body+'}'));
process.env.QAG3_VALIDATOR_MANIFEST = `${__dirname}/manifest.subtask-history-candidate.yml`;
require('./test.cjs');
console.log('PASS: conjunction fixtures; nine modules/app/scopes unchanged; Task companion branch preserved. Local checks, not deployment/E2E proof.');
