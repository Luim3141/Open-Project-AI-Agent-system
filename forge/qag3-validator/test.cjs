const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const yaml = require('../../tools/forge-cli/node_modules/@forge/cli/node_modules/yaml');
const manifest = yaml.parse(fs.readFileSync(process.env.QAG3_VALIDATOR_MANIFEST || `${__dirname}/manifest.yml`, 'utf8'));
const rules = Object.fromEntries(manifest.modules['jira:workflowValidator'].map(r => [r.key, r.expression]));
const project = { id: 10002, key: 'QAG3' };
const task = { key: 'QAG3-2', project, issueType: { id: 10011 }, status: { id: 10009 }, childIssues: [] };
const epic = { key: 'QAG3-1', project, issueType: { id: 10000 }, childIssues: [task] };
const pm = { accountId: '712020:0d04982c-00bf-46af-b3a7-446d0f44edfb', active: true };
class RichText {
  constructor(value) { this.plainText = value.fixturePlainText; }
}
function jiraType(value) {
  if (value instanceof RichText) return 'RichText';
  if (typeof value === 'string') return 'string';
  if (value !== null && typeof value === 'object') return 'Map';
  return typeof value;
}
// JS fixtures check predicate logic only, not the Jira expression engine or visibility.
function allowed(key, issue = epic, user = pm, originalIssue = issue) {
  // Jira exposes description as RichText, unlike multiline custom fields returned as ADF maps.
  issue = { ...issue, description: typeof issue.description === 'string' ? { plainText: issue.description } : issue.description };
  originalIssue = { ...originalIssue, description: typeof originalIssue.description === 'string' ? { plainText: originalIssue.description } : originalIssue.description };
  originalIssue.getNewestChangelog = (field, filter = {}) => {
    if (!Array.isArray(originalIssue.changelogs)) throw Error('history unavailable');
    const change = originalIssue.changelogs.find(c => c.items.some(i => i.fieldId === field && Object.entries(filter).every(([k, v]) => i[k] === v)));
    return change ? { ...change, created: change.created ?? Number(change.id), items: change.items.filter(i => i.fieldId === field) } : null;
  };
  const expression = rules[key].replaceAll(/typeof ([\w.]+) == '(Map|String|string|RichText)'/g, "jiraType($1) == '$2'");
  try {
    const result = vm.runInNewContext(expression, { issue, user, originalIssue, RichText, jiraType }, { timeout: 100 }) === true;
    // Task Approve/Deploy require both server validators; provenance alone is insufficient.
    const needsCompanion = (key === 'qag3-qa-current' && issue.issueType.id === 10011) ||
      (key === 'qag3-subtask-acceptance' && rules['qag3-qa-freshness'].includes('let subtaskGate ='));
    const historyGate = key === 'qag3-subtask-acceptance' && rules['qag3-subtask-history'];
    return result && (!needsCompanion ||
      vm.runInNewContext(rules['qag3-qa-freshness'], { issue, originalIssue, user }, { timeout: 100 }) === true) &&
      (!historyGate || vm.runInNewContext(historyGate.replaceAll(/typeof ([\w.]+) == '(Map|String|string|RichText)'/g, "jiraType($1) == '$2'"),
        { issue, originalIssue, user, RichText, jiraType }, { timeout: 100 }) === true);
  }
  catch { return false; }
}
assert.equal(allowed('qag3-pm-only'), true);
assert.equal(allowed('qag3-pm-only', epic, { ...pm, accountId: '712020:47b24428-aa71-4363-b68f-29ed2285aad8' }), true);
for (const user of [null, { ...pm, active: false }, { ...pm, accountId: 'not-pm' }]) {
  assert.equal(allowed('qag3-pm-only', epic, user), false);
}
assert.equal(allowed('qag3-epic-children-done'), true);
for (const children of [null, [], [null], [{ ...task, status: { id: 3 } }],
  [{ ...task, status: { id: 10013 } }], [{ ...task, issueType: { id: 10010 } }],
  [{ ...task, key: 'KAN-2', project: { id: 10001, key: 'KAN' } }], [task, { ...task, status: { id: 3 } }]]) {
  assert.equal(allowed('qag3-epic-children-done', { ...epic, childIssues: children }), false);
}
for (const key of Object.keys(rules)) {
  assert.equal(allowed(key, { ...epic, project: { id: 10001, key: 'KAN' } }), false);
  assert.equal(allowed(key, { ...epic, project: { id: 10002, key: 'SAM1' } }), false);
}
assert.equal(allowed('qag3-epic-children-done', { ...epic, issueType: { id: 10011 } }), false);
assert.equal(manifest.modules.function, undefined);
assert.equal(manifest.permissions, undefined);
const taskWithChildren = { ...task, childIssues: [{ ...task, issueType: { id: 10010 } }] };
assert.equal(allowed('qag3-task-subtasks-done', taskWithChildren), true);
assert.equal(allowed('qag3-task-subtasks-done', { ...taskWithChildren, childIssues: [] }), true);
for (const childIssues of [null, [null], [task], [{ ...taskWithChildren.childIssues[0], status: { id: 3 } }]]) {
  assert.equal(allowed('qag3-task-subtasks-done', { ...taskWithChildren, childIssues }), false);
}
const changed = { ...task, customfield_10043: 'New repair reason' };
assert.equal(allowed('qag3-fresh-change-reason', changed, pm, { ...task, customfield_10043: 'Previous reason' }), true);
assert.equal(allowed('qag3-fresh-change-reason', changed), false);
for (const reason of [null, '', ' \n ', 42, { fixturePlainText: ' ' }]) {
  assert.equal(allowed('qag3-fresh-change-reason', { ...task, customfield_10043: reason }, pm, task), false);
}
assert.equal(allowed('qag3-fresh-change-reason', { ...task, customfield_10043: { fixturePlainText: 'Repair regression' } }, pm, task), true);
const richReason = { ...task, customfield_10043: new RichText({ fixturePlainText: 'Repair regression' }) };
assert.equal(allowed('qag3-fresh-change-reason', richReason, pm, task), true);
assert.equal(allowed('qag3-fresh-change-reason', richReason, pm, richReason), false);
assert.equal(allowed('qag3-fresh-change-reason', richReason, pm,
  { ...task, customfield_10043: new RichText({ fixturePlainText: 'Previous reason' }) }), true);
