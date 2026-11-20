"""An illustrated beginner handbook; native arrows are checked against saved Jira evidence."""
import json
import math
from pathlib import Path
from collections import Counter
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT/'jira-bot/handbook-source-2026-10-13.json').read_text(encoding='utf-8'))
OUT = ROOT/'Giao_trinh_Jira_QAG3_truc_quan_2026-10-13.docx'
ASSETS = ROOT/'jira-bot/learning-guide-2026-10-13'
ASSETS.mkdir(exist_ok=True)
if OUT.exists():
    raise FileExistsError('Keep the previous document; choose a new output name')
FONT = 'C:/Windows/Fonts/arial.ttf'
BOLD = 'C:/Windows/Fonts/arialbd.ttf'
BLUE, RED, GREEN, GRAY = '#245A81', '#AD433E', '#287255', '#6B7280'
coverage = {k:set() for k in ('epic','task','subtask')}
figures = []

def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)

def wrap(draw, text, size, width, bold=False):
    lines = []
    for raw in text.split('\n'):
        line = ''
        for word in raw.split():
            candidate = (line + ' ' + word).strip()
            if draw.textlength(candidate, font=font(size,bold)) > width and line:
                lines.append(line); line = word
            else:
                line = candidate
        lines.append(line)
    return lines

def centered(draw, xy, text, size=50, width=620, color='#182C3D', bold=False):
    lines = wrap(draw,text,size,width,bold)
    height = len(lines)*(size+12)
    for i,line in enumerate(lines):
        draw.text((xy[0],xy[1]-height/2+i*(size+12)),line,font=font(size,bold),fill=color,anchor='mt')

def node(draw, center, text, width=700, height=160, fill='#E9F1F7', color=BLUE):
    x,y=center
    draw.rounded_rectangle((x-width/2,y-height/2,x+width/2,y+height/2),radius=24,fill=fill,outline=color,width=4)
    centered(draw,center,text,size=52,width=width-48,bold=True)

def arrow(draw, points, color=BLUE, label=None, label_at=None, label_width=370):
    draw.line(points,fill=color,width=7,joint='curve')
    a,b=points[-2],points[-1]
    angle=math.atan2(b[1]-a[1],b[0]-a[0])
    tip=b
    left=(b[0]-28*math.cos(angle)+14*math.sin(angle),b[1]-28*math.sin(angle)-14*math.cos(angle))
    right=(b[0]-28*math.cos(angle)-14*math.sin(angle),b[1]-28*math.sin(angle)+14*math.cos(angle))
    draw.polygon([tip,left,right],fill=color)
    if label:
        lines=wrap(draw,label,44,label_width)
        w=max(draw.textlength(x,font=font(44)) for x in lines)+24; h=len(lines)*56+12
        x,y=label_at
        draw.rounded_rectangle((x-w/2,y-h/2,x+w/2,y+h/2),radius=9,fill='white')
        centered(draw,(x,y),label,44,label_width,color=color)

def save_figure(name, img, source, semantics):
    path=ASSETS/(name+'.png'); img.save(path)
    (ASSETS/(name+'.mmd')).write_text(source,encoding='utf-8')
    figures.append({'name':name,'png':str(path),'source':name+'.mmd','semantics':semantics})
    return path

def actual_edges(kind, ids):
    data=DATA['workflows'][kind]['workflow']
    wf=data['workflows'][0]
    names={s['statusReference']:s['name'] for s in data['statuses']}
    edges=[]
    for tid in ids:
        t=next(t for t in wf['transitions'] if t['id']==str(tid))
        links=t['links'] or [{}]
        for link in links:
            start=names.get(link.get('fromStatusReference'),'TẠO MỚI')
            end=names[t['toStatusReference']]
            edges.append((start,end,f"{tid}  {t['name']}"))
            coverage[kind].add((str(tid),link.get('fromStatusReference'),t['toStatusReference']))
    return edges

def rows_diagram(name, rows, kind=None, color=BLUE):
    # Each horizontal arrow is independent; no implicit route between rows.
    if kind: rows=actual_edges(kind,rows)
    img=Image.new('RGB',(2200,100+len(rows)*210),'white'); d=ImageDraw.Draw(img)
    source=['flowchart LR']
    for i,(start,end,label) in enumerate(rows):
        y=110+i*210
        node(d,(440,y),start,700,150,fill='#F0F4F8',color=color)
        node(d,(1760,y),end,700,150,fill='#E8F4ED' if end in ('Done','ĐƯỢC ĐI TIẾP') else '#E9F1F7',color=GREEN if end=='Done' else color)
        arrow(d,[(810,y),(1385,y)],color,label,(1100,y),400)
        source.append(f'  a{i}["{start}"] -->|"{label}"| b{i}["{end}"]')
    return save_figure(name,img,'\n'.join(source),'native transitions' if kind else 'conceptual explanation')

def chain(name, nodes, labels, kind=None, ids=None):
    if kind:
        edges=actual_edges(kind,ids)
        assert len(edges)==len(ids)
        assert all(edges[i][1]==edges[i+1][0] for i in range(len(edges)-1))
        nodes=[edges[0][0]]+[e[1] for e in edges]; labels=[e[2] for e in edges]
    rows=math.ceil(len(nodes)/2)
    img=Image.new('RGB',(2200,rows*340+80),'white'); d=ImageDraw.Draw(img)
    positions=[]
    for i in range(len(nodes)):
        row=i//2; col=i%2 if row%2==0 else 1-i%2
        positions.append((460 if col==0 else 1740,150+row*340))
    for i,label in enumerate(labels):
        x,y=positions[i]; nx,ny=positions[i+1]
        if y==ny:
            sign=1 if nx>x else -1
            arrow(d,[(x+sign*365,y),(nx-sign*365,y)],label=label,label_at=(1100,y),label_width=470)
        else:
            arrow(d,[(x,y+86),(x,ny-86)],label=label,label_at=(x,(y+ny)/2),label_width=700)
    for pos,text in zip(positions,nodes):
        node(d,pos,text,720,165,fill='#E8F4ED' if text in ('Done','XONG') else '#E9F1F7',color=GREEN if text in ('Done','XONG') else BLUE)
    source=['flowchart LR']+[f'  n{i}["{text}"]' for i,text in enumerate(nodes)]
    source += [f'  n{i} -->|"{label}"| n{i+1}' for i,label in enumerate(labels)]
    return save_figure(name,img,'\n'.join(source),'native transitions' if kind else 'conceptual explanation')

