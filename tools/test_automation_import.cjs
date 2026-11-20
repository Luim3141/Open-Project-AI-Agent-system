const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const bundle = JSON.parse(fs.readFileSync(path.join(__dirname, '../jira-bot/QAG3-A04-A05-import.json'), 'utf8'));
const scope = 'ari:cloud:jira:560ef0cc-d24b-4613-98d3-d541afe8f32b:project/10002';
const owner = '712020:0d04982c-00bf-46af-b3a7-446d0f44edfb';
const khai = '712020:47b24428-aa71-4363-b68f-29ed2285aad8';
const ids = new Set();
const allowed = new Set(['jira.issue.field.changed', 'jira.multiple.issue.event', 'jira.jql.condition', 'jira.comparator.condition', 'codebarrel.action.log', 'jira.issue.refresh.issue', 'jira.issue.related', 'jira.issues.related.condition', 'jira.condition.container.block', 'jira.condition.if.block', 'jira.issue.transition', 'jira.create.variable', 'jira.issue.edit', 'jira.issue.outgoing.email']);
function inspect(node, parent = null, conditionParent = null) {
  assert(!ids.has(node.id), 'duplicate component ID'); ids.add(node.id);
  assert(allowed.has(node.type), node.type);
  assert.equal(node.parentId, parent); assert.equal(node.conditionParentId, conditionParent);
  if (node.type === 'jira.issue.transition') {
    assert(['In Progress', 'REVIEW'].includes(node.value.destinationStatus.value));
    assert.equal(node.value.operations.length, 1);
    assert.equal(node.value.operations[0].field.value, 'QAG3 Change reason');
  }
  node.children.forEach(child => inspect(child, node.id));
  node.conditions.forEach(child => inspect(child, null, node.id));
}
assert.equal(bundle.cloud, true); assert.equal(bundle.rules.length, 2);
for (const rule of bundle.rules) {
  assert.equal(rule.state, 'DISABLED'); assert.equal(rule.canOtherRuleTrigger, false);
  assert.deepEqual(rule.ruleScope.resources, [scope]);
  assert.equal(rule.ruleHome.ruleLifecycleHome.locationARI, scope);
  // Native import needs the original export envelope; verify new Jira IDs after import.
  for (const key of ['id', 'idUuid', 'clientKey', 'partitionId', 'created', 'updated', 'currentVersionId', 'checksum']) assert(key in rule, key);
  inspect(rule.trigger); rule.components.forEach(node => inspect(node));
}
const [a04, a05] = bundle.rules;
assert.equal(a04.id, 6377414); assert.equal(a05.id, 6427495);
assert.notEqual(a04.name, 'QAG3 A01 - Start Epic on Task delivery');
assert.notEqual(a05.name, 'QAG3 A03 - Reopen Epic on approved Task change');
assert.equal(a04.actor.value, owner);
assert.deepEqual(a04.trigger.value.fields, [{ value: 'parent', type: 'field' }]);
assert(a04.trigger.conditions[0].value.includes('qag3-scope-approved'));
const branch = a04.components.at(-1);
assert.equal(branch.value.relatedType, 'jql');
assert.equal(branch.value.jql, 'project = QAG3 AND issuetype = 10000 AND id in ({{fieldChange.from|0}},{{fieldChange.to|0}})');
assert.equal(a05.trigger.value.events.length, 1);
assert.equal(a05.trigger.value.events[0].labelKey, 'com.codebarrel.automation.trigger.multiple.transitioned');
assert.equal(a05.trigger.value.eventFilters[0], scope);
assert.equal(a05.actor.value, '557058:f58131cb-b67d-43c7-b30d-6b58d40bd077');
assert(ids.size < 65);