const choices = [10020, 10021, 10022, 10023, 10025, 10026, 10027].map(id => ({ id: String(id) }));
const delivery = { ...task, customfield_10044: choices, customfield_10045: 'Test report TEST-42 / build abc' };
assert.equal(allowed('qag3-task-delivery-checklist', delivery), true);
assert.equal(allowed('qag3-task-delivery-checklist', { ...delivery, customfield_10044: choices.map(c => c.id == 10023 ? { id: '10024' } : c) }), true);
for (const customfield_10044 of [null, [], choices.filter(c => c.id != 10023), [...choices, { id: '10024' }], choices.filter(c => c.id != 10026)]) {
  assert.equal(allowed('qag3-task-delivery-checklist', { ...delivery, customfield_10044 }), false);
}
assert.equal(allowed('qag3-task-delivery-checklist', { ...delivery, customfield_10045: ' ' }), false);
for (const outsideProject of [{ id: 10001, key: 'KAN' }, { id: 10002, key: 'SAM1' }]) {
  assert.equal(allowed('qag3-fresh-change-reason', { ...changed, project: outsideProject }, pm, task), false);
  assert.equal(allowed('qag3-task-subtasks-done', { ...taskWithChildren, project: outsideProject }), false);
  assert.equal(allowed('qag3-task-delivery-checklist', { ...delivery, project: outsideProject }), false);
}
const qa = { accountId: '712020:94d1f95d-9618-4f25-8284-41105336b942', active: true };
const qaText = ['Revision: build-42', 'Environment: Test - shared', 'Test scope: TC-1, TC-2',
  'Result: PASS', 'Evidence: report-42', 'Retest: PASSED', 'Bug references / retest rationale: BUG-42 retested PASS'].join('\n');
const testing = { ...task, labels: [], status: { id: 10018 }, summary: 'Login', description: 'Acceptance criteria',
  parent: { id: 10078 }, assignee: { accountId: 'dev' }, customfield_10045: null };
