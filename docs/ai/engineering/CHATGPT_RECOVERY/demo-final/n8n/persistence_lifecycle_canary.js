'use strict';
// Real vendor persistence + JSON + filesystem stores; only execution-entity transactions are stubbed.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const crypto = require('node:crypto');
const base = '/usr/local/lib/node_modules/n8n';
const resolve = name => require.resolve(name, {paths: [base]});
const {FsByteStore} = require(resolve('@n8n/blob-storage'));
const {ExecutionDataJsonStore} = require(base + '/dist/executions/execution-data/execution-data-json-store.js');
const {ExecutionPersistence} = require(base + '/dist/executions/execution-persistence.js');
const root = fs.mkdtempSync('/tmp/qldapm-fs-canary-');
const marker = {header: 'SYNTHETIC_HEADER_4492', nested: 'SYNTHETIC_NESTED_4492', text: 'SYNTHETIC_TEXT_4492'};
const data = () => ({executionData: {nodeExecutionStack: [{data: {main: [[{json: {nested: {unknown_field: marker.nested}}}]]}}]},
  resultData: {runData: {Trigger: [{data: {main: [[{json: {headers: {authorization: 'Bearer ' + marker.header},
    nested: {unknown_field: marker.nested}, description: 'unrestricted input ' + marker.text}}]]}}]},
    error: {message: 'unrestricted failure ' + marker.text}}});
const workflow = () => ({id: 'elfapV5D2PTnLiHW', versionId: 'synthetic-version', name: 'Canary', nodes: [], connections: {}, settings: {}});
const reporter = {error() {throw new Error('UNEXPECTED_VENDOR_STORE_ERROR');}};
const store = new ExecutionDataJsonStore(new FsByteStore({storagePath: root, reportError: reporter.error}), reporter);
let counter = 0;
const tx = {insert: async () => ({identifiers: [{id: String(++counter)}]}), update: async () => ({affected: 1})};
const repository = {runInTransaction: async (ctx, fn) => fn(tx), manager: {transaction: async fn => fn(tx)}};
const persistence = new ExecutionPersistence(repository, null, store, null, {modeTag: 'fs'}, {}, {}, reporter, {emit() {}});

async function inspect(name, ref) {
  const key = store.options.key(ref);
  const bytes = fs.readFileSync(root + '/' + key);
  const text = bytes.toString('utf8');
  const leaked = Object.fromEntries(Object.entries(marker).map(([field, value]) => [field, text.includes(value)]));
  assert.equal(leaked.header, false, name + ' known auth header must be redacted');
  assert.equal(leaked.nested, false, name + ' nested input must not persist');
  assert.equal(leaked.text, false, name + ' free text must not persist');
  const readBack = await store.read(ref, 'fs');
  assert.ok(readBack.data && readBack.workflowData);
  return {case: name, real_filesystem_bytes: bytes.length, leaked, read_back: true,
    disposition: 'CANONICAL_LIFECYCLE_STORAGE_PASS'};
}

(async () => {
  const results = [];
  for (const status of ['success', 'error']) {
    const executionId = await persistence.create({data: data(), workflowData: workflow(), status, workflowId: 'elfapV5D2PTnLiHW'});
    results.push(await inspect(status + '_create', {workflowId: 'elfapV5D2PTnLiHW', executionId}));
  }
  const retryId = await persistence.create({data: data(), workflowData: workflow(), status: 'new', retryOf: '2', workflowId: 'elfapV5D2PTnLiHW'});
  const ref = {workflowId: 'elfapV5D2PTnLiHW', executionId: retryId};
  results.push(await inspect('retry_create', ref));
  await persistence.applyDataUpdate(ref, 'fs', 'synthetic-version', {data: data(), workflowData: workflow()}, undefined);
  results.push(await inspect('full_overwrite', ref));
  await persistence.applyDataUpdate(ref, 'fs', 'synthetic-version', {data: data()}, undefined);
  results.push(await inspect('partial_data_update', ref));
  await persistence.applyDataUpdate(ref, 'fs', 'synthetic-version', {workflowData: workflow()}, undefined);
  results.push(await inspect('partial_workflow_update', ref));
  const sources = [base + '/dist/executions/execution-persistence.js',
    base + '/dist/executions/execution-data/execution-data-json-store.js',
    resolve('@n8n/blob-storage').replace(/index\.js$/, 'fs-byte-store.js'), '/opt/qldapm/n8n_storage_redaction.js'];
  console.log(JSON.stringify({status: 'CANONICAL_RETENTION_PASS_REAL_FILESYSTEM', results,
    source_sha256: Object.fromEntries(sources.map(path => [path, crypto.createHash('sha256').update(fs.readFileSync(path)).digest('hex')]))}));
})().catch(error => {console.log(JSON.stringify({status: 'PROBE_FAILED', error_type: error.name, diagnostic: error.message})); process.exitCode = 1;});
