// Existing pinned persistence hooks receive workflow identity even for partial updates.
const fs = require('node:fs');
const path = '/usr/local/lib/node_modules/n8n/dist/executions/execution-persistence.js';
let source = fs.readFileSync(path, 'utf8');
for (const [before, after] of [
  ['.redactBundle(payload, flatted_1);', '.redactBundle(payload, flatted_1, ref.workflowId);'],
  ['.redactBundle(bundle, flatted_1);', '.redactBundle(bundle, flatted_1, ref.workflowId);']
]) {
  if (source.split(before).length !== 2) throw new Error('LIFECYCLE_STORAGE_HOOK_NOT_UNIQUE');
  source = source.replace(before, after);
}
fs.writeFileSync(path, source);