def hierarchy():
    img=Image.new('RGB',(2200,1120),'white'); d=ImageDraw.Draw(img)
    for a,b in [((1100,225),(1100,355)),((1100,515),(1100,645))]:arrow(d,[a,b])
    for x in (240,670,1100,1530,1960):arrow(d,[(1100,805),(1100,860),(x,860),(x,940)])
    node(d,(1100,145),'DỰ ÁN QAG3',980)
    node(d,(1100,435),'EPIC  Việc lớn',980)
    node(d,(1100,725),'TASK  Một chức năng',980)
    for x,text in zip((240,670,1100,1530,1960),('BA\nĐặc tả','BE\nBackend','FE\nFrontend','QA\nKiểm thử','PM\nBàn giao')):node(d,(x,1020),text,390,150)
    return save_figure('01_cay_cong_viec',img,'flowchart TB\nProject --> Epic --> Task\nTask --> BA\nTask --> BE\nTask --> FE\nTask --> QA\nTask --> PM','conceptual hierarchy; not workflow transitions')

HIER=hierarchy()
SYSTEM=rows_diagram('02_ai_lam_gi',[('Người dùng','Jira','Ghi và xem công việc'),('Người dùng','Workflow','Bấm nút chuyển'),('Workflow','Jira','Cập nhật khi đạt điều kiện'),('Jira','Automation','Sự kiện phù hợp'),('Jira','Bot giám sát','Đọc dữ liệu'),('Bot giám sát','Báo cáo riêng','Tổng hợp và giải thích')])
EPIC_MAIN=chain('03_epic_duong_chinh',[],[],kind='epic',ids=[1,2,4,5,6])
EPIC_BACK=rows_diagram('04_epic_quay_lai',[3,7,8,10],kind='epic',color=RED)
EPIC_CANCEL=rows_diagram('05_epic_huy',[9],kind='epic',color=RED)
TASK_A=chain('06_task_chuan_bi_code',[],[],kind='task',ids=[1,2,3,4,5])
TASK_B=chain('07_task_test_ban_giao',[],[],kind='task',ids=[7,8,10,13,14])
TASK_BACK=rows_diagram('08_task_sua_lai',[6,9,11,12,15,16],kind='task',color=RED)
SUB_BUS=chain('09_subtask_nghiep_vu',[],[],kind='subtask',ids=[1,2,3,4])
SUB_DEV=chain('10_subtask_code',[],[],kind='subtask',ids=[1,2,7,9,10,12,4])
SUB_BACK=rows_diagram('11_subtask_sua_lai',[5,6,8,11,13],kind='subtask',color=RED)
QA_FLOW=rows_diagram('12_cua_kiem_tra',[('Bấm Pass testing','Vẫn ở IN TESTING','Sai người hoặc thiếu bằng chứng'),('Bấm Pass testing','REVIEW','Đúng người và đủ bằng chứng'),('Bấm Approve hoặc Deploy','Giữ trạng thái cũ','Một điều kiện chưa đạt'),('Bấm Approve hoặc Deploy','ĐƯỢC ĐI TIẾP','TẤT CẢ điều kiện đã đạt')])
A12=rows_diagram('13_a01_a02',[('Task bắt đầu làm','Epic READY → In Progress','A01 và đúng điều kiện'),('Task cuối cùng Done','Epic In Progress → REVIEW','A02 và mọi Task con Done'),('Epic REVIEW','Epic Done','PM Accept Epic  KHÔNG phải A02')])
A3=rows_diagram('14_a03',[('Task chưa Done có nhãn duyệt','Epic REVIEW → In Progress','A03 kèm reason mới'),('Task chưa Done có nhãn duyệt','Epic Done → In Progress','A03 kèm reason mới'),('Epic CANCELLED','Giữ CANCELLED','A03 không tự khôi phục')])
A4=rows_diagram('15_a04',[('Cha mới REVIEW hoặc Done','In Progress','Có Task chuyển đến chưa Done'),('Cha mới READY','In Progress','Task chuyển đến đã bắt đầu'),('Cha cũ hoặc mới In Progress','REVIEW','Có Task và tất cả Task Done'),('Cha cũ hoặc mới REVIEW','In Progress','Rỗng hoặc có Task chưa Done'),('Cha cũ Done','Giữ Done','Chỉ chuyển Task ra khỏi cha')])
A5=chain('16_a05',['ĐẾN BƯỚC CẦN XEM LẠI','ĐỌC LẠI ISSUE','CHỐT LẦN NHẮC','BÌNH LUẬN NHẮC PM'],['Task hoặc Subtask đúng trigger','Đúng event và chưa có marker','Ghi marker rồi gửi comment'])
BOT=chain('17_bot',['JIRA','RUNNER LOCAL','STATE VÀ EVENTS','HEARTBEAT CHAT','BÁO CÁO RIÊNG'],['Đọc đủ dữ liệu','Lưu chu kỳ hoàn tất','Kiểm process và dữ liệu mới','Chỉ báo thay đổi có ý nghĩa'])
DATES=chain('18_lich',['LỊCH EPIC','LỊCH TASK','LỊCH SUBTASK'],['Task nằm trong lịch Epic','Subtask nằm trong lịch Task'])
SCHEME=rows_diagram('19_scheme',[('Epic','QAG3 Epic Lifecycle v1','Scheme chọn theo loại việc'),('Task','QAG3 Task Delivery v1','Scheme chọn theo loại việc'),('Sub-task','QAG3 Individual Work v1','Scheme chọn theo loại việc')])
for kind in coverage:
    wf=DATA['workflows'][kind]['workflow']['workflows'][0]
    expected={(t['id'],l.get('fromStatusReference'),t['toStatusReference']) for t in wf['transitions'] for l in (t['links'] or [{}])}
    assert coverage[kind]==expected, (kind,expected-coverage[kind],coverage[kind]-expected)
(ASSETS/'diagram-checks.json').write_text(json.dumps({'source':'handbook-source-2026-10-13.json','checkedNativeEdges':{k:len(v) for k,v in coverage.items()},'allNativeRoutesCovered':True,'figures':figures},ensure_ascii=False,indent=2),encoding='utf-8')

doc=Document(); sec=doc.sections[0]
sec.page_width=Inches(8.5); sec.page_height=Inches(11)
sec.top_margin=sec.bottom_margin=Inches(.65)
sec.left_margin=sec.right_margin=Inches(.75)
for name,size in [('Normal',12),('Title',27),('Subtitle',14),('Heading 1',20),('Heading 2',15),('Caption',10)]:
    s=doc.styles[name]; s.font.name='Arial'; s.font.size=Pt(size); s.font.color.rgb=RGBColor(0,0,0)
    s.paragraph_format.space_after=Pt(8)
    if name.startswith('Heading'):s.paragraph_format.keep_with_next=True
doc.styles['Normal'].paragraph_format.line_spacing=1.12
for parent in (doc.styles.element,doc.element):
    for b in list(parent.iter(qn('w:pBdr'))):b.getparent().remove(b)
