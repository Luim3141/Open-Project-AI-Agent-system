"""Private review from a frozen complete monitor cycle; no Jira writes."""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'jira-bot'
source = json.loads((DATA / 'EPIC_REVIEW_RUNTIME_2026-10-15.json').read_text(encoding='utf-8'))
catalog = json.loads((DATA / 'EPIC_REVIEW_SOURCE_2026-10-15.json').read_text(encoding='utf-8'))
runtime = source['state']
assert runtime['readComplete'] and runtime['projectKey'] == 'QAG3'
assert catalog['isLast'] is True
assert source['processAndEventVerified'] is True
assert datetime.fromisoformat(source['event']['sourceObservedAtUtc']) == datetime.fromisoformat(runtime['observedAtUtc'])
assert source['event']['readComplete'] is True
members = [
 ('Hiệp', 'BA', '712020:0d04982c-00bf-46af-b3a7-446d0f44edfb', 'Đặc tả và tiêu chí nghiệm thu'),
 ('Đức', 'BE', '712020:7141e4e4-a663-4691-a3ec-fec3efb6df5a', 'Phần xử lý Backend'),
 ('Trần Thế Duy', 'FE', '712020:da12735c-4da8-46d6-801d-46c9898c681d', 'Giao diện Frontend'),
 ('Hưng', 'Tester', '712020:94d1f95d-9618-4f25-8284-41105336b942', 'Kiểm thử và retest'),
 ('Khai Dương', 'PM', '712020:47b24428-aa71-4363-b68f-29ed2285aad8', 'Nghiệm thu và bàn giao'),
]
scope_keys = {k for groups in runtime['memberAssessment']['members'].values()
              for group in groups.values() for k in group['issueKeys']}
items = {x['key']: x for x in runtime['issues'] if x['key'] in scope_keys}
assert len(items) == len(scope_keys) and len(items) == 329
done = lambda x: x['category'] == 'done' and not x['cancelled']
epics = [x for x in catalog['issues'] if x['key'] in items
         and items[x['key']]['kind'] == 'Epic' and done(items[x['key']])]
assert epics and all(x['fields']['status']['statusCategory']['key'] == 'done' for x in epics)
profiles = []
for epic in epics:
    tasks = [x for x in items.values() if x['kind'] == 'Task' and x['parentKey'] == epic['key']]
    task_keys = {x['key'] for x in tasks}
    children = [x for x in items.values() if x['kind'] == 'Subtask' and x['parentKey'] in task_keys]
    assert tasks and children and all(x['parentKnown'] for x in tasks + children)
    rows = []
    for name, role, account, duty in members:
        assigned = sorted([x for x in children if x['assigneeKnown'] and x['assigneeAccountId'] == account], key=lambda x: int(x['key'].split('-')[1]))
        rows.append({'name': name, 'role': role, 'accountId': account, 'duty': duty,
                     'total': len(assigned), 'done': sum(done(x) for x in assigned),
                     'keys': [x['key'] for x in assigned]})
    assert sum(r['total'] for r in rows) == len(children)
    profiles.append({'epic': epic, 'tasks': tasks, 'children': children, 'rows': rows})
all_tasks = [x for p in profiles for x in p['tasks']]
all_subs = [x for p in profiles for x in p['children']]
assert len({x['key'] for x in all_tasks}) == len(all_tasks)
assert len({x['key'] for x in all_subs}) == len(all_subs)

doc = Document()
section = doc.sections[0]
section.page_width, section.page_height = Inches(8.5), Inches(11)
section.top_margin = section.bottom_margin = Inches(.65)
section.left_margin = section.right_margin = Inches(.75)
for style_name, size in [('Normal', 11), ('Title', 25), ('Heading 1', 18), ('Heading 2', 13)]:
    s = doc.styles[style_name]
    s.font.name, s.font.size, s.font.color.rgb = 'Arial', Pt(size), RGBColor(0, 0, 0)
    s.paragraph_format.space_after = Pt(8)
    s.paragraph_format.line_spacing = 1.12
    border = s.element.find('.//' + qn('w:pBdr'))
    if border is not None:
        border.getparent().remove(border)
