'use strict';
const assert = require('node:assert/strict');
const {ExecutionPersistence} = require('/usr/local/lib/node_modules/n8n/dist/executions/execution-persistence.js');
const canary = 'synthetic-overwrite-canary';

(async () => {
  for (const mode of ['db', 'filesystem']) {
    let saved;
    const tx = {update: async () => ({affected: 1})};
    const repo = {manager: {transaction: async fn => fn(tx)}};
    const store = {overwrite: async (ref, bundle) => { saved = bundle; return 1; },
      write: async (ref, bundle) => { saved = bundle; return 1; }};
    const persistence = new ExecutionPersistence(repo, null, store, store, null, null, {}, null, {emit() {}});
    const data = {resultData: {runData: {Trigger: [{data: {main: [[{json: {headers: {
      authorization: 'Bearer ' + canary, 'x-qldapm-webhook-token': canary}}}]]}}]}}};
    const workflowData = {id: 'fixture', nodes: [{parameters: {headerParameters: {parameters: [
      {name: 'X-QLDAPM-Webhook-Token', value: canary}]}}}]};
    await persistence.applyDataUpdate({workflowId: 'fixture', executionId: '1'}, mode, 'version',
      {data, workflowData}, undefined);
    assert.equal(JSON.stringify(saved).includes(canary), false, mode + ' full overwrite leaked');
    assert.equal(data.resultData.runData.Trigger[0].data.main[0][0].json.headers['x-qldapm-webhook-token'], canary);
  }
  console.log('PASS execution full overwrite redacts database and filesystem storage copies');
})().catch(error => { console.error(error); process.exitCode = 1; });