footer=sec.footer.paragraphs[0]; footer.alignment=1
footer.add_run('Học Jira QAG3  |  ').font.size=Pt(9)
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE')
r=OxmlElement('w:r');t=OxmlElement('w:t');t.text='1';r.append(t);field.append(r);footer._p.append(field)
page=0
step_index=0

def p(text,style=None):
    after_table=len(doc.element.body)>1 and doc.element.body[-2].tag==qn('w:tbl')
    paragraph=doc.add_paragraph(text,style)
    if after_table:paragraph.paragraph_format.space_before=Pt(8)
    return paragraph
def h(text):return doc.add_heading(text,2)
def bullet(text):return p(text,'List Bullet')
def step(text):
    global step_index
    step_index+=1
    paragraph=p(f'{step_index}. {text}')
    paragraph.paragraph_format.left_indent=Inches(.22)
    paragraph.paragraph_format.first_line_indent=Inches(-.22)
    return paragraph
def lesson(title,idea):
    global page, step_index
    if page:doc.add_page_break()
    page+=1
    step_index=0
    doc.add_heading(title,1)
    p(idea)
def picture(path,caption,max_height=3.8):
    im=Image.open(path); w,h=im.size
    width=min(7.0,max_height*w/h)
    para=p('');para.alignment=1
    run=para.add_run();shape=run.add_picture(str(path),width=Inches(width))
    shape._inline.docPr.set('descr',caption)
    para.paragraph_format.keep_with_next=True
    p(caption.replace('  ',' '),'Caption')
def smalltable(headers,rows,widths):
    table=doc.add_table(rows=1,cols=len(headers));table.autofit=False
    for c,w in zip(table.columns,widths):c.width=Inches(w)
    for c,text in zip(table.rows[0].cells,headers):c.text=text
    for row in rows:
        for c,text in zip(table.add_row().cells,row):c.text=str(text)
    for i,row in enumerate(table.rows):
        trpr=row._tr.get_or_add_trPr();trpr.append(OxmlElement('w:cantSplit'))
        if i==0:trpr.append(OxmlElement('w:tblHeader'))
        for c,w in zip(row.cells,widths):
            c.width=Inches(w);pr=c._tc.get_or_add_tcPr()
            borders=OxmlElement('w:tcBorders')
            for edge in ('top','left','bottom','right'):
                b=OxmlElement('w:'+edge);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'D9D9D9');borders.append(b)
            pr.append(borders)
            sh=OxmlElement('w:shd');sh.set(qn('w:val'),'clear');sh.set(qn('w:fill'),'DCE6F1' if i==0 else 'FFFFFF');pr.append(sh)
            mar=OxmlElement('w:tcMar')
            for edge in ('top','left','bottom','right'):
                m=OxmlElement('w:'+edge);m.set(qn('w:w'),'100');m.set(qn('w:type'),'dxa');mar.append(m)
            pr.append(mar)
            for pp in c.paragraphs:
                pp.paragraph_format.space_after=Pt(4)
                for rr in pp.runs:rr.font.size=Pt(10.5);rr.bold=i==0
    return table

p('Học cách dùng Jira QAG3 bằng hình','Title')
p('Từ chưa biết gì đến tự quản lý công việc','Subtitle')
p('Ngày 13 tháng 10 năm 2026 | Bản hướng dẫn dành cho người mới')
p('Bạn không cần biết lập trình để đọc tài liệu này. Hãy tưởng tượng cả nhóm đang làm một bài tập chung. Jira là cuốn sổ để ghi việc nào cần làm, ai làm và việc đang đến đâu.')
picture(HIER,'Hình 1  Việc lớn được chia thành việc nhỏ và phần việc của từng người',3.2)
p('Ta sẽ học từng bước: hiểu công việc, đi theo mũi tên, chuẩn bị thứ cần kiểm tra, rồi mới bấm nút trên Jira. Tên tiếng Anh trong hình được giữ đúng để bạn tìm thấy trên màn hình.')
p('Đây là dự án học tập mô phỏng. Bot giám sát đang tạm dừng. Các automation A01–A05 vẫn bật. Báo cáo mô tả cấu hình QAG3 đã đối soát ngày 13/10/2026, không tự thay đổi Jira.')
page=1

lesson('1 Cách đọc những hình trong sách','Một mũi tên có nghĩa là có thể đi từ ô này sang ô kia bằng đúng nút ghi trên đường đi. Có đường đi không có nghĩa lúc nào cũng được đi: cửa kiểm tra có thể chưa cho qua.')
bullet('Ô màu xanh: một chỗ công việc đang đứng, gọi là trạng thái.')
bullet('Ô Done màu xanh lá: trạng thái hoàn tất. Trong dự án này, dữ liệu hoàn tất là mô phỏng học tập.')
bullet('Mũi tên xanh: đi tiếp. Mũi tên đỏ: quay lại sửa, mở lại hoặc hủy.')
bullet('Số trước tên nút, như 15 Reopen, là mã của nút chuyển. Không phải số ngày hoặc điểm.')
bullet('Hình nhiều hàng: đọc từng hàng riêng, từ trái sang phải. Không nối cuối hàng này với đầu hàng khác.')
h('Bạn nên học theo thứ tự nào')
step('Bài 2–4: hiểu việc lớn, việc nhỏ, người làm và các ô trên màn hình.')
step('Bài 5–11: học ba workflow và tất cả đường đi, kể cả quay lại sửa.')
step('Bài 12–14: hiểu checklist và bằng chứng để qua cửa kiểm tra.')
step('Bài 15–19: hiểu việc nào Jira tự làm và bot làm gì.')
step('Bài 20–25: thực hành, sửa lỗi và tự cập nhật hệ thống.')
p('Workflow nghĩa là đường đi của công việc. Condition là điều kiện để thấy/dùng đường. Validator là người gác cửa kiểm tra trước khi chuyển. Action là việc Jira làm khi chuyển thành công, như đặt hoặc xóa Resolution.')

lesson('2 Việc lớn việc nhỏ và phần việc của tôi','Ví dụ dễ nhớ: nhóm muốn làm một chức năng đăng nhập. Không giao cả chức năng cho một người rồi coi mọi người khác không có việc.')
picture(HIER,'Hình 2  Cây công việc là quan hệ cha con không phải đường chuyển trạng thái',3.0)
bullet('Epic = việc lớn, ví dụ Tài khoản và Role. Trong Epic có nhiều Task.')
bullet('Task = một chức năng, ví dụ Đăng nhập. Task thuộc một Epic.')
bullet('Subtask = phần việc của một người, ví dụ viết backend hoặc kiểm thử. Subtask thuộc một Task.')
p('QAG3 có 11 Epic, 53 Task và 265 Subtask WBS. Mỗi Task WBS chia năm phần việc. Những issue thử riêng không tính vào WBS. Một Subtask Done không khiến cả Task và Epic tự Done.')
p('Parent là cha. Khi thêm Task, Parent là Epic. Khi thêm Subtask, Parent là Task. Chọn sai cha giống đặt bài tập vào nhầm tập vở.')

