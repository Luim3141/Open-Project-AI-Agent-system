from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(r'D:\AI project\QLDAPM chat')
OUT = ROOT / 'Trinh_bay_Workflow_QAG3_2026-10-09.docx'
if OUT.exists():
    assert Document(OUT).core_properties.title == 'Workflow Epic Task và Subtask QAG3'
doc = Document()
s = doc.sections[0]
s.page_width, s.page_height = Inches(8.5), Inches(11)
s.top_margin = s.bottom_margin = Inches(.65)
s.left_margin = s.right_margin = Inches(.7)
for name, size in [('Normal', 11), ('Title', 23), ('Heading 1', 18), ('Heading 2', 14)]:
    st = doc.styles[name]
    st.font.name = 'Calibri'
    st.font.size = Pt(size)
    st.font.color.rgb = RGBColor(0, 0, 0)
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.line_spacing = 1.05
for border in doc.styles.element.xpath('.//w:pBdr'):
    border.getparent().remove(border)
doc.core_properties.title = 'Workflow Epic Task và Subtask QAG3'
doc.core_properties.author = 'Nhóm QLDAPM'

def p(text, style=None):
    return doc.add_paragraph(text, style)

def h(text, page=False):
    x = doc.add_heading(text, 1)
    x.paragraph_format.page_break_before = page

