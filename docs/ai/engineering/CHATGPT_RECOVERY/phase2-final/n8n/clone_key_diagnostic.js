'use strict';
// Clone-only: stdin contains protected archive environment; output is aggregate metadata.
const fs = require('node:fs');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const root = '/tmp/restore';
const home = root + '/.n8n';
const env = {...process.env, ...input.env, HOME: root, N8N_USER_FOLDER: root,
  N8N_DIAGNOSTICS_ENABLED: 'false', N8N_VERSION_NOTIFICATIONS_ENABLED: 'false',
  N8N_TEMPLATES_ENABLED: 'false', N8N_LOG_LEVEL: 'info'};
const sqlite = require(require.resolve('sqlite3', {paths: ['/usr/local/lib/node_modules/n8n']}));
const {Cipher} = require('/usr/local/lib/node_modules/n8n/node_modules/n8n-core/dist/encryption/cipher.js');
const db = new sqlite.Database(home + '/database.sqlite');
const query = sql => new Promise((resolve, reject) => db.all(sql, (error, rows) => error ? reject(error) : resolve(rows)));
const close = () => new Promise((resolve, reject) => db.close(error => error ? reject(error) : resolve()));
const canonical = value => Array.isArray(value) ? value.map(canonical) : value && typeof value === 'object'
  ? Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])])) : value;