// This evaluates only these candidate predicates, not Jira's JQL/permissions or server engine.
function smart(value, ctx) {
  return value.replace(/\{\{([^{}]+)\}\}/g, (_, token) => {
    const [key, fallback = ''] = token.split('|'); return String(ctx[key] ?? fallback);
  });
}
function passes(node, ctx, children = []) {
  if (node.type === 'jira.comparator.condition') {
    const same = smart(node.value.first, ctx) === smart(node.value.second, ctx);
    assert(['EQUALS', 'NOT_EQUALS'].includes(node.value.operator));
    return node.value.operator === 'EQUALS' ? same : !same;
  }
  if (node.type === 'jira.issues.related.condition') {
    assert.equal(node.value.relatedType, 'stories');
    if (node.value.operator === 'present') return children.length > 0;
    assert.equal(node.value.operator, 'allmatch');
    assert.equal(node.value.compareJql, 'project = QAG3 AND issuetype = 10011 AND status = 10009');
    return children.every(child => child.project === 'QAG3' && child.type === 10011 && child.status === 10009);
  }
  assert.equal(node.type, 'jira.jql.condition');
  const status = /status = (\d+)/.exec(node.value);
  assert(status, 'unhandled test predicate');
  return ctx.project === 'QAG3' && ctx.type === 10000 && ctx['issue.status.id'] === Number(status[1]);
}
const blocks = branch.children.at(-1).children;
const statuses = [10010, 10011, 3, 10012, 10009, 10013];
const done = { project: 'QAG3', type: 10011, status: 10009 };
const open = { ...done, status: 3 };
const sets = [[], [done], [done, open], [open], Array(150).fill(done), [...Array(149).fill(done), open], [{ ...done, type: 10010 }], [{ ...done, project: 'KAN' }]];
let cases = 0;
for (const status of statuses) for (const children of sets) for (const taskStatus of [10010, 3, 10009]) for (const isNew of [false, true]) {
  const ctx = { project: 'QAG3', type: 10000, 'issue.status.id': status, 'issue.id': isNew ? 2 : 1, 'fieldChange.to': 2, 'triggerIssue.status.id': taskStatus };
  const match = blocks.find(block => block.conditions.every(node => passes(node, ctx, children)));
  const actions = match?.children.filter(node => node.type === 'jira.issue.transition') ?? [];
  assert(actions.length <= 1);
  const result = actions[0]?.value.destinationStatus.value ?? null;
  const allDone = children.length > 0 && children.every(child => child.project === 'QAG3' && child.type === 10011 && child.status === 10009);
  const expected = status === 10012 && !allDone ? 'In Progress' : status === 3 && allDone ? 'REVIEW' : status === 10011 && isNew && ![10010,10009].includes(taskStatus) ? 'In Progress' : status === 10009 && isNew && taskStatus !== 10009 ? 'In Progress' : null;
  assert.equal(result, expected, JSON.stringify({ status, taskStatus, isNew, children: children.length }));
  assert(!blocks.some(block => block.conditions.every(node => passes(node, { ...ctx, project: 'KAN' }, children))), 'cross-project branch');
  cases++;
}
const parentGuards = a04.components.filter(node => node.type === 'jira.comparator.condition');
const guard = ctx => parentGuards.every(node => passes(node, ctx));
assert(guard({ 'issue.parent.id': 2, 'fieldChange.from': 1, 'fieldChange.to': 2 }));
assert(guard({ 'issue.parent.id': null, 'fieldChange.from': 1, 'fieldChange.to': null }));
assert(!guard({ 'issue.parent.id': 3, 'fieldChange.from': 1, 'fieldChange.to': 2 }));
assert(!guard({ 'issue.parent.id': 2, 'fieldChange.from': 2, 'fieldChange.to': 2 }));
assert(!guard({}));