lesson('3 Năm người làm những phần nào','Vai trò là phần việc đã phân công. Quyền truy cập là việc tài khoản được phép làm trên Jira. Hai thứ này khác nhau.')
smalltable(['Người','Công việc dễ hiểu','Tên vai trò'],[['Hiệp','Hỏi cần làm gì và điều phối','BA và PM'],['Đức','Làm phần xử lý phía sau','BE'],['Duy','Làm phần người dùng nhìn và bấm','FE'],['Hưng','Thử để tìm lỗi và retest','QA hoặc Tester'],['Khai','Điều phối và nghiệm thu','PM']],[1.1,4.4,1.5])
h('Ai bấm nút ai được giao việc')
p('Assignee là người đang được giao việc. Actor là người bấm nút hoặc tài khoản chạy automation. Bạn có thể nhìn thấy hai tên khác nhau. Nhánh Subtask BE/FE xét assignee; nhiều cửa QA và PM xét actor.')
p('Hai PM được cấu hình bằng accountId của Hiệp và Khai. QA thật là tài khoản Hưng. Chỉ đổi tên hiển thị thành PM hoặc Tester không làm tài khoản được nhận diện đúng.')
h('Vì sao admin vẫn có thể bị chặn')
p('Admin có thể sửa cấu hình nếu đủ quyền. Nhưng khi bấm chuyển việc, validator vẫn kiểm tra. Trong mô phỏng, Hiệp có ngoại lệ ghi SIMULATED PASS hoặc SIMULATED ACCEPTED theo đúng điều kiện. Đó không phải chữ ký QA thật của Hưng.')
p('Lời mời thành viên và quyền Jira cần kiểm tra riêng. Thêm người mới còn phải cập nhật allowlist và nhánh Subtask; hệ thống không tự học tài khoản mới từ email.')

lesson('4 Jira workflow automation và bot khác nhau','Hãy nhìn hệ thống như một cuốn sổ, một bộ đường đi, vài người trợ giúp và một người đọc sổ để báo cáo.')
picture(SYSTEM,'Hình 3  Cách hiểu các thành phần không phải pipeline bắt buộc cho mọi thao tác',3.0)
bullet('Jira giữ công việc, ngày, người làm, bình luận và lịch sử.')
bullet('Workflow quyết định từ trạng thái này có thể đi đến trạng thái nào.')
bullet('Automation A01–A05 nghe sự kiện phù hợp rồi hỗ trợ Epic hoặc nhắc PM.')
bullet('Bot đọc Jira và viết báo cáo riêng. Bot không tự làm code, nghiệm thu hoặc chấm người bằng dữ liệu giả.')
p('MCP là cách AI gọi thao tác được Jira hỗ trợ, giống nhờ người chuyển lời đúng quy định. MCP chính thức quản lý issue; local qag3-admin bổ sung thao tác cấu hình QAG3 có preview. Browser là cách thao tác màn hình khi cần, không phải MCP.')
p('Bot đang tạm dừng không có nghĩa Jira tắt. Workflow và A01–A05 vẫn chạy trong Jira Cloud.')

lesson('5 Epic đi từ ý tưởng đến nghiệm thu','Epic là chiếc cặp chứa nhiều việc. PM kiểm tra phạm vi trước; nhóm làm các Task; cuối cùng PM mới nghiệm thu Epic.')
picture(EPIC_MAIN,'Hình 4  Đường chính của Epic đầy đủ các nút Create Approve scope Start delivery Submit acceptance Accept Epic',3.7)
bullet('NEW: mới ghi ý tưởng. READY: PM đã duyệt phạm vi. In Progress: đang làm.')
bullet('REVIEW: chờ xem xét nghiệm thu. Done: đã đi qua Accept Epic.')
bullet('Approve scope cần PM, owner active, mô tả và bằng chứng phạm vi mới khớp mọi Task con.')
bullet('Submit acceptance cần ít nhất một Task; mọi Task và Subtask con đều Done.')
bullet('Accept Epic cần thêm PM, checklist và bằng chứng tích hợp/bàn giao mới. A02 chỉ giúp đến REVIEW, không thay nút này.')
p('Start delivery hiện không có validator bổ sung riêng. Điều kiện nghiệp vụ mong muốn và điều kiện đã gắn thật không được đánh đồng.')

lesson('6 Epic quay lại sửa mở lại hủy và khôi phục','Có lúc nhóm đổi ý hoặc phát hiện cần làm lại. Chọn đúng đường, không kéo công việc đến trạng thái bất kỳ.')
picture(EPIC_BACK,'Hình 5  Bốn đường quay lại của Epic đọc riêng từng hàng',2.5)
picture(EPIC_CANCEL,'Hình 6  Cancel Epic cho phép hủy từ bốn trạng thái này',2.5)
p('Return và Reopen cần Change reason mới. Restore cần PM, reason mới và xóa Resolution. Cancel cần PM và reason mới. Reanalyse chưa có validator bổ sung riêng.')
p('Cấu hình thật: Return/Reopen chưa có PM-only riêng; Cancel chưa có action đặt Resolution. Đây là điểm cần cân nhắc khi cập nhật, không được coi là đã khóa đủ mọi nhánh.')

lesson('7 Task hiểu yêu cầu rồi làm code','Task là một chức năng. Đi từng bước giúp nhóm biết đang hỏi yêu cầu, đang làm hay đang kiểm tra.')
picture(TASK_A,'Hình 7  Nửa đầu Task từ Create đến Submit code',3.7)
bullet('IN ANALYSIS: làm rõ cần gì. READY FOR DEV: đã đủ để bắt đầu. In Progress: đang làm.')
bullet('CODE REVIEW: đang xem lại code. Người làm chưa tự coi chức năng đã xong.')
p('Ví dụ Đăng nhập: trước hết biết đăng nhập bằng gì và lỗi nào cần báo. Sau đó mới làm code và gửi xem lại. BA, BE, FE, QA, PM có Subtask riêng bên dưới.')
p('Các transition sớm ở hình này chưa có actor validator bổ sung. Phân công BA/Dev là cách tổ chức công việc; không khẳng định mọi nút đều đã khóa theo vai trò.')
h('Việc cần làm trên Jira')
step('Mở Task, kiểm Parent và assignee. Đọc mô tả và các Subtask.')
step('Bấm tên trạng thái, chọn đúng transition đang có. Không chọn trạng thái không xuất hiện.')
step('Khi đã làm code, dùng Submit code để đến CODE REVIEW.')

