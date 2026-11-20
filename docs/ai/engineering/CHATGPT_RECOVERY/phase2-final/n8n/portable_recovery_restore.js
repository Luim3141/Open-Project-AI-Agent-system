'use strict';
// Portable Linux verifier: raw 32-byte recovery key is delivered exclusively over stdin.
const fs = require('node:fs');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
process.on('uncaughtException', error => {console.log(JSON.stringify({status: 'FAILED', error_type: error.name})); process.exit(1);});
process.umask(0o077);
const magic = Buffer.from('QLDAPM-N8N-RECOVERY-V1\n');
const key = fs.readFileSync(0);
assert.equal(key.length, 32, 'RECOVERY_KEY_LENGTH_INVALID');
assert.equal(process.env.N8N_ENCRYPTION_KEY, undefined, 'DOCKER_SECRET_ENV_DENIED');
const bundle = fs.readFileSync(process.argv[2]);
assert.ok(bundle.subarray(0, magic.length).equals(magic), 'RECOVERY_FORMAT_INVALID');
const nonce = bundle.subarray(magic.length, magic.length + 12);
const ciphertext = bundle.subarray(magic.length + 12, -16);
const tag = bundle.subarray(-16);
function decrypt(bytes, candidateKey = key, aad = magic) {
  const decipher = crypto.createDecipheriv('aes-256-gcm', candidateKey, nonce);
  decipher.setAAD(aad);
  decipher.setAuthTag(tag);
  return Buffer.concat([decipher.update(bytes), decipher.final()]);
}
const tampered = Buffer.from(ciphertext);
tampered[Math.floor(tampered.length / 2)] ^= 1;
assert.throws(() => decrypt(tampered));
assert.throws(() => decrypt(ciphertext, crypto.randomBytes(32)));
assert.throws(() => decrypt(ciphertext, key, Buffer.from('WRONG_SCHEMA')));
const payload = JSON.parse(decrypt(ciphertext));
assert.equal(payload.schema, 'qldapm.n8n.recovery-payload.v1');
const archive = Buffer.from(payload.archive_base64, 'base64');
const envBytes = Buffer.from(payload.environment_base64, 'base64');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
assert.equal(sha(archive), payload.manifest.archive_plaintext_sha256);
assert.equal(sha(envBytes), payload.manifest.environment_plaintext_sha256);
const root = '/tmp/restore';
const home = root + '/.n8n';
fs.mkdirSync(home, {recursive: true, mode: 0o700});
const extracted = cp.spawnSync('tar', ['-C', home, '-xf', '-'], {input: archive, timeout: 30000});
assert.equal(extracted.status, 0, 'CLONE_ARCHIVE_EXTRACT_FAILED');
const preserved = Object.fromEntries(envBytes.toString('utf8').split(/\r?\n/).filter(line => line.includes('='))
  .map(line => {const offset = line.indexOf('='); return [line.slice(0, offset), line.slice(offset + 1)];}));
const config = JSON.parse(fs.readFileSync(home + '/config'));
assert.ok(config.encryptionKey === preserved.N8N_ENCRYPTION_KEY, 'ORIGINAL_KEY_CONFIG_MISMATCH');
assert.ok(config.encryptionKey, 'ORIGINAL_KEY_MISSING');
// n8n reads its original key from config in tmpfs; neither instance nor recovery key is an env/argument.
const env = {...process.env, HOME: root, N8N_USER_FOLDER: root, N8N_DIAGNOSTICS_ENABLED: 'false',
  N8N_VERSION_NOTIFICATIONS_ENABLED: 'false', N8N_LOG_LEVEL: 'error'};
const result = cp.spawnSync('n8n', ['export:credentials', '--all', '--decrypted', '--output=' + root + '/credentials.json'],
  {env, encoding: 'utf8', timeout: 120000, maxBuffer: 20 * 1024 * 1024});
assert.equal(result.status, 0, 'CLONE_CREDENTIAL_EXPORT_FAILED');
const credentials = JSON.parse(fs.readFileSync(root + '/credentials.json'));
assert.equal(credentials.length, 4, 'CLONE_CREDENTIAL_COUNT_CHANGED');
assert.ok(credentials.every(credential => credential.data && typeof credential.data === 'object'));
const sqlite = require(require.resolve('sqlite3', {paths: ['/usr/local/lib/node_modules/n8n']}));
const db = new sqlite.Database(home + '/database.sqlite');
const query = sql => new Promise((resolve, reject) => db.all(sql, (error, rows) => error ? reject(error) : resolve(rows)));
(async () => {
  const report = {status: 'PORTABLE_LINUX_RESTORE_VERIFIED_OLD_KEY_ONLY', node_version: process.version,
    schema: payload.schema, original_bytes_match_manifest: true, aes_gcm_tag_verified: true,
    tampered_ciphertext_rejected: true, wrong_key_rejected: true, wrong_aad_rejected: true,
    recovery_key_transport: 'stdin_only_32_raw_bytes', n8n_key_transport: 'original_config_inside_tmpfs_only',
    no_dpapi_in_container: true, decrypted_credentials: credentials.length,
    integrity: (await query('PRAGMA integrity_check'))[0].integrity_check,
    workflows: (await query('SELECT count(*) total,sum(active) active FROM workflow_entity'))[0],
    published: (await query('SELECT count(*) n FROM workflow_entity w JOIN workflow_history h ON h.versionId=w.activeVersionId AND h.workflowId=w.id WHERE w.active=1'))[0].n,
    workflow_sharing: (await query('SELECT count(*) n FROM shared_workflow s JOIN workflow_entity w ON w.id=s.workflowId JOIN project p ON p.id=s.projectId'))[0].n,
    credential_sharing: (await query('SELECT count(*) n FROM shared_credentials s JOIN credentials_entity c ON c.id=s.credentialsId JOIN project p ON p.id=s.projectId'))[0].n,
    owners: (await query("SELECT count(*) n FROM user WHERE roleSlug='global:owner'"))[0].n,
    n8n_version: cp.spawnSync('n8n', ['--version'], {env, encoding: 'utf8', timeout: 30000}).stdout.trim(),
    n8n_export_command_sha256: sha(fs.readFileSync('/usr/local/lib/node_modules/n8n/dist/commands/export/credentials.js'))};
  assert.equal(report.integrity, 'ok');
  assert.equal(report.workflows.total, 16);
  assert.equal(report.workflows.active, 16);
  assert.equal(report.published, 16);
  assert.equal(report.workflow_sharing, 16);
  assert.equal(report.credential_sharing, 4);
  assert.equal(report.owners, 1);
  db.close();
  console.log(JSON.stringify(report));
})().catch(error => {console.log(JSON.stringify({status: 'FAILED', error_type: error.name})); db.close(); process.exitCode = 1;});
