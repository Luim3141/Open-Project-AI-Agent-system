"""Build the private operating handbook from verified local evidence."""
import json
import re
from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT

ROOT = Path(__file__).resolve().parents[1]
SOURCE = json.loads((ROOT / 'jira-bot/handbook-source-2026-10-13.json').read_text(encoding='utf-8'))
OUT = ROOT / 'So_tay_van_hanh_Jira_QAG3_2026-10-13.docx'
if OUT.exists():
    raise FileExistsError('Preserve existing deliverable; choose a new version')
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2)
sec.left_margin = sec.right_margin = Cm(2)
for name, size in [('Normal', 11), ('Title', 26), ('Subtitle', 12), ('Heading 1', 18), ('Heading 2', 14), ('Heading 3', 12)]:
    style = doc.styles[name]
    style.font.name = 'Calibri'
    style.font.size = Pt(size)
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.paragraph_format.space_after = Pt(7)
    if name.startswith('Heading'):
        style.font.bold = True
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.space_before = Pt(12)
doc.styles['Normal'].paragraph_format.line_spacing = 1.15
footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer.add_run('QAG3  |  Hướng dẫn vận hành  |  Trang ').font.size = Pt(9)
field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE'); footer._p.append(field)
settings = doc.settings.element
update = OxmlElement('w:updateFields'); update.set(qn('w:val'), 'true'); settings.append(update)

def p(text, style=None):
    text = readable(text)
    return doc.add_paragraph(text, style)

def h(text, level=1):
    return doc.add_heading(text, level)