lesson('8 Task kiểm thử rồi bàn giao','CODE REVIEW là điểm tiếp nối từ bài trước. Sau kiểm thử vẫn còn bước PM duyệt và bàn giao.')
picture(TASK_B,'Hình 8  Nửa sau Task từ Approve code đến Deploy',3.7)
bullet('READY FOR TEST: sẵn sàng thử. IN TESTING: đang thử. REVIEW: đã gửi kết quả thử để xem xét.')
bullet('READY FOR RELEASE: PM đã Approve nhưng chưa Done. Deploy mới đưa Task Done.')
bullet('Pass testing cần QA thật hoặc ngoại lệ mô phỏng đúng điều kiện, bằng chứng mới và checkbox retest khớp.')
bullet('Approve cần PM và QA còn hiệu lực. Deploy cần thêm mọi Subtask Done và checklist bàn giao đầy đủ.')
p('Deploy ở đây là tên nút quản lý công việc. Nút không tự triển khai code lên máy chủ. Dữ liệu hiện tại là mô phỏng học tập.')
p('Approve/Deploy hiện không có screen nhập thêm riêng. Chuẩn bị field/checklist trước, nhưng chữ ký QA phải được tạo đúng lúc Pass testing.')

lesson('9 Task sai thì quay lại bằng đường nào','Đọc mỗi hàng như một câu: đang ở ô bên trái, bấm nút giữa, sang ô bên phải. Không có đường Task nào trong hình này quay về NEW.')
picture(TASK_BACK,'Hình 9  Toàn bộ sáu đường sửa lại retest và mở lại Task',4.2)
bullet('Code rejected, Bug found, ReDev đưa về In Progress để sửa.')
bullet('Retest đưa REVIEW về IN TESTING. Retest before release đưa READY FOR RELEASE về IN TESTING và chỉ PM được bấm.')
bullet('Reopen từ Done cần PM và reason mới; xóa Resolution rồi về In Progress.')
p('Nếu sửa nội dung sau QA, kết quả QA cũ có thể hết hiệu lực. Cách đúng là sửa xong, kiểm thử lại và ký evidence mới; không chỉ đổi chữ PASS trong field.')

lesson('10 Subtask của BA Tester và PM','Những phần việc này không phải viết code. Vì vậy chúng có một đường ngắn hơn.')
picture(SUB_BUS,'Hình 10  Nhánh Subtask nghiệp vụ cho assignee BA Tester PM',3.2)
bullet('Start work: bắt đầu phần việc. Submit work: gửi phần việc để xem lại.')
bullet('Approve work: nghiệm thu phần việc. Cần đồng thời ba cửa acceptance, freshness và history.')
p('Ví dụ Subtask Đặc tả đăng nhập: BA viết nội dung và điều kiện đạt; gửi review; PM kiểm tra rồi duyệt. Evidence mới phải cho biết đã xem cái gì và kết luận ra sao.')
p('Ngoài ngoại lệ mô phỏng của owner, PM không được tự nghiệm thu phần việc đang hoặc từng được giao cho chính mình. Đổi assignee hôm nay không xóa lịch sử hôm qua.')
p('Nếu Subtask từng là việc Dev hoặc từng qua trạng thái Dev, history gate vẫn có thể yêu cầu QA. Đổi người được giao sang BA không tự bỏ QA.')

lesson('11 Subtask của BE FE và các đường sửa lại','BE và FE phải đi qua code review và kiểm thử. Nhánh được chọn theo assignee, không phải tên người đang bấm.')
picture(SUB_DEV,'Hình 11  Nhánh Dev của Subtask dùng cùng Approve work với nhánh nghiệp vụ',3.4)
picture(SUB_BACK,'Hình 12  Năm đường quay lại của Subtask tất cả được vẽ riêng',2.5)
p('Các nút code/test 7–13 có condition assignee BE/FE. Approve work giữ ba validator cùng lúc. Reopen cần reason mới và xóa Resolution, nhưng chưa có PM-only riêng. Rework hiện không có reason validator bổ sung.')
p('Hình 10–12 ghép lại bao phủ mọi transition Subtask hiện hành. Các nút chung Create, Start work, Approve work xuất hiện lại vì cả hai nhánh đều dùng chúng.')

lesson('12 Cửa kiểm tra vì sao bấm mà không đi','Hãy coi validator như người kiểm tra bài trước khi nộp. Chỉ cần thiếu một thứ bắt buộc, công việc phải đứng nguyên ở chỗ cũ.')
picture(QA_FLOW,'Hình 13  Không đạt thì giữ trạng thái đạt mọi điều kiện mới chuyển tiếp',3.2)
h('Bốn điều cần tự hỏi trước khi bấm')
step('Tôi đang dùng đúng tài khoản được cho phép chưa?')
step('Những việc con cần xong đã Done hết chưa?')
step('Checklist đã đầy đủ và không mâu thuẫn chưa?')
step('Bằng chứng có mới và được ký đúng thời điểm chưa?')
p('QA còn hiệu lực nghĩa là kết quả thử vẫn ứng với công việc hiện tại. Nếu sửa yêu cầu, Parent, assignee hoặc evidence sau QA, cửa có thể yêu cầu thử lại.')
p('Ba cửa Subtask Approve work là một bộ. Tách logic ra nhiều validator giúp giảm chi phí mỗi expression; không có nghĩa được xóa một cửa để đi nhanh.')

lesson('13 Checklist bằng chứng và lý do thay đổi','Checklist là danh sách thứ cần xác nhận. Evidence là thứ giúp người khác xem lại vì sao xác nhận. Change reason nói vì sao mở lại hoặc hủy.')
h('Tám ô checklist hiện có')
for text in ['AC verified: đã đối chiếu yêu cầu đạt.','Lead review completed: đã review kỹ thuật theo nghiệp vụ.','QA passed: có kết quả QA đạt.','Retest passed: đã thử lại và đạt.','Retest not required: không cần thử lại, có lý do.','BA accepted: BA chấp nhận.','PM approved: PM duyệt.','Test deployment smoke passed: kiểm tra nhanh môi trường Test đạt.']:bullet(text)
p('Retest passed và Retest not required là hai lựa chọn thay nhau. Chọn đúng một. Chọn cả hai giống vừa nói đã thử lại vừa nói không cần thử lại.')
p('Task Deploy cần AC, Lead, QA, BA, PM, smoke và một retest. Epic Accept cần AC, QA, BA, PM, smoke và một retest; không bắt option Lead riêng ở gate đó.')
p('Tick checkbox không tự chứng minh đúng người đã kiểm tra. QA gate còn xem actor và changelog. Change reason phải khác giá trị cũ; evidence mới không được chỉ sao chép chữ ký cũ.')

