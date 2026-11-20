// Read-only metadata scan; never print header values or execution bodies.
const sqlite = require(require.resolve('sqlite3', {paths:['/usr/local/lib/node_modules/n8n']}));
const flatted = require(require.resolve('flatted', {paths:['/usr/local/lib/node_modules/n8n']}));
const db = new sqlite.Database('/home/node/.n8n/database.sqlite', sqlite.OPEN_READONLY);
const sensitive = /^(authorization|proxy-authorization|x-qldapm-webhook-token|x-api-key|x-n8n-api-key|cookie|set-cookie|signature)$/i;
const encryptionKey = process.env.N8N_ENCRYPTION_KEY;
db.all("SELECT e.id,e.workflowId,w.name,e.status,e.deletedAt,d.data,d.workflowData FROM execution_entity e JOIN execution_data d ON d.executionId=e.id LEFT JOIN workflow_entity w ON w.id=e.workflowId WHERE CAST(e.id AS INTEGER)>=2886 ORDER BY CAST(e.id AS INTEGER)", (error, rows) => {
  if (error) throw error;
  const summary = {};
  for (const row of rows) {
    const name = row.name || 'unknown';
    const tally = summary[name] ||= {executions:0, sensitive_value_paths:0, bearer_string_paths:0, current_encryption_key_found:false};
    tally.executions++;
    for (const field of ['data','workflowData']) {
      let data;
      try { data = field === 'data' ? flatted.parse(row[field]) : JSON.parse(row[field]); }
      catch { tally.parse_errors=(tally.parse_errors||0)+1; continue; }
      const seen = new WeakSet();
      function walk(value, key) {
        if (typeof value === 'string') {
          const isTemplate = value.includes('{{') || value.includes('$json') || value.includes('$credentials');
          if (sensitive.test(key) && value && value !== '[REDACTED]' && !isTemplate) tally.sensitive_value_paths++;
          if (/\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]{12,}/i.test(value) && !isTemplate && !value.includes('[REDACTED]')) tally.bearer_string_paths++;
          if (encryptionKey && value.includes(encryptionKey)) tally.current_encryption_key_found = true;
          return;
        }
        if (!value || typeof value !== 'object' || seen.has(value)) return;
        seen.add(value);
        for (const [k,v] of Object.entries(value)) walk(v,k);
      }
      walk(data,'');
    }
  }
  console.log(JSON.stringify({scope:'execution IDs >=2886; metadata only',summary}));
  db.close();
});
