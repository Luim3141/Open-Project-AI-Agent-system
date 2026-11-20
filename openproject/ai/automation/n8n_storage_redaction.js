// Storage copies only: executing workflow inputs/authentication remain unchanged.
'use strict';
const sensitive = /^(authorization|proxy-authorization|x-qldapm-webhook-token|x-api-key|x-n8n-api-key|cookie|set-cookie|signature)$/i;
const lifecycleWorkflow = 'elfapV5D2PTnLiHW';
function lifecycleMetadata(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
  const out = {};
  for (const key of ['event_id', 'run_id', 'correlation_id', 'trace_event_id']) {
    if (typeof value[key] === 'string' && /^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/.test(value[key])) out[key] = value[key];
  }
  if (value.project_id === 6) out.project_id = 6;
  for (const key of ['schema_version', 'work_package_id', 'published_at']) if (Number.isSafeInteger(value[key]) && value[key] > 0) out[key] = value[key];
  if (typeof value.timestamp === 'number' && Number.isFinite(value.timestamp) && value.timestamp >= 0) out.timestamp = value.timestamp;
  if (['QUEUED','PLANNING','RUNNING','REVIEWING','COMPLETED','FAILED','REVIEW','OBSERVED'].includes(value.status)) out.status = value.status;
  if (['supervisor','pm','ba','dev','reviewer','qa'].includes(value.agent_id)) out.agent_id = value.agent_id;
  if (['REQUEST_RECEIVED','PLAN_CREATED','AGENT_ASSIGNED','AGENT_STARTED','AGENT_COMPLETED','AGENT_FAILED','REVIEW_COMPLETED','RUN_COMPLETED','RUN_FAILED'].includes(value.event_type)) out.event_type = value.event_type;
  if (typeof value.error_code === 'string' && /^[A-Z][A-Z0-9_]{0,79}$/.test(value.error_code)) out.error_code = value.error_code;
  if (value.event) out.event = lifecycleMetadata(value.event);
  if (value.body) out.body = lifecycleMetadata(value.body);
  return out;
}
function replacer(key, value) {
  if (sensitive.test(key) || (key === 'value' && typeof this.name === 'string' && sensitive.test(this.name))) return '[REDACTED]';
  return typeof value === 'string' ? value.replace(/\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+/gi, '$1 [REDACTED]') : value;
}
exports.redactBundle = function redactBundle(payload, flatted, workflowId) {
  try {
    const copy = {...payload};
    if (copy.data !== undefined) {
      const lifecycle = (workflowId || copy.workflowData?.id) === lifecycleWorkflow;
      copy.data = flatted.stringify(flatted.parse(copy.data), lifecycle ? function(key, value) {
        if (key === 'json') return lifecycleMetadata(value);
        if (key === 'binary') return undefined;
        if (key === 'error' && value) return {message: 'LIFECYCLE_EXECUTION_FAILED', name: 'Error'};
        return replacer.call(this, key, value);
      } : replacer);
    }
    if (copy.workflowData !== undefined) copy.workflowData = JSON.parse(JSON.stringify(copy.workflowData, replacer));
    return copy;
  } catch {
    throw new Error('EXECUTION_PAYLOAD_REDACTION_FAILED');
  }
};