lesson('14 Viết bằng chứng sao cho dùng được','Bằng chứng tốt giống bài làm có tên bài, phiên bản, chỗ đã thử, kết quả và thứ để người khác xem lại. Đừng chỉ ghi xong rồi.')
h('QA cần bảy nhãn đúng tên')
for text in ['Revision: phiên bản đang thử.','Environment: bắt đầu bằng Test - rồi ghi môi trường.','Test scope: đã thử phần nào.','Result: PASS của Hưng hoặc SIMULATED PASS của Hiệp trong mô phỏng hợp lệ.','Evidence: đường dẫn hoặc mô tả chứng cứ cụ thể.','Retest: kết quả thử lại hoặc không cần thử lại.','Bug references / retest rationale: lỗi liên quan hoặc lý do không cần retest.']:bullet(text)
p('Mỗi nhãn xuất hiện đúng một lần và có nội dung. Ghi evidence mới ngay tại Pass testing. Nhãn qag3-simulation phải có từ trước nếu dùng ngoại lệ mô phỏng; không giả nói tài khoản Hưng đã ký.')
h('BA Tester PM gửi review nghiệp vụ')
p('Dùng Revision, Review scope, Review result, Evidence. Kết quả ACCEPTED; ngoại lệ owner mô phỏng dùng SIMULATED ACCEPTED. Bằng chứng phải mới tại nghiệm thu.')
h('Epic có bằng chứng riêng')
p('Approve scope: Scope version, Scope tasks, Acceptance criteria, Scope result APPROVED, Evidence. Accept Epic: Scope version, Scope tasks, Integration result PASS, Handover result COMPLETE, Evidence, Retest, Bug references / retest rationale. Scope tasks phải khớp chính xác mọi Task con.')
p('Giới hạn nhập liệu 2.21: parser đã kiểm thử với dấu phân cách gồm backslash và chữ n trong text. Xuống dòng ADF thông thường có thể lỗi. Dùng adapter đã kiểm thử, đọc lại trước duyệt; không bỏ gate để chữa lỗi nhập liệu.')

lesson('15 A01 A02 giúp Epic theo dõi Task','Hai trợ giúp này giúp cặp việc lớn biết các việc nhỏ đang làm đến đâu. Chúng không thay PM nghiệm thu.')
picture(A12,'Hình 14  A01 bắt đầu Epic A02 đưa chờ nghiệm thu PM mới đưa Done',3.0)
bullet('A01 nghe Task vào IN ANALYSIS, READY FOR DEV, In Progress, CODE REVIEW, READY FOR TEST, IN TESTING, REVIEW hoặc READY FOR RELEASE và có Parent.')
bullet('A01 đọc lại cha; cha phải là Epic QAG3 đang READY. Cha NEW giữ NEW, phải duyệt scope trước.')
bullet('A02 chỉ nghe event chuyển đến Done của Task có Parent. Cha In Progress, có Task và mọi Task Done thì chuyển REVIEW.')
p('Actor của cả hai là Automation for Jira. Rule chỉ xử lý sự kiện mới hợp lệ; không tự sửa mọi issue Done cũ ngay khi bật.')
p('Ví dụ: Task cuối cùng của Đăng nhập Done, Epic có thể lên REVIEW. Muốn Epic Done, PM vẫn phải kiểm tra đầy đủ rồi Accept Epic.')

lesson('16 A03 mở lại Epic khi thêm việc được duyệt','Epic đã review hoặc Done mà có thêm phần việc chưa Done thì phải xem xét lại. A03 giúp phản ánh việc đó.')
picture(A3,'Hình 15  A03 không tự khôi phục Epic đã hủy',3.0)
bullet('Task được tạo hoặc chuyển trạng thái; Task chưa Done, có Parent, có qag3-scope-approved.')
bullet('Cha REVIEW hoặc Done về In Progress, kèm Change reason mới.')
bullet('Cha CANCELLED không được A03 tự restore.')
p('Actor là User who triggered, tức người gây ra sự kiện. Rule vẫn chịu quyền và gate của người đó. Nhãn qag3-scope-approved cho biết phạm vi được nghiệp vụ cho phép xử lý, không cấp thêm quyền truy cập.')
p('Nếu không có nhãn, A03 có thể không làm gì. Đừng kết luận Jira hỏng chỉ vì thấy No actions performed. Hãy kiểm Task, Parent, status, label và audit.')

lesson('17 A04 khi chuyển Task sang Epic khác','Chuyển một Task giống chuyển một cuốn vở từ cặp cũ sang cặp mới. Phải xem cả hai cặp, không chỉ cặp mới.')
picture(A4,'Hình 16  Các trường hợp A04 sau Parent change đọc từng hàng như một điều kiện riêng',3.6)
bullet('Trigger là Parent thay đổi trên Task QAG3 có nhãn qag3-scope-approved.')
bullet('Rule lấy ID cha cũ/mới, đọc lại; chỉ xử lý Epic thuộc QAG3.')
bullet('Actor là người gây sự kiện. Không tự Cancel, Restore hoặc Accept Epic Done.')
p('Cha cũ Done được giữ Done khi chỉ lấy Task ra. Cha REVIEW có thể về In Progress nếu rỗng hoặc còn Task chưa Done. Epic In Progress đủ Task và tất cả Done có thể lên REVIEW.')
p('Các nhánh được xét khi rule chạy, không phải một giao dịch khóa mọi thay đổi cùng lúc. Nếu nhiều người sửa Parent đồng thời, phải đọc audit và trạng thái cuối của cả hai Epic.')

lesson('18 A05 nhắc PM xem việc','A05 giống lời nhắc thầy cô xem bài. Nó không chấm bài, không ký QA và không nghiệm thu thay người.')
picture(A5,'Hình 17  Nhắc đúng lần review bằng comment và mention PM',3.0)
bullet('Task vào CODE REVIEW, REVIEW, READY FOR RELEASE; hoặc Subtask vào CODE REVIEW, REVIEW.')
bullet('Rule chốt lần nhắc theo issue/status/updated, đọc lại rồi kiểm marker.')
bullet('Chưa có marker: ghi đã thử gửi, rồi comment. Assignee Khai thì @Hiệp; trường hợp khác thì @Khai.')
p('Actor là Automation for Jira. Hai action comment, không email. Comment được người có quyền xem issue nhìn thấy. addCommentOnce=false cho phép nhắc lại ở lần review mới.')
p('Marker chỉ nói đã thử. Nếu ghi marker rồi gửi comment lỗi, không coi đã gửi thành công. Trước gửi lại hãy xem Audit log và comment thật. Chưa bảo đảm đúng một lần trong mọi tình huống đồng thời.')

