'use strict';

// Probe n8n's real retry method with synthetic stored data; persistence and runner are stubs.
const assert = require('node:assert/strict');
const {ExecutionService} = require('/usr/local/lib/node_modules/n8n/dist/executions/execution.service.js');
const {AbortedExecutionRetryError} = require('/usr/local/lib/node_modules/n8n/dist/errors/aborted-execution-retry.error.js');
const synthetic = 'SYNTHETIC_RETRY_INPUT';
const request = {executionId: '1', sharedWorkflowIds: ['fixture'], user: {id: 'test'}};
const base = {status: 'error', finished: false, workflowId: 'fixture', workflowData: {id: 'fixture'}};

async function probe(data) {
  let runnerReceivedInput = false;
  const context = {
    executionPersistence: {findWithUnflattenedData: async () => ({...base, data})},
    workflowRunner: {run: async (input) => {
      runnerReceivedInput = JSON.stringify(input.executionData).includes(synthetic);
      throw new Error('SYNTHETIC_RUNNER_STOP');
    }},
  };
  try {
    await ExecutionService.prototype.retry.call(context, request);
    throw new Error('UNEXPECTED_RETRY_RETURN');
  } catch (error) {
    return {abortedRetry: error instanceof AbortedExecutionRetryError,
      runnerStopped: error.message === 'SYNTHETIC_RUNNER_STOP', runnerReceivedInput};
  }
}

(async () => {
  const metadataOnly = await probe({resultData: {runData: {}}});
  const withPayload = await probe({executionData: {nodeExecutionStack: [{data: synthetic}]}, resultData: {runData: {}}});
  console.log(JSON.stringify({metadata_only: metadataOnly, payload_control: withPayload}));
  assert.equal(metadataOnly.abortedRetry, true);
  assert.equal(metadataOnly.runnerReceivedInput, false);
  assert.equal(withPayload.runnerStopped, true);
  assert.equal(withPayload.runnerReceivedInput, true);
})().catch(error => { console.error(error.name); process.exitCode = 1; });