function run(args, runtimeEnv = env) {
  const result = cp.spawnSync('n8n', args, {env: runtimeEnv, encoding: 'utf8', timeout: 120000, maxBuffer: 20 * 1024 * 1024});
  return {exit: result.status, text: result.stdout + '\n' + result.stderr};
}
function exportPlain(path, runtimeEnv = env) {
  // A successful exit code alone is insufficient: the vendor catch() logs and may return zero.
  const result = run(['export:credentials', '--all', '--decrypted', '--output=' + path], runtimeEnv);
  let credentials = null;
  if (result.exit === 0 && fs.existsSync(path)) credentials = JSON.parse(fs.readFileSync(path));
  return {exit: result.exit, credentials, decrypt_error: /decrypt|authenticate data/i.test(result.text)};
}
function canUnwrap(rows, key) {
  const cipher = new Cipher({encryptionKey: key}, {});
  return rows.filter(row => {try {cipher.decryptDEKWithInstanceKey(row.value); return true;} catch {return false;}}).length;
}
async function serverRestartProbe() {
  let logs = '';
  const server = cp.spawn('n8n', ['start'], {env: {...env, N8N_PORT: '5678',
    N8N_LISTEN_ADDRESS: '127.0.0.1', N8N_LOG_LEVEL: 'info'}, stdio: ['ignore', 'pipe', 'pipe']});
  server.stdout.on('data', chunk => {logs = (logs + chunk).slice(-1024 * 1024);});
  server.stderr.on('data', chunk => {logs = (logs + chunk).slice(-1024 * 1024);});
  let ready = false;
  try {
    for (let attempt = 0; attempt < 150 && server.exitCode === null; attempt++) {
      try {
        const response = await fetch('http://127.0.0.1:5678/healthz/readiness', {signal: AbortSignal.timeout(500)});
        if (response.status === 200) {ready = true; break;}
      } catch {}
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    if (ready) {
      for (let attempt = 0; attempt < 60 && [...logs.matchAll(/Activated workflow/g)].length < 16 && server.exitCode === null; attempt++) {
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
    // Only localhost exists in --network none; workflow schedules cannot reach external systems.
    return {ready, activated_workflows: [...logs.matchAll(/Activated workflow/g)].length,
      registered_webhooks: (await query('SELECT count(*) n FROM webhook_entity'))[0].n,
      lifecycle_webhook_registered: (await query("SELECT count(*) n FROM webhook_entity WHERE webhookPath='qldapm-lifecycle' AND method='POST'"))[0].n,
      key_bootstrap_error: /cannot be read with this instance encryption key|Encryption key seeding failed/.test(logs)};
  } finally {
    if (server.exitCode === null) {
      server.kill('SIGTERM');
      await Promise.race([new Promise(resolve => server.once('exit', resolve)), new Promise(resolve => setTimeout(resolve, 10000))]);
      if (server.exitCode === null) server.kill('SIGKILL');
    }
  }
}
(async () => {
  const report = {mode: input.mode, n8n_version: run(['--version']).text.trim(), source_sha256: {}};
  for (const path of ['dist/commands/import/credentials.js', 'dist/commands/export/credentials.js',
    'dist/encryption/key-manager.service.js', 'dist/encryption/encryption-bootstrap.service.js',
    'node_modules/n8n-core/dist/encryption/cipher.js', 'dist/executions/execution-persistence.js']) {
    report.source_sha256[path] = crypto.createHash('sha256').update(fs.readFileSync('/usr/local/lib/node_modules/n8n/' + path)).digest('hex');
  }
  report.integrity = (await query('PRAGMA integrity_check'))[0].integrity_check;
  report.workflows = (await query('SELECT count(*) total, sum(active) active FROM workflow_entity'))[0];
  report.published = (await query('SELECT count(*) n FROM workflow_entity w JOIN workflow_history h ON h.versionId=w.activeVersionId AND h.workflowId=w.id WHERE w.active=1'))[0].n;
  report.workflow_sharing = (await query('SELECT count(*) n FROM shared_workflow s JOIN workflow_entity w ON w.id=s.workflowId JOIN project p ON p.id=s.projectId'))[0].n;
  report.credential_sharing = (await query('SELECT count(*) n FROM shared_credentials s JOIN credentials_entity c ON c.id=s.credentialsId JOIN project p ON p.id=s.projectId'))[0].n;
  report.owner_count = (await query("SELECT count(*) n FROM user WHERE roleSlug='global:owner'"))[0].n;
  report.wf04_retention = (await query("SELECT settings FROM workflow_entity WHERE name LIKE 'WF04%'")).map(row => {
    const settings = JSON.parse(row.settings); return Object.fromEntries(['saveDataErrorExecution', 'saveDataSuccessExecution',
      'saveManualExecutions', 'saveExecutionProgress'].map(key => [key, settings[key]]));
  });
  const workflowFingerprint = async () => crypto.createHash('sha256').update(JSON.stringify(canonical(await query('SELECT id,active,activeVersionId,nodes,connections,settings FROM workflow_entity ORDER BY id')))).digest('hex');
  report.workflow_fingerprint_before = await workflowFingerprint();
  const before = exportPlain(root + '/before.json');
  report.old_key_decrypt = {exit: before.exit, count: before.credentials?.length ?? null};
  assert.equal(before.credentials?.length, 4, 'BASELINE_CREDENTIAL_DECRYPT_FAILED');
  const rows = await query("SELECT id,value,algorithm FROM deployment_key WHERE type='data_encryption'");
  assert.ok(rows.length > 0, 'PERSISTED_DEK_EVIDENCE_MISSING');
  report.deployment_keys = {count: rows.length, algorithms: rows.map(row => row.algorithm).sort(), old_key_unwrap_count: canUnwrap(rows, env.N8N_ENCRYPTION_KEY)};
  const credentialCipherBefore = await query('SELECT id,data FROM credentials_entity ORDER BY id');
  if (input.mode === 'same_database_migration') {
    const newKey = crypto.randomBytes(32).toString('hex');
    const configPath = home + '/config';
    const config = JSON.parse(fs.readFileSync(configPath));
    assert.equal(config.encryptionKey, env.N8N_ENCRYPTION_KEY, 'KEY_PRECEDENCE_MISMATCH');
    config.encryptionKey = newKey;
    fs.writeFileSync(configPath, JSON.stringify(config), {mode: 0o600});
    const newEnv = {...env, N8N_ENCRYPTION_KEY: newKey};
    report.deployment_keys.new_key_unwrap_count = canUnwrap(rows, newKey);
    const imported = run(['import:credentials', '--input=' + root + '/before.json'], newEnv);
    const after = exportPlain(root + '/after.json', newEnv);
    const cipherAfter = await query('SELECT id,data FROM credentials_entity ORDER BY id');
    report.migration = {import_exit: imported.exit,
      reported_import_count: Number(imported.text.match(/Successfully imported (\d+)/)?.[1] ?? 0),
      import_error: /An error occurred while importing/.test(imported.text),
      ciphertext_changed: credentialCipherBefore.filter((row, index) => row.data !== cipherAfter[index]?.data).length,
      new_key_decrypt_exit: after.exit, new_key_decrypt_count: after.credentials?.length ?? null,
      new_key_decrypt_error: after.decrypt_error,
      legacy_dek_unchanged: JSON.stringify(rows) === JSON.stringify(await query("SELECT id,value,algorithm FROM deployment_key WHERE type='data_encryption'"))};
    // Direct cryptographic control isolates import encryption from persisted-key lookup.
    const newCipher = new Cipher({encryptionKey: newKey}, {});
    report.migration.direct_new_instance_key_decrypt_count = cipherAfter.filter(row => {
      try {const plain = JSON.parse(newCipher.decryptWithInstanceKey(row.data));
        return JSON.stringify(canonical(plain)) === JSON.stringify(canonical(before.credentials.find(c => c.id === row.id)?.data));
      } catch {return false;}
    }).length;
    assert.equal(report.deployment_keys.old_key_unwrap_count, rows.length);
    assert.equal(report.deployment_keys.new_key_unwrap_count, 0);
    assert.equal(report.migration.direct_new_instance_key_decrypt_count, 4);
    assert.equal(report.migration.new_key_decrypt_count, null);
    assert.equal(report.migration.legacy_dek_unchanged, true);
    report.status = 'ROOT_CAUSE_REPRODUCED_MASTER_KEY_CUTOVER_BLOCKED';
  } else {
    // Separate CLI processes reinitialize the key manager; no inherited in-memory cache.
    const after = exportPlain(root + '/restart.json');
    report.independent_cli_restart = {exit: after.exit, count: after.credentials?.length ?? null,
      credential_data_equal: JSON.stringify(canonical(before.credentials)) === JSON.stringify(canonical(after.credentials))};
    assert.equal(report.independent_cli_restart.credential_data_equal, true);
    report.server_process_restarts = [await serverRestartProbe(), await serverRestartProbe()];
    assert.ok(report.server_process_restarts.every(probe => probe.ready && !probe.key_bootstrap_error));
    const restarted = exportPlain(root + '/after-server-restart.json');
    report.post_server_restart_decrypt = {exit: restarted.exit, count: restarted.credentials?.length ?? null,
      credential_data_equal: JSON.stringify(canonical(before.credentials)) === JSON.stringify(canonical(restarted.credentials))};
    assert.equal(report.post_server_restart_decrypt.credential_data_equal, true);
    report.status = 'RESTORE_ROLLBACK_CREDENTIALS_VERIFIED';
  }
  report.workflow_fingerprint_after = await workflowFingerprint();
  assert.equal(report.workflow_fingerprint_after, report.workflow_fingerprint_before);
  assert.equal(report.integrity, 'ok');
  assert.equal(report.published, 16);
  assert.equal(report.workflow_sharing, 16);
  await close();
  console.log(JSON.stringify(report));
})().catch(async error => {console.log(JSON.stringify({status: 'FAILED', error_type: error.name,
  code: /^SQLITE_[A-Z_]+$/.test(error.code || '') ? error.code : null})); try {await close();} catch {} process.exitCode = 1;});