const attested = { ...testing, customfield_10045: qaText, customfield_10044: [{ id: '10022' }, { id: '10023' }] };
assert.equal(allowed('qag3-qa-attest', attested, qa, testing), true);
assert.equal(allowed('qag3-qa-attest', { ...attested, issueType: { id: 10010 } }, qa, testing), true);
for (const actor of [pm, null, { ...qa, active: false }, { ...qa, accountId: 'bot' }]) {
  assert.equal(allowed('qag3-qa-attest', attested, actor, testing), false);
}
for (const text of ['', null, 42, qaText.replace('Revision: build-42', 'Revision: '),
  qaText.replace('Result: PASS', 'Result: FAIL'), qaText + '\nRevision: forged',
  qaText.replace('Environment: Test - shared', 'Environment: Production'),
  qaText.replace('Retest: PASSED', 'Retest: NOT REQUIRED')]) {
  assert.equal(allowed('qag3-qa-attest', { ...attested, customfield_10045: text }, qa, testing), false);
}
assert.equal(allowed('qag3-qa-attest', attested, qa, attested), false);
assert.equal(allowed('qag3-qa-attest', { ...attested, customfield_10045: ' ' + qaText + ' ' }, qa, attested), false);
assert.equal(allowed('qag3-qa-attest', attested, qa, { ...testing, status: { id: 3 } }), false);
assert.equal(allowed('qag3-qa-attest', { ...attested, customfield_10044: [...attested.customfield_10044, { id: '10024' }] }, qa, testing), false);
const noRetest = { ...attested, customfield_10045: qaText.replace('Retest: PASSED', 'Retest: NOT REQUIRED'),
  customfield_10044: [{ id: '10022' }, { id: '10024' }] };
assert.equal(allowed('qag3-qa-attest', noRetest, qa, testing), true);
const simulatedText = qaText.replace('Result: PASS', 'Result: SIMULATED PASS');
const simulatedTesting = { ...testing, labels: ['qag3-simulation'] };
const simulatedAttested = { ...attested, labels: ['qag3-simulation'], customfield_10045: simulatedText };
assert.equal(allowed('qag3-qa-attest', simulatedAttested, pm, simulatedTesting), true);
for (const actor of [qa, { ...pm, active: false }, { ...pm, accountId: 'another-admin' }]) {
  assert.equal(allowed('qag3-qa-attest', simulatedAttested, actor, simulatedTesting), false);
}
assert.equal(allowed('qag3-qa-attest', simulatedAttested, pm, testing), false);
assert.equal(allowed('qag3-qa-attest', { ...simulatedAttested, labels: [] }, pm, simulatedTesting), false);
assert.equal(allowed('qag3-qa-attest', { ...simulatedAttested, customfield_10045: qaText }, pm, simulatedTesting), false);
assert.equal(allowed('qag3-qa-attest', simulatedAttested, pm, simulatedAttested), false);
const passEvent = { id: '42', author: qa, items: [
  { fieldId: 'status', from: '10018', to: '10012' },
  { fieldId: 'customfield_10045', fromString: null, toString: qaText }] };
const review = { ...attested, status: { id: 10012 }, changelogs: [passEvent] };
const simulatedPass = { ...passEvent, author: pm,
  items: [passEvent.items[0], { ...passEvent.items[1], toString: simulatedText }] };
const simulatedReview = { ...review, labels: ['qag3-simulation'], customfield_10045: simulatedText, changelogs: [simulatedPass] };
assert.equal(allowed('qag3-qa-current', simulatedReview), true);
assert.equal(allowed('qag3-qa-current', { ...simulatedReview, labels: [] }), false);
assert.equal(allowed('qag3-qa-current', { ...simulatedReview, customfield_10045: qaText }), false);
assert.equal(allowed('qag3-qa-current', { ...simulatedReview,
  changelogs: [{ ...simulatedPass, author: qa }] }), false);
assert.equal(allowed('qag3-qa-current', { ...simulatedReview,
  changelogs: [{ id: '43', items: [{ fieldId: 'description' }] }, simulatedPass] }), false);
assert.equal(allowed('qag3-qa-current', review), true);
const qaAdf = {type:'doc',version:1,content:[{type:'paragraph',content:[{type:'text',text:qaText}]}]};
assert.equal(allowed('qag3-qa-current', { ...review, customfield_10045: qaAdf }), true);
assert.equal(allowed('qag3-qa-current', { ...review, customfield_10045: {type:'doc',content:[{type:'panel',content:qaAdf.content}]} }), false);
assert.equal(allowed('qag3-qa-current', { ...review, changelogs: [{id:'43',author:qa,items:[{fieldId:'customfield_10045',toString:qaText}]},passEvent] }), false);
assert.equal(allowed('qag3-qa-current', { ...review, issueType: { id: 10010 } }), true);
for (const changelogs of [null, [], [{ ...passEvent, author: pm }], [{ ...passEvent, author: null }],
  [{ ...passEvent, author: { ...qa, active: false } }], [{ ...passEvent, items: passEvent.items.slice(0, 1) }]]) {
  assert.equal(allowed('qag3-qa-current', { ...review, changelogs }), false);
}
assert.equal(allowed('qag3-qa-current', { ...review, changelogs: [{ ...passEvent,
  items: [passEvent.items[0], { ...passEvent.items[1], toString: 'Different signed revision' }] }] }), false);