def table(headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.autofit = False
    for c, w in zip(t.columns, widths): c.width = Inches(w)
    for c, value in zip(t.rows[0].cells, headers): c.text = value
    repeat = OxmlElement('w:tblHeader')
    t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for row in rows:
        for c, value in zip(t.add_row().cells, row): c.text = value
    for i, row in enumerate(t.rows):
        row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        for j, cell in enumerate(row.cells):
            cell.width = Inches(widths[j])
            pr = cell._tc.get_or_add_tcPr()
            shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear'); shd.set(qn('w:fill'), '24476A' if i == 0 else ('F1F4F7' if i % 2 == 0 else 'FFFFFF')); pr.append(shd)
            margins = OxmlElement('w:tcMar')
            for side in ['top', 'left', 'bottom', 'right']:
                el = OxmlElement('w:' + side); el.set(qn('w:w'), '85'); el.set(qn('w:type'), 'dxa'); margins.append(el)
            pr.append(margins)
            for para in cell.paragraphs:
                para.paragraph_format.space_after = Pt(1)
                para.paragraph_format.line_spacing = 1.0
                for r in para.runs:
                    r.font.size = Pt(10.5)
                    r.bold = i == 0
                    if i == 0: r.font.color.rgb = RGBColor(255,255,255)
    borders = OxmlElement('w:tblBorders')
    for side in ['top','left','bottom','right','insideH','insideV']:
        el = OxmlElement('w:' + side); el.set(qn('w:val'),'single'); el.set(qn('w:sz'),'4'); el.set(qn('w:color'),'D9D9D9'); borders.append(el)
    t._tbl.tblPr.insert_element_before(borders, 'w:shd', 'w:tblLayout', 'w:tblCellMar', 'w:tblLook')
    return t

def field(para, instruction, cache=''):
    for typ in ['begin', 'separate', 'end']:
        if typ == 'separate':
            el = OxmlElement('w:instrText'); el.set(qn('xml:space'),'preserve'); el.text = instruction; para.add_run()._r.append(el)
        el = OxmlElement('w:fldChar'); el.set(qn('w:fldCharType'),typ); para.add_run()._r.append(el)
        if typ == 'separate' and cache: para.add_run(cache)

p('Workflow Epic Task và Subtask QAG3', 'Title')
p('Hướng dẫn vận hành nhóm PM · BA · BE · FE · Tester | Cập nhật 09/10/2026')
p('Epic quản lý phạm vi và nghiệm thu; Task quản lý bàn giao chức năng; Subtask quản lý đầu việc cá nhân. Tên trạng thái giữ nguyên như cấu hình Jira.')
p('Trạng thái triển khai: ba workflow đã lưu nhưng đang Inactive, chưa áp dụng vào QAG3. Các điều kiện nghiệp vụ dưới đây là tiêu chuẩn cần đạt; mục Cấu hình hiện có nêu riêng phần đã lưu trên Jira.')
toc = p('')
field(toc, ' TOC \\o "1-1" \\h \\z \\u ', 'Epic · Task · Subtask')

h('Workflow Epic')
p('QAG3 Epic Lifecycle v1 | NEW → READY → IN PROGRESS → REVIEW → DONE; nhánh hủy là CANCELLED.')
epic = [
('NEW', 'Làm rõ mục tiêu, phạm vi và tiêu chí nghiệm thu.'),
('READY', 'PM duyệt phạm vi; có owner, tiêu chí rõ và ít nhất một Task được duyệt.'),
('IN PROGRESS', 'Ít nhất một Task bắt đầu làm; các Task có thể ở những giai đoạn khác nhau.'),
('REVIEW', 'Có Task trong phạm vi và tất cả đã Done; chờ nghiệm thu tổng thể.'),
('DONE', 'PM nghiệm thu mục tiêu, kiểm thử tích hợp và bàn giao; không còn lỗi chặn.'),
('CANCELLED', 'PM chủ động hủy và ghi lý do; không tự hủy hoặc xóa Task con.')]
table(['Trạng thái', 'Ý nghĩa và điều kiện nghiệp vụ'], epic, [1.45,5.65])
doc.add_heading('Các nhánh và thay đổi phạm vi', 2)
table(['Chuyển trạng thái', 'Khi nào sử dụng'], [
('READY → NEW', 'Reanalyse: cần phân tích lại trước khi bắt đầu.'),
('REVIEW → IN PROGRESS', 'Return: nghiệm thu không đạt hoặc thêm Task chưa Done đã được PM duyệt.'),
('DONE → IN PROGRESS', 'Reopen: sửa thiếu sót thuộc phạm vi đã duyệt; ghi lý do và giữ lịch sử nghiệm thu.'),
('NEW / READY / IN PROGRESS / REVIEW → CANCELLED', 'Cancel Epic: PM duyệt hủy, có lý do; không có cạnh hủy trực tiếp từ Done.'),
('CANCELLED → NEW', 'Restore: PM khôi phục, ghi lý do và duyệt lại phạm vi.')], [2.5,4.6])
p('Thêm Task vào Epic In Progress không đổi trạng thái. Tính năng mở rộng phiên bản sau nên tạo Epic mới liên kết Epic cũ. Sửa câu chữ không tự mở lại Epic. Tiến độ tính theo Task Done / tổng Task hiện tại; Epic rỗng là “Chưa có phạm vi”.')
p('Cấu hình hiện có: Accept Epic đặt Resolution = Done; Reopen và Restore xóa Resolution. Chưa có gate native cho PM, Epic rỗng, tất cả Task Done hoặc lý do bắt buộc; automation đối soát Epic chưa bật.')

h('Workflow Task', True)
p('QAG3 Task Delivery v1 | Luồng chính gồm 10 trạng thái, dùng để bàn giao một chức năng.')
p('NEW → IN ANALYSIS → READY FOR DEV → IN PROGRESS → CODE REVIEW → READY FOR TEST → IN TESTING → REVIEW → READY FOR RELEASE → DONE')
task = [
('NEW → IN ANALYSIS', 'Start analysis', 'BA bắt đầu làm rõ yêu cầu và phạm vi.'),
('IN ANALYSIS → READY FOR DEV', 'Analysis done', 'Yêu cầu, tiêu chí nghiệm thu và phạm vi đủ rõ để phát triển.'),
('READY FOR DEV → IN PROGRESS', 'Start dev', 'BE/FE nhận việc; các Subtask và phụ thuộc đã được xác định.'),
('IN PROGRESS → CODE REVIEW', 'Submit code', 'Có mã nguồn, kết quả tự kiểm tra và bằng chứng để reviewer xem.'),
('CODE REVIEW → READY FOR TEST', 'Approve code', 'Reviewer duyệt code; có bản build Test và test case phù hợp.'),
('READY FOR TEST → IN TESTING', 'Start test', 'Tester có môi trường, dữ liệu và bản build sẵn sàng.'),
('IN TESTING → REVIEW', 'Pass testing', 'Kiểm thử đạt; không còn lỗi chặn hoặc lỗi chưa retest trong phạm vi nghiệm thu.'),
('REVIEW → READY FOR RELEASE', 'Approve', 'Lead review, retest nếu cần, BA xác nhận và PM duyệt checklist.'),
('READY FOR RELEASE → DONE', 'Deploy', 'Triển khai lên Test tập trung, smoke test đạt; mọi Subtask và checklist hoàn tất.')]
assert len(task) == 9 and len(epic) == 6
table(['Chuyển trạng thái', 'Thao tác', 'Điều kiện nghiệp vụ'], task, [2.4,1.15,3.55])
doc.add_heading('Các nhánh trả lại và mở lại', 2)
table(['Nhánh', 'Chuyển trạng thái', 'Điều kiện nghiệp vụ'], [
('Code rejected', 'CODE REVIEW → IN PROGRESS', 'Reviewer chỉ rõ phần code cần sửa.'),
('Bug found', 'IN TESTING → IN PROGRESS', 'Tester ghi lỗi, cách tái hiện và người xử lý; sửa xong đi lại qua review và test.'),
('ReDev', 'REVIEW → IN PROGRESS', 'BA/PM hoặc reviewer yêu cầu sửa kết quả trong phạm vi Task.'),
('Retest', 'REVIEW → IN TESTING', 'Cần kiểm thử lại; ghi lý do và phạm vi retest.'),
('Reopen', 'DONE → IN PROGRESS', 'Phát hiện thiếu sót sau bàn giao; ghi lý do. Yêu cầu mới tạo Task mới từ NEW.')], [1.1,2.55,3.45])
p('Cấu hình hiện có: Deploy có điều kiện tất cả Subtask ở Done và đặt Resolution = Done; Reopen xóa Resolution. Gate checklist, quyền reviewer/QA/PM và lý do chưa được thực thi đầy đủ. Deploy ở đây là môi trường Test của bài tập, không mặc định Production.')

h('Workflow Subtask', True)
p('QAG3 Individual Work v1 | Mỗi Subtask có một owner và một đầu ra kiểm chứng được; chọn nhánh theo loại công việc của người được giao.')
doc.add_heading('Hai luồng thực hiện', 2)
p('BA / Tester / PM: NEW → IN PROGRESS → REVIEW → DONE')
p('BE / FE: NEW → IN PROGRESS → CODE REVIEW → READY FOR TEST → IN TESTING → REVIEW → DONE')
sub = [
('NEW', 'Đầu việc đã tạo; xác định owner, đầu ra và checklist của Task cha.'),
('IN PROGRESS', 'Owner đang thực hiện công việc được giao.'),
('CODE REVIEW', 'Chỉ nhánh BE/FE: mã nguồn đang chờ reviewer kiểm tra.'),
('READY FOR TEST', 'Chỉ nhánh BE/FE: code được duyệt và đã sẵn sàng kiểm thử.'),
('IN TESTING', 'Chỉ nhánh BE/FE: Tester kiểm tra đầu ra của Subtask phát triển.'),
('REVIEW', 'Đầu ra chờ xác nhận; nhánh BE/FE phải có kết quả test đạt.'),
('DONE', 'Đầu ra được duyệt và checklist hoàn tất. Tester không kết thúc QA khi lỗi cần retest còn tồn tại.')]
assert len(sub) == 7
p('NEW là đầu việc chờ bắt đầu; IN PROGRESS là đang làm; REVIEW là chờ duyệt đầu ra; DONE là đầu ra đã được chấp nhận. Với BE/FE, CODE REVIEW chờ duyệt code, READY FOR TEST chờ kiểm thử, IN TESTING đang kiểm thử.')
doc.add_heading('Chuyển trạng thái và các nhánh', 2)
table(['Thao tác', 'Chuyển trạng thái', 'Điều kiện nghiệp vụ'], [
('Start work', 'NEW → IN PROGRESS', 'Owner bắt đầu đầu việc.'),
('Submit work', 'IN PROGRESS → REVIEW', 'BA/Tester/PM gửi đầu ra và bằng chứng.'),
('Submit code', 'IN PROGRESS → CODE REVIEW', 'BE/FE gửi code và kết quả tự kiểm tra.'),
('Approve code / Start test / Pass testing', 'CODE REVIEW → READY FOR TEST → IN TESTING → REVIEW', 'Code được duyệt, kiểm thử được bắt đầu và kết quả đạt theo thứ tự.'),
('Approve work', 'REVIEW → DONE', 'Người duyệt xác nhận đầu ra và checklist.'),
('Code rejected / Bug found', 'CODE REVIEW hoặc IN TESTING → IN PROGRESS', 'Chỉ nhánh phát triển; ghi phát hiện cần sửa.'),
('Retest', 'REVIEW → IN TESTING', 'Chỉ nhánh phát triển; cần kiểm thử lại.'),
('Rework / Reopen', 'REVIEW hoặc DONE → IN PROGRESS', 'Mọi nhánh; cần sửa hoặc mở lại, có lý do.')], [1.75,2.5,2.85])
p('Cấu hình hiện có: nhánh được lọc theo Assignee của năm tài khoản đã xác minh, không theo Jira Role hay người bấm nút. Tester có thể kiểm thử Subtask được giao cho BE/FE nếu có quyền thao tác. Đổi assignee có thể đổi nhánh; người ngoài mapping hoặc chưa được giao cần được đối soát trước khi chạy.')
p('Approve work đặt Resolution = Done; Reopen xóa Resolution. Gate người duyệt, checklist, lý do và lỗi chưa retest vẫn cần cấu hình và kiểm thử. Subtask không có Deploy; bước này thuộc Task cha.')
p('Quy tắc liên cấp cần triển khai: Task bắt đầu thì Epic READY sang In Progress; tất cả Task Done chỉ đưa Epic tới Review; thêm hoặc mở lại Task chưa Done trong Epic Review/Done phải đối soát để đưa Epic về In Progress. Không tự nghiệm thu Epic.')
p('Nguồn đối soát: jira-workflows.md mục 13–14 và cấu hình read-back ngày 09/10/2026. QAG3 vẫn dùng scheme 10003; scheme QAG3 Managed Delivery v1 chưa được gắn. Chưa nghiệm thu runtime trên Jira.')
footer = s.footer.paragraphs[0]
footer.alignment = 2
footer.add_run('QAG3  |  Trang ')
field(footer, ' PAGE ', '1')
for r in footer.runs: r.font.size = Pt(9)
settings = OxmlElement('w:updateFields'); settings.set(qn('w:val'),'true'); doc.settings.element.insert_element_before(settings, 'w:hdrShapeDefaults', 'w:footnotePr', 'w:endnotePr', 'w:compat', 'w:docVars', 'w:rsids')
assert len(doc.tables) == 5
doc.save(OUT)
check = Document(OUT)
assert len(check.tables) == 5
assert all(t.cell(0,0).text for t in check.tables)
print(OUT)
