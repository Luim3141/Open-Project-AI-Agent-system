const assert = require('node:assert/strict');
const flatted = require(require.resolve('flatted', {paths: ['/usr/local/lib/node_modules/n8n']}));
const {redactBundle} = require('/opt/qldapm/n8n_storage_redaction.js');
const secret = 'synthetic-canary-only';
const input = {headers: {Authorization: 'Bearer ' + secret, 'X-QLDAPM-Webhook-Token': secret,
  Cookie: secret}, status: 'READY', correlation_id: 'kept'};
input.self = input;
input.headerParameters = {parameters: [{name: 'X-QLDAPM-Webhook-Token', value: secret},
  {name: 'Authorization', value: 'Basic ' + secret}, {name: 'Accept', value: 'application/json'}]};
input.error = 'Request failed: Basic ' + secret;
const payload = {data: flatted.stringify(input), workflowData: {nodes: [input.headerParameters], metadata: {signature: secret}}};
const result = redactBundle(payload, flatted);
assert.ok(!JSON.stringify(result).includes(secret));
assert.equal(input.headers.Authorization, 'Bearer ' + secret);
assert.ok(payload.data.includes(secret));
const parsed = flatted.parse(result.data);
assert.equal(parsed.status, 'READY');
assert.equal(parsed.correlation_id, 'kept');
assert.equal(parsed.self, parsed);
assert.equal(parsed.headerParameters.parameters[2].value, 'application/json');
assert.equal(input.headerParameters.parameters[0].value, secret);
assert.throws(() => redactBundle({data: '{invalid'}, flatted), /REDACTION_FAILED/);
console.log('PASS storage-only redaction: headers/signature, cycles, metadata, original immutable, malformed fail-closed');