lesson('19 Bot giám sát đang nghỉ nhưng Jira vẫn làm việc','Bot chỉ đọc sổ để làm báo cáo. Tạm dừng bot không tạm dừng nhóm hay automation trong Jira.')
picture(BOT,'Hình 18  Đường dữ liệu giám sát hiện đang tạm dừng',3.2)
bullet('Runner local đọc đủ Jira mỗi giờ, lưu state và event chu kỳ. Không tự sửa Jira.')
bullet('Heartbeat trong chat kiểm quota, process thật, run/cycle và dữ liệu mới rồi mới nhận định.')
bullet('Lỗi đọc hoặc dữ liệu cũ: UNKNOWN, giữ báo cáo thành công trước. Không báo tiến độ bằng 0 chỉ vì đọc lỗi.')
p('Ngày 13/10: heartbeat PAUSED, Windows task Disabled, không còn runner/wrapper. State và report giữ nguyên. Lịch continuation khác chưa bị thay trong lần pause này.')
p('Gemini hiện DISABLED_CONFIG; chưa gọi AI Gemini live trong luồng này. Muốn dùng cần key mới, xác nhận Free Tier không billing và chỉ gửi số tổng hợp, không dữ liệu cá nhân.')
p('Máy cần chạy, OAuth cần hợp lệ. Chưa bảo đảm bot hoạt động 24/7 qua logoff, sleep hoặc reboot. Muốn bật lại cần bật task và heartbeat, kiểm không có process trùng và đợi chu kỳ thành công.')

lesson('20 Làm một chức năng từ đầu đến cuối','Bài tập này giúp bạn biết việc tiếp theo phải tìm ở đâu. Đây là bài thực hành mô phỏng, không xác nhận phần mềm thật đã chạy.')
step('Chọn Epic NEW. Kiểm owner, mô tả và các Task con. PM chuẩn bị scope rồi Approve scope để đến READY.')
step('Mở một Task. Kiểm Parent, assignee, Start date, Due date. Start analysis rồi Analysis done, Start dev.')
step('Mở năm Subtask. BA/Tester/PM theo nhánh nghiệp vụ; BE/FE theo nhánh code. Mỗi người cập nhật phần việc riêng.')
step('BE/FE qua code review và testing. Khi có lỗi thì sửa, thử lại, ký bằng chứng mới. PM độc lập hoặc ngoại lệ owner mô phỏng duyệt theo gate.')
step('Khi mọi Subtask Done, Task vẫn phải qua Pass testing, PM Approve, Deploy. Chuẩn bị đủ checklist và evidence.')
step('Task cuối Done: xem A02 có đưa Epic REVIEW chưa. PM kiểm phạm vi, tích hợp, bàn giao rồi Accept Epic.')
step('Mở History và Automation Audit log. Xác minh trạng thái, Resolution, comment; không chỉ nhìn thanh màu.')
h('Một nguyên tắc nên nhớ')
p('Đừng bấm Done chỉ để thanh màu xanh đẹp. Với mô phỏng, ghi đúng kết quả giả định và phân biệt chữ ký thật với ngoại lệ mô phỏng. Với công việc thật, phải có bằng chứng tương ứng.')

lesson('21 Ngày bắt đầu ngày hết hạn Sprint và worklog','Ngày trên Timeline là lịch dự định. Nó không phải đồng hồ chứng minh ai đã làm bao lâu.')
picture(DATES,'Hình 19  Lịch con nằm trong lịch cha không phải workflow chuyển trạng thái',2.4)
bullet('Start date: dự định bắt đầu. Due date: dự định kết thúc. Lịch WBS hiện đã điền cho 329 mục, từ 03/04 đến 31/12/2026.')
bullet('Task nằm trong lịch Epic; Subtask nằm trong lịch Task. Đổi ngày cha phải đọc lại ngày con, không cho rằng tự đổi tất cả.')
bullet('Timeline board 3: mở Epic rồi Task, chọn khoảng xem đủ rộng, dùng Work item start/end dates thay Align to Sprint khi xem ngày từng mục.')
p('Sprint là một đợt làm có mục tiêu và khoảng thời gian riêng. Backlog là kho việc chưa chọn vào đợt. Không khẳng định Sprint/capacity/release đã thiết lập đủ chỉ từ việc có Start/Due.')
p('Worklog ghi thời lượng và author. Các bản hiện có là mô phỏng do admin ghi: 265 bản, 384 giờ đã đối soát ở lượt trước. Không gán đó thành thời gian thật mỗi thành viên. Story point là ước lượng độ lớn, không phải giờ.')

lesson('22 Nhìn báo cáo mà không hiểu nhầm','Báo cáo tốt giúp bạn biết cần xem chỗ nào. Nó không nên biến số liệu giả thành lời khen hay chê người thật.')
smalltable(['Loại việc WBS','Done','Đang làm','NEW','Tổng'],[['Epic',7,1,3,11],['Task',39,0,14,53],['Subtask',195,0,70,265]],[2.2,1.1,1.3,1.1,1.3])
p('Snapshot 13/10 lúc 11:36 +07: mỗi vai trò có 39/53 Subtask Done, khoảng 73,58%. Đây là tỷ lệ phần việc mô phỏng, không phải điểm giỏi/kém. Không cộng 39 Task với 195 Subtask thành 234 chức năng hoàn thành.')
p('Ba Epic NEW là QAG3-243 Comment, QAG3-274 Dashboard, QAG3-299 Notification. Toàn bộ 14 Task và 70 Subtask dưới chúng đã NEW, Resolution rỗng. Epic QAG3-212 còn In Progress dù Task con Done, nên PM cần xem xét.')
p('Completion chức năng dùng Task/Story Done-category không CANCELLED/CANCELED, chia tổng Task/Story trong scope. Việc hủy vẫn ở mẫu số. Không có phạm vi thì tỷ lệ để null, không ghi 100%.')
p('Bot tách năm chiều: giao việc đúng hẹn, chất lượng, phối hợp, trách nhiệm, đóng góp. Hiện thiếu bằng chứng nên overallScore=null. Assignee, checkbox và worklog giả không chứng minh ai làm thật.')

lesson('23 Khi bị chặn hãy tìm lỗi theo cách này','Giữ nguyên issue. Đọc thông báo lỗi. Kiểm từng thứ nhỏ trước khi sửa cấu hình lớn.')
h('Không thấy nút chuyển')
p('Kiểm trạng thái hiện tại, assignee và nhánh BE/FE hoặc BA/Tester/PM. Condition có thể giấu nút. Kiểm quyền tài khoản; không đoán transition ID.')
h('Thiếu lý do hoặc QA hết hiệu lực')
p('Reason phải mới, không rỗng. QA phải được ký đúng tại Pass testing. Sửa việc sau QA thì dùng Retest và evidence mới. Chỉ sửa chữ PASS trong field không chữa được chữ ký thiếu.')
h('Automation không làm gì')
p('Mở Project settings → Automation → rule → Audit log. Kiểm trigger, project, Parent, status, label. A03/A04 cần qag3-scope-approved; A01 không đưa Epic NEW sang In Progress; A02 không tự Done Epic.')
h('Không thấy thanh Timeline hoặc đọc lỗi')
p('Kiểm ngày từng issue, khoảng xem và việc đã mở rộng hàng chưa. Bot thiếu dữ liệu hoặc Jira 429 thì giữ last success, báo UNKNOWN. Không chạy collector trùng, đổi sang cookie browser hoặc trả phí để né giới hạn.')
h('Bài tự kiểm tra')
p('Một Subtask Done nhưng Task chưa Done có sai không? Không. Epic REVIEW có phải xong không? Chưa. Bot PAUSED có tắt A05 không? Không. Tick QA passed có bằng chữ ký QA không? Không.')