def table(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.autofit = False
    for i, value in enumerate(headers): t.rows[0].cells[i].text = value
    for row in rows:
        for c, value in zip(t.add_row().cells, row): c.text = readable(str(value))
    for ri, row in enumerate(t.rows):
        if ri == 0:
            repeat = OxmlElement('w:tblHeader'); row._tr.get_or_add_trPr().append(repeat)
        for ci, cell in enumerate(row.cells):
            if widths: cell.width = Cm(widths[ci])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            pr = cell._tc.get_or_add_tcPr()
            borders = OxmlElement('w:tcBorders')
            for edge in ('top', 'left', 'bottom', 'right'):
                b = OxmlElement('w:' + edge); b.set(qn('w:val'), 'single'); b.set(qn('w:sz'), '4'); b.set(qn('w:color'), 'D9D9D9'); borders.append(b)
            pr.append(borders)
            margins = OxmlElement('w:tcMar')
            for edge in ('top', 'left', 'bottom', 'right'):
                m = OxmlElement('w:' + edge); m.set(qn('w:w'), '85'); m.set(qn('w:type'), 'dxa'); margins.append(m)
            pr.append(margins)
            shade = OxmlElement('w:shd'); shade.set(qn('w:fill'), 'DCE6F1' if ri == 0 else ('F5F7FA' if ri % 2 == 0 else 'FFFFFF')); pr.append(shade)
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(3)
                paragraph.paragraph_format.line_spacing = 1.08
                for run in paragraph.runs:
                    run.font.size = Pt(9.5)
                    if ri == 0: run.bold = True
    p('')
    return t

def readable(text):
    # Artifact-only editorial corrections; identifiers and source evidence stay unchanged.
    replacements = {
        'chảimớiREVIEW/Done': 'Epic cha mới ở REVIEW/Done',
        'QA pased': 'QA passed', 'QApased': 'QA passed',
        'readbackhiệnhành': 'readback hiện hành', 'hiệnhành': 'hiện hành',
        'hiệnINSUFFICIENT_EVIDENCE': 'hiện INSUFFICIENT_EVIDENCE',
        'đãkiểmchứng': 'đã kiểm chứng', 'Đãkiểmchứng': 'Đã kiểm chứng',
        'Chưakiểmchứngđầyđủ': 'Chưa kiểm chứng đầy đủ',
        'Chưabảovệtấtcảbusinessroletrênmọitransition': 'Chưa bảo vệ tất cả vai trò nghiệp vụ trên mọi transition',
        'khôngđược': 'không được', 'khôngphải': 'không phải', 'khôngcó': 'không có',
        'khôngđổi': 'không đổi', 'khôngtự': 'không tự ', 'khôngphụ thuộc': 'không phụ thuộc',
        'khôngblank': 'không blank', 'khôngđủ': 'không đủ', 'khônglà': 'không là',
        'khônggỡ': 'không gỡ', 'khôngsửa': 'không sửa', 'khônglưu': 'không lưu',
        'khôngauto': 'không tự động ', 'khôngsuy': 'không suy', 'khôngchứng': 'không chứng',
        'khôngcoi': 'không coi', 'khôngghi': 'không ghi', 'khôngné': 'không né',
        'khôngkill': 'không kill', 'khôngxóa': 'không xóa', 'khôngrestart': 'không restart',
        'khôngpermission': 'không phải permission', 'khôngatomic': 'không atomic',
        'khôngnhắc': 'không nhắc', 'khôngJira': 'không Jira', 'khôngraw': 'không raw',
        'khôngs': 'không s', 'khôngp': 'không p',
        'cóthể': 'có thể', 'cóParent': 'có Parent', 'cóPM': 'có PM', 'córeason': 'có reason',
        'cóTask': 'có Task', 'cóqag3': 'có qag3', 'cóscreen': 'có screen', 'cógiátrị': 'có giá trị',
        'đúngmột': 'đúng một', 'đúngproject': 'đúng project', 'đúngtype': 'đúng type',
        'đúngQA': 'đúng QA', 'đúngprefix': 'đúng prefix', 'đúngentry': 'đúng entry',
        'đúngapp': 'đúng app', 'đúngPID': 'đúng PID', 'đúngrule': 'đúng rule',
        'đúngscript': 'đúng script', 'đúngnhánh': 'đúng nhánh', 'đúngPM': 'đúng PM',
        'đúngQLDAPM': 'đúng QLDAPM', 'đúngformat': 'đúng format',
        'chỉcho': 'chỉ cho', 'chỉcó': 'chỉ có', 'chỉPM': 'chỉ PM', 'chỉbỏ': 'chỉ bỏ',
        'chỉsửa': 'chỉ sửa', 'chỉđể': 'chỉ để', 'chỉnotify': 'chỉ notify',
        'phảiđọc': 'phải đọc', 'phảidùng': 'phải dùng', 'phảitắt': 'phải tắt', 'phảiqua': 'phải qua',
        'đượckiểm': 'được kiểm', 'đượcduyệt': 'được duyệt', 'đượcxử': 'được xử',
        'đãcommit': 'đã commit', 'đãPass': 'đã Pass', 'đãký': 'đã ký', 'đãtừng': 'đã từng',
        'đãkiểm': 'đã kiểm', 'đãđược': 'đã được', 'đãbắtđầu': 'đã bắt đầu',
        'trướctransition': 'trước transition', 'sautrim': 'sau trim', 'trướcapprove': 'trước approve',
        'trướcQA': 'trước QA', 'trướcresend': 'trước resend', 'saughi': 'sau ghi',
        'sauQA': 'sau QA', 'SauQA': 'Sau QA', 'sauPass': 'sau Pass', 'sauchildexitlỗi': 'sau child exit lỗi',
        'mới ngaytransition': 'mới ngay transition', 'reasonkhácgiátrịcũ': 'reason khác giá trị cũ',
        'giữkey': 'giữ key', 'giữhistory': 'giữ history', 'giữsummary': 'giữ summary',
        'giữhợplệ': 'giữ hợp lệ', 'giữaudit': 'giữ audit', 'giữbefore': 'giữ before',
        'giữprompt': 'giữ prompt', 'giữtoànbộ': 'giữ toàn bộ', 'Giữtoànbộ': 'Giữ toàn bộ',
        'giữoldDone': 'giữ old Done', 'giữfilter': 'giữ filter', 'Giữfilter': 'Giữ filter',
        'mọiSubtask': 'mọi Subtask', 'MọiSubtask': 'Mọi Subtask', 'mọiTask': 'mọi Task',
        'mọitransition': 'mọi transition', 'mọievent': 'mọi event', 'mỗicompletecycle': 'mỗi complete cycle',
        'Mỗicompletecycle': 'Mỗi complete cycle', 'mỗiitem': 'mỗi item', 'mỗiđợtupdate': 'mỗi đợt update',
        'từngSubtask': 'từng Subtask', 'từngaccount': 'từng account', 'từngkind': 'từng kind',
        'từngmục': 'từng mục', 'từngrule': 'từng rule',
        'vàevidence': 'và evidence', 'vàQA': 'và QA', 'vàreason': 'và reason', 'vàscreen': 'và screen',
        'vàfreshness': 'và freshness', 'vàmọi': 'và mọi', 'vàgate': 'và gate',
        'vàtests': 'và tests', 'vàlabels': 'và labels', 'vàhistory': 'và history',
        'vàTask': 'và Task', 'vàworkflow': 'và workflow', 'vàlatestedit': 'và latest edit',
        'vàlatest': 'và latest ', 'vàTestenvironment': 'và Test environment',
        'vàcó': 'và có', 'vàđúng': 'và đúng', 'vàbằng': 'và bằng', 'vàEvidence': 'và Evidence',
        'vàthời': 'và thời', 'vàgiữ': 'và giữ', 'vàTimeline': 'và Timeline',
        'hoặctransitioned': 'hoặc transitioned', 'hoặcrework': 'hoặc rework',
        'hoặcHiệp': 'hoặc Hiệp', 'hoặcowner': 'hoặc owner', 'hoặcmissingfield': 'hoặc missing field',
        'hoặcquyếtđịnh': 'hoặc quyết định', 'hoặcmigrationpreview': 'hoặc migration preview',
        'hoặcreplayoperation': 'hoặc replay operation',
        'nếucần': 'nếu cần', 'nếucha': 'nếu cha', 'nếuđã': 'nếu đã', 'nếuprocess': 'nếu process',
        'nếuchildPython': 'nếu child Python', 'nếukhông': 'nếu không', 'nếuđổi': 'nếu đổi',
        'cầncommittedQA': 'cần committed QA', 'cầnfresh': 'cần fresh', 'cầnQA': 'cần QA',
        'cầnPM': 'cần PM', 'cầnscope': 'cần scope', 'cầnkey': 'cần key', 'cầnnhưng': 'cần nhưng',
        'Cầnhủy': 'Cần hủy', 'Cầnmở': 'Cần mở',
        'hiệnENABLED': 'hiện ENABLED', 'hiệnDISABLED_CONFIG': 'hiện DISABLED_CONFIG',
        'hiệnkhông': 'hiện không', 'cònIn Progress': 'còn In Progress', 'đangDone': 'đang Done',
        'vềNEW': 'về NEW', 'vềIn Progress': 'về In Progress', 'vềIN TESTING': 'về IN TESTING',
        'sangIP': 'sang IP', 'sangREVIEW': 'sang REVIEW', 'vềREADY': 'về READY',
        'củasummary': 'của summary', 'của từng': 'của từng', 'củachat': 'của chat',
        'củaowner': 'của owner', 'choHiệp': 'cho Hiệp', 'choHưng': 'cho Hưng',
        'choquytrìnhthường': 'cho quy trình thường', 'chođánhgiá': 'cho đánh giá',
        'chođánh': 'cho đánh', 'trongnativecontext': 'trong native context', 'trongtext': 'trong text',
        'trongPass': 'trong Pass', 'trongQAG3': 'trong QAG3', 'trongreport': 'trong report',
        'trongD:': 'trong D:', 'trênJiraCloud': 'trên Jira Cloud',
        'tại10010': 'tại 10010', 'tại10011': 'tại 10011',
        'bắtđầu': 'bắt đầu', 'bắt buộc': 'bắt buộc', 'thayđổi': 'thay đổi',
        'dữliệu': 'dữ liệu', 'dữliệugiả': 'dữ liệu giả', 'bằngchứng': 'bằng chứng',
        'bằng chứngnguồn': 'bằng chứng nguồn', 'nghiệpvụ': 'nghiệp vụ', 'ngườimới': 'người mới',
        'ngườilàm': 'người làm', 'kếtquả': 'kết quả', 'môphỏng': 'mô phỏng',
        'giảthành': 'giả thành', 'thànhPASS': 'thành PASS', 'claimtài khoản': 'claim tài khoản',
        'nhậpsai': 'nhập sai', 'thôngthường': 'thông thường', 'phức tạp': 'phức tạp',
        'nhưmongmuốn': 'như mong muốn', 'hai ký tự': 'hai ký tự', 'separatorhai': 'separator hai',
        'điềuchỉnh': 'điều chỉnh', 'phâncông': 'phân công', 'thiết kế': 'thiết kế',
        'đánhgiá': 'đánh giá', 'hiệu suất': 'hiệu suất', 'năng suất': 'năng suất',
        'chưaDone': 'chưa Done', 'chưađạt': 'chưa đạt', 'Chưa sửaparser': 'Chưa sửa parser',
        'lỗiqueued': 'lỗi queued', 'lỗimới': 'lỗi mới', 'lượtresume': 'lượt resume',
        'nhấtquán': 'nhất quán', 'đốichiếu': 'đối chiếu', 'đối chiếuPID': 'đối chiếu PID',
        'kiểmCIM': 'kiểm CIM', 'kiểm0': 'kiểm 0', 'kiểmrawParent': 'kiểm raw Parent',
        'kiểmtra': 'kiểm tra', 'kiểmthử': 'kiểm thử', 'runtimeexpensiveoperations': 'runtime expensive operations',
        'nativeBE/FE': 'native BE/FE', 'type-checkBoolean': 'type-check Boolean', 'lintPASS': 'lint PASS',
        'E2E toàn': 'E2E toàn', 'làE2E': 'là E2E', 'làscope': 'là scope',
        'eventgốc': 'event gốc', 'eventkey': 'event key', 'eventreviewmới': 'event review mới',
        'status+updated': 'status + updated', 'trạngthái': 'trạng thái', 'thực thi': 'thực thi',
        'scopeQAG3': 'scope QAG3', 'scope hiện': 'scope hiện', 'scopeapprovedlabel': 'scope-approved label',
        'markerthìghiattemptmarker rồicomment': 'marker thì ghi attempt marker rồi comment',
        'attemptmetadata': 'attempt metadata', 'commentdelivery': 'comment delivery',
        'commentthật': 'comment thật', 'message không': 'message không', 'điểmhiệu': 'điểm hiệu',
        'actorvà': 'actor và', 'chạy vàgate': 'chạy và gate', 'vẫnchi': 'vẫn chi',
        'hoặcSubtask': 'hoặc Subtask', 'hoặcDone': 'hoặc Done', 'Taskcon': 'Task con',
        'EpicIP': 'Epic IP', 'EpicNEW': 'Epic NEW', 'EpicREADY': 'Epic READY', 'EpicREVIEW': 'Epic REVIEW',
        'ParentEpic': 'Parent Epic', 'BranchParent': 'Branch Parent', 'TaskQAG3': 'Task QAG3',
        'TaskDone': 'Task Done', 'Taskđã': 'Task đã', 'Taskchưa': 'Task chưa', 'Task và': 'Task và',
        'allTaskDone': 'all Task Done', 'Taskscope': 'Task scope', 'TaskApproveDeploy': 'Task Approve/Deploy',
        'SubtaskDone': 'Subtask Done', 'Subtask cóowner': 'Subtask có owner',
        'activeworkflow': 'active workflow', 'nativecondition': 'native condition',
        'scope/evidenceintegrationhandovermới': 'scope và evidence integration/handover mới',
        'Development2.21': 'Development 2.21', 'development2.21': 'development 2.21',
        'heartbeatPAUSED': 'heartbeat PAUSED', 'WindowsTaskDisabled': 'Windows Task Disabled',
        'khôngcònpythonrunner/wrapper': 'không còn Python runner/wrapper',
        'đượcgiữ': 'được giữ', 'botlocal': 'bot local', 'đangbật': 'đang bật',
        'officialMCP': 'official MCP', 'quahelperjira_mcp.py': 'qua helper jira_mcp.py',
        'issuetype': 'issue type', 'fullpagination': 'full pagination', 'tớiisLast': 'tới isLast',
        '--interval3600': '--interval 3600', 'single-processlockWindows': 'single-process lock Windows',
        'atomicjson': 'atomic JSON', 'eventrunId': 'event runId', 'làat-logonInteractive/Limited': 'là at-logon Interactive/Limited',
        'hiddenwindow': 'hidden window', 'bounded3retry cách60s': 'bounded 3 retry cách 60s',
        'Taskkhông': 'Task không', 'Windowsservice24/7': 'Windows service 24/7', 'bảođảm': 'bảo đảm',
        'Heartbeatmỗi': 'Heartbeat mỗi', 'phút15': 'phút 15', 'trongchat': 'trong chat',
        'rồiprocess': 'rồi process', 'eventfreshness': 'event freshness',
        'Runnerđang': 'Runner đang', 'sống/fresh': 'sống/fresh', 'dùngstatekhôngcollect': 'dùng state, không collect',
        'lần2': 'lần 2', 'Runneralive': 'Runner alive', 'snapshotstale/error': 'snapshot stale/error',
        'chờchu kỳ': 'chờ chu kỳ', 'chỉvìtimeout': 'chỉ vì timeout', 'Geminioptional': 'Gemini optional',
        'antoàn': 'an toàn', 'FreeTierconfirmed': 'Free Tier confirmed', 'paidfallback': 'paid fallback',
        'Chỉnumericaggregate': 'Chỉ numeric aggregate', 'rawJira': 'raw Jira', 'draft cósourcetimestamp': 'draft có source timestamp',
        'làcollectorbaseline': 'là collector baseline', 'làrunnerstate': 'là runner state',
        'bằngruntime': 'bằng runtime', 'runtime vàojira_gemini.py': 'runtime vào jira_gemini.py',
        'làcursor': 'là cursor', 'giữnotificationdedup': 'giữ notification dedup',
        'vàevidencekhác': 'và evidence khác', 'nóthànhstateJira': 'nó thành state Jira',
        'TỷlệfunctionalDone': 'Tỷ lệ functional Done', 'Task/StoryDone-category': 'Task/Story Done-category',
        'tổngTask/Storyscope': 'tổng Task/Story trong scope', 'Công việchủy': 'Công việc hủy', 'ởmẫu': 'ở mẫu',
        'tổng0': 'tổng 0', 'chỉqag3-wbs': 'chỉ qag3-wbs', 'snapshot11:36': 'snapshot 11:36',
        'mỗi5vai trò39/53SubtaskDone': 'mỗi vai trò có 39/53 Subtask Done',
        'Năm chiều đánh giá deliveryreliability,quality,collaboration,ownership,contribution': 'Năm chiều đánh giá: delivery reliability, quality, collaboration, ownership, contribution',
        'workloggiảdoadmin': 'worklog giả do admin', 'chứng minhngười': 'chứng minh người',
        'Resetvề': 'Reset về', 'khôngphảidefect': 'không phải defect',
        'Botchỉnotify meaningfulchange': 'Bot chỉ notify meaningful change', 'blocker cóevidence': 'blocker có evidence',
        'quyếtđịnhcầnowner': 'quyết định cần owner', 'HTTP400Artifactscũ': 'HTTP 400 Artifacts cũ',
        'MởEpic': 'Mở Epic', 'ApproveScope': 'Approve scope', 'Startanalysis': 'Start analysis',
        'Analysisdone': 'Analysis done', 'Startdev': 'Start dev', 'Startwork': 'Start work',
        'Submitwork': 'Submit work', 'Submitcode': 'Submit code', 'Approvecode': 'Approve code',
        'Starttest': 'Start test', 'Passtesting': 'Pass testing', 'Approvework': 'Approve work',
        'PMreview': 'PM review', 'Task đi': 'Task đi ', 'Nếubug': 'Nếu bug', 'nhánhsửa': 'nhánh sửa',
        'prefixQA': 'prefix QA', 'Reviewevidence': 'Review evidence', 'rồimongApprove': 'rồi mong Approve',
        'sửađángkể': 'sửa đáng kể', 'Review resultACCEPTED': 'Review result ACCEPTED',
        'Nhánhreview': 'Nhánh review ', 'dùng4prefix': 'dùng 4 prefix', 'Ghi rõtài': 'Ghi rõ tài',
        'chứngcứreviewmới': 'chứng cứ review mới', 'copykết': 'copy kết',
        'parserexpression': 'parser expression', 'ADFformatphức tạp': 'ADF format phức tạp',
        'nhờadapter': 'nhờ adapter', 'gửiADFparagraph/text': 'gửi ADF paragraph/text',
        'đúngđịnhdạng': 'đúng định dạng', 'bỏgate': 'bỏ gate',
        'checkboxTask': 'checkbox Task', 'QAcurrent': 'QA current', 'PMApprove': 'PM Approve',
        'PMDeploy': 'PM Deploy', 'Readyforrelease': 'Ready for release', 'PMAcceptEpic': 'PM Accept Epic',
        'Change reasonkhác': 'Change reason khác', 'transition, giữ': 'transition, giữ',
        'di chuyểnchéo': 'di chuyển chéo', 'Cancelhiện': 'Cancel hiện', 'actionsetresolution': 'action set Resolution',
        'ParentTask': 'Parent Task', 'xácnhận': 'xác nhận', 'A04Auditlog': 'A04 Audit log',
        'SubtaskParent': 'Subtask Parent', 'app/APIpreview': 'app/API preview',
        'approvedhash': 'approved hash', 'exacthash,currentversion': 'exact hash, current version',
        'bảnv2/inactive': 'bản v2/inactive', 'activev9/v10/v11': 'active v9/v10/v11',
        'currentpreview': 'current preview', 'Updateworkflow': 'Update workflow', 'Editworkflow': 'Edit workflow',
        'Mapmọistatus': 'Map mọi status', 'cộtDone': 'cột Done', 'timelineWork item': 'timeline Work item',
        'AligntoSprint': 'Align to Sprint', 'testhappy+negative': 'test happy + negative',
        'deploydevelopmentđúngapp': 'deploy development đúng app', '1partnerconjunction': '1 partner conjunction',
        'Exportbefore': 'Export before', 'Auditlog/readback': 'Audit log/readback',
        'heartbeatmonitor': 'heartbeat monitor', 'cả2': 'cả 2', 'theoýđịnh': 'theo ý định',
        'CIMnoprocesstrùng': 'CIM không process trùng', 'TOMLbằngtay': 'TOML bằng tay',
        'updatesallowlist/routing': 'update allowlist/routing', 'Default/othersite': 'Default/other site',
        'project10002mapping3type': 'project 10002 mapping 3 type', 'Enable/Start đúng': 'Enable/Start đúng',
        'đangsống': 'đang sống', 'bậtmonitorheartbeatACTIVE': 'bật monitor heartbeat ACTIVE',
        'COLLECTEDcomplete': 'COLLECTED complete', 'PAUSED →': ' PAUSED →',
        'MuốntắtA01đếnA05phải': 'Muốn tắt A01 đến A05 phải', 'riêngởJiraAutomation': 'riêng ở Jira Automation',
        'thao tácbot': 'thao tác bot', 'nhận diệnWBS': 'nhận diện WBS', 'opt-inphạmvi': 'opt-in phạm vi',
        'làmappingnhậpliệu': 'là mapping nhập liệu', 'dùngchốngtrùng': 'dùng chống trùng',
        'thaykeyJira': 'thay key Jira', 'bằngsourceID': 'bằng source ID', 'cũkhiAPIsetarray': 'cũ khi API set array',
        'markerA05': 'marker A05', 'Thêmngười': 'Thêm người', 'resolveaccountId,assignabilityvàmembership': 'resolve accountId, assignability và membership',
        'cậpnhậtmanifest': 'cập nhật manifest', 'PM/QA/Dev/businessallowlists': 'PM/QA/Dev/business allowlists',
        'nativeSubtaskcondition': 'native Subtask condition', 'A05routing': 'A05 routing',
        'cấptoànquyềnadminchỉ': 'cấp toàn quyền admin chỉ', 'bỏactorcheck': 'bỏ actor check',
        'emailpassword': 'email password', 'thiếureason': 'thiếu reason', 'Reasonblank/cũ': 'Reason blank/cũ',
        'fieldkhôngtrênscreen': 'field không trên screen', 'Nhậpreasonmới': 'Nhập reason mới',
        'APItextareacầnADF': 'API textarea cần ADF', 'Approvefail': 'Approve fail',
        'QAentry': 'QA entry', 'Returntesting rồifreshQA': 'Return testing rồi fresh QA',
        'Forgehistory': 'Forge history', 'táithiệnfixture': 'tái hiện fixture',
        'optimizetraversalrồitestnative': 'optimize traversal rồi test native', 'ToDonefilter': 'To Done filter',
        'Epicstatus': 'Epic status', 'lúcchạy': 'lúc chạy', 'bỏfilterđểnhận': 'bỏ filter để nhận',
        'ĐọclistJiraIssueTransitions': 'Đọc listJiraIssueTransitions', 'đoánID': 'đoán ID',
        'Runnerstale nhưngPIDcòn': 'Runner stale nhưng PID còn', 'chờcycle': 'chờ cycle',
        'MCPtrùng': 'MCP trùng', 'Collectorpartial/429/authfail': 'Collector partial/429/auth fail',
        'lastsuccess': 'last success', 'browsersession': 'browser session',
        'TimelinekhônghiệnTask/Subtask': 'Timeline không hiện Task/Subtask', 'Đọcfieldtừngmục': 'Đọc field từng mục',
        'Workitemdates': 'Work item dates', 'đổi ngày chỉđểđẹpchart': 'đổi ngày chỉ để đẹp chart',
        'khôi phụcexportbefore': 'khôi phục export before', 'khôi phụcnguồn': 'khôi phục nguồn',
        'sauđó mớigỡhistorygate': 'sau đó mới gỡ history gate', 'lighteracceptanceđang': 'lighter acceptance đang',
        'appđanggắnworkflow': 'app đang gắn workflow', 'Resetstatus': 'Reset status',
        'xóalịch sử': 'xóa lịch sử', 'SnapshotBefore': 'Snapshot Before', 'làdữliệu': 'là dữ liệu',
        'ghiđèlại329issue': 'ghi đè lại 329 issue', 'scheme10004gắnQAG3': 'scheme 10004 gắn QAG3',
        '84descendantresetNEWvàclearResolution': '84 descendant reset NEW và clear Resolution',
        'runnercomplete335issue': 'runner complete 335 issue', '108PythonJiratests ởlượtbậtbot': '108 Python Jira tests ở lượt bật bot',
        'toànbộ': 'toàn bộ', 'identitynonPMnative': 'identity non-PM native',
        'historycựcdài': 'history cực dài', 'QA/releasethật': 'QA/release thật',
        'các hàngkhôngrule': 'các hàng không rule', 'thànhhardgate': 'thành hard gate',
        'ítgate': 'ít gate', 'cònthiếu': 'còn thiếu', 'JiraFree': 'Jira Free',
        'latercóStandardtrialbanner': 'later có Standard trial banner', 'đốisoátbillinglivecuối': 'đối soát billing live cuối',
        'planFreehiện hành': 'plan Free hiện hành', 'chi phí0bấtbiến': 'chi phí 0 bất biến',
        'ForgeCLI dependencyaudit': 'Forge CLI dependency audit', 'securityclean': 'security clean',
        'ỨngdụngForge': 'Ứng dụng Forge', 'promotionproduction': 'promotion production',
        'MCPcachedcatalog': 'MCP cached catalog', 'sourcefresh25tool': 'source fresh 25 tool',
        'effectivepolicy': 'effective policy', 'Lịchcontinue setupkhácmonitor': 'Lịch continue setup khác monitor',
        'lầnpause': 'lần pause', 'UsernênreviewScheduled': 'User nên review Scheduled',
        'continuationcònchạy': 'continuation còn chạy', 'Báocáo': 'Báo cáo',
        'toànsiteJira/fulladmin': 'toàn site Jira/full admin', 'đãhoànthiện100%': 'đã hoàn thiện 100%',
        'Cácfilequan trọng nằmtrong': 'Các file quan trọng nằm trong',
        'AGENTS.mdquytắc': 'AGENTS.md (quy tắc)', 'jira-management.mdtrạngthái': 'jira-management.md (trạng thái)',
        'jira-workflows.mdthiếtkếvàhistory': 'jira-workflows.md (thiết kế và history)',
        'architecture.mdkiếntrúc': 'architecture.md (kiến trúc)', 'JIRA_BOT.mdmonitor': 'JIRA_BOT.md (monitor)',
        'JIRA_TEAM_QAG3.jsonaccountmapping': 'JIRA_TEAM_QAG3.json (account mapping)',
        'manifest.ymllogic': 'manifest.yml (logic)', 'jira_admin_mcp.pyguardedadmin': 'jira_admin_mcp.py (guarded admin)',
        'jira_bot.pycollector': 'jira_bot.py (collector)', 'jira_monitor.pyrunner': 'jira_monitor.py (runner)',
        'Start-JiraMonitor.ps1supervisor': 'Start-JiraMonitor.ps1 (supervisor)',
        'Evidencehiện hành': 'Evidence hiện hành', 'đọcworkflow/scheme/ruletrực tiếp': 'đọc workflow/scheme/rule trực tiếp',
        '.jsonnativeactivation': '.json (native activation)', '.jsonbefore/after': '.json (before/after)',
        '.jsonrunner': '.json (runner)', '.mdmô phỏng': '.md (mô phỏng)',
        'Nativebeforeadminauditlưutrongspecialfolder': 'Native before/admin audit lưu trong special folder ',
        'tokenstore': 'token store', 'uploadra ngoài': 'upload ra ngoài', 'trongJira': 'trong Jira',
        'associationvàworkflowversionlive': 'association và workflow version live', 'nguồnhiện hành': 'nguồn hiện hành',
        'chốtđíchvàscope': 'chốt đích và scope', 'đọcbefore': 'đọc before', 'thay đổinhỏ': 'thay đổi nhỏ',
        'nếuđòihỏi': 'nếu đòi hỏi', 'testpositive/negative': 'test positive/negative',
        'lưureport/rollback': 'lưu report/rollback', 'đánhdấuhoànthànhkhichỉ': 'đánh dấu hoàn thành khi chỉ',
        'quytrìnhđểchủdựánchủđộng': 'quy trình để chủ dự án chủ động ',
        'nhầmmô phỏngthànhkếtquảthật': 'nhầm mô phỏng thành kết quả thật',
    }
    for old, new in sorted(replacements.items(), key=lambda item: -len(item[0])):
        text = text.replace(old, new)
    return text

def bullets(items):
    for item in items: p(item, 'List Bullet')

gate_names = {
 'qag3-pm-only':'PM được duyệt', 'qag3-epic-readiness':'Scope readiness',
 'qag3-epic-children-done':'Task và Subtask con Done', 'qag3-epic-acceptance':'Epic acceptance',
 'qag3-fresh-change-reason':'Reason mới', 'qag3-qa-attest':'QA ký kết quả mới',
 'qag3-qa-current':'QA còn hiệu lực', 'qag3-qa-freshness':'QA freshness companion',
 'qag3-task-subtasks-done':'Mọi Subtask Done', 'qag3-task-delivery-checklist':'Checklist bàn giao',
 'qag3-subtask-acceptance':'Subtask acceptance', 'qag3-subtask-history':'History và QA provenance'}

def rule_summary(t):
    bits = [gate_names.get(v.get('parameters', {}).get('key', '').split('/')[-1], v['ruleKey']) for v in t.get('validators', [])]
    condition = t.get('conditions')
    if condition:
        serialized = json.dumps(condition)
        bits.append('Nhánh theo assignee BE hoặc FE' if '7141e4e4' in serialized else 'Nhánh theo assignee BA Tester PM' if 'check-field-value' in serialized else 'Native child Done condition')
    if t.get('transitionScreen'): bits.append('Screen ' + t['transitionScreen']['parameters']['screenId'])
    for a in t.get('actions', []):
        if a.get('parameters', {}).get('field') == 'resolution': bits.append('Resolution Done' if a['parameters'].get('value') else 'Xóa Resolution')
    return '; '.join(bits) or 'Không có rule bổ sung tại transition này'

def workflow_catalog(kind):
    data = SOURCE['workflows'][kind]['workflow']
    wf = data['workflows'][0]
    statuses = {x['statusReference']:x['name'] for x in data['statuses']}
    p(f"Cấu hình đọc trực tiếp: {wf['name']}, version {wf['version']['versionNumber']}. ID workflow: {wf['id']}.")
    rows = []
    for t in sorted(wf['transitions'], key=lambda x:int(x['id'])):
        origin = ', '.join(statuses[l['fromStatusReference']] for l in t['links'] if l.get('fromStatusReference')) or 'Create'
        rows.append([t['id'], t['name'], origin + ' → ' + statuses[t['toStatusReference']], rule_summary(t)])
    table(['ID', 'Thao tác', 'Từ và đến', 'Rule hiện hành'], rows, [0.7,3.0,4.5,8.8])

p('Hướng dẫn vận hành hệ thống Jira QAG3', 'Title')
p('Báo cáo cấu hình hiện hành và sổ tay sử dụng cho chủ dự án', 'Subtitle')
p('Ngày chốt 13 tháng 10 năm 2026  |  Phiên bản tài liệu 1  |  Tài liệu riêng tư')
p('Hệ thống QAG3 đã có backlog, lịch mô phỏng, ba workflow đang được áp dụng và năm automation A01 đến A05 được bật. Bot giám sát local và lịch báo cáo trong chat đã tạm dừng theo yêu cầu mới nhất. Việc tạm dừng bot không tắt automation trong Jira.')
p('Tài liệu giải thích cách dùng và thay đổi cấu hình, bao gồm mọi transition của ba workflow, 12 validator Forge, các trường bằng chứng, năm automation, bot giám sát, quyền và lỗi thường gặp. Dữ liệu dự án, tiến độ, worklog và nhận định thành viên là mô phỏng học tập; chúng không chứng minh sản phẩm hay công việc thật đã được nghiệm thu.')
table(['Thành phần', 'Trạng thái chốt'], [
 ['QAG3 Managed Delivery v1', 'Scheme 10004 gắn QAG3 10002'],
 ['Epic Task Subtask', 'Active; version 9 / 10 / 11'],
 ['A01 A02 A03 A04 A05', 'ENABLED; chỉ phạm vi QAG3'],
 ['Bot giám sát và Windows runner', 'PAUSED / Disabled; 0 runner hoặc wrapper'],
 ['Backlog WBS', '329 mục; 11 Epic, 53 Task, 265 Subtask'],
 ['Nguồn số liệu gần nhất', '13/10/2026 11:36:21 +07; 335 mục kể cả 6 fixture'] ], [6,11])
h('Cách đọc tài liệu',2)
p('Đọc phần 1 đến 3 để hiểu hệ thống và dữ liệu; phần 4 đến 8 để thao tác workflow và automation; phần 9 đến 12 để vận hành bot, sửa cấu hình và xử lý lỗi. Phụ lục ghi ID và nguồn để tra cứu. Bảng “Rule hiện hành” là cấu hình được đọc thật, không phải mọi yêu cầu nghiệp vụ trong tài liệu thiết kế cũ.')
doc.add_page_break()
h('Mục lục')
tocp = p('')
toc = OxmlElement('w:fldSimple'); toc.set(qn('w:instr'), 'TOC \\o "1-2" \\h \\z \\u'); tocp._p.append(toc)
p('Trong Word có thể bấm vào tiêu đề hoặc dùng Navigation Pane. Nếu số trang chưa cập nhật, chọn toàn bộ tài liệu rồi nhấn F9 để cập nhật mục lục.')
doc.add_page_break()
h('1 Kiến trúc và ranh giới hệ thống')
p('Người dùng hoặc AI thao tác issue qua Jira. Workflow chạy condition, validator và action ngay tại transition. Jira Automation nhận sự kiện sau thay đổi để điều phối Epic hoặc nhắc PM. Bot Windows chỉ đọc dữ liệu định kỳ và ghi state local; heartbeat trong chat đọc state để nhận định. Bốn cơ chế này khác nhau, không nên gọi tất cả là MCP hoặc bot.')
table(['Lớp', 'Vai trò', 'Giới hạn'], [
 ['Jira Cloud', 'Lưu issue, Parent, assignee, ngày, workflow, audit', 'Nguồn trạng thái chính; không thay thế code hoặc sản phẩm'],
 ['Official atlassian MCP', 'Issue, transition, search, sprint và đọc nguồn được hỗ trợ', 'Quyền và operation thực tế của phiên; không full Jira admin'],
 ['Local qag3-admin', 'API Atlassian chính thức cho cấu hình QAG3 cố định', 'Preview, hash, current version, audit; không URL hoặc shell tùy ý'],
 ['Browser trong app', 'Fallback quản trị thiếu operation MCP', 'Thao tác UI, phải đọc lại; không được gọi là MCP'],
 ['Forge Workflow Gates', '12 expression validator server-side', 'Development 2.21.0; không function/storage/egress/API scopes'],
 ['Jira Automation', 'A01 đến A05 xử lý sự kiện', 'Không auto nghiệm thu Epic; không đồng bộ mọi status cha con'],
 ['Runner và heartbeat', 'Thu dữ liệu và báo cáo riêng tư', 'Đang tạm dừng; phụ thuộc host, OAuth, app và quota'] ], [3.3,6.2,7.5])
p('Đích duy nhất của cấu hình này là https://luimjiraqldapm.atlassian.net, project QAG3, ID10002, board3. KAN và SAM1 không thuộc phạm vi. Thư mục có thẩm quyền: D:\\AI project\\QLDAPM chat. Workspace C:\\Users\\LUIM\\Documents\\QLDAPM chỉ là con trỏ legacy.')
h('2 Dữ liệu vai trò và trạng thái hiện tại')
p('Epic chứa các Task chức năng đầu cuối. Mỗi Task WBS có năm Subtask tương ứng BA, BE, FE, Tester và PM. Task không phải bản sao của từng Subtask. Worklog, story point và lịch giả định không trở thành capacity hoặc hiệu suất thật.')
table(['Người', 'Vai trò nghiệp vụ', 'Email'], [[ 'Hiệp', 'BA và PM', 'hiepk40c@gmail.com'],['Đức','BE','nguyenduc6325@gmail.com'],['Duy','FE','ttheduy1401@gmail.com'],['Hưng','Tester','Duyhungls2005@gmail.com'],['Khai','PM','2101minhkhai@gmail.com']], [2,4,11])
p('Hai PM được validator nhận diện bằng accountId của Hiệp và Khai, không phải chuỗi email hay một project role mới. Nhánh Subtask kiểm tra assignee theo năm accountId đã cấu hình. Business role khác project permission. Lời mời đã gửi và assignability đã từng xác minh; không lấy điều đó làm bằng chứng mọi người đã accept lời mời hoặc có quyền admin.')
table(['Cấp WBS', 'Done', 'In Progress', 'NEW', 'Tổng'], [['Epic',7,1,3,11],['Task',39,0,14,53],['Subtask',195,0,70,265]], [4.2,3.2,3.2,3.2,3.2])
p('Ba Epic NEW là QAG3-243 Comment, QAG3-274 Dashboard, QAG3-299 Notification. Toàn bộ14Task và70Subtask bên dưới đã reset vềNEW, Resolution rỗng, không đổi ngày hoặc assignee. Đường reset tạm đã bị gỡ; hiện không có transition reset vềNEW dành cho mọi Task/Subtask. Epic QAG3-212 Issue / Bug cònIn Progress dù Task con đangDone; đây là bước cần PM xem xét, không lý do để bot tự nghiệm thu.')
h('3 Trường dữ liệu checklist và bằng chứng')
table(['Field', 'ID', 'Cách dùng'], [['Start date','10015','Ngày bắt đầu kế hoạch; timeline dùng cùng Due date'],['Due date','duedate','Ngày kết thúc kế hoạch; không thời gian hoàn thành thực'],['Change reason','10043','Lý do mới khi mở lại, trả Epic, hủy hoặc restore có gate'],['Acceptance checklist','10044','Multicheckboxes; tick thủ công là dữ liệu, không chữ ký QA'],['Review evidence','10045','Evidence có cấu trúc; QA ký tại chính transition Pass testing']], [4,2,11])
table(['Option', 'ID', 'Ý nghĩa'], [['AC verified','10020','AC đã kiểm tra'],['Lead review completed','10021','Review kỹ thuật hoàn thành theo nghiệp vụ'],['QA passed','10022','Kết quả QA; gate còn kiểm tra actor và history'],['Retest passed','10023','Retest PASSED'],['Retest not required','10024','Retest NOT REQUIRED có lý do'],['BA accepted','10025','BA chấp nhận'],['PM approved','10026','PM duyệt'],['Test deployment smoke passed','10027','Smoke test môi trường Test']], [6,2,9])
p('Chọn đúng một trong10023 hoặc10024. Tick cả hai hoặc không tick đều bị chặn ở các gate yêu cầu retest. Checklist Task Deploy cần10020,10021,10022,10025,10026,10027 và đúng một lựa chọn retest. Epic Accept cần10020,10022,10025,10026,10027 và đúng một retest; không suy rằng checkboxLead tự xác minh reviewer thật.')
p('Screen10010 là QAG3 Scrum Default Issue Screen cho Task/Subtask. Screen10011 là Epic Screen. Các field không bắt buộc trên mọi edit/create; validator chỉ bắt buộc dữ liệu ở transition đã gắn. Field scheme QAG3 Gate Fields v1 giữ cấu hình cũ và thêm ba gate field. Không nhầm field availability riêng QAG3 với custom field context đã restrict toàn site.')
h('4 Workflow Epic')
p('Luồng chính: NEW → READY → In Progress → REVIEW → Done. NEW là phạm vi chưa duyệt; READY đã duyệt scope; In Progress đang điều phối; REVIEW chờ nghiệm thu; Done đã qua Accept Epic. CANCELLED là trạng thái hủy, không đồng nghĩa bàn giao thành công.')
workflow_catalog('epic')
p('Approve scope cần PM, owner active, description và evidence mới có Scope version, Scope tasks, Acceptance criteria, Scope result APPROVED, Evidence. Danh sách Scope tasks phân cách dấu phẩy phải khớp đúng toàn bộ Task con hiện tại, không thiếu hoặc trùng.')
p('Submit acceptance và Accept Epic kiểm tra Epic không rỗng, toàn bộ Task cùng mọi Subtask của chúng có statusDone10009. Accept còn cần evidence mới, scope hiện hành, Integration result PASS, Handover result COMPLETE, Evidence, Retest và Bug references / retest rationale; không đổi owner, summary hoặc description ngay trong acceptance.')
p('Cảnh báo cấu hình thật: Reanalyse3 và Start delivery4 không có validator riêng; Return7 và Reopen8 có reason nhưng không có PM-only riêng tại transition. Cancel9 có PM và reason nhưng không có action đặt Resolution trong readback hiện hành. Vì vậy “chỉ PM mọi nhánh và Resolution hủy đầy đủ” là mục cần bổ sung/kiểm thử, không được xem là đã bảo đảm. Quyền Jira thường vẫn áp dụng.')
h('5 Workflow Task')
p('Luồng chính: NEW → IN ANALYSIS → READY FOR DEV → In Progress → CODE REVIEW → READY FOR TEST → IN TESTING → REVIEW → READY FOR RELEASE → Done. Trạng thái READY FOR RELEASE vẫn chưaDone; “Deploy” trong quy trình này là nghiệm thu triển khai Test, không deploy sản phẩm thật tự động.')
workflow_catalog('task')
bullets(['Code rejected, Bug found và ReDev đưa vềIn Progress để sửa; Retest đưa REVIEW vềIN TESTING; Retest before release đưa READY FOR RELEASE vềIN TESTING và cóPM gate.', 'Pass testing cần ngườiQA thật hoặc ngoại lệ mô phỏng của Hiệp, evidence mới và retest nhất quán. Chỉ edit field thànhPASS trước đó không tạo chữ ký transition.', 'Approve cầnPM, QA-current vàQA-freshness. Deploy cầnPM, mọiSubtaskDone, checklist bàn giao và cùng haiQA gate; native condition cũng kiểm tra childDone.', 'Reopen cầnPM vàreason mới, xóaResolution rồi trở vềIn Progress; không reset vềNEW. Các nhánh phân tích/code/test đầu không có actor validator bổ sung trong cấu hình thật; BA/Dev/Tester là phân công nghiệp vụ, không tự có actor gate ở mọi bước.'])
h('6 Workflow Subtask và hai nhánh')
p('Nhánh BA Tester PM: NEW → In Progress → REVIEW → Done. Nhánh BE FE: NEW → In Progress → CODE REVIEW → READY FOR TEST → IN TESTING → REVIEW → Done. Chỉ có một workflow Subtask với hai đường dựa theo assignee, không phải năm workflow riêng.')
workflow_catalog('subtask')
p('Nếu giao một Subtask cho BE hoặcFE, đườngSubmit work thông thường không hiện; dùngSubmit code. Nếu giao choBA/Tester/PM, dùngSubmit work, không bắt họ quaCode Review. Điều kiện xét assignee, không xét actor người bấm. History gate vẫn nhận ra Subtask từng gánDev/từng đi trạng tháiDev, nên đổi assignee vềBA không tự loại yêu cầuQA.')
p('Approve work4 là phép AND của acceptance, freshness và history; không tháo riêng một validator. Ngoài ngoại lệowner mô phỏng, PM phải độc lập với người được giao hiện tại và lịch sử giao việc. Rework5 không córeason validator riêng. Reopen6 cầnreason mới vàclearResolution nhưng không cóPM-only riêng tại transition; khác vớiTask Reopen15.')
h('7 Catalog đủ 12 validator và điều kiện thực thi')
catalog = [
 ('qag3-pm-only','Chỉ hai PM account active trong QAG3/10002. Quyền Jira nền vẫn phải cho phép transition. Không phải quyền org admin và không thay bằng tênemail.'),
 ('qag3-epic-children-done','Epic đúngtype10000, có ít nhất mộtTask; tất cảTask10011 status10009; danh sáchSubtask10010 của từngTask phải đọc được và đều10009. Đây là kiểm tra trạng thái, không kiểm tra code.'),
 ('qag3-fresh-change-reason','Reason khôngblank sautrim và phải khác reason đãcommit trước transition. ADF/RichText chuyển thànhplain text; giá trị cũ lưu sẵn khôngđủ.'),
 ('qag3-task-subtasks-done','Task10011; danh sáchchild phải đọc được; mọiSubtask đúngproject/type/statusDone. Predicate every có thể đúng cho list rỗng, nên không mô tả gate này là “luôn cần ít nhất mộtSubtask”. Native condition còn chạy ởDeploy.'),
 ('qag3-task-delivery-checklist','Đủ sáuoption checklistTask, đúng một retest vàevidence khôngblank. Gate này không xác minh tài khoảnLead/BA hoặc nội dungbằng chứng thực.'),
 ('qag3-qa-attest','Trướctransition phải ởIN TESTING. TesterHưng active kýPASS, hoặcHiệp kýSIMULATED PASS khi nhãnqag3-simulation đã có trướctransition. Evidence mới, bảyfield đúngprefix, Environment bắt đầuTest - vàQA/retest checkbox khớp.'),
 ('qag3-qa-current','Có historyPass testing10018→10012; thay Review evidence ngay cùngentry vớiPass; author đúngQA hoặcowner mô phỏng; evidence không bị thay sauký. Approve/Deploy giữsummary/description/Parent/assignee và phải cùng chạyfreshness.'),
 ('qag3-subtask-acceptance','Subtask cóowner. Dev cầncommittedQA; nhánh nghiệp vụ chưaQA cầnfresh structured review gồmRevision,Review scope,Review result,Evidence. ACCEPTED chođánh giá thường hoặcSIMULATED ACCEPTED theoowner exception. Cầncảhistory/freshness để đủchính sách.'),
 ('qag3-epic-readiness','ChỉPM từNEW; owneractive, descriptionnonblank, evidencefresh đủ5prefix; Scope resultAPPROVED vàdanh sáchTask khớp currentchild scope chínhxác.'),
 ('qag3-epic-acceptance','ChỉPM từREVIEW; owneractivekhôngđổi, corefields khôngđổi; evidencefresh đủ7prefix, IntegrationPASS/HandoverCOMPLETE, checklistEpic và retestnhấtquán, Taskscope khớp vàDone. Child gate riêng bổ sung kiểm traSubtaskDone.'),
 ('qag3-qa-freshness','Task: đối chiếu latest status/evidence vàlatestedit củasummary/description/Parent/assignee/evidence; chỉchoPass hoặcApprove sauPass phùhợp. Subtask: actorPM, owneractive, corefields khôngđổi khiapprove vàQA/retest checkbox nhấtquán nếuđãPass. Không thay QA-current/history.'),
 ('qag3-subtask-history','Đọcfull assignment/status/history để phát hiện everDev vàselfreview. Dev cầnQA provenance/signature đúngentry, bảyfield, authorvàTestenvironment; relevantedit hoặcrework sauQA làmstale. Khôngcắt history; runtimeexpensiveoperations còn là giới hạn cần stress test.')]
for key, explanation in catalog:
    h(gate_names[key],2); p('Module ' + key + '. ' + explanation)
p('Các predicate được nốiAND qua nhiều validator để tránh giới hạn expensiveoperations của Jira. Development2.21 đã qua nativeBE/FE positive và stale/reuse negative mục tiêu; không coi type-checkBoolean hoặc lintPASS làE2E toàn hệ thống. Source manifest là nơi quyết định logic; tên vàerrorMessage không thể thay thế predicate.')
h('8 Jira Automation A01 đến A05')
p('Tất cả hiệnENABLED, scopeQAG3/10002; không còn điều kiệnqag3-test trongtrigger A02 đếnA05. A03/A04 vẫn cầnqag3-scope-approved. CanOtherRuleTrigger=false giúp không cho rule khác kích hoạt dây chuyền; không phải giao dịchatomic hoặc exactly-once. Rule chỉ nhận sự kiện phùhợp sau khi bật, không tựbackfill dữ liệu cũ.')
automation = [
 ('A01 Start Epic on Task delivery','Task vào một trạng thái xử lý: IN ANALYSIS, READY FOR DEV, In Progress, CODE REVIEW, READY FOR TEST, IN TESTING, REVIEW hoặc READY FOR RELEASE và cóParent.','BranchParent, refetch, EpicQAG3 đangREADY10011 → In Progress.','Automation for Jira. EpicNEW không được tựduyệt scope; nếuchaNEW thìrule không đưa sangIP.'),
 ('A02 Ready Epic for acceptance','Work item transitioned, To statusDone; JQLTask10011 status10009 cóParent.','ParentEpicIP; refetch, childrenpresent vàmọiTaskconDone → REVIEW.','Automation for Jira. Không AcceptEpic/Done. ToDone filter đã sửa lỗiqueuedApprove/Deploy cùngthấyDone; stress nhiềuTask chưađạt exactly-once.'),
 ('A03 Reopen Epic on approved Task change','Taskcreated hoặctransitioned, khôngDone, cóParent vàqag3-scope-approved.','EpicREVIEW hoặcDone → In Progress vớiChange reason mới. KhôngrestoreCANCELLED.','User who triggered. Đây làmetadata scope, khôngpermission; người chạy vàgate/quyền thật vẫnchi phối.'),
 ('A04 Reconcile old and new Epic after Parent change','Parentchanged trênTaskQAG3 cóqag3-scope-approved.','Đối soát rawParentold/new, refetch, đúngEpic/QAG3: chảimớiREVIEW/Done cóTaskchưaDone thìIP; READY gặpTaskđãbắtđầu thìIP. VớiEpicIP đủnonempty/allTaskDone thìREVIEW; REVIEW thiếuTask/mấtTask/chưaDone thìIP.','User who triggered; giữoldDone khichỉbỏTask, khôngautoDone/Cancel/Restore. Nhánhcurrent scope khôngatomic, cần đọcAuditlog cảcha cũ/mới.'),
 ('A05 Notify independent PM review coordinator','Task vàoCODE REVIEW/REVIEW/READY FOR RELEASE hoặcSubtask vàoCODE REVIEW/REVIEW.','Freeze eventkey theoissue status+updated; refetch+so sánh trạngthái; chưa marker thìghiattemptmarker rồicomment. AssigneeKhai → @Hiệp; trườnghợp khác → @Khai.','Automation for Jira; hai commentactions, khôngemail. addCommentOnce=false đểeventreviewmới vẫnnhắc. Marker không chứng minhcommentdelivery; message không phảiQA/acceptance hoặcđiểmhiệu suất.')]
for title, trigger, action, limits in automation:
    h(title,2); p('Kích hoạt: '+trigger); p('Thực hiện: '+action); p('Actor và giới hạn: '+limits)
p('A04 áp dụng kiểm tra trạng thái thực tại lúc thực thi, có thể khác eventgốc nếu có người sửa đồng thời. KhiAudit ghiNo actions performed, trước hết kiểm traParent/status/label; không mặc định thiếuquyền. VớiA05 thấtbại saughi marker, kiểm tra audit vàcommentthật trước resend; không xóa hàng loạtmarker hoặc bật rulechaining để chữatriệu chứng.')
h('9 Bot giám sát và đánh giá thành viên')
p('Trạng thái chốt: heartbeatPAUSED; WindowsTaskDisabled; khôngcònpythonrunner/wrapper. State/events/report đượcgiữ nguyên. A01 đếnA05 chạytrênJiraCloud vẫnEnabled, khôngphụ thuộcbotlocal đangbật.')
bullets(['Collector jira_bot.py gọi officialMCP quahelperjira_mcp.py, kiểm traowner/site/cloud/project vàissuetype; đọcfullpagination tớiisLast. Lỗi hoặcmissingfield bắt buộc → UNKNOWN, giữlastsuccess.', 'Runner jira_monitor.py --interval3600 cósingle-processlockWindows, atomicjson vàeventrunId/PID/cycle/completedAtUtc. Mỗicompletecycle tạo metrics vàmemberAssessment; khôngJira writes.', 'Start-JiraMonitor.ps1 làat-logonInteractive/Limited supervisor, hiddenwindow, IgnoreNew, bounded3retry cách60s sauchildexitlỗi. Taskkhông phảiWindowsservice24/7; logoff/sleep/off không được bảođảm.', 'Heartbeatmỗi giờ phút15 trongchat kiểm quota rồiprocess/eventfreshness<=interval+120s. Runnerđang sống/fresh thì dùngstatekhôngcollect/Gemini lần2. Runneralive nhưngsnapshotstale/error thìUNKNOWN,chờchu kỳ, khôngrestart chỉvìtimeout.', 'Geminioptional hiệnDISABLED_CONFIG. Cầnkey mới antoàn vàFreeTierconfirmed; không paidfallback. Chỉnumericaggregate, khôngrawJira/names/emails/personnelassessment. Gemini output chỉdraft cósourcetimestamp, không lệnh Jira.'])
p('Hai schema khác nhau: jira-bot/state-QAG3.json làcollectorbaseline, runtime/state-QAG3.json làrunnerstate. Không ghi đè baseline bằngruntime hoặc đưa runtime vàojira_gemini.py --snapshot. runtime-cursor.json làcursorcủachat, giữnotificationdedup vàevidencekhác; khôngsửa nóthànhstateJira.')
p('TỷlệfunctionalDone = Task/StoryDone-category khôngCANCELLED/CANCELED chia tổngTask/Storyscope. Công việchủy vẫn ởmẫu số; tổng0→null. MemberAssessment chỉqag3-wbs, loạiqag3-test/excluded-from-performance; từngaccount và từngkind táchriêng. Ởsnapshot11:36+07, mỗi5vai trò39/53SubtaskDone=73,58%. Không cộngEpic/Task/Subtask thànhnăng suất.')
p('Năm chiều đánhgiá deliveryreliability,quality,collaboration,ownership,contribution hiệnINSUFFICIENT_EVIDENCE; overallScore=null. Jira assignee/status/workloggiảdoadmin khôngchứng minhngườilàm. ResetvềNEW khôngphảidefect. Botchỉnotify meaningfulchange,lỗimới,blocker cóevidence hoặcquyếtđịnhcầnowner; khôngnhắc timestamp-only hoặcHTTP400Artifactscũ.')
h('10 Hướng dẫn thao tác từ đầu đến cuối')
h('10 1 Bắt đầu một Epic NEW',2)
p('MởEpic → kiểm traTaskcon/owner/description/AC → chọnApprove scope. NhậpScopeversion mới, chínhxácScopeTaskkeys,AC,Scope resultAPPROVED vàEvidence trênscreen10011. PMđúngaccount xácnhận. Epic vềREADY. Startanalysis Taskcon sẽchoA01 đưaEpic sangIP; chưaApproveScope thìA01 không thểđưaEpicNEW sangIP.')
h('10 2 Làm Task và Subtask',2)
p('Task điStartanalysis → Analysisdone → Startdev; từngSubtaskStartwork. BA/Tester/PM Submitwork rồiPMreview; BE/FE Submitcode → Approvecode → Starttest → Passtesting. Nếubug/reviewreject, dùngnhánhsửa/retest, giữkey/Parent vàbằng chứngnguồn. Hoàn thànhSubtask bằngApprovework; Task vẫnphảiquaQA,Approve vàDeploy riêng.')
h('10 3 Điền QA và review đúng thời điểm',2)
p('Bảy prefixQA phải xuất hiện đúngmột lần vàcógiátrị: Revision:, Environment:, Test scope:, Result:, Evidence:, Retest:, Bug references / retest rationale:. Environment bắtđầuTest -; ResultPASS choHưng hoặcSIMULATED PASS choHiệp vớiqag3-simulation đãcommit từtrước. Nhập Reviewevidence mới ngay trongPass testing, tickQApased vàđúngmộtRetest. SauQA khôngsửa bằngchứng/corefields rồimongApprove giữhợplệ; sửađángkể thìRetest vàQA mới.')
p('Nhánhreviewnghiệpvụ dùng4prefix: Revision:, Review scope:, Review result:, Evidence:. Review resultACCEPTED choquytrìnhthường; owner môphỏngdùngSIMULATED ACCEPTED. Ghi rõtài liệu/chứngcứreviewmới. Không copykếtquảgiảthànhPASS thật hoặcclaimtài khoảnQAđãký.')
p('Lưu ý nhập liệu hiện hành: parserexpression đã đượckiểm thử với separatorhai ký tự backslash vàn trongtext; xuốngdòng thôngthường/ADFformatphức tạpcóthể khôngđượcxử lýnhưmongmuốn. Đểtránh nhậpsai, nhờadapter đãkiểm thử gửiADFparagraph/text đúngđịnhdạng vàđọc lại trướcapprove. Chưa sửaparser này trongcấu hình2.21. Không paste mẫu bất kỳ rồibỏgate để vượt lỗi.')
h('10 4 Nghiệm thu mở lại và đổi phạm vi',2)
p('Chuẩn bị đầy đủcheckboxTask trướcQA, vìApprove/Deploy khôngcóscreenbổsung trongreadbackhiệnhành. MọiSubtaskDone, QAcurrent, PMApprove → Readyforrelease; PMDeploy → Done/ResolutionDone. A02 cóthểđưaEpicIP sangREVIEW, nhưngchỉPMAcceptEpic mớiDone vàcầnscope/evidenceintegrationhandovermới.')
p('Cầnmở lại: chọnReopen, nhậpChange reasonkhácgiátrịcũ ngaytransition, giữhistory. Rework/retest dùngđườnghiện có, khôngdi chuyểnchéovềNEW. Cầnhủy/restoreEpic: PM, freshreason, đọc lạiResolution vìCancelhiệnkhôngcóactionsetresolution. ĐổiParentTask: xácnhậnqag3-scope-approved, ghi nhậncha cũ/mới, xemA04Auditlog; khôngautođổiSubtaskParentkhác nếu khôngđượcduyệt.')
h('11 Tự cập nhật cấu hình theo ý muốn')
p('Thực hiện từng thayđổi nhỏ vàgiữbefore snapshot/export. Đọcassociation/status/transition hiệnhành, khôngrestorebảnv2/inactive từtài liệucũ vàoactivev9/v10/v11. Nếuapp/APIpreview yêu cầuapprovedhash, phảidùngexacthash,currentversion vàthời hạn; khôngđổi timestamp hoặcreplayoperationđãstarted.')
table(['Muốn thay', 'Nơi sửa', 'Điểm phải giữ và kiểm thử'], [
 ['Ngày và phân công','Issue Start date Due date Assignee','Đọc lại mỗiitem; childnằm trongcha; role-routing cóthểđổi theoassignee'],
 ['Board và timeline','QAG3 board3 vàTimeline settings','Mapmọistatus vàcộtDone đúng; timelineWork item start/end dates khôngAligntoSprint'],
 ['Trạng thái và transition','Project settings Workflows rồiEditworkflow','Add/edit nhỏ, Updateworkflow; giữQA/Resolution/gate, testhappy+negative'],
 ['ValidatorForge','forge/qag3-validator/manifest.yml vàworkflowrule','Test/lint/type/runtime; deploydevelopmentđúngapp; khônggỡ1partnerconjunction'],
 ['A01 đếnA05','QAG3 settings Automation','Exportbefore; trigger/scope/actor/labels/frozenkey; save vàAuditlog/readback'],
 ['Bot giám sát','Windows task vàheartbeatmonitor','Bật/tắt cả2 theoýđịnh;CIMnoprocesstrùng;khôngsửaTOMLbằngtay'],
 ['Nhóm thành viên','Jira admin membership vàJIRA_TEAM_QAG3.json','Email khônglàaccountId; updatesallowlist/routing nếuđổingười'],
 ['Field/screen/scheme','Jira admin vàlocalqag3-admin','KhôngsửaDefault/othersite; project10002mapping3type; currentpreview/rollback'] ], [3,5,9])
h('11 1 Bật lại và tạm dừng bot',2)
p('Bật lại: kiểmCIMkhôngrunner/wrapperđúngscript đangsống → Enable-ScheduledTask vàStart-ScheduledTask đúngQLDAPM-Jira-MCP-Monitor → dùngautomation_update bậtmonitorheartbeatACTIVE giữprompt/cadence/thread → đợiCOLLECTEDcomplete → đối chiếuPID/python/command/CreationDate/runId/cycle/freshness. Khôngtạodaemonkhác nếuprocessvẫnsống.')
p('Tạm dừng: automation_updatePAUSED → Disable-ScheduledTask → Stop-ScheduledTask → nếuchildPythoncònsống,đối chiếuPID/Parent/CreationDate/đúngscript rồiStop-Process đúngPID → kiểm0runner/wrapper. KhôngkilltoànPython/Codex,khôngxóastate/events. MuốntắtA01đếnA05phảitắt riêngởJiraAutomation; thao tácbot khôngtắtchúng.')
h('11 2 Đổi nhãn hoặc thêm thành viên',2)
p('qag3-wbs nhận diệnWBS chođánhgiá; qag3-simulation cho dữliệugiả; qag3-scope-approved opt-inphạmviA03/A04; qag3-test vàexcluded-from-performance loại fixture. source-ID làmappingnhậpliệu,dùngchốngtrùng;khôngđượcthaykeyJira bằngsourceID. Giữtoànbộlabels cũkhiAPIsetarray;markerA05 làattemptmetadata,khôngchứngcứgửi.')
p('Thêmngườimới khôngtựnhậnnhánh/gate: cầnresolveaccountId,assignabilityvàmembership; cậpnhậtmanifestPM/QA/Dev/businessallowlists, nativeSubtaskcondition, A05routingnếucần, JIRA_TEAM_QAG3.json vàtests. Khôngcấptoànquyềnadminchỉđể bỏactorcheck; khônglưu token/emailpasswordtrongreport.')
h('12 Sửa lỗi thường gặp và rollback')
table(['Hiện tượng', 'Kiểm tra', 'Cách xử lý'], [
 ['Không thấy transition','Status nguồn, assignee routing, nativecondition, quyền','ĐọclistJiraIssueTransitions; đúngnhánh/actor,khôngđoánID'],
 ['400 thiếureason','Reasonblank/cũ hoặc fieldkhôngtrênscreen','Nhậpreasonmới tại10010/10011; APItextareacầnADF'],
 ['QA stale hoặcApprovefail','QAentry+evidence signature/coreedit/checklist','Returntesting rồifreshQA;khôngchỉsửaPASS thủcông'],
 ['Too many expensive operations','Forgehistory/childlist trongnativecontext','Giữconjunction; táithiệnfixture;optimizetraversalrồitestnative'],
 ['A02 chạy chồng','ToDonefilter vàEpicstatus lúcchạy','GiữfilterDone,refetch/currentcondition; khôngbỏfilterđểnhậnmọievent'],
 ['A03/A04 không chạy','Scopeapprovedlabel/Parent/project/actor','KiểmrawParent vàgate;nhãnkhôngthaypermission'],
 ['A05 không nhắc','Audit, comment, frozenkey, attemptmarker','Đọccommentthậttrướcresend;khôngcoimarker=delivery;emailkhôngđược dùnghiệnnay'],
 ['Runnerstale nhưngPIDcòn','Command/CreationDate/latestcomplete vàhelper','UNKNOWN,chờcycle;khôngrestart/dođọcMCPtrùng'],
 ['Collectorpartial/429/authfail','Pagination/status/error vàOAuth','Giữlastsuccess; khôngghi0/100%;khôngnéquota,browsersessionhoặcpaidfallback'],
 ['TimelinekhônghiệnTask/Subtask','Start/Due vàrange/rowexpand','Đọcfieldtừngmục; Workitemdates; khôngđổi ngày chỉđểđẹpchart'] ], [4,6,7])
p('Rollback automation: khôi phụcexportbefore hoặc tắt đúngrule; giữaudit/commenthistory. Rollback app2.21: khôi phụcnguồn2.19 trước, sauđó mớigỡhistorygate theoapprovedpreview. Khônggỡhistory/freshnesskhi lighteracceptanceđang chạy, khônguninstallappđanggắnworkflow. Resetstatuskhôngphảixóalịch sử; cầnđườngtransitionđượckiểmsoát hoặcmigrationpreview riêng. SnapshotBefore làdữliệuđốichiếu, khônglệnh ghiđèlại329issue.')
h('13 Phần đã kiểm chứng và phần chưa hoàn thiện')
bullets(['Đãkiểmchứng: scheme10004gắnQAG3; baactiveworkflow; A01đếnA05Enabled; targetednativeQA/business/BE/FE/reopen/stale; TaskApproveDeploy; A03reason, A04Parentreconcile, A05commentPM;84descendantresetNEWvàclearResolution;runnercomplete335issue/memberAssessment;108PythonJiratests ởlượtbậtbot.', 'Chưakiểmchứngđầyđủ: T01đếnT23 toànbộ, identitynonPMnative,multiTaskconcurrency/atomicity/exactlyonce, linkedBug/reviewerLeadBA, historycựcdài, code/QA/releasethật, reboot/appclosed/sleep/OAuthexpiry/quota-recoveryởlượtresume.', 'Chưabảovệtấtcảbusinessroletrênmọitransition: các hàngkhôngrulekhôngđượcmô tảthànhhardgate. EpicReanalyse/StartdeliveryvàTaskearlysteps, SubtaskRework cònítgate; EpicCancelResolution actioncònthiếu.', 'JiraFreeđãtừngđượcdowngrade,cácUIlatercóStandardtrialbanner; chưađốisoátbillinglivecuối. KhôngkhẳngđịnhplanFreehiệnhành hoặcchi phí0bấtbiến. ForgeCLI dependencyaudit cũ cófinding, khôngcoi lintPASS làsecurityclean.', 'ỨngdụngForge đangdevelopment2.21, khôngpromotionproductionđãverified. MCPcachedcatalogcóthểkhácsourcefresh25tool; reload/restartcóthểcầnnhưngkhôngtựsửaeffectivepolicy.', 'Lịchcontinue setupkhácmonitor; lầnpause này chỉtắtmonitor. UsernênreviewSchedulednếukhôngmuốncontinuationcònchạy. BáocáokhôngđánhgiárằngtoànsiteJira/fulladmin đãhoànthiện100%.'])
h('14 Nguồn tra cứu và ID cấu hình')
table(['Đối tượng', 'Giá trị'], [['Project/cloud','QAG3 / 10002 / 560ef0cc-d24b-4613-98d3-d541afe8f32b'],['Scheme','10004 QAG3 Managed Delivery v1'],['Epic workflow','5079dd5a-c3a9-4049-a1d7-70c0acc6a365 v9'],['Task workflow','9f21c6fc-718d-4f3c-aca9-49ab9c89c899 v10'],['Subtask workflow','7512e21c-34cd-4fc8-baf4-9398f36f3e37 v11'],['Forge app','f6f77ef8-978a-4e85-a3df-b30d3ef38d06 development2.21'],['Monitorheartbeat','bot-theo-d-i-ti-n-jira-qag3 PAUSED']], [5,12])
table(['Automation','UUID'], [[row['name'].split(' - ')[0],row['uuid']] for row in SOURCE['automation']['rules']], [5,12])
p('Cácfilequan trọng nằmtrongD:\\AI project\\QLDAPM chat: AGENTS.mdquytắc; jira-management.mdtrạngthái; jira-workflows.mdthiếtkếvàhistory; architecture.mdkiếntrúc; JIRA_BOT.mdmonitor; JIRA_TEAM_QAG3.jsonaccountmapping; forge/qag3-validator/manifest.ymllogic; tools/jira_admin_mcp.pyguardedadmin; tools/jira_bot.pycollector; tools/jira_monitor.pyrunner; tools/Start-JiraMonitor.ps1supervisor.')
p('Evidencehiệnhành: jira-bot/handbook-source-2026-10-13.json đọcworkflow/scheme/ruletrực tiếp; automation-fullscope-2026-10-13.jsonnativeactivation; new-epic-reset-before/result-2026-10-13.jsonbefore/after; MONITOR_RESUME_2026-10-13T043621Z.jsonrunner; REPORT_MEMBERS_2026-10-13T043621Z.mdmôphỏng. NativebeforeadminauditlưutrongspecialfolderLOCALAPPDATA/QLDAPM/jira-admin-audit, khôngphảitokenstore vàkhônguploadra ngoài.')
p('Tra cứu trongJira: Project settings → Workflows; Project settings → Automation → từngrule → Auditlog/Settings; issue → History/Worklog/Childworkitems; board3 → Timeline. Đọc mô tả workflow “Inactive/pending” cũ khôngđủkếtluậnchưaactive: associationvàworkflowversionlive mới lànguồnhiệnhành.')
for url in ['https://support.atlassian.com/jira-cloud-administration/docs/create-workflow-transitions/', 'https://support.atlassian.com/jira-cloud-administration/docs/configure-resolutions-in-a-jira-workflow/', 'https://developer.atlassian.com/cloud/jira/platform/jira-expressions/', 'https://support.atlassian.com/cloud-automation/docs/jira-automation-triggers/', 'https://learn.chatgpt.com/docs/automations?surface=app']:
    p(url)
p('Trước mỗiđợtupdate: chốtđíchvàscope → đọcbefore → thayđổinhỏ → preview/approvalnếuđòihỏi → ghi → đọc lại → testpositive/negative → lưureport/rollback. Khôngđánhdấuhoànthànhkhichỉcódraft/fieldtick/settingcard. Đây làquytrìnhđểchủdựánchủđộngđiềuchỉnh màkhôngmất dữliệuhoặc nhầmmôphỏngthànhkếtquảthật.')
editorial = {
    22: 'Ba Epic NEW là QAG3-243 Comment, QAG3-274 Dashboard, QAG3-299 Notification. Toàn bộ 14 Task và 70 Subtask bên dưới đã về NEW, Resolution rỗng, không đổi ngày hoặc assignee. Đường reset tạm đã được gỡ; hiện không có transition reset về NEW cho mọi Task/Subtask. Epic QAG3-212 Issue / Bug còn In Progress dù Task con đang Done: PM cần xem xét, bot không tự nghiệm thu.',
    26: 'Chọn đúng một trong 10023 hoặc 10024. Tick cả hai hoặc không tick đều bị chặn tại gate yêu cầu retest. Task Deploy cần 10020, 10021, 10022, 10025, 10026, 10027 và một lựa chọn retest. Epic Accept cần 10020, 10022, 10025, 10026, 10027 và một retest. Checkbox Lead không tự xác minh reviewer thật.',
    27: 'Screen 10010 là QAG3 Scrum Default Issue Screen cho Task/Subtask; screen 10011 là Epic Screen. Các field không bắt buộc trên mọi edit/create: validator chỉ yêu cầu tại transition đã gắn. Field scheme QAG3 Gate Fields v1 giữ cấu hình cũ và thêm ba gate field. Khả năng hiển thị riêng QAG3 không đồng nghĩa custom field context đã bị giới hạn trên toàn site.',
    33: 'Submit acceptance và Accept Epic kiểm tra Epic không rỗng, mọi Task và Subtask con đều ở status Done (10009). Accept còn cần evidence mới, scope hiện hành, Integration result PASS, Handover result COMPLETE, Evidence, Retest và Bug references / retest rationale. Không được đổi owner, summary hoặc description ngay trong acceptance.',
    39: 'Code rejected, Bug found và ReDev đưa về In Progress để sửa. Retest đưa REVIEW về IN TESTING. Retest before release đưa READY FOR RELEASE về IN TESTING, chỉ PM được thực hiện.',
    40: 'Pass testing cần QA thật hoặc ngoại lệ mô phỏng của Hiệp, evidence mới và retest nhất quán. Chỉ sửa field thành PASS trước đó không tạo chữ ký tại transition.',
    41: 'Approve cần PM, QA-current và QA-freshness. Deploy cần PM, mọi Subtask Done, checklist bàn giao và cả hai QA gate; native condition cũng kiểm tra child Done.',
    42: 'Reopen cần PM và reason mới; xóa Resolution, trở về In Progress chứ không về NEW. Các bước phân tích/code/test đầu chưa có actor validator bổ sung: BA/Dev/Tester là phân công nghiệp vụ, không phải hard gate ở mọi bước.',
    47: 'Assignee BE/FE dùng Submit code, không dùng Submit work. Assignee BA/Tester/PM dùng Submit work và không phải qua Code Review. Condition xét người được giao, không xét người bấm. History gate nhận ra Subtask từng được giao Dev hoặc từng qua trạng thái Dev, nên đổi assignee về BA không loại yêu cầu QA.',
    48: 'Approve work (4) yêu cầu đồng thời acceptance, freshness và history; không tháo riêng một validator. Ngoài ngoại lệ owner mô phỏng, PM phải độc lập với người được giao hiện tại và lịch sử. Rework (5) không có reason validator riêng. Reopen (6) cần reason mới và xóa Resolution, nhưng chưa có PM-only riêng như Task Reopen (15).',
    51: 'Module qag3-pm-only. Chỉ account active của Hiệp hoặc Khai trong QAG3/10002. Quyền Jira nền vẫn phải cho phép transition. Đây không phải org-admin permission; tên hiển thị hoặc email không thay accountId.',
    53: 'Module qag3-epic-children-done. Epic đúng type 10000, có ít nhất một Task. Mọi Task type 10011 ở status 10009; danh sách Subtask type 10010 phải đọc được và tất cả cũng ở status 10009. Đây là kiểm tra trạng thái, không phải kiểm tra code.',
    55: 'Module qag3-fresh-change-reason. Reason phải có nội dung sau trim, khác reason đã lưu trước transition. RichText/ADF được đọc thành plain text; dùng lại giá trị cũ không đạt gate.',
    57: 'Module qag3-task-subtasks-done. Task đúng type 10011; danh sách child phải đọc được và mọi Subtask đúng project/type/status Done. Điều kiện every có thể đúng với danh sách rỗng, nên không khẳng định gate luôn cần ít nhất một Subtask. Native condition còn chạy ở Deploy.',
    59: 'Module qag3-task-delivery-checklist. Đủ sáu option checklist Task, đúng một lựa chọn retest và evidence không rỗng. Gate này không xác minh tài khoản Lead/BA hoặc tính thật của nội dung bằng chứng.',
    61: 'Module qag3-qa-attest. Trước transition phải ở IN TESTING. Tester Hưng active ký PASS; Hiệp chỉ ký SIMULATED PASS khi nhãn qag3-simulation đã được lưu từ trước. Evidence phải mới, đủ bảy prefix; Environment bắt đầu bằng Test - và có nội dung phía sau. Checkbox QA và retest phải khớp kết quả.',
    63: 'Module qag3-qa-current. Phải có history Pass testing (10018 → 10012) và thay Review evidence ngay trong cùng changelog entry. Author đúng QA hoặc owner mô phỏng, evidence không bị sửa sau ký. Approve/Deploy giữ summary, description, Parent, assignee và chạy cùng freshness.',
    65: 'Module qag3-subtask-acceptance. Subtask cần owner. Dev cần QA đã ký và lưu; nhánh nghiệp vụ chưa qua QA cần review mới gồm Revision, Review scope, Review result, Evidence. Kết quả là ACCEPTED, hoặc SIMULATED ACCEPTED theo ngoại lệ owner. Acceptance phải chạy cùng history và freshness.',
    67: 'Module qag3-epic-readiness. PM duyệt từ NEW; owner active, description có nội dung, evidence mới đủ năm prefix. Scope result là APPROVED. Danh sách Scope tasks phải khớp chính xác mọi Task con hiện tại, không thiếu hoặc trùng.',
    69: 'Module qag3-epic-acceptance. PM duyệt từ REVIEW; owner active và các field cốt lõi không đổi trong thao tác. Evidence mới đủ bảy prefix, Integration result PASS, Handover result COMPLETE; checklist và retest nhất quán. Task scope phải khớp và Done; child gate riêng kiểm tra Subtask Done.',
    71: 'Module qag3-qa-freshness. Task đối chiếu status/evidence và lần sửa summary, description, Parent, assignee, evidence gần nhất; chỉ chấp nhận Pass hoặc Approve hợp lệ sau Pass. Với Subtask, kiểm tra PM, owner active, field cốt lõi không đổi khi duyệt và checkbox QA/retest nhất quán nếu đã Pass. Không thay thế QA-current/history.',
    73: 'Module qag3-subtask-history. Đọc đầy đủ lịch sử assignment/status để phát hiện từng làm Dev và tự review. Dev cần chữ ký QA đúng entry, đủ bảy prefix, author hợp lệ và môi trường Test. Sửa nội dung liên quan hoặc rework sau QA làm bằng chứng hết hiệu lực. Không cắt history; cần stress test lịch sử rất dài do giới hạn expensive operations.',
    74: 'Các predicate nối AND qua nhiều validator để giảm expensive operations mỗi expression. Development 2.21 đã qua native BE/FE positive và stale/reuse negative mục tiêu. Type-check Boolean hoặc lint PASS không thay E2E toàn hệ thống. Source manifest quyết định logic; tên và errorMessage chỉ để giải thích lỗi.',
    76: 'A01–A05 hiện ENABLED, scope QAG3/10002. A02–A05 đã bỏ điều kiện qag3-test khỏi trigger; A03/A04 vẫn cần qag3-scope-approved. CanOtherRuleTrigger=false ngăn rule khác kích hoạt dây chuyền, nhưng không tạo giao dịch atomic hoặc exactly-once. Rule chỉ nhận sự kiện mới phù hợp, không tự xử lý lại dữ liệu cũ.',
    79: 'Thực hiện: branch Parent, đọc lại dữ liệu; Epic QAG3 đang READY (10011) chuyển sang In Progress.',
    80: 'Actor và giới hạn: Automation for Jira. Epic NEW không được tự duyệt scope; nếu cha còn NEW thì A01 không đưa sang In Progress.',
    82: 'Kích hoạt: Work item transitioned, To status = Done; Task type 10011, status 10009, có Parent.',
    83: 'Thực hiện: đọc lại Epic cha đang In Progress. Nếu có Task con và mọi Task con Done, đưa Epic sang REVIEW.',
    84: 'Actor và giới hạn: Automation for Jira. Không Accept Epic hoặc chuyển Done. Filter To Done đã sửa lỗi event Approve xếp hàng nhưng khi xử lý lại thấy Done. Chưa bảo đảm exactly-once khi nhiều Task đổi đồng thời.',
    86: 'Kích hoạt: Task được tạo hoặc chuyển trạng thái, chưa Done, có Parent và nhãn qag3-scope-approved.',
    87: 'Thực hiện: Epic cha REVIEW hoặc Done chuyển sang In Progress với Change reason mới. Không restore CANCELLED.',
    88: 'Actor và giới hạn: User who triggered. Nhãn scope là metadata nghiệp vụ, không phải quyền truy cập. Người chạy vẫn chịu gate và permission thật.',
    90: 'Kích hoạt: Parent thay đổi trên Task QAG3 có nhãn qag3-scope-approved.',
    91: 'Thực hiện: lấy Parent cũ/mới, đọc lại và chỉ xử lý Epic QAG3. Cha mới REVIEW/Done có Task chưa Done → In Progress; cha READY có Task đã bắt đầu → In Progress. Epic In Progress có ít nhất một Task và mọi Task Done → REVIEW. Epic REVIEW rỗng hoặc có Task chưa Done → In Progress.',
    92: 'Actor và giới hạn: User who triggered. Giữ cha cũ Done khi chỉ bỏ Task; không tự Done/Cancel/Restore. Đối soát không atomic; cần xem Audit log của cả cha cũ và cha mới.',
    94: 'Kích hoạt: Task vào CODE REVIEW, REVIEW, READY FOR RELEASE; hoặc Subtask vào CODE REVIEW, REVIEW.',
    95: 'Thực hiện: chốt event key theo issue, status, updated; đọc lại và so sánh trạng thái. Nếu chưa có marker, ghi marker đã thử rồi bình luận. Assignee Khai → @Hiệp; trường hợp khác → @Khai.',
    96: 'Actor và giới hạn: Automation for Jira. Hai action comment, không email. addCommentOnce=false để lần review mới vẫn được nhắc. Marker không chứng minh comment đã gửi; bình luận không phải bằng chứng QA, nghiệm thu hoặc điểm hiệu suất.',
    97: 'A04 xét trạng thái tại lúc thực thi, có thể khác event gốc nếu có sửa đồng thời. Audit ghi No actions performed: kiểm tra Parent, status, label trước khi kết luận thiếu quyền. A05 lỗi sau ghi marker: xem audit và comment thật trước gửi lại. Không xóa hàng loạt marker hoặc bật rule chaining để chữa triệu chứng.',
    99: 'Trạng thái chốt: heartbeat PAUSED; Windows task Disabled; không còn Python runner/wrapper. State, events, report được giữ nguyên. A01–A05 trên Jira Cloud vẫn Enabled và không phụ thuộc bot local.',
    100: 'Collector jira_bot.py dùng official MCP qua jira_mcp.py; xác minh owner/site/cloud/project/issue type và đọc đủ pagination đến isLast. Lỗi hoặc thiếu field bắt buộc → UNKNOWN, giữ last successful snapshot.',
    101: 'Runner jira_monitor.py --interval 3600 dùng single-process lock Windows, atomic JSON, event có runId/PID/cycle/completedAtUtc. Mỗi chu kỳ hoàn tất ghi metrics và memberAssessment; không sửa Jira.',
    102: 'Start-JiraMonitor.ps1 là supervisor at-logon Interactive/Limited, hidden window, IgnoreNew; tối đa ba retry cách 60 giây sau child exit lỗi. Không phải Windows service 24/7; logoff, sleep, tắt máy chưa được bảo đảm.',
    103: 'Heartbeat mỗi giờ phút 15 trong chat kiểm quota rồi đối chiếu process và event. Dữ liệu chỉ fresh khi latest complete không cũ hơn interval + 120 giây. Runner sống và fresh: dùng state, không thu hoặc gọi Gemini lần hai. Runner sống nhưng stale/lỗi: UNKNOWN, chờ chu kỳ; không restart chỉ vì timeout.',
    104: 'Gemini optional hiện DISABLED_CONFIG. Cần key mới lưu an toàn và xác nhận Free Tier chưa billing; không fallback trả phí. Chỉ gửi numeric aggregate, không raw Jira, tên, email hay đánh giá nhân sự. Kết quả chỉ là draft có source timestamp, không phải lệnh Jira.',
    105: 'Hai schema riêng: jira-bot/state-QAG3.json là collector baseline; runtime/state-QAG3.json là runner state. Không ghi đè baseline bằng runtime hoặc đưa runtime vào jira_gemini.py --snapshot. runtime-cursor.json là cursor của chat, giữ metadata chống thông báo lặp, không phải Jira state.',
    106: 'Functional completion = Task/Story thuộc Done-category và không CANCELLED/CANCELED, chia tổng Task/Story trong scope. Công việc hủy vẫn ở mẫu số; tổng bằng 0 → chưa có phạm vi, tỷ lệ null. MemberAssessment chỉ qag3-wbs, loại qag3-test/excluded-from-performance. Snapshot 11:36 +07: mỗi vai trò có 39/53 Subtask Done = 73,58%; không cộng Epic/Task/Subtask thành năng suất.',
    107: 'Năm chiều delivery reliability, quality, collaboration, ownership, contribution hiện INSUFFICIENT_EVIDENCE; overallScore=null. Assignee/status/worklog giả do admin không chứng minh người làm thật. Reset NEW không phải defect. Bot chỉ nhắc biến động có ý nghĩa, lỗi mới, blocker có bằng chứng hoặc việc cần owner; không nhắc timestamp-only hay lỗi HTTP400 Artifacts cũ.',
    110: 'Mở Epic → kiểm tra Task con, owner, description/AC → chọn Approve scope. Tại screen 10011, nhập Scope version mới, Scope tasks chính xác, Acceptance criteria, Scope result APPROVED và Evidence. PM xác nhận → READY. Khi Task con Start analysis, A01 có thể đưa Epic sang In Progress; cha còn NEW thì A01 không duyệt thay PM.',
    112: 'Task đi Start analysis → Analysis done → Start dev. Mỗi Subtask Start work: BA/Tester/PM Submit work rồi PM review; BE/FE Submit code → Approve code → Start test → Pass testing. Có lỗi/reject: dùng nhánh sửa/retest, giữ key/Parent và bằng chứng. Hoàn thành Subtask bằng Approve work; Task vẫn phải qua QA, Approve, Deploy riêng.',
    114: 'QA evidence cần đúng một lần mỗi prefix và có giá trị: Revision:, Environment:, Test scope:, Result:, Evidence:, Retest:, Bug references / retest rationale:. Environment bắt đầu bằng Test -. Hưng ký Result PASS; Hiệp dùng SIMULATED PASS và qag3-simulation đã lưu từ trước. Nhập Review evidence mới ngay trong Pass testing; tick QA passed và đúng một retest. Sửa nội dung liên quan sau QA thì phải Retest và ký QA mới.',
    115: 'Review nghiệp vụ cần Revision:, Review scope:, Review result:, Evidence:. Kết quả ACCEPTED cho quy trình thường; owner mô phỏng dùng SIMULATED ACCEPTED. Ghi tài liệu hoặc chứng cứ review mới. Không biến kết quả giả thành PASS thật hoặc khẳng định QA đã ký.',
    116: 'Giới hạn nhập liệu hiện hành: expression parser được kiểm thử với separator gồm hai ký tự backslash và n trong text. Xuống dòng thông thường hoặc ADF phức tạp có thể không được xử lý như mong muốn. Dùng adapter đã kiểm thử gửi ADF đúng định dạng, đọc lại trước approve. Chưa sửa parser trong bản 2.21; không bỏ gate để vượt lỗi nhập liệu.',
    118: 'Chuẩn bị checklist Task trước QA, vì Approve/Deploy hiện không có screen bổ sung. Mọi Subtask Done, QA còn hiệu lực: PM Approve → READY FOR RELEASE; PM Deploy → Done/Resolution Done. A02 có thể đưa Epic In Progress sang REVIEW; chỉ Accept Epic mới đưa Done, với scope và evidence tích hợp/bàn giao mới.',
    119: 'Mở lại: chọn Reopen, nhập Change reason khác giá trị cũ ngay tại transition, giữ history. Rework/retest dùng đường có sẵn, không tự reset NEW. Hủy/restore Epic cần PM và reason mới; đọc lại Resolution vì Cancel chưa có action set Resolution. Đổi Parent Task: nhãn qag3-scope-approved, xác minh cha cũ/mới và xem A04 Audit log.',
    121: 'Thay đổi từng phần nhỏ, giữ before snapshot/export. Đọc association/status/transition hiện hành; không khôi phục workflow inactive/version cũ lên active v9/v10/v11. Nếu API yêu cầu approved hash, dùng đúng hash, current version và thời hạn. Không sửa timestamp hoặc replay operation đã started.',
    124: 'Bật lại: kiểm CIM không còn runner/wrapper đúng script → Enable-ScheduledTask và Start-ScheduledTask cho QLDAPM-Jira-MCP-Monitor → automation_update đưa heartbeat ACTIVE, giữ prompt/cadence/thread → đợi COLLECTED complete → đối chiếu PID, python, command, CreationDate, runId/cycle/freshness. Không tạo daemon thứ hai khi process còn sống.',
    125: 'Tạm dừng: automation_update PAUSED → Disable-ScheduledTask → Stop-ScheduledTask. Nếu child Python còn sống, xác minh PID/Parent/CreationDate/script rồi Stop-Process đúng PID; kiểm 0 runner/wrapper. Không kill toàn bộ Python/Codex, không xóa state/events. Muốn tắt A01–A05 phải làm riêng trong Jira Automation.',
    127: 'qag3-wbs nhận diện WBS; qag3-simulation cho dữ liệu giả; qag3-scope-approved opt-in A03/A04; qag3-test/excluded-from-performance loại fixture. Nhãn source-ID phục vụ mapping nhập/chống trùng, không thay Jira key. Giữ labels cũ khi API set array. Marker A05 ghi lần thử, không phải xác nhận gửi.',
    128: 'Thêm người không tự có nhánh/gate. Cần resolve accountId, membership, assignability; cập nhật manifest allowlist PM/QA/Dev/nghiệp vụ, native Subtask condition, A05 routing nếu cần, JIRA_TEAM_QAG3.json và tests. Không cấp admin chỉ để bỏ actor check; không ghi token/password trong report.',
    131: 'Rollback automation: khôi phục export before hoặc tắt đúng rule, giữ audit/comment history. Rollback app 2.21: khôi phục nguồn 2.19 trước rồi mới gỡ history gate qua preview được duyệt. Không gỡ một gate khi acceptance đã được tách logic, không uninstall app đang gắn workflow. Reset status không xóa lịch sử; before snapshot không phải lệnh ghi đè 329 issue.',
    133: 'Đã kiểm chứng: scheme 10004 gắn QAG3; ba workflow active; A01–A05 Enabled; targeted native QA/nghiệp vụ/BE/FE/reopen/stale; Task Approve/Deploy; A03 reason, A04 Parent reconcile, A05 comment PM; 84 descendant NEW/Resolution rỗng; runner thu đủ 335 issue/memberAssessment; 108 Python Jira tests ở lượt bật bot.',
    134: 'Chưa kiểm chứng đầy đủ: toàn bộ T01–T23, identity non-PM native, nhiều Task đồng thời/atomicity/exactly-once, linked Bug/reviewer Lead/BA, history cực dài, code/QA/release thật, reboot/app đóng/sleep/OAuth hết hạn/quota recovery ở lượt resume.',
    135: 'Chưa có hard gate cho mọi vai trò tại mọi transition: Epic Reanalyse/Start delivery, Task các bước đầu và Subtask Rework còn ít gate. Epic Cancel còn thiếu action Resolution. Bảng transition chỉ ra đúng những rule hiện có, không diễn giải hàng trống thành kiểm soát đã triển khai.',
    136: 'Jira Free từng được downgrade; một số UI sau đó có Standard trial banner. Chưa đối soát billing live cuối nên không cam kết plan Free hiện hành hoặc chi phí 0 bất biến. Forge CLI dependency audit cũ có finding; lint PASS không đồng nghĩa security clean.',
    137: 'Forge đang development 2.21, chưa xác minh promotion production. MCP cached catalog có thể khác catalog nguồn; có thể cần reload/restart nhưng không tự sửa effective policy. Tài liệu không tuyên bố full-admin trên toàn site đã hoàn thiện.',
    138: 'Lịch tiếp tục setup khác monitor: lần tạm dừng này chỉ tắt monitor. Nếu muốn dừng mọi lịch, cần xem và tắt riêng lịch continuation; không suy việc tắt bot đã tắt tất cả scheduled task.',
    143: 'Nguồn nội bộ: jira-bot/handbook-source-2026-10-13.json (workflow/scheme/rule đọc thật); automation-fullscope-2026-10-13.json (activation); new-epic-reset-before/result-2026-10-13.json (before/after); MONITOR_RESUME_2026-10-13T043621Z.json; MONITOR_PAUSE_2026-10-13T044841Z.json; REPORT_MEMBERS_2026-10-13T043621Z.md. Admin audit nằm dưới LOCALAPPDATA/QLDAPM/jira-admin-audit; không chứa token store và không upload ra ngoài.',
    144: 'Tra cứu Jira: Project settings → Workflows; Project settings → Automation → rule → Audit log/Settings; issue → History/Work log/Child work items; board 3 → Timeline. Mô tả cũ Inactive/pending không quyết định trạng thái: association và workflow version live mới là nguồn hiện hành.',
    150: 'Mỗi đợt cập nhật: chốt đích/scope → đọc before → thay đổi nhỏ → preview/approval nếu cần → ghi → đọc lại → kiểm thử positive/negative → lưu báo cáo/rollback. Không đánh dấu hoàn thành chỉ từ draft, checkbox hoặc setting card. Cách này giúp chủ dự án điều chỉnh mà không mất dữ liệu hoặc nhầm mô phỏng thành kết quả thật.'
}
assert len(doc.paragraphs) == 151, 'Paragraph structure changed; re-check editorial mapping'
for index, text in editorial.items():
    doc.paragraphs[index].text = text
doc.paragraphs[2].text = 'Ngày chốt 13 tháng 10 năm 2026 | Phiên bản tài liệu 1 | Tài liệu riêng tư'
for parent in (doc.styles.element, doc.element):
    for border in list(parent.iter(qn('w:pBdr'))):
        border.getparent().remove(border)
cached_page = OxmlElement('w:r')
cached_text = OxmlElement('w:t'); cached_text.text = '1'; cached_page.append(cached_text); field.append(cached_page)
for index in range(145, 150):
    doc.paragraphs[index].paragraph_format.space_after = Pt(3)
    for run in doc.paragraphs[index].runs:
        run.font.size = Pt(9)
operating_sections = [
    ('2.1 Backlog, liên kết cha con và lịch mô phỏng', 'Heading 2'),
    ('Backlog là danh sách phạm vi đã nhập từ WBS: Epic theo module, Task theo chức năng, Subtask theo vai trò. Khi thêm Task, chọn đúng Epic trong Parent; khi thêm Subtask, Parent là Task, không phải Epic. Kiểm tra nhãn source-ID trước khi nhập lại để tránh trùng. Các fixture kiểm thử phải giữ qag3-test/excluded-from-performance và không nhập vào mẫu số WBS. Không coi đổi Parent là sao chép hoặc xóa công việc: key/history giữ nguyên, A04 đối soát hai Epic.', None),
    ('Lịch là kế hoạch giả lập học tập, không phải timestamp thực thi. Đợt lập lịch hiện có ngày Start/Due cho 329 mục, từ 03/04 đến 31/12/2026. Epic được xếp lần lượt; Task nằm trong khoảng Epic, Subtask nằm trong khoảng Task. Ngày sớm hơn không chứng minh đã làm từ ngày đó; Done không tự cập nhật Start/Due. Đổi lịch phải đối soát từng child, không chỉ kéo thanh Epic rồi cho rằng mọi Task/Subtask đã đổi.', None),
    ('2.2 Board, Sprint và Timeline', 'Heading 2'),
    ('Board QAG3 ID 3 dùng để xem và thao tác công việc; Project settings → Workflows là cấu hình phía sau, không phải board. Trạng thái có thể không hiện trên board nếu chưa được map vào cột. Cột cuối cần chứa trạng thái Done thật; READY FOR RELEASE không phải Done. Khi thiếu thẻ, kiểm tra board filter, quick filter, sprint và status mapping, không kết luận issue đã bị xóa.', None),
    ('Timeline của board 3: chọn range đủ rộng, mở Epic rồi Task để thấy Subtask, sử dụng Work item start/end dates thay vì Align to Sprint khi muốn xem ngày riêng từng mục. Chưa xác minh lại mọi setting board/Sprint trong lượt báo cáo này. Không cam kết tạo Sprint, start/complete Sprint, capacity hoặc release version đã được cấu hình chỉ từ việc có lịch Start/Due. Muốn vận hành Sprint: kiểm backlog, thêm Task phù hợp, nhập goal và lịch, start khi được chủ dự án quyết định; complete phải xem công việc chưa Done và chọn đưa về backlog/Sprint tiếp theo.', None),
    ('2.3 Comment, worklog, báo cáo và quyền', 'Heading 2'),
    ('Comment dùng trao đổi; @mention PM của A05 là nhắc điều phối và được người có quyền xem issue nhìn thấy. History là nguồn đổi field/status; Work log ghi thời lượng và author, không đồng nghĩa assignee là người đã làm. Các worklog hiện có là mô phỏng, gồm 265 bản/384 giờ đã đối soát ở lượt trước và do admin ghi. Story point là ước lượng tương đối, không phải giờ thực tế; không cộng hai loại thành điểm năng suất.', None),
    ('Dashboard/report Jira phụ thuộc filter, quyền và dữ liệu đang hiển thị; bot local là nguồn báo cáo riêng, không tự tạo mọi dashboard. Notifications còn chịu cấu hình Jira, quyền xem issue và tùy chọn cá nhân; A05 comment không bảo đảm email đến hộp thư. Người được mời tự accept. Admin có quyền cấu hình nhưng workflow validator vẫn có thể chặn transition; quyền quản trị không tự tạo chữ ký QA thật. Khi thêm người hoặc thay role, cập nhật cả native condition và allowlist Forge, không chỉ đổi assignee.', None)
]
anchor = doc.paragraphs[23]._p
for text, style in operating_sections:
    added = doc.add_paragraph(text, style)
    anchor.addprevious(added._p)
doc.paragraphs[10].text = '\n'.join(p.text for p in doc.paragraphs if p.style.name == 'Heading 1' and p.text != 'Mục lục')
doc.paragraphs[11].text = 'Mục lục theo chương. Trong Word, dùng View → Navigation Pane để nhảy đến tiêu đề và chỉnh sửa từng phần.'
clean_tables = {
    9: [
        ['Ngày và phân công', 'Issue: Start date, Due date, Assignee', 'Đọc lại từng item; lịch con nằm trong lịch cha; assignee có thể đổi nhánh workflow.'],
        ['Board và timeline', 'QAG3 board 3 / Timeline settings', 'Map đầy đủ status, cột Done đúng; dùng Work item start/end dates, không Align to Sprint.'],
        ['Status / transition', 'Project settings → Workflows → Edit workflow', 'Thay đổi nhỏ; Update workflow; giữ QA/Resolution/gate, test cả đạt và bị chặn.'],
        ['Forge validator', 'forge/qag3-validator/manifest.yml và workflow rule', 'Lint/type/runtime, deploy đúng app; không gỡ một gate của phép AND.'],
        ['A01–A05', 'QAG3 settings → Automation', 'Export trước; kiểm trigger/scope/actor/label/event key; Save, Audit log và readback.'],
        ['Bot giám sát', 'Windows task và monitor heartbeat', 'Bật/tắt cả hai; CIM không có process trùng; không sửa TOML bằng tay.'],
        ['Thành viên', 'Jira admin membership; JIRA_TEAM_QAG3.json', 'Email không thay accountId; cập nhật allowlist/routing và kiểm thử khi đổi người.'],
        ['Field/screen/scheme', 'Jira admin và local qag3-admin', 'Không sửa Default/project khác; QAG3 10002 mapping ba type; preview/rollback hiện hành.']
    ],
    10: [
        ['Không thấy transition', 'Status nguồn, assignee routing, native condition, quyền', 'Đọc listJiraIssueTransitions; chọn đúng nhánh/actor, không đoán ID.'],
        ['400 thiếu reason', 'Reason rỗng/cũ hoặc field thiếu trên screen', 'Nhập reason mới tại screen 10010/10011; textarea API cần ADF.'],
        ['QA stale / Approve fail', 'QA entry, evidence signature, core edit, checklist', 'Quay về testing và ký QA mới; không chỉ sửa PASS thủ công.'],
        ['Too many expensive operations', 'History/child list của expression trong native context', 'Giữ phép AND; tái hiện fixture, tối ưu traversal rồi test transition thật.'],
        ['A02 chạy chồng', 'Filter To Done và trạng thái Epic lúc chạy', 'Giữ filter Done/refetch/current condition, không nhận mọi event.'],
        ['A03/A04 không chạy', 'Nhãn scope approved, Parent, project, actor', 'Kiểm raw Parent và gate; label không thay permission.'],
        ['A05 không nhắc', 'Audit, comment, event key, attempt marker', 'Đọc comment thật trước gửi lại; marker không bằng delivery; không dùng email.'],
        ['Runner stale nhưng PID còn', 'Command, CreationDate, latest complete, helper', 'UNKNOWN, chờ chu kỳ; không restart/đọc MCP trùng vì timeout.'],
        ['Collector partial / 429 / auth fail', 'Pagination, response status, OAuth', 'Giữ last success; không ghi 0/100%, không né quota bằng browser/paid fallback.'],
        ['Timeline thiếu Task/Subtask', 'Start/Due từng mục, range, mở rộng hàng', 'Chọn Work item dates; không sửa ngày chỉ để làm đẹp chart.']
    ]
}
for ti, rows in clean_tables.items():
    assert len(doc.tables[ti].rows) == len(rows) + 1
    for row, values in zip(list(doc.tables[ti].rows)[1:], rows):
        for cell, text in zip(row.cells, values):
            cell.text = text
cell_order = ['cnfStyle', 'tcW', 'gridSpan', 'hMerge', 'vMerge', 'tcBorders', 'shd', 'noWrap', 'tcMar', 'textDirection', 'tcFitText', 'vAlign', 'hideMark']
for t in doc.tables:
    for row in t.rows:
        cant_split = OxmlElement('w:cantSplit')
        row._tr.get_or_add_trPr().append(cant_split)
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9.5)
            pr = cell._tc.get_or_add_tcPr()
            for shade in pr.findall(qn('w:shd')):
                shade.set(qn('w:val'), 'clear')
            children = sorted(list(pr), key=lambda e: cell_order.index(e.tag.split('}')[-1]) if e.tag.split('}')[-1] in cell_order else 99)
            for child in children:
                pr.remove(child)
            for child in children:
                pr.append(child)
doc.core_properties.title = 'Hướng dẫn vận hành hệ thống Jira QAG3'
doc.core_properties.subject = 'Workflow automation gates monitor and update runbook'
doc.core_properties.author = 'Chủ dự án QAG3'
doc.save(OUT)
assert len(doc.tables) >= 10 and len(SOURCE['workflows']['task']['workflow']['workflows'][0]['transitions']) == 16
print(OUT)
