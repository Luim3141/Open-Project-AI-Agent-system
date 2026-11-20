// Version-locked patch; an upstream code change must fail the image build.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const target = '/usr/local/lib/node_modules/n8n/dist/executions/execution-persistence.js';
let source = fs.readFileSync(target, 'utf8');
if (crypto.createHash('sha256').update(source).digest('hex') !== '3ea676961011dd574cc13726b2be85f7cc1f64b6ed55c7cde1deed9f4b998454') {
  throw new Error('UNVERIFIED_N8N_STORAGE_VERSION');
}
const marker = '    async writeData(mode, ref, payload, tx) {\n';
if (source.split(marker).length !== 2) throw new Error('STORAGE_HOOK_NOT_UNIQUE');
source = source.replace(marker, marker + "        payload = require('/opt/qldapm/n8n_storage_redaction.js').redactBundle(payload, flatted_1);\n");
const overwrite = "                    return mode === 'db'\n                        ? await this.dbStore.overwrite(ref, bundle, tx)\n                        : await this.jsonStore.write(ref, bundle, mode);";
if (source.split(overwrite).length !== 2) throw new Error('STORAGE_OVERWRITE_HOOK_NOT_UNIQUE');
source = source.replace(overwrite, "                    const redacted = require('/opt/qldapm/n8n_storage_redaction.js').redactBundle(bundle, flatted_1);\n                    return mode === 'db'\n                        ? await this.dbStore.overwrite(ref, redacted, tx)\n                        : await this.jsonStore.write(ref, redacted, mode);");
fs.writeFileSync(target, source);
// Cover the retained legacy DB update API too; it must not bypass the storage boundary.
const repository = path.join(path.dirname(require.resolve('@n8n/db', {paths: ['/usr/local/lib/node_modules/n8n']})), 'repositories/execution.repository.js');
let legacy = fs.readFileSync(repository, 'utf8');
for (const [before, after] of [
  ['executionData.workflowData = workflowData;', "executionData.workflowData = require('/opt/qldapm/n8n_storage_redaction.js').redactBundle({workflowData}, flatted_1).workflowData;"],
  ['executionData.data = (0, flatted_1.stringify)(data);', "executionData.data = require('/opt/qldapm/n8n_storage_redaction.js').redactBundle({data: (0, flatted_1.stringify)(data)}, flatted_1).data;"]
]) {
  if (legacy.split(before).length !== 2) throw new Error('LEGACY_STORAGE_HOOK_NOT_UNIQUE');
  legacy = legacy.replace(before, after);
}
fs.writeFileSync(repository, legacy);
