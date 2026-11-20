const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const template = fs.readFileSync(path.join(__dirname, '../core/overlay/app/views/qldapm_work_packages/_navigation.html.erb'), 'utf8');
const script = template.replace(/^<%= javascript_tag nonce: true do %>\s*/, '').replace(/<% end %>\s*$/, '');
function run(query, present = 11) {
  const href = 'http://localhost:18088/projects/qldapm-local/gantt' + query;
  const rows = new Map(Array.from({length: present}, (_, i) => [38 + i, {
    collapsed: false,
    querySelector() { return {classList: {contains: () => this.collapsed}, dispatchEvent: event => { assert.equal(event.type, 'click'); assert.equal(event.bubbles, true); if (!state.ignoreClicks) this.collapsed = !this.collapsed; }}; }
  }]));
  const state = {redirect: null, callback: null, stored: false};
  const location = new URL(href); location.replace = url => {state.redirect = url;};
  vm.runInNewContext(script, {
    URL, window: {location}, MouseEvent: class {constructor(type, options) {this.type = type; Object.assign(this, options);}},
    document: {addEventListener() {}, removeEventListener() {}, querySelector: s => rows.get(Number(s.match(/wp-row-(\d+)/)[1]))?.querySelector()},
    sessionStorage: {getItem: () => state.stored, setItem: () => {state.stored = true;}},
    setTimeout() {}, setInterval: cb => {state.callback = cb; return 1;}, clearInterval() {}
  });
  return {...state, rows, snapshot: () => state};
}
const initial = run('?query_id=32&pp=500');
const redirected = new URL(initial.redirect);
assert.deepEqual(JSON.parse(redirected.searchParams.get('query_props')), {pp: 500, hi: true, tv: true});
assert.equal(redirected.searchParams.get('query_id'), '32');
assert.equal(redirected.searchParams.has('pp'), false);
const props = {pp: 100, tv: true, f: [{n: 'status', o: '=', v: ['1']}], t: 'id:desc'};
const selected = run('?query_props=' + encodeURIComponent(JSON.stringify(props)));
assert.equal(selected.redirect, null);
selected.callback();
assert.equal([...selected.rows.values()].filter(r => r.collapsed).length, 11);
selected.rows.get(38).collapsed = false;
selected.callback();
assert.equal(selected.rows.get(38).collapsed, false, 'user expansion must survive later DOM mutations');
const partial = run('?query_props=' + encodeURIComponent(JSON.stringify({pp: 500})), 1);
partial.callback();
assert.equal(partial.snapshot().stored, false, 'do not mark initialization on a partial render');
const lateHandlers = run('?query_props=' + encodeURIComponent(JSON.stringify({pp: 500})));
lateHandlers.snapshot().ignoreClicks = true;
lateHandlers.callback();
assert.equal(lateHandlers.snapshot().stored, false, 'unhandled clicks are not successful initialization');
lateHandlers.snapshot().ignoreClicks = false;
lateHandlers.callback();
assert.equal(lateHandlers.snapshot().stored, true, 'finish only after Native collapse is acknowledged');
assert.equal(run('?query_props=' + encodeURIComponent(JSON.stringify({pp: 100, hi: false}))).callback, null);
const filtered = new URL(run('?query_props=' + encodeURIComponent(JSON.stringify({tv: true, f: props.f, t: props.t}))).redirect);
assert.deepEqual(JSON.parse(filtered.searchParams.get('query_props')), {tv: true, f: props.f, t: props.t, pp: 500});
assert.equal(run('?query_props=%7Bbroken').redirect, null);
assert.equal(run('?query_props=null').redirect, null);
const spaced = new URL(run('?query_props=' + encodeURIComponent(JSON.stringify({f:[{n:'subject',o:'~',v:['hello world']}]}))).redirect);
assert.equal(spaced.search.includes('+'), false, 'Native query decoding expects percent-encoded spaces');
assert.equal(JSON.parse(spaced.searchParams.get('query_props')).f[0].v[0], 'hello world');
console.log('PASS: Native query pagination, filter/sort preservation, render race, user expansion, malformed input');