// shortcut: constant Task lookups cover named core fields/status, not malformed unrelated metadata; use a scoped function if that extra contract is required.
assert.equal(allowed('qag3-qa-current', { ...review, changelogs: [{ id: '43', items: [{}] }, passEvent] }), true);
assert.equal(allowed('qag3-qa-current', { ...review, issueType: { id: 10010 }, changelogs: [{ id: '43', items: [{}] }, passEvent] }), false);
for (const fieldId of ['summary', 'description', 'parent', 'assignee', 'customfield_10045']) {
  assert.equal(allowed('qag3-qa-current', { ...review,
    changelogs: [{ id: '43', items: [{ fieldId }] }, passEvent] }), false);
}
for (const [from, to] of [['10012', '3'], ['10012', '10018'], ['10009', '3'], ['10018', '3']]) {
  assert.equal(allowed('qag3-qa-current', { ...review,
    changelogs: [{ id: '43', items: [{ fieldId: 'status', from, to }] }, passEvent] }), false);
}
const release = { ...review, status: { id: 10019 }, changelogs: [
  { id: '43', items: [{ fieldId: 'status', from: '10012', to: '10019' }, { fieldId: 'customfield_10044' }] }, passEvent] };
assert.equal(allowed('qag3-qa-current', release), true);
assert.equal(allowed('qag3-qa-current', { ...release, issueType: { id: 10010 } }), false);
for (const diff of [{ summary: 'New scope' }, { description: 'New AC' }, { parent: { id: 99 } },
  { assignee: { accountId: 'other' } }, { customfield_10045: qaText + '\nPM approved' }]) {
  assert.equal(allowed('qag3-qa-current', { ...review, ...diff }, pm, review), false);
}
for (const key of ['qag3-qa-attest', 'qag3-qa-current']) {
  assert.equal(allowed(key, { ...review, project: { id: 10001, key: 'KAN' } }, qa, testing), false);
}
assert.equal(allowed('qag3-qa-current', { ...review, changelogs: [
  { id: '44', author: pm, items: passEvent.items }, passEvent] }), false);
assert.equal(allowed('qag3-qa-current', { ...review, changelogs: [passEvent,
  { id: '41', items: [{ fieldId: 'status', from: '10012', to: '3' }] }] }), true);
const developer = { accountId: '712020:7141e4e4-a663-4691-a3ec-fec3efb6df5a', active: true };
const devSubtask = { ...review, issueType: { id: 10010 }, assignee: developer };
assert.equal(allowed('qag3-subtask-acceptance', devSubtask), true);
for (const choices of [null, [], [{id:'10022'}], [{id:'10022'},{id:'10023'},{id:'10024'}]]) {
  assert.equal(allowed('qag3-subtask-acceptance', {...devSubtask,customfield_10044:choices}),false);
}
const simulatedDev = { ...simulatedReview, issueType: { id: 10010 }, assignee: developer };
assert.equal(allowed('qag3-subtask-acceptance', simulatedDev), true);
assert.equal(allowed('qag3-subtask-acceptance', { ...simulatedDev, labels: [] }), false);
const simulatedSelf = { ...simulatedDev, assignee: pm, changelogs: [simulatedPass,
  { id: '41', items: [{ fieldId: 'assignee', from: developer.accountId, to: pm.accountId }] }] };
assert.equal(allowed('qag3-subtask-acceptance', simulatedSelf), true);
assert.equal(allowed('qag3-subtask-acceptance', { ...devSubtask, changelogs: [] }), false);
const businessBefore = { ...devSubtask, assignee: qa, changelogs: [], customfield_10045: null };
const businessReview = { ...businessBefore, customfield_10045: 'Revision: testplan-v2\nReview scope: AC-1, AC-2\nReview result: ACCEPTED\nEvidence: testplan-42' };
assert.equal(allowed('qag3-subtask-acceptance', businessReview, pm, businessBefore), true);
const selfBefore = { ...businessBefore, assignee: pm, labels: ['qag3-simulation'],
  changelogs: [{ id: '1', items: [{ fieldId: 'assignee', from: pm.accountId, to: pm.accountId }] }] };
const selfReview = { ...selfBefore,
  customfield_10045: businessReview.customfield_10045.replace('Review result: ACCEPTED', 'Review result: SIMULATED ACCEPTED') };