doc.core_properties.title = 'Đánh giá phần việc trong các Epic đã Done của QAG3'
doc.core_properties.author = 'QAG3 Project Operations'

def p(text):
    paragraph = doc.add_paragraph(text)
    paragraph.paragraph_format.space_before = Pt(4)
    return paragraph

def table(headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.autofit = False
    for col, w in zip(t.columns, widths):
        col.width = Inches(w)
    borders = OxmlElement('w:tblBorders')
    for side in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        e = OxmlElement('w:' + side)
        for k, v in [('val','single'), ('sz','4'), ('color','D9D9D9')]: e.set(qn('w:' + k), v)
        borders.append(e)
    t._tbl.tblPr.append(borders)
    for row, values in [(t.rows[0], headers)] + [(t.add_row(), r) for r in rows]:
        for cell, value, width in zip(row.cells, values, widths):
            cell.width = Inches(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cell.text = str(value)
            tcpr = cell._tc.get_or_add_tcPr()
            margins = OxmlElement('w:tcMar')
            for side in ['top','left','bottom','right']:
                e = OxmlElement('w:' + side); e.set(qn('w:w'), '95'); e.set(qn('w:type'), 'dxa'); margins.append(e)
            tcpr.append(margins)
            for para in cell.paragraphs:
                para.paragraph_format.space_after = Pt(2)
                for r in para.runs: r.font.size = Pt(10)
        trpr = row._tr.get_or_add_trPr(); trpr.append(OxmlElement('w:cantSplit'))
    t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
    for cell in t.rows[0].cells:
        fill = OxmlElement('w:shd'); fill.set(qn('w:fill'), 'DFEAF4'); cell._tc.get_or_add_tcPr().append(fill)
        for r in cell.paragraphs[0].runs: r.bold = True
    return t

stamp = datetime.fromisoformat(runtime['observedAtUtc']).astimezone(timezone.utc).strftime('%H:%M:%S UTC ngày %d/%m/%Y')
doc.add_heading('Đánh giá phần việc trong các Epic đã Done của QAG3', 0)
p('Báo cáo riêng cho chủ dự án ngày 15 tháng 10 năm 2026. Dữ liệu học tập mô phỏng, không phải đánh giá năng lực lao động thực tế.')
p(f'Bot đã thu đầy đủ {len(runtime["issues"])} issue qua MCP. Trong WBS, {len(epics)} Epic đang Done, chứa {sum(done(x) for x in all_tasks)}/{len(all_tasks)} Task và {sum(done(x) for x in all_subs)}/{len(all_subs)} Subtask Done. Mỗi thành viên được trình bày theo đúng phần việc hiện đang được giao.')
doc.add_heading('Kết luận chính', 1)
p('Các tỷ lệ dưới đây đo mức hoàn tất trên Jira. Chúng không đo tốc độ lập trình, số lỗi thực tế hoặc mức độ hợp tác. Không xếp hạng thành viên vì worklog, lịch và tiến độ đã được giả lập để học vận hành dự án.')
table(['Epic đã Done', 'Task Done', 'Subtask Done'], [[x['epic']['key'] + ' ' + x['epic']['fields']['summary'], f"{sum(done(i) for i in x['tasks'])}/{len(x['tasks'])}", f"{sum(done(i) for i in x['children'])}/{len(x['children'])}"] for x in profiles], [4.3,1.1,1.6])
p(f'Nguồn thu của runner: {stamp}. Sáu fixture kiểm thử được loại theo phạm vi memberAssessment. Epic QAG3-212 chưa Done nên không nằm trong mẫu đánh giá này, dù một số Task con đã Done.')

for index, profile in enumerate(profiles, 1):
    doc.add_page_break()
    e = profile['epic']; f = e['fields']; tasks = profile['tasks']; subs = profile['children']
    doc.add_heading(f"{index} {f['summary'].replace('/', 'và').replace('&', 'và')}", 1)
    p(f"{e['key']} · Trạng thái Epic Done · https://luimjiraqldapm.atlassian.net/browse/{e['key']}")
    start = f.get('customFields',{}).get('Start date',{}).get('value','UNKNOWN')
    p(f"Lịch kế hoạch mô phỏng: {start} đến {f.get('duedate','UNKNOWN')}. Đây không phải khoảng thời gian làm việc đã được xác minh.")
    p(f"Mức hoàn tất quan sát được: {sum(done(x) for x in tasks)}/{len(tasks)} Task và {sum(done(x) for x in subs)}/{len(subs)} Subtask. Mỗi hàng dưới đây là phần việc Subtask của một thành viên, không cộng Task và Epic vào cùng mẫu số.")
    rows=[]
    for r in profile['rows']:
        ratio = f"{100*r['done']/r['total']:.0f}%" if r['total'] else 'Không có phạm vi'
        rows.append([r['name']+'\n'+r['role'], f"{r['done']}/{r['total']}\n{ratio}", ', '.join(r['keys']) or 'Không có'])
    table(['Thành viên và vai trò', 'Done trên số giao', 'Subtask làm căn cứ'], rows, [1.55,1.05,4.4])
    doc.add_heading('Nhận định cho từng phần việc', 2)
    p('Hiệp phụ trách đặc tả và tiêu chí nghiệm thu; Đức phụ trách Backend; Trần Thế Duy phụ trách Frontend; Hưng phụ trách kiểm thử và retest; Khai Dương phụ trách nghiệm thu và bàn giao. Bảng phản ánh assignee hiện tại, không chứng minh chính người đó đã thực hiện mọi thao tác.')
    pm_tasks = [x for x in tasks if x['assigneeAccountId'] == members[-1][2]]
    p(f"Riêng PM đang được giao thêm {len(pm_tasks)} Task điều phối và Epic này. Các cấp này chỉ báo riêng để tránh tính một chức năng thành nhiều thành tích.")
    doc.add_heading('Hiệu suất và việc cần kiểm tra', 2)
    p('Đánh giá hoàn tất mô phỏng: phần việc đã ở Done theo số liệu trong bảng. Đánh giá đúng hạn, chất lượng, phối hợp, chủ động và đóng góp: CHƯA ĐỦ BẰNG CHỨNG; không chấm điểm tổng. Nếu cần đánh giá thật, PM cần đối chiếu sản phẩm, kết quả test và lịch sử bàn giao có tác giả.')
    p('Task thuộc Epic: '+', '.join(x['key'] for x in sorted(tasks,key=lambda x:int(x['key'].split('-')[1])))+'.')

doc.add_page_break()
doc.add_heading('Tổng hợp theo thành viên', 1)
p('Chỉ xét bảy Epic WBS đã Done, không đưa các Epic đang làm hoặc NEW vào mẫu số. Tỷ lệ trong mẫu Done có thiên lệch chọn mẫu: không dùng để kết luận toàn bộ dự án đã hoàn thành.')
table(['Thành viên', 'Phần việc mô phỏng', 'Subtask Done'], [[name+'\n'+role, duty, f"{sum(r['done'] for pr in profiles for r in pr['rows'] if r['accountId']==account)}/{sum(r['total'] for pr in profiles for r in pr['rows'] if r['accountId']==account)}"] for name,role,account,duty in members], [1.65,3.65,1.7])
doc.add_heading('Nhận xét để cải thiện cách vận hành', 2)
for text in [
 'BA nên gắn bản đặc tả và tiêu chí nghiệm thu vào từng Task để người kiểm tra hiểu thế nào là làm xong.',
 'BE và FE nên gắn commit hoặc bản demo, ghi rõ phiên bản đã review và đã test. Đây là đề xuất thu bằng chứng, không phải kết luận hiện tại làm kém.',
 'Tester nên lưu kết quả từng test case và lần retest, kèm phiên bản. Số Subtask Done không thay cho tỷ lệ lỗi hoặc độ phủ kiểm thử.',
 'PM nên chốt bàn giao và giữ lịch sử thay đổi phạm vi. Không lấy tổng số Epic, Task và Subtask làm tổng năng suất.',
 'Hiệp kiêm BA và PM nhưng phần việc ở bảng được đếm theo assignee của Subtask, không nhân đôi vì kiêm nhiều vai trò.'
]: p(text)

doc.add_page_break()
doc.add_heading('Cách đọc số liệu và trạng thái bot', 1)
table(['Chiều đánh giá', 'Kết luận'], [[x,'Chưa đủ bằng chứng để chấm'] for x in ['Giao việc đúng hẹn','Chất lượng','Phối hợp','Trách nhiệm và giao tiếp','Đóng góp kỹ thuật hoặc nghiệp vụ']], [3.25,3.75])
p('Điểm tổng để trống, không coi thiếu dữ liệu là 0 điểm. Báo cáo không dùng làm căn cứ tuyển dụng, lương thưởng hay xếp hạng. Mọi kết quả học tập cần được ghi rõ là mô phỏng.')
p('Công thức tỷ lệ hoàn tất của một thành viên trong một Epic: số Subtask của người đó thuộc Epic và ở Done, không hủy, chia tổng Subtask đang được giao trong Epic. Nếu tổng bằng 0 thì không có phạm vi, không ghi 100%. Liên kết được đi theo Subtask → Task → Epic, không suy từ tên hoặc mã liền nhau.')
p(f"Bot đang chạy theo chu kỳ {source['event']['intervalSeconds']} giây. Process python.exe PID {source['event']['pid']}, runId {source['event']['runId']}, cycle {source['event']['cycle']}. Windows task và heartbeat cũ đã được bật lại; lịch chat giữ mỗi giờ phút 15 và chỉ báo biến động có ý nghĩa.")
p(f"Gemini: {runtime['geminiStatus']}. Báo cáo này tính từ dữ liệu runner và nhận định local, không tuyên bố có đánh giá Gemini live. Process và sự kiện hiện hành đã khớp; chưa nghiệm thu lại vận hành khi reboot, đóng app, logoff hoặc sleep.")
p('MCP session check: identity và accessible resources PASS; getJiraIssue QAG3-1 xác minh project10002; searchJiraIssuesUsingJql đọc hết Epic tới isLast=true. Runner dùng official_atlassian_mcp, readComplete=true. Không dùng browser, không sửa issue hoặc automation Jira, không gửi email hay bình luận nhân sự.')
p('Nguồn kiểm tra local: jira-bot/EPIC_REVIEW_SOURCE_2026-10-15.json và jira-bot/EPIC_REVIEW_RUNTIME_2026-10-15.json. Snapshot nhiều request không nguyên tử. Chưa đọc mới toàn bộ changelog, worklog, linked Bug hoặc bằng chứng QA cho từng người; do đó không suy ra cycle time, trễ hạn, tỷ lệ lỗi hay năng lực thực tế.')

out = ROOT / 'Danh_gia_thanh_vien_theo_Epic_Done_QAG3_2026-10-15.docx'
assert not out.exists(), 'Refusing overwrite of existing report'
doc.save(out)
check = Document(out)
assert len(check.tables) == len(epics)+3
assert len([x for x in check.paragraphs if x.text.startswith('Task thuộc Epic:')]) == len(epics)
print(json.dumps({'file':str(out),'doneEpics':len(epics),'tasks':len(all_tasks),'doneTasks':sum(done(x) for x in all_tasks),'subtasks':len(all_subs),'doneSubtasks':sum(done(x) for x in all_subs),'memberSubtaskTotals':{name:sum(r['total'] for pr in profiles for r in pr['rows'] if r['accountId']==account) for name,role,account,duty in members}},ensure_ascii=False))
