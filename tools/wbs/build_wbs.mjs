import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { Workbook } from '@oai/artifact-tool';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../..');
const output = path.join(root, 'Jira_WBS_QAG3_v7_DRAFT.csv');
const sourcePath = path.join(root, 'user-story-web-quan-ly-du-an-rut-gon.docx');
const sources = JSON.parse(await fs.readFile(path.join(here, 'source_stories.json'), 'utf8'));
const plans = JSON.parse(await fs.readFile(path.join(here, 'breakdown.json'), 'utf8'));
const sourceRead = spawnSync('C:/Users/LUIM/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe', ['-c',
  'import json,sys; from docx import Document; print(json.dumps([[[c.text for c in r.cells] for r in t.rows] for t in Document(sys.argv[1]).tables][2:],ensure_ascii=False))', sourcePath], { encoding: 'utf8' });
assert.equal(sourceRead.status, 0, sourceRead.stderr);
const liveTables = JSON.parse(sourceRead.stdout);
assert.equal(liveTables.length, 11);
for (const [i, epic] of sources.entries()) {
  assert.equal(epic.epicId, liveTables[i][1][0].match(/EPIC (\d+)/)[1]);
  for (const [j, s] of epic.stories.entries()) {
    assert.equal(`${s.id}\n${s.story}`, liveTables[i][j + 1][1]);
    assert.deepEqual(s.ac, liveTables[i][j + 1][2].split('\n'));
  }
  assert.equal(epic.stories.length, liveTables[i].length - 1);
}
assert.equal(plans.length, 53);
const planById = new Map(plans.map(p => [p[0], p]));
assert.equal(planById.size, 53);
const emails = { BA: 'hiepk40c@gmail.com', BE: 'nguyenduc6325@gmail.com', FE: 'ttheduy1401@gmail.com', QA: 'Duyhungls2005@gmail.com', PM: '2101minhkhai@gmail.com' };
const headers = ['Project Key', 'Issue Type', 'Issue ID', 'Issue Key', 'Parent', 'Source ID', 'Epic Name', 'Summary', 'Description', 'Acceptance Criteria', 'Checklist', 'Assignee', 'Proposed Role', 'Proposed Assignee Email', 'Reviewer Requirement', 'Status', 'Priority', 'Proposed Priority', 'Original Estimate', 'Simulation Estimate Hours', 'Simulation Points', 'Proposed Sprint', 'Depends On Source IDs', 'Integration With Source IDs', 'Labels', 'Approval'];
const taskChecklist = [
  'BA chốt yêu cầu/AC, quyền và trường hợp lỗi; PM duyệt phạm vi.',
  'BE/FE có bản code, unit/integration test và review độc lập; không tự approve code.',
  'Bản Test tập trung sẵn sàng; Task READY FOR TEST trước khi QA chạy test.',
  'QA lưu test case, actual/expected và kết quả; mọi Fix Bug được sửa và retest đạt.',
  'Lead review → Retest nếu cần hoặc ghi rõ không cần → BA xác nhận → PM duyệt.',
  'Mọi Subtask bắt buộc DONE; deploy Test và smoke đạt; PM mới chuyển Task DONE.',
  'Không chốt điểm thật từ estimate mô phỏng; giữ baseline khi thay đổi phạm vi.'
].join('\n');
const rows = [];
const add = (type, id, parent, summary, role, extra = {}) => {
  const row = { 'Project Key': 'QAG3', 'Issue Type': type, 'Issue ID': String(rows.length + 1), 'Issue Key': '', Parent: parent,
    'Source ID': id, 'Epic Name': '', Summary: summary, Description: '', 'Acceptance Criteria': '', Checklist: '', Assignee: '',
    'Proposed Role': role, 'Proposed Assignee Email': emails[role], 'Reviewer Requirement': '', Status: 'NEW', Priority: '',
    'Proposed Priority': id.startsWith('AUTH') || id === 'E01' ? 'High' : 'Medium', 'Original Estimate': '',
    'Simulation Estimate Hours': '', 'Simulation Points': '', 'Proposed Sprint': '', 'Depends On Source IDs': '',
    'Integration With Source IDs': '', Labels: `qag3-wbs source-${id}`, Approval: 'DRAFT', ...extra };
  rows.push(row);
  return row;
};
const roleHours = Object.fromEntries(Object.keys(emails).map(r => [r, 0]));
for (const epic of sources) {
  assert.notEqual(epic.epicId, '11');
  const er = add('Epic', `E${epic.epicId}`, '', epic.name, 'PM', {
    'Epic Name': epic.name,
    Description: `Phạm vi: ${epic.stories.map(s => s.id).join(', ')}. Epic quản lý kết quả bàn giao, không phải một Task tổng.`,
    'Acceptance Criteria': 'Có ít nhất một Task trong phạm vi đã duyệt và mọi Task hiện thời DONE.\nKiểm thử tích hợp/bàn giao đạt, không lỗi chặn; PM nghiệm thu trực tiếp.\nCó snapshot phạm vi; không tự DONE hoặc sửa kết quả Sprint đã chốt.',
    Checklist: 'PM duyệt owner/phạm vi/AC trước READY.\nChỉ REVIEW sau khi đọc toàn bộ Task hiện thời.\nPM-only nghiệm thu/hủy/khôi phục; lý do bắt buộc và Resolution đúng.\nThay đổi phạm vi theo jira-workflows.md; không xóa Task để làm đẹp tiến độ.',
    'Reviewer Requirement': 'PM đã xác minh project role; không phải quyền edit issue',
  });
  for (const story of epic.stories) {
    assert.equal(story.ac.length, 2);
    const p = planById.get(story.id);
    assert.ok(p, `Thiếu phân tích ${story.id}`);
    const [, ba, be, fe, qa, beHours, feHours, qaHours, depends, proposedSprint] = p;
    const baHours = beHours >= 10 || qaHours >= 7 ? 4 : 3;
    const pmHours = qaHours >= 7 ? 3 : 2;
    const total = baHours + beHours + feHours + qaHours + pmHours;
    const title = story.story.split('tôi muốn ')[1].split(' để ')[0].replace(/\.$/, '');
    const integrations = story.id === 'TSK-04' ? 'NOT-01' : story.id === 'PRJ-04' ? 'NOT-01' : story.id === 'CMT-05' ? 'NOT-03' : story.id === 'KAN-02' || story.id === 'BUG-05' ? 'NOT-02' : story.id === 'NOT-01' ? 'NOT-04 NOT-05' : '';
    // shortcut: undated five-sprint proposal; schedule only after verified capacity and refinement.
    const sprint = ['NOT-01', 'NOT-04', 'NOT-05'].includes(story.id) ? 2 : ['NOT-02', 'NOT-03'].includes(story.id) ? 4 : proposedSprint;
    const tr = add('Task', story.id, er['Issue ID'], `${story.id} — ${title[0].toUpperCase()}${title.slice(1)}`, 'PM', {
      Description: `${story.story}\n\nAcceptance Criteria nguồn:\n${story.ac.map((a, i) => `${i + 1}. ${a}`).join('\n')}\n\nPhân tích: ${ba}.\nTask là đơn vị bàn giao chức năng; owner PM điều phối, công việc cá nhân nằm ở Subtask.\nEstimate chỉ là đề xuất mô phỏng Junior, chưa phải cam kết hoặc thời gian thực.`,
      'Acceptance Criteria': story.ac.join('\n'), Checklist: taskChecklist,
      'Reviewer Requirement': 'Lead được PM chỉ định → QA retest khi cần → BA xác nhận → PM duyệt',
      'Simulation Estimate Hours': total, 'Simulation Points': total, 'Proposed Sprint': `S${sprint} (đề xuất, chưa chốt lịch)`,
      'Depends On Source IDs': depends, 'Integration With Source IDs': integrations,
    });
    const work = [
      ['BA', baHours, `Đặc tả và AC cho ${story.id}`, `${ba}. Đầu ra: mini-spec/wireframe cần thiết, ma trận quyền, dữ liệu mẫu và test scenarios có thể kiểm chứng.`,
        'Yêu cầu khớp hai AC nguồn; quyết định chưa rõ được PM duyệt.\nBàn giao hợp đồng dữ liệu/hành vi cho BE/FE/QA; BA xác nhận UAT sau Lead/retest tại checklist Task.', '', 'PM review đặc tả; BA xác nhận UAT ở Task sau kiểm thử'],
      ['BE', beHours, `Backend cho ${story.id}`, `${be}. Đầu ra: logic/dữ liệu/API và kiểm tra tự động; dùng lại nền tảng hiện có, không khóa stack chưa chốt.`,
        'Bao phủ logic và validation của hai AC; xác minh quyền ở server, không chỉ UI.\nCó unit/integration tests, xử lý lỗi/request lặp theo nghiệp vụ; có PR và bản Test.\nReviewer độc lập duyệt code; không tự approve phần mình viết.', `${story.id}-BA`, 'Reviewer code độc lập có chuyên môn do PM chỉ định'],
      ['FE', feHours, `Frontend cho ${story.id}`, `${fe}. Đầu ra: màn hình/thao tác hoàn chỉnh nối dữ liệu thật, không chỉ từng nút/ô nhập.`,
        'Luồng chính và lỗi theo AC hoạt động; loading/empty/error, keyboard và safe rendering phù hợp.\nKhông hiển thị dữ liệu ngoài quyền; trạng thái UI khớp kết quả server.\nCó test UI/tích hợp, PR và code review độc lập; dùng mock hợp đồng chỉ trong phát triển.', `${story.id}-BA`, 'Reviewer code độc lập có chuyên môn do PM chỉ định'],
      ['QA', qaHours, `Kiểm thử và retest cho ${story.id}`, `Viết test case từ hai AC và chạy trên bản Test: ${qa}. Đầu ra: test cases, test execution, bug/retest evidence.`,
        'Có case cho hai AC, luồng lỗi, dữ liệu rỗng/quyền và rủi ro cụ thể đã nêu.\nChỉ chạy test khi Task READY FOR TEST; mọi lỗi có bước tái hiện, mức độ, Dev gốc và Fix Bug Subtask.\nKhông DONE khi còn lỗi chưa sửa/chưa retest; Lead yêu cầu retest thì bổ sung bằng chứng trước BA/PM duyệt.', `${story.id}-BE ${story.id}-FE`, 'Lead/PM đối soát kết quả và Fix Bug; QA không tự xác nhận lỗi chưa retest'],
      ['PM', pmHours, `Nghiệm thu và bàn giao ${story.id}`, `Điều phối review, nghiệm thu hai AC của ${story.id}; xác nhận bản Test và bàn giao tính năng. Đầu ra: checklist duyệt, thông tin phiên bản/Test và biên bản bàn giao.`,
        'Có Lead review, retest hoặc lý do không cần, BA xác nhận và PM approval có bằng chứng.\nCác Subtask BA/BE/FE/QA và Fix Bug DONE; deploy Test + smoke đạt, không mặc định Production.\nThay đổi phạm vi có phê duyệt và snapshot; PM hoàn tất Subtask bàn giao trước khi chuyển Task DONE.', `${story.id}-QA`, 'BA xác nhận phạm vi; PM nghiệm thu Task bằng role hợp lệ'],
    ];
    for (const [role, hours, summary, description, checklist, prerequisites, reviewer] of work) {
      roleHours[role] += hours;
      add('Sub-task', `${story.id}-${role}`, tr['Issue ID'], summary, role, {
        Description: `${description}\n\nPhạm vi kiểm thử nguồn:\n${story.ac.join('\n')}\n\nDữ liệu estimate: mô phỏng Junior, đề xuất chờ PM/refinement; không phải worklog thực.`,
        Checklist: checklist, 'Reviewer Requirement': reviewer, 'Simulation Estimate Hours': hours, 'Simulation Points': hours,
        'Proposed Sprint': tr['Proposed Sprint'], 'Depends On Source IDs': prerequisites,
      });
    }
  }
}
assert.equal(rows.length, 329);
const ids = new Map(rows.map(r => [r['Source ID'], r]));
const numericIds = new Map(rows.map(r => [r['Issue ID'], r]));
assert.equal(ids.size, rows.length);
assert.equal(numericIds.size, rows.length);
assert.deepEqual(Object.fromEntries(['Epic', 'Task', 'Sub-task'].map(t => [t, rows.filter(r => r['Issue Type'] === t).length])), { Epic: 11, Task: 53, 'Sub-task': 265 });
for (const r of rows) {
  assert.equal(r['Project Key'], 'QAG3');
  assert.equal(r.Assignee, '');
  assert.equal(r['Original Estimate'], '');
  assert.equal(r.Approval, 'DRAFT');
  if (r.Parent) assert.equal(numericIds.get(r.Parent)?.['Issue Type'], r['Issue Type'] === 'Task' ? 'Epic' : 'Task');
  for (const id of `${r['Depends On Source IDs']} ${r['Integration With Source IDs']}`.split(/\s+/).filter(Boolean)) assert.ok(ids.has(id), `Phụ thuộc không tồn tại ${id}`);
  for (const value of Object.values(r)) assert.ok(!/^[=+\-@\t\r]/.test(String(value)), `CSV formula-like field ${r['Source ID']}`);
}
const visited = new Set(), visiting = new Set();
function visit(id) {
  assert.ok(!visiting.has(id), `Chu trình phụ thuộc ${id}`);
  if (visited.has(id)) return;
  visiting.add(id);
  for (const dependency of ids.get(id)['Depends On Source IDs'].split(/\s+/).filter(Boolean)) visit(dependency);
  visiting.delete(id);
  visited.add(id);
}
for (const id of ids.keys()) visit(id);
const taskHours = rows.filter(r => r['Issue Type'] === 'Task').reduce((sum, r) => sum + r['Simulation Estimate Hours'], 0);
assert.equal(taskHours, Object.values(roleHours).reduce((a, b) => a + b, 0));
for (const t of rows.filter(r => r['Issue Type'] === 'Task')) {
  const children = rows.filter(r => r.Parent === t['Issue ID']);
  assert.deepEqual(children.map(r => r['Proposed Role']).sort(), ['BA', 'BE', 'FE', 'PM', 'QA']);
  assert.equal(children.reduce((s, r) => s + r['Simulation Estimate Hours'], 0), t['Simulation Estimate Hours']);
}
const matrix = [headers, ...rows.map(r => headers.map(h => r[h]))];
const wb = Workbook.create();
const sheet = wb.worksheets.add('WBS');
sheet.getRange(`A1:Z${matrix.length}`).values = matrix;
sheet.showGridLines = false;
sheet.getRange(`A1:Z${matrix.length}`).format.font = { name: 'Arial', size: 11 };
sheet.getRange('A1:Z1').format.fill = '#1F4E78';
sheet.getRange('A1:Z1').format.font = { name: 'Arial', size: 11, color: '#FFFFFF', bold: true };
sheet.getRange('A1:F10').format.columnWidth = 16;
sheet.freezePanes.freezeRows(1);
wb.recalculate();
console.log((await wb.inspect({ kind: 'table', range: 'WBS!A1:H4', include: 'values', tableMaxRows: 4, tableMaxCols: 8, maxChars: 1200 })).ndjson);
const authored = sheet.getRange(`A1:Z${matrix.length}`).values;
assert.deepEqual(authored, matrix);
// shortcut: this runtime has no documented CSV exporter; serialize verified authored cells as RFC 4180 CSV.
const csv = '\uFEFF' + authored.map(r => r.map(v => `"${String(v ?? '').replaceAll('"', '""')}"`).join(',')).join('\r\n') + '\r\n';
assert.ok(Buffer.byteLength(csv) > 100000);
const preview = await wb.render({ sheetName: 'WBS', range: 'A1:F9', scale: 1.5, format: 'png' });
await fs.writeFile(path.join(here, 'preview.png'), new Uint8Array(await preview.arrayBuffer()));
let existing;
try { existing = await fs.readFile(output); } catch (error) { if (error.code !== 'ENOENT') throw error; }
if (existing && !existing.equals(Buffer.from(csv))) {
  // Only replace this builder's verified first draft, never an independently edited CSV.
  assert.equal(createHash('sha256').update(existing).digest('hex'), '25c3f960ec513a86a2cb419f9f6c9dcf69deac1239babb7514ff8f0da4f8db39');
}
if (!existing || !existing.equals(Buffer.from(csv))) await fs.writeFile(output, csv, { encoding: 'utf8', flag: existing ? 'w' : 'wx' });
console.log(JSON.stringify({ output, counts: { Epic: 11, Task: 53, Subtask: 265 }, sourceAcceptanceCriteria: 106, simulatedHours: taskHours, roleHours,
  csvSHA256: createHash('sha256').update(csv).digest('hex'), sourceSHA256: createHash('sha256').update(await fs.readFile(sourcePath)).digest('hex'),
  tests: ['live Word source exact match', 'all 53 decompositions', 'unique IDs', 'valid parent hierarchy', '5 roles per Task', 'all references exist', 'prerequisite DAG', 'estimate rollups/no double count', 'no real assignee/worklog/estimate', 'formula injection guard', 'artifact cells exact match'] }, null, 2));