const variable = a05.components[0];
assert.equal(variable.type, 'jira.create.variable'); assert.equal(variable.value.lazy, false);
const markerEdit = a05.components.find(node => node.type === 'jira.issue.edit');
assert.equal(markerEdit.value.sendNotifications, false);
assert.deepEqual(markerEdit.value.operations[0].value.REMOVE, []);
assert.equal(markerEdit.value.operations[0].field.value, 'labels');
assert.equal(markerEdit.value.operations[0].type, 'ADDREMOVE');
const dedup = a05.components.find(node => node.type === 'jira.jql.condition');
assert.equal(dedup.value, 'project = QAG3 AND (labels is EMPTY OR labels not in ("{{qag3A05EventKey}}"))');
const notify = a05.components.at(-1);
function candidateAttempt(labels, status, timestamp, assignee) {
  const ctx = { 'triggerIssue.status.id': status, 'triggerIssue.updated.toMillis': timestamp, 'issue.assignee.accountId': assignee };
  const key = smart(variable.value.query.value, ctx);
  if (labels.has(key)) return null;
  ctx.qag3A05EventKey = key;
  labels.add(smart(markerEdit.value.operations[0].value.ADD[0].value, ctx));
  const match = notify.children.find(block => block.conditions.every(node => passes(node, ctx)));
  return match.children[0].value.to[0].value;
}
assert.equal(candidateAttempt(new Set(), 10012, 1, khai), 'hiepk40c@gmail.com');
assert.equal(candidateAttempt(new Set(), 10012, 1, owner), '2101minhkhai@gmail.com');
assert.equal(candidateAttempt(new Set(), 10012, 1, null), '2101minhkhai@gmail.com');
const labels = new Set(['source-AUTH-01', 'qag3-simulation']);
assert(candidateAttempt(labels, 10012, 10, owner));
assert.equal(candidateAttempt(labels, 10012, 10, owner), null);
assert(candidateAttempt(labels, 10012, 11, owner));
assert(labels.has('source-AUTH-01')); assert(labels.has('qag3-simulation'));
// shortcut: marker-before-send may suppress a failed email; manual audited resend is required.
assert.equal(candidateAttempt(labels, 10012, 11, owner), null);
const stale = a05.components.find(node => node.type === 'jira.comparator.condition');
assert(!passes(stale, { 'issue.status.id': 3, 'triggerIssue.status.id': 10012 }));
assert(passes(stale, { 'issue.status.id': 10012, 'triggerIssue.status.id': 10012 }));
if (process.argv.length > 2) {
  assert.equal(process.argv.length, 4, 'provide both actual Jira export paths');
  function semantic(node) {
    const { id, parentId, conditionParentId, checksum, ...rest } = node;
    if (rest.type === 'jira.issue.edit' && rest.schemaVersion === 12) rest.schemaVersion = 10;
    if (rest.type === 'jira.issue.outgoing.email' && rest.schemaVersion === 5) rest.schemaVersion = 3;
    return { ...rest, children: rest.children.map(semantic), conditions: rest.conditions.map(semantic) };
  }
  for (const [index, exportPath] of process.argv.slice(2).entries()) {
    const saved = JSON.parse(fs.readFileSync(exportPath, 'utf8')).rules[0];
    const wanted = bundle.rules[index];
    assert.equal(saved.name, wanted.name); assert.equal(saved.state, 'DISABLED');
    assert.notEqual(saved.idUuid, wanted.idUuid, 'import must create a new rule, not replace the template');
    assert.deepEqual(saved.ruleScope, wanted.ruleScope); assert.equal(saved.canOtherRuleTrigger, false);
    assert.deepEqual(semantic(saved.trigger), semantic(wanted.trigger));
    assert.deepEqual(saved.components.map(semantic), wanted.components.map(semantic));
    assert.equal(saved.actor.value, '557058:f58131cb-b67d-43c7-b30d-6b58d40bd077');
  }
  console.log('PASS: both actual Jira exports retain candidate trigger/graph/scope; new rule identities; import resets actor to Automation for Jira.');
}
console.log(`PASS: ${ids.size} native graph components; ${cases} A04 local decision cases; Parent/stale/replay/routing/label-preservation guards.`);
console.log('NOT VERIFIED: actor execution permissions, email quota/delivery, child visibility/pagination, concurrent duplicate execution and E2E.');