assert.equal(allowed('qag3-subtask-acceptance', selfReview, pm, selfBefore), true);
assert.equal(allowed('qag3-subtask-acceptance', { ...selfReview, labels: [] }, pm, selfBefore), false);
assert.equal(allowed('qag3-subtask-acceptance', selfReview, pm, { ...selfBefore, labels: [] }), false);
assert.equal(allowed('qag3-subtask-acceptance', selfReview, { ...pm, active: false }, selfBefore), false);
assert.equal(allowed('qag3-subtask-acceptance', { ...selfReview, customfield_10045: businessReview.customfield_10045 }, pm, selfBefore), false);
assert.equal(allowed('qag3-subtask-acceptance', selfReview, pm, selfReview), false);
assert.equal(allowed('qag3-subtask-acceptance', { ...businessReview, assignee: pm }, pm, { ...businessBefore, assignee: pm }), false);
assert.equal(allowed('qag3-subtask-acceptance', { ...businessReview, assignee: pm },
  { ...pm, accountId: '712020:47b24428-aa71-4363-b68f-29ed2285aad8' }, { ...businessBefore, assignee: pm }), true);
for (const user of [qa, developer, null, { ...pm, active: false }]) {
  assert.equal(allowed('qag3-subtask-acceptance', businessReview, user, businessBefore), false);
}
for (const history of [null, [{ id: '1', items: [{ fieldId: 'status', to: '10016' }] }],
  [{ id: '1', items: [{ fieldId: 'assignee', from: developer.accountId, to: qa.accountId }] }],
  [{ id: '1', items: [{ fieldId: 'assignee', from: pm.accountId, to: qa.accountId }] }]]) {
  const old = { ...businessBefore, changelogs: history };
  assert.equal(allowed('qag3-subtask-acceptance', { ...businessReview, changelogs: history }, pm, old), false);
}
for (const text of [null, ' ', businessReview.customfield_10045.replace('ACCEPTED', 'REJECTED'),
  businessReview.customfield_10045 + '\nRevision: forged']) {
  assert.equal(allowed('qag3-subtask-acceptance', { ...businessReview, customfield_10045: text }, pm, businessBefore), false);
}
assert.equal(allowed('qag3-subtask-acceptance', businessReview), false);
assert.equal(allowed('qag3-subtask-acceptance', { ...businessReview, changelogs: [{ id: '2', items: [{}] }] },
  pm, { ...businessBefore, changelogs: [{ id: '2', items: [{}] }] }), false);
assert.equal(allowed('qag3-subtask-acceptance', { ...businessReview, assignee: { ...qa, active: false } }, pm, businessBefore), false);
assert.equal(allowed('qag3-subtask-acceptance', { ...businessReview, assignee: { accountId: 'unknown', active: true } }, pm, businessBefore), false);
assert.equal(allowed('qag3-subtask-acceptance', { ...businessReview, summary: 'Changed AC' }, pm, businessBefore), false);
const epicOwner = { ...pm };
const scopedTask = { ...task, key: 'QAG3-2', childIssues: [{ ...task, key: 'QAG3-3', issueType: { id: 10010 } }] };
const epicBefore = { ...epic, summary: 'Authentication', description: 'Acceptance criteria', assignee: epicOwner,
  status: { id: 10010 }, childIssues: [scopedTask], customfield_10045: null };
