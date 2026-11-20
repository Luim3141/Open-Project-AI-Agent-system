'use strict';

// Run in the n8n candidate image with --network none; these markers are synthetic.
const assert = require('node:assert/strict');
const flatted = require(require.resolve('flatted', {paths: ['/usr/local/lib/node_modules/n8n']}));
const {redactBundle} = require('/opt/qldapm/n8n_storage_redaction.js');
const markers = {header: 'SYNTHETIC_HEADER_X', nested: 'SYNTHETIC_NESTED_X', free_text: 'SYNTHETIC_FREE_TEXT_X'};
const input = {headers: {authorization: 'Bearer ' + markers.header},
  nested: {message: markers.nested}, text: 'context ' + markers.free_text};
const stored = JSON.stringify(redactBundle({data: flatted.stringify(input)}, flatted));
const leaked = Object.fromEntries(Object.entries(markers).map(([key, value]) => [key, stored.includes(value)]));
assert.deepEqual(leaked, {header: false, nested: true, free_text: true});
console.log(JSON.stringify({marker_source: 'synthetic', leaked}));