lesson('24 Tự đổi hệ thống mà không làm mất việc','Workflow là đường đi. Scheme là người chọn đường đúng theo loại công việc. QAG3 đã gắn scheme mới, không còn chờ migration trong cấu hình đã đối soát.')
picture(SCHEME,'Hình 20  Scheme 10004 chọn ba workflow theo loại issue',2.6)
step('Muốn đổi ngày/người: sửa trên issue, đọc lại Parent, ngày con và assignee routing.')
step('Muốn đổi đường: Project settings → Workflows → Edit workflow. Lưu bản trước, sửa nhỏ, preview, publish/update theo trạng thái Jira hiện hành rồi đọc lại.')
step('Muốn đổi gate: sửa manifest Forge và rule tương ứng. Lint/type-check chưa đủ; phải thử transition thật với ca đạt và ca bị chặn.')
step('Muốn đổi A01–A05: export trước, sửa trigger/condition/actor/action, save, kiểm Audit log. Không bật rule chaining chỉ để bỏ qua lỗi.')
step('Muốn thêm người: resolve accountId, quyền/assignability; cập nhật allowlist, condition Subtask, A05 routing và team mapping; kiểm thử lại.')
p('Migration chỉ dùng khi đổi association hoặc mapping trạng thái. Lưu before, xem từng trạng thái cũ sang mới và kiểm số issue. Không dùng bản workflow cũ ghi đè bản active v9/v10/v11.')
p('Rollback nghĩa là quay về cấu hình trước đã lưu, không xóa issue/history. Đừng gỡ một gate của bộ AND hoặc uninstall Forge đang gắn rule.')

lesson('25 Các cửa hiện có và phần cần nhớ khi cập nhật','Phần này để tra cứu sau khi đã hiểu đường đi. Cửa nào chưa gắn thì không được nói là hệ thống đã bảo vệ đầy đủ.')
for text in [
    'PM only: nhận đúng hai PM active, không nhìn tên hiển thị.',
    'Epic children Done: có Task và mọi Task/Subtask con Done.',
    'Fresh change reason: lý do khác giá trị đã lưu trước.',
    'Task Subtasks Done: mọi Subtask Done; phép every có thể đúng với danh sách rỗng.',
    'Task delivery checklist: đủ option, đúng một retest, evidence có nội dung.',
    'QA attest: đúng actor, đang testing, evidence mới tại Pass testing.',
    'QA current: chữ ký đúng cùng entry, evidence chưa bị thay.',
    'Subtask acceptance: nghiệm thu phần việc bằng review hoặc QA hợp lệ.',
    'Epic readiness: owner/mô tả/scope mới và danh sách Task chính xác.',
    'Epic acceptance: scope đúng, Task Done, tích hợp/bàn giao và checklist.',
    'QA freshness: đối chiếu sửa đổi liên quan sau lần thử.',
    'Subtask history: nhớ giao việc và trạng thái cũ, kiểm độc lập và QA provenance.'
]:bullet(text)
p('Các giới hạn còn lại: Epic Cancel chưa có Resolution action; Return/Reopen Epic và Reopen Subtask chưa có PM-only riêng; vài nhánh sớm chưa khóa actor. Chưa kiểm thử toàn bộ T01–T23, mọi tài khoản ngoài PM, đồng thời nhiều Task, linked Bug/Lead/BA hoặc history cực dài.')
p('Forge hiện development 2.21; chưa xác minh production promotion. Billing live cuối chưa đối soát, không cam kết Free hoặc 0 phí bất biến. Lint PASS không chứng minh dependency sạch mọi lỗi bảo mật.')

lesson('26 Từ điển nhỏ và nơi tra cứu','Khi quên một từ, quay lại đây. Tên trong Jira vẫn giữ nguyên để bạn tìm đúng ô và đúng nút.')
smalltable(['Tên trên Jira','Hiểu đơn giản'],[['Issue / work item','Một mục công việc có mã QAG3-...'],['Status','Công việc đang đứng ở đâu'],['Transition','Nút để đi sang trạng thái khác'],['Resolution','Kết quả đóng việc; mở lại thường phải xóa'],['Checklist','Danh sách việc cần xác nhận'],['Evidence','Bằng chứng để xem lại kết quả'],['Retest','Thử lại sau sửa hoặc thay đổi'],['Audit log','Sổ ghi automation chạy thế nào'],['Changelog / History','Sổ ghi issue đã thay đổi gì'],['Marker','Dấu ghi lần thử xử lý, không bảo đảm thành công']],[2.3,4.7])
p('Project QAG3 ID 10002; board 3; scheme 10004 QAG3 Managed Delivery v1. Field Start date 10015; Change reason 10043; Acceptance checklist 10044; Review evidence 10045; Due date là duedate. Screen Task/Subtask 10010, Epic 10011.')
p('Đọc lại cấu hình: Project settings → Workflows hoặc Automation. Đọc công việc: mở issue → History, Work log, Child work items. Đọc lịch: board 3 → Timeline. Nguồn đường đi: jira-bot/handbook-source-2026-10-13.json; nguồn gate: forge/qag3-validator/manifest.yml. Mã sơ đồ và kiểm tra cạnh nằm trong jira-bot/learning-guide-2026-10-13.')
p('Hướng dẫn chính thức để học thêm: support.atlassian.com/jira-cloud-administration; support.atlassian.com/cloud-automation; developer.atlassian.com/cloud/jira/platform/jira-expressions. Với dự án này, hãy đọc cấu hình thật trước khi áp dụng một ví dụ chung trên mạng.')
p('Nhớ câu cuối: biết việc đang ở đâu, biết ai cần làm gì, biết thiếu điều kiện nào, rồi mới bấm chuyển. Không cần thuộc mã kỹ thuật để bắt đầu.')

doc.core_properties.title='Học cách dùng Jira QAG3 bằng hình'
doc.core_properties.author='Chủ dự án QAG3'
doc.core_properties.subject='Illustrated beginner learning guide from verified workflow evidence'
assert len(doc.inline_shapes)==20 and len(coverage['task'])==16
doc.save(OUT)
print(json.dumps({'document':str(OUT),'lessons':page-1,'figures':len(doc.inline_shapes),'nativeEdges':{k:len(v) for k,v in coverage.items()}},ensure_ascii=False))