const readyEvidence = 'Scope version: v1\nScope tasks: QAG3-2\nAcceptance criteria: AUTH-01 AC1/AC2\nScope result: APPROVED\nEvidence: scope-v1';
const epicReady = { ...epicBefore, customfield_10045: readyEvidence };
assert.equal(allowed('qag3-epic-readiness', epicReady, pm, epicBefore), true);
const acceptingBefore = { ...epicBefore, status: { id: 10012 }, customfield_10045: readyEvidence };
const acceptingText = 'Scope version: v1\nScope tasks: QAG3-2\nIntegration result: PASS\nHandover result: COMPLETE\nEvidence: integration-v1\nRetest: PASSED\nBug references / retest rationale: fix-bug-report-v1';
const accepting = { ...acceptingBefore, customfield_10045: acceptingText, customfield_10044: choices };
assert.equal(allowed('qag3-epic-acceptance', accepting, pm, acceptingBefore), true);
for (const [key, current, old] of [['qag3-epic-readiness', epicReady, epicBefore], ['qag3-epic-acceptance', accepting, acceptingBefore]]) {
  for (const actor of [null, qa, { ...pm, active: false }]) assert.equal(allowed(key, current, actor, old), false);
  for (const childIssues of [null, [], [null], [scopedTask, { ...scopedTask, key: 'QAG3-8' }],
    [{ ...scopedTask, key: 'KAN-2', project: { id: 10001, key: 'KAN' } }], [{ ...scopedTask, issueType: { id: 10010 } }]]) {
    assert.equal(allowed(key, { ...current, childIssues }, pm, old), false);
  }
  for (const text of [null, 42, ' ', current.customfield_10045.replace('Scope tasks: QAG3-2', 'Scope tasks: QAG3-999'),
    current.customfield_10045.replace('Scope tasks: QAG3-2', 'Scope tasks: QAG3-2,QAG3-2'),
    current.customfield_10045 + '\nScope version: duplicate']) {
    assert.equal(allowed(key, { ...current, customfield_10045: text }, pm, old), false);
  }
  for (const assignee of [null, { ...pm, active: false }]) assert.equal(allowed(key, { ...current, assignee }, pm, old), false);
  assert.equal(allowed(key, current, pm, current), false);
  assert.equal(allowed(key, current, pm, { ...old, status: { id: 10009 } }), false);
}
assert.equal(allowed('qag3-epic-readiness', { ...epicReady, description: ' ' }, pm, epicBefore), false);
for (const diff of [{ summary: 'Changed scope' }, { description: 'Changed AC' }, { assignee: qa },
  { customfield_10044: choices.filter(c => c.id != '10026') }, { customfield_10044: [...choices, { id: '10024' }] }]) {
  assert.equal(allowed('qag3-epic-acceptance', { ...accepting, ...diff }, pm, acceptingBefore), false);
}
for (const child of [{ ...scopedTask, status: { id: 3 } }]) {
  assert.equal(allowed('qag3-epic-acceptance', { ...accepting, childIssues: [child] }, pm, acceptingBefore), false);
}
assert.equal(allowed('qag3-epic-acceptance', { ...accepting, customfield_10045: acceptingText.replace('Retest: PASSED', 'Retest: NOT REQUIRED'),
  customfield_10044: choices.map(c => c.id == '10023' ? { id: '10024' } : c) }, pm, acceptingBefore), true);
console.log('Predicate fixture tests PASS (QA, Subtask and Epic scope/acceptance); no Jira runtime or deployment verification.');
const noProjectReads = { ...scopedTask, childIssues: scopedTask.childIssues.map(sub => ({ ...sub,
  get project() { throw new Error('Descendant project lookup exceeds runtime budget'); } })),
  get project() { throw new Error('Descendant project lookup exceeds runtime budget'); } };
assert.equal(allowed('qag3-epic-acceptance', { ...accepting, childIssues: [noProjectReads] }, pm, acceptingBefore), true);
for (const child of [{ ...scopedTask, childIssues: null },
  { ...scopedTask, childIssues: [{ ...scopedTask.childIssues[0], status: { id: 3 } }] },
  { ...scopedTask, childIssues: [{ ...scopedTask.childIssues[0], key: 'KAN-3' }] }]) {
  assert.equal(allowed('qag3-epic-children-done', { ...accepting, childIssues: [child] }), false);
}
assert.equal(allowed('qag3-epic-children-done', { ...accepting, childIssues: [noProjectReads] }), true);
assert.equal(allowed('qag3-epic-acceptance', { ...accepting, key: 'KAN-1', project: { id: 10001, key: 'KAN' } }, pm, acceptingBefore), false);
const paragraphs = text => ({ type: 'doc', version: 1, content: text.split('\n').map(line =>
  ({ type: 'paragraph', content: [{ type: 'text', text: line }] })) });
const acceptingADF = { ...accepting, customfield_10045: paragraphs(acceptingText) };
assert.equal(allowed('qag3-epic-acceptance', acceptingADF, pm,
  { ...acceptingBefore, customfield_10045: paragraphs(readyEvidence) }), true);
assert.equal(allowed('qag3-epic-acceptance', acceptingADF, pm, acceptingADF), false);
const unsupportedADF = { type: 'doc', version: 1, content: [{ type: 'unsupported' }] };
assert.equal(allowed('qag3-epic-acceptance', { ...acceptingADF, customfield_10045: unsupportedADF }, pm, acceptingBefore), false);
assert.equal(allowed('qag3-epic-acceptance', acceptingADF, pm,
  { ...acceptingBefore, customfield_10045: unsupportedADF }), false);
