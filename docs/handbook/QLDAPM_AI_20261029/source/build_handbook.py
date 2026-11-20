from pathlib import Path
import json,math,textwrap,datetime
from PIL import Image,ImageDraw,ImageFont
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from workflows import WORKFLOWS

ROOT=Path(__file__).resolve().parent.parent
ASSETS=ROOT/'assets'
OUT=ROOT/'Cam_nang_AI_RAG_Second_Brain_n8n_QLDAPM_MAIN.docx'
inventory=json.loads((ROOT/'source/workflow_inventory.json').read_text(encoding='utf-8'))
live={w['name'][:4]:w for w in inventory['workflows']}
versions=json.loads((ROOT/'source/technology_versions.json').read_text(encoding='utf-8'))
fontfile='C:/Windows/Fonts/arial.ttf';boldfile='C:/Windows/Fonts/arialbd.ttf'

def wrapped(draw,text,font,width):
    lines=[]
    for part in text.split('\n'):
        current=''
        for word in part.split():
            trial=(current+' '+word).strip()
            if draw.textlength(trial,font=font)>width and current:lines.append(current);current=word
            else:current=trial
        lines.append(current)
    return lines

def box(draw,rect,text,fill='#EAF1F7',size=37):
    draw.rounded_rectangle(rect,radius=18,fill=fill,outline='#405B72',width=3)
    f=ImageFont.truetype(fontfile,size);x0,y0,x1,y1=rect
    lines=wrapped(draw,text,f,x1-x0-36);height=len(lines)*(size+9)
    assert height<y1-y0-12,(text,rect)
    for i,line in enumerate(lines):
        draw.text(((x0+x1-draw.textlength(line,font=f))/2,(y0+y1-height)/2+i*(size+9)),line,font=f,fill='#142A3A')

def arrow(draw,a,b,color='#385B72',width=6):
    draw.line([a,b],fill=color,width=width)
    angle=math.atan2(b[1]-a[1],b[0]-a[0]);s=18
    draw.polygon([b,(b[0]-s*math.cos(angle-.45),b[1]-s*math.sin(angle-.45)),(b[0]-s*math.cos(angle+.45),b[1]-s*math.sin(angle+.45))],fill=color)

def flow(name,labels,rows=1):
    cols=math.ceil(len(labels)/rows);W=2100;H=rows*215+40
    image=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(image)
    width=(W-100-(cols-1)*48)/cols
    for i,label in enumerate(labels):
        row=i//cols;col=i%cols
        x=50+col*(width+48);y=25+row*215
        box(d,(x,y,x+width,y+160),label,'#FFF0D8' if any(t in label.lower() for t in ['human','qa review','pm review','phê duyệt']) else '#EAF1F7',32 if len(labels)>5 else 38)
        if col<cols-1 and i<len(labels)-1:arrow(d,(x+width+4,y+80),(x+width+44,y+80))
        elif row<rows-1 and i<len(labels)-1:
            d.line([(x+width/2,y+160),(x+width/2,y+185),(50+width/2,y+185)],fill='#385B72',width=5)
            arrow(d,(50+width/2,y+185),(50+width/2,y+215))
    p=ASSETS/(name+'.png');image.save(p);return p

def architecture():
    im=Image.new('RGB',(2100,960),'white');d=ImageDraw.Draw(im)
    nodes=[((40,40,650,210),'Người dùng\nTrình duyệt'),((750,40,1350,210),'OpenProject Core\nUI và Native API'),((1450,40,2060,210),'PostgreSQL\nNguồn nghiệp vụ'),
      ((750,365,1350,535),'AI Gateway\nAuth và Supervisor'),((40,365,650,535),'n8n\nActor webhook hoặc machine'),((1450,365,2060,535),'Gemini thật\nProvider bên ngoài'),
      ((40,710,650,905),'Second Brain\nSQLite và FTS5'),((750,710,1350,905),'Ollama trên Windows\nBGE M3 1024D'),((1450,710,2060,905),'Qdrant\nVector và provenance')]
    for rect,text in nodes:box(d,rect,text,fill='#F3F5F7' if 'Windows' in text or 'ngoài' in text else '#EAF1F7',size=41)
    for a,b in [((650,125),(740,125)),((1350,125),(1440,125)),((1050,210),(1050,355)),((650,450),(740,450)),((1350,450),(1440,450)),((850,535),(345,700)),((1050,535),(1050,700)),((1230,535),(1740,700))]:arrow(d,a,b)
    f=ImageFont.truetype(fontfile,28)
    d.text((1070,270),'Signed UI bridge',font=f,fill='#263C4D');d.text((75,575),'Gateway đọc Native theo actor và project',font=f,fill='#263C4D')
    im.save(ASSETS/'architecture.png')

architecture()
flow('rag_pipeline',['Native source và quyền','Scanner tạo durable job','Parse và chia chunks','BGE M3 embedding','Qdrant và FTS5','Revalidate rồi citation'],rows=2)
flow('request_route',['Người dùng và scope','Deterministic nếu đủ','Supervisor nếu cần','Agent Gemini có guard','Reviewer local','Final answer và receipt'],rows=2)
flow('approval_flow',['Yêu cầu thay đổi','Proposal và exact hash','Human xem preview','Quyết định đúng actor','Native gates và write','Readback và sync'],rows=2)
flow('qa_flow',['Native AC và evidence','Runner hoặc QA capture','QA review độc lập','PM review độc lập','Transition proposal','Native gate và readback'],rows=2)
flow('wbs_flow',['BA output có hash','Immutable WBS draft','Manager adopt','Next node hoặc relation','Human duyệt proposal','Native receipt và RAG'],rows=2)
flow('recovery_flow',['Lỗi dependency','Persist pending hoặc retry','Bounded backoff và lease','Read job trước retry','Worker khôi phục','Verified không trùng'],rows=2)
flow('task_states',['NEW','IN ANALYSIS','READY FOR DEV','IN PROGRESS','CODE REVIEW','READY FOR TEST','IN TESTING','REVIEW','READY FOR RELEASE','DONE'],rows=2)
flow('epic_states',['NEW','READY','IN PROGRESS','REVIEW','DONE'])
flow('subtask_states',['NEW','IN PROGRESS','REVIEW','DONE'])
for w in WORKFLOWS:flow('flow_'+w['code'],w['flow'])

doc=Document();sec=doc.sections[0]
sec.page_width=Inches(8.5);sec.page_height=Inches(11)
sec.top_margin=Inches(.63);sec.bottom_margin=Inches(.62);sec.left_margin=Inches(.72);sec.right_margin=Inches(.72)
sec.header_distance=Inches(.24);sec.footer_distance=Inches(.25)
for style in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3','Caption']:
    s=doc.styles[style];s.font.name='Calibri';s.font.color.rgb=RGBColor(0,0,0)
    s.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Calibri')
doc.styles['Normal'].font.size=Pt(11)
doc.styles['Normal'].paragraph_format.line_spacing=1.08
doc.styles['Normal'].paragraph_format.space_after=Pt(5)
for style,size in [('Title',29),('Heading 1',20),('Heading 2',14),('Heading 3',12)]:
    doc.styles[style].font.size=Pt(size);doc.styles[style].font.bold=True
    doc.styles[style].paragraph_format.space_after=Pt(8)
    doc.styles[style].paragraph_format.space_before=Pt(8 if style!='Title' else 0)
doc.styles['Caption'].font.size=Pt(9);doc.styles['Caption'].font.italic=True
doc.styles['Caption'].paragraph_format.space_after=Pt(7)
header=sec.header.paragraphs[0];header.text='QLDAPM MAIN   |   CẨM NANG SỬ DỤNG AI VÀ TỰ ĐỘNG HÓA'
header.runs[0].font.size=Pt(8);header.runs[0].font.color.rgb=RGBColor(0,0,0)
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
footer.add_run('QLDAPM  |  29 10 2026  |  ')
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
for r in footer.runs:r.font.size=Pt(8)
doc.core_properties.title='Cẩm nang sử dụng AI RAG Second Brain và n8n trong QLDAPM MAIN'
doc.core_properties.author='QLDAPM';doc.core_properties.subject='Hướng dẫn sử dụng và vận hành hệ thống local'

pages=[];figures=[]
def page(title):
    if pages:doc.add_page_break()
    h=doc.add_heading(title,level=1) if pages else doc.add_paragraph(title,'Title')
    name='section_'+str(len(pages)+1)
    start=OxmlElement('w:bookmarkStart');start.set(qn('w:id'),str(len(pages)+1));start.set(qn('w:name'),name)
    end=OxmlElement('w:bookmarkEnd');end.set(qn('w:id'),str(len(pages)+1));h._p.insert(0,start);h._p.append(end)
    pages.append({'title':title,'bookmark':name})

def para(text,boldlead=None):
    p=doc.add_paragraph()
    if boldlead and text.startswith(boldlead):p.add_run(boldlead).bold=True;p.add_run(text[len(boldlead):])
    else:p.add_run(text)
    return p
def sub(text):return doc.add_heading(text,2)
def steps(lines):
    for i,t in enumerate(lines,1):para(f'{i}. {t}')
def bullets(lines):
    for t in lines:para('• '+t)
def table(headers,rows,widths=None,size=10.3):
    t=doc.add_table(rows=1,cols=len(headers));t.autofit=False
    widths=widths or [7.06/len(headers)]*len(headers)
    for c,w in zip(t.columns,widths):c.width=Inches(w)
    for cell,text in zip(t.rows[0].cells,headers):cell.text=text
    repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for row in rows:
        cells=t.add_row().cells
        for cell,text,w in zip(cells,row,widths):cell.text=str(text);cell.width=Inches(w)
    for i,row in enumerate(t.rows):
        pr=row._tr.get_or_add_trPr();cant=OxmlElement('w:cantSplit');pr.append(cant)
        for cell in row.cells:
            tcpr=cell._tc.get_or_add_tcPr();marg=OxmlElement('w:tcMar')
            for key,val in [('top',75),('left',90),('bottom',75),('right',90)]:
                e=OxmlElement('w:'+key);e.set(qn('w:w'),str(val));e.set(qn('w:type'),'dxa');marg.append(e)
            tcpr.append(marg)
            if i==0:
                shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E9EDF1');tcpr.append(shade)
            for p in cell.paragraphs:
                p.paragraph_format.space_after=Pt(2);p.paragraph_format.line_spacing=1.03
                for run in p.runs:run.font.size=Pt(size);run.bold=i==0;run.font.color.rgb=RGBColor(0,0,0)
    doc.add_paragraph().paragraph_format.space_after=Pt(1)
    return t
def picture(name,caption,maxheight=3.4,width=7.02):
    path=ASSETS/name
    assert path.exists(),path
    im=Image.open(path);w,h=im.size
    # Crop the document view only; preserve the original screenshot bytes.
    crops={'02_pm_output_full.jpg':(1672,452,437,576),'05_second_brain_search.jpg':(285,425,1050,590),'08_qa_detail.jpg':(285,170,600,520)}
    crop=crops.get(name)
    cw,ch=(crop[2],crop[3]) if crop else (w,h)
    use_width=min(width,maxheight*cw/ch)
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.keep_with_next=True
    shape=p.add_run().add_picture(str(path),width=Inches(use_width));shape._inline.docPr.set('descr',caption)
    if crop:
        x,y,cw,ch=crop
        rect=OxmlElement('a:srcRect')
        for key,value in [('l',x/w),('t',y/h),('r',(w-x-cw)/w),('b',(h-y-ch)/h)]:rect.set(key,str(round(value*100000)))
        fill=shape._inline.xpath('.//pic:blipFill')[0];fill.insert(1,rect)
        shape.height=Inches(use_width*ch/cw)
        ext=shape._inline.xpath('.//a:xfrm/a:ext')[0];ext.set('cx',str(shape.width));ext.set('cy',str(shape.height))
    cap=doc.add_paragraph(f'Hình {len(figures)+1}  {caption}','Caption');cap.alignment=WD_ALIGN_PARAGRAPH.CENTER
    figures.append({'file':name,'caption':caption})
def code(text):
    p=doc.add_paragraph();p.paragraph_format.space_after=Pt(8)
    run=p.add_run(text);run.font.name='Consolas';run.font.size=Pt(9.2)
def toc_link(title,anchor,page_number):
    p=doc.add_paragraph();p.paragraph_format.space_after=Pt(5)
    h=OxmlElement('w:hyperlink');h.set(qn('w:anchor'),anchor)
    r=OxmlElement('w:r');t=OxmlElement('w:t');t.text=f'{title}   {page_number}';r.append(t);h.append(r);p._p.append(h)

page('Cẩm nang sử dụng AI\nQLDAPM MAIN')
para('AI Assistant  RAG  Second Brain  n8n','AI Assistant')
para('Hướng dẫn thao tác và vận hành cho PM BA FE BE QA và người quản lý hệ thống')
para('Phiên bản ngày 29 tháng 10 năm 2026  |  Múi giờ Asia Bangkok')
picture('03_assistant_dashboard.jpg','Giao diện MAIN thực tế của tài khoản Owner tại Project 5',maxheight=3.4)
para('Tài liệu giúp người dùng hỏi đúng dữ liệu, đọc nguồn trích dẫn, theo dõi agent, chuẩn bị thay đổi có kiểm soát và hiểu phần nào hệ thống tự chạy. Người vận hành có thể tra cứu đủ 16 workflow, lịch, điều kiện thành công và cách xử lý lỗi mà vẫn bảo toàn dữ liệu nghiệp vụ.')
para('Nguyên tắc sử dụng: OpenProject là nguồn nghiệp vụ; Second Brain là chỉ mục hỗ trợ; Gemini đưa ra phân tích; quyết định QA và PM thuộc người có quyền. Mọi thay đổi phải khớp scope, hash, phiên bản và Native workflow hiện tại.')
para('Phạm vi: MAIN local, Project 5 qldapm-local. Jira Cloud và Staging là các môi trường riêng; các hướng dẫn này không cấp quyền thao tác sang những môi trường đó.')

page('Mục lục')
toc_placeholder=doc.add_paragraph('Mục lục được tạo theo các chương bên dưới.')

page('01 Bắt đầu sử dụng trong mười phút')
steps(['Mở http://127.0.0.1:18088, đăng nhập bằng tài khoản riêng và hoàn tất 2FA nếu hệ thống yêu cầu. Chọn QLDAPM — Local Community, Project 5.',
 'Mở AI Assistant ở menu dự án. Kiểm tra Gateway ok, OpenProject authenticated và trạng thái provider. Không đưa password, mã 2FA hoặc API key vào prompt.',
 'Bắt đầu bằng câu hỏi chỉ đọc có ID cụ thể, ví dụ phân tích công việc #376 và nêu nguồn. Muốn đếm công việc, hỏi một tiêu chí rõ ràng mỗi lần.',
 'Đọc final answer, mở citation và kiểm lockVersion. Mở Execution Monitor nếu cần xem agent nào chạy, model calls và receipt.',
 'Dùng Second Brain để tìm thông tin liên quan. Nếu nội dung chưa mới, kiểm nguồn Native và freshness trước khi yêu cầu reindex.',
 'Nếu cần sửa dữ liệu, yêu cầu một thay đổi nhỏ, đọc preview before/after rồi để PM/Owner có quyền quyết định exact proposal. QA review vẫn là một bước riêng.'])
table(['Muốn làm gì','Nơi bắt đầu'],[
 ('Hỏi số liệu hoặc phân tích','AI Assistant'),('Tìm và mở nguồn','Second Brain trên trang Assistant'),('Xem từng bước AI','Execution Monitor / Lịch sử xử lý'),
 ('Kiểm tra bằng chứng','Bằng chứng QA / Kiểm duyệt'),('Theo dõi automation','n8n Overview → Executions'),('Đối soát lỗi kỹ thuật','Run ID + Trace ID + execution ID + receipt')],[2.8,4.26])
para('Các URL local chỉ truy cập trên máy có dịch vụ chạy. Không mặc định địa chỉ 127.0.0.1 trên một máy khác sẽ trỏ về QLDAPM của bạn.')

page('02 Hệ thống phối hợp như thế nào')
picture('architecture.png','Các thành phần triển khai và những đường giao tiếp chính',maxheight=3.4)
para('Người dùng làm việc qua OpenProject Core. Core gọi AI Gateway bằng signed bridge; Gateway xác minh actor/project và đọc Native API theo quyền thật. PostgreSQL lưu dữ liệu nghiệp vụ và lịch sử của OpenProject.')
para('Second Brain lưu tài liệu, chunks, metadata và chỉ mục FTS5 trong SQLite; Qdrant lưu vectors cùng provenance. Ollama chạy BGE-M3 trên máy Windows để tạo embedding 1024 chiều. Gateway phối hợp retrieval và revalidation trước khi dùng nội dung trong phân tích.')
para('n8n điều phối 16 workflow có adapter nghiệp vụ. Các nhánh có actor nhận quyền từ người gọi; các lịch machine dùng route cố định và không được coi là người phê duyệt. Scanner trong Gateway chạy độc lập, vì vậy n8n không nằm bắt buộc trong mọi lần đồng bộ Native.')
para('Gemini là provider bên ngoài cho các phân tích cần model. Quota, data scope và audit được kiểm tra tại backend. Không phải mọi câu hỏi, agent hoặc workflow đều cần một model call.')

page('03 Vai trò và ranh giới quyền')
table(['Vai trò','Sử dụng AI và tri thức','Thay đổi và review'],[
 ('PM','Đọc, phân tích, tìm nguồn, xem báo cáo theo quyền','Quản lý công việc/proposal/WBS khi đủ Native permission và gate; không tự thay QA độc lập.'),
 ('BA hoặc BA PM','Phân tích yêu cầu, scope, WBS draft, bình luận được phép','BA-PM là tên policy lịch sử của BA; không mang toàn bộ quyền PM.'),
 ('FE và BE','Phân tích kỹ thuật, tìm nguồn, nhận biết dependency và bình luận','Không tự tạo/sửa/chuyển trạng thái công việc qua AI nếu policy chỉ cấp đọc và bình luận.'),
 ('QA','Đọc, thiết kế test, thu thập evidence và các QA tools được phép','Review phải đúng stage và độc lập. Kết quả runner không cấp quyền approve thay người khác.'),
 ('AI System Owner','Quản trị/giám sát AI theo capability và scope thực','Không đồng nhất với mọi Native admin. Không vượt hash, version, gate hoặc reviewer độc lập.'),
 ('Machine n8n','Status, daily/weekly collector và monitor theo route cố định','Không actor, không consent, không Native write hoặc model ở các collector lịch.')],[1.15,2.65,3.26])
para('Quyền hiển thị trên UI là thông tin để tra cứu; server vẫn kiểm tra lại membership, role, project và Native permission ở mỗi thao tác. Actor hoặc role tự khai trong body webhook không tạo authority.')
para('Hai ranh giới cần phân biệt: quyền thao tác với proposal của Gateway và quyền Native để ghi công việc; quyền viết một loại evidence cũng không bảo đảm được phép review evidence đó. Gate hiện hành có thể hạn chế chặt hơn bảng quyền tổng quát.')
para('Muốn kiểm tra quyền hiện tại: Assistant → Role & AI Permissions. Khi actor đổi vai trò hoặc mất quyền nguồn, dừng dùng kết quả cũ và đọc lại bằng phiên đăng nhập hiện hành.')

page('04 Gửi yêu cầu trong AI Assistant')
picture('04_assistant_form.jpg','Form nhập yêu cầu và chế độ xử lý trên MAIN',maxheight=3.6)
steps(['Chọn chế độ xử lý: Gemini đã cấu hình, Gemini Business Tools chỉ đọc, hoặc Supervisor local không dùng model.',
 'Nêu mục tiêu, ID công việc và phạm vi. Nếu chỉ cần phân tích, ghi rõ chỉ đọc, không tạo đề xuất, không sửa dữ liệu.',
 'Ô giới hạn ID là phạm vi ghi bổ sung khi contract hỗ trợ; không phải quyền truy cập mới. Nội dung ngoài quyền vẫn bị chặn.',
 'Bấm Gửi yêu cầu một lần. Ghi run_id, đọc trạng thái và chờ kết quả bền vững; không gửi lặp để thúc tiến độ.',
 'Mở nguồn và xem plan/receipt trước khi dùng phân tích để ra quyết định. Nếu có proposal, xử lý theo phần 23 thay vì coi câu trả lời là lệnh đã chạy.'])
para('Supervisor local phù hợp với phân tích/draft theo contract. Chế độ này không chứng minh đã gọi Gemini hoặc model đã tiêu thụ RAG. Các câu hỏi số liệu được nhận dạng rõ có thể được deterministic tool trả trực tiếp với model_used=false.')

page('05 Viết prompt có thể kiểm chứng')
table(['Nhu cầu','Mẫu yêu cầu an toàn'],[
 ('Đếm một loại việc','Hiện tại có bao nhiêu công việc loại Task chưa hoàn thành? Chỉ đọc số liệu, không tạo đề xuất.'),
 ('Phân tích một việc','Phân tích rủi ro công việc #376 theo dữ liệu hiện tại. Nêu nguồn, phiên bản và giới hạn. Chỉ đọc.'),
 ('Yêu cầu BA','Phân tích yêu cầu của công việc #49, chỉ rõ acceptance criteria còn thiếu. Không cập nhật công việc.'),
 ('Chuẩn bị WBS','Đề xuất phân rã yêu cầu thành Epic Task Subtask, giữ trace yêu cầu và dependency. Chỉ tạo bản phân tích có cấu trúc, chưa ghi Native.'),
 ('Thiết kế test','Lập test cases cho công việc #49, gồm happy path, dữ liệu sai và quyền truy cập. Không tự xác nhận QA PASS.'),
 ('Chuẩn bị thay đổi','Đề xuất cập nhật mô tả cho công việc do tôi chọn. Hiển thị before/after và exact scope; chưa thực thi cho đến khi người có quyền duyệt.')],[1.35,5.71])
sub('Cách đọc câu trả lời')
para('Tách dữ kiện từ Native, diễn giải của AI và đề xuất hành động. Citation đúng ID/version xác minh nguồn đầu vào; nó không bảo đảm mọi nhận định, nguyên nhân hoặc khuyến nghị trong văn bản đều đúng.')
para('Ví dụ đã kiểm tra: câu hỏi đếm Task trả 57, còn dashboard tổng hợp trả 339 Work Packages được phép xem. Hai số thuộc hai tập dữ liệu khác nhau. Hãy đối chiếu bộ lọc và thời điểm, không coi chênh lệch này mặc nhiên là lỗi.')
sub('Những nội dung nên tránh')
bullets(['Không gộp quá nhiều câu hỏi đếm và thay đổi trong cùng một prompt. Chia thành các yêu cầu có thể đối soát.',
 'Không dán key, token, mật khẩu, mã 2FA hoặc yêu cầu bỏ gate/quota vào chat.',
 'Không yêu cầu model tự quyết định QA, đóng Bug hoặc cấp quyền chỉ vì một kết quả trông hợp lý.'])

page('06 Supervisor và các Agent')
picture('request_route.png','Lộ trình xử lý từ yêu cầu tới kết quả đã lưu',maxheight=1.8)
table(['Agent','Vai trò trong contract'],[
 ('Supervisor','Phân loại yêu cầu, tạo plan/dependency, điều phối và tổng hợp.'),('PM','Đánh giá tiến độ, rủi ro, phạm vi và đề xuất quản lý.'),
 ('BA','Phân tích nghiệp vụ, khoảng trống yêu cầu và WBS có cấu trúc.'),('FE','Tư vấn tương tác UI, accessibility, trạng thái và tích hợp API.'),
 ('BE','Tư vấn API, auth, validation, transaction và failure handling.'),('DEV','Phân tích kỹ thuật chung, FE/BE breakdown và dependency.'),
 ('QA','Thiết kế test, regression gaps và triage; không tự ký nghiệm thu.'),('Reviewer','Kiểm định local về reference/version/scope/RBAC, không gọi model để giả lập human review.')],[1.2,5.86])
para('Agent registry mô tả năng lực được cấu hình. Một run chỉ gọi các agent cần cho plan của nó. IDLE hoặc LIVE_SUCCESS gần nhất không có nghĩa tất cả agent đang chạy, hay tất cả đã được kiểm thử live ở thời điểm này.')
para('Các agent Gemini dùng chung central quota limiter. Plan bị giới hạn context, agent count, model calls, timeout và retry; giới hạn thực tế được backend cấu hình. Reviewer local có thể chặn nguồn sai nhưng không đánh giá thay QA/PM về chất lượng nghiệp vụ.')

page('07 Đọc Execution Monitor')
picture('01_monitor.jpg','Một run MAIN đã hoàn tất với PM Gemini và Reviewer local',maxheight=3.3)
steps(['Mở Execution Monitor / Lịch sử xử lý từ Control Center, chọn đúng run của mình.',
 'Đọc Run ID, Trace ID, actor/project và execution mode. Kiểm số model calls, tokens, errors/retries và thời lượng đã ghi nhận.',
 'Chọn node Supervisor hoặc agent. Tab Kết quả xử lý hiển thị output riêng nếu đã lưu; thiếu telemetry được ghi là chưa có dữ liệu.',
 'Đọc timeline và báo cáo cuối; mở citation để kiểm nguồn Native. Readonly replay chỉ phát lại sự kiện, không chạy lại model hoặc mutation.'])
para('Ví dụ trong hình: run c5d44a1d… có 18 events, PM dùng một generateContent và Reviewer chạy local. countTokens cùng generateContent là hai HTTP phases, không phải hai lượt generation. Tổng duration của execution và duration riêng provider có thể khác nhau.')
para('Nếu UI báo Nguồn hoặc quyền đã đổi, nội dung cũ có thể bị ẩn. Không dùng token của người khác hoặc thao tác replay để né kiểm quyền.')

page('08 Xem output và xác minh nguồn')
picture('02_pm_output_full.jpg','Output riêng của PM Agent và nguồn tham chiếu trong run đã lưu; vùng giao diện được phóng lớn',maxheight=4.3,width=3.9)
steps(['Đọc phần Nội dung kết quả của agent và phần Giới hạn; phân biệt gợi ý với dữ kiện nguồn.',
 'Mở #ID và phiên bản trong Nguồn tham chiếu. Đối chiếu subject, trạng thái, parent, assignee, ngày và nội dung Native.',
 'Nếu nguồn đã đổi, yêu cầu phân tích mới theo phiên bản hiện hành thay vì dùng output cũ làm approval.'])
para('Run mẫu dẫn về #376 v0, subject test2, Subtask thuộc parent #49 và trạng thái NEW. Đây là ví dụ đọc dữ liệu thật đã được giữ nguyên; không sử dụng công việc này làm fixture ghi/xóa chỉ vì tên chứa test.')
para('Khi báo một lỗi, gửi Run ID/Trace ID, thời điểm, actor role, expected/actual và citation. Không cần gửi key hoặc toàn bộ database để điều tra.')

page('09 Tìm kiếm bằng Second Brain và RAG')
picture('05_second_brain_search.jpg','Tìm test2 trong Second Brain và đọc citation có lockVersion',maxheight=3.5)
steps(['Tại vùng Second Brain, nhập từ khóa nghiệp vụ hoặc ID/title cần tra cứu và bấm Tìm kiếm.',
 'Đọc snippet, nguồn #ID và lockVersion. Một truy vấn có thể trả nhiều kết quả liên quan, không chỉ một exact match.',
 'Mở citation để kiểm toàn bộ nguồn. Kết quả đã revalidate quyền và phiên bản tại thời điểm đọc.',
 'Nếu cần phân tích, đặt yêu cầu mới với ID rõ ràng. Trí nhớ hoặc đoạn trích trong RAG không phải quyền để sửa nguồn.'])
para('Hybrid retrieval phối hợp semantic vectors của Qdrant với tìm từ khóa FTS5. Gateway kiểm scope, role, actor snapshot và Native freshness trước khi đưa context phù hợp cho model. Canonical document và actor-scoped snapshot là hai loại nguồn khác nhau.')
para('Không thấy kết quả có thể do chưa index, thay đổi đang chờ sync, quyền bị thu hồi, nguồn đã stale hoặc dependency lỗi. Trước tiên mở Native và đọc status; đừng lập chỉ mục lại toàn bộ corpus theo thói quen.')

page('10 Đồng bộ tự động từ Native')
picture('rag_pipeline.png','Chuỗi tự động Native change tới retrieval có kiểm quyền',maxheight=2.0)
para('Khi người dùng được phép tạo/sửa Work Package, Gateway scanner khoảng 60 giây phát hiện thay đổi và đưa cache-refresh job vào durable outbox. Worker đọc source, chuẩn hóa, chia chunks, tạo embedding BGE-M3 rồi cập nhật Qdrant/FTS5. Chỉ khi readback hợp lệ job mới đạt verified.')
table(['Điểm cần kiểm','Cách đọc'],[
 ('Source','ID, lockVersion, source hash, updatedAt và activity hash khi áp dụng.'),('Scanner','generation và observed_at phải tiếp tục cập nhật; changed=0 có thể bình thường khi không có sửa đổi.'),
 ('Job','pending/running/retry/verified hoặc dlq; xem attempts/error/lease.'),('Index','Document/chunk/vector identity và FTS phải liên hệ theo provenance.'),('Retrieval','Chỉ context hiện hành còn quyền mới được đưa vào answer/citation.')],[1.3,5.76])
para('Bình luận mới có thể được phát hiện theo updatedAt; sửa/xóa bình luận còn được audit theo lô tối đa 32 Work Packages mỗi scan. Với 339 visible WPs, một vòng audit khoảng 11 phút. Đây là giới hạn thiết kế, không phải hứa đồng bộ mọi loại thay đổi ngay lập tức.')
para('Snapshot bình luận bị giới hạn ở 20 bình luận gần nhất, mỗi snippet tối đa 750 ký tự; hash nội dung đầy đủ phục vụ freshness. Thu hồi quyền làm nội dung không được truy xuất, không tự xóa lịch sử hoặc protected vectors.')

page('11 Tài liệu file và nguồn tri thức')
para('Nguồn file phải được người vận hành đăng ký phía server bằng source_key, path/root cố định, SHA256, loại nội dung và allowed roles. Người dùng thông thường tra cứu nguồn đã được cấp; webhook không phải một cơ chế upload file bất kỳ.')
table(['Loại nguồn','Điều kiện và giới hạn'],[
 ('Native Work Package','Đọc theo actor/project, version và quyền hiện tại. Không mặc định mọi dữ liệu trên instance đều thuộc Project 5.'),
 ('Markdown và DOCX','Nguồn server-pinned đã đăng ký; kiểm hash và role. Nội dung được trích/chia chunks theo pipeline.'),
 ('PDF có lớp text','Giới hạn hiện hành: input 256 KiB, tối đa 64 trang; parser bị chặn tài nguyên và thời gian.'),
 ('PDF không hợp lệ','Encrypted/corrupt/image-only/empty hoặc vượt giới hạn bị từ chối toàn bộ; không giả lập OCR hay đánh dấu parse một phần là thành công.'),
 ('Feedback','Feedback submit/get/decision/apply giữ ID/hash/scope; không biến ghi chú thành quyền sửa nguồn hoặc approve QA.')],[1.65,5.41])
steps(['PM/Owner được phép kiểm registry và exact file hash, không đặt key hay nội dung nhạy cảm không thuộc scope vào tài liệu nguồn.',
 'Gọi ingest/reindex qua đường đã cấu hình với stable request_id. Dùng search/read để xác minh document và revision mới.',
 'Khi file thay đổi hợp lệ, cập nhật cấu hình nguồn bằng quy trình kỹ thuật được phép, rồi reindex. Không sửa hash chỉ để một file ngoài registry được chấp nhận.'])
para('Ví dụ nguồn tài liệu workflow đã được đăng ký có source_key main-workflow-contract. Hãy kiểm quyền và registry hiện tại trước khi dùng; mẫu tên không là cam kết rằng mọi actor đều được đọc.')

page('12 Danh mục toàn bộ workflow n8n')
para('16 workflow hiện hành đều active/published tại thời điểm đối soát. Chỉ WF07, WF12 và WF16 có lịch production; các workflow còn lại dùng webhook/đường gọi theo actor. Scanner tự động nằm trong Gateway.')
table(['WF','Chức năng','Trigger','Authority'],[(w['code'],w['title'],{'WF07':'08:00 mỗi ngày','WF12':'Thứ Sáu 17:00','WF16':'Mỗi 15 phút'}.get(w['code'],'Webhook'), 'Machine + actor' if w['code']=='WF12' else 'Machine' if w['code'] in {'WF07','WF16'} else 'Actor') for w in WORKFLOWS],[.55,3.24,1.65,1.62],size=10)
para('Actor webhook yêu cầu hai lớp phù hợp: webhook header credential và Authorization bearer của người gọi; bearer không được thay bằng shared PM credential. Machine dùng route cố định, key/HMAC/nonce theo contract và không mang human approval.')
para('Các trang tiếp theo giải thích đầu vào, gate và actual business result. Tên node hoặc mô tả cũ không thay thế hành vi đang publish. Không bấm Execute Workflow để giả bằng chứng natural schedule.')

for pair in range(0,16,2):
    a,b=WORKFLOWS[pair:pair+2]
    page(f'{13+pair//2:02d} Quy trình {a["code"]} và {b["code"]}')
    for w in [a,b]:
        sub(w['code']+' '+w['title'])
        picture('flow_'+w['code']+'.png','Luồng '+w['code']+' theo contract hiện hành',maxheight=.62)
        for label,key in [('Mục đích','purpose'),('Kích hoạt','trigger'),('Đầu vào','inputs'),('Điều kiện','gates'),('Kết quả','result'),('Khi lỗi','failure')]:para(label+': '+w[key],label+':')

page('21 Lịch tự động và báo cáo nghiệp vụ')
table(['Tác vụ','Lịch Asia Bangkok','Kết quả cần đối chiếu'],[
 ('Native scanner','Khoảng60giây trong Gateway','generation/freshness → job → verified; không cần n8n cron.'),
 ('WF07 Daily','08:00 mỗi ngày','daily:YYYY-MM-DD; COMPLETED/READY và ready=targets.'),
 ('WF12 Weekly','Thứ Sáu 17:00','weekly:ngày-thứ-Hai; rolling 7 days/as_of_date; report/hash theo actor.'),
 ('WF16 Health','Mỗi 15 phút','health_monitor:bucket 900 giây; technical success tách khỏi HEALTHY/DEGRADED.'),
 ('Ollama health','Logon và mỗi 5 phút','Một daemon/listener, BGE-M3 có sẵn, task result 0.'),
 ('Main backup','Logon và kiểm mỗigiờ','Snapshot khi đủ 24 giờ từ last-success; NOT_DUE là kết quả bình thường.'),
 ('Natural observer','Hai one-shot 08:05 và17:05','Chỉ đọc execution/receipt sau lịch; không gọi workflow.')],[1.2,1.75,4.11],size=10)
picture('13_wf07_execution.jpg','WF07 execution 2646 được n8n kích hoạt tự nhiên lúc08 giờ ngày29 tháng10',maxheight=2.7)
para('Lượt daily này có receipt e9bdf13b-6647-41df-b1d9-597fbc99e11e, READY 5/5. Owner không nằm trong các target daily; vì vậy Owner có thể thấy Chưa có tóm tắt, trong khi các tài khoản nghiệp vụ đã có báo cáo. Báo cáo stale khi fingerprint dữ liệu actor thay đổi.')
para('Máy phải thức, LUIM đăng nhập và Docker sẵn sàng cho runtime local. Schedule có thể bị lỡ khi host ngủ/tắt; không tự biến một manual run thành natural evidence, không bịa catch-up. WF12 ngày 30/10 17:00 chưa được quan sát tại thời điểm biên soạn.')

page('22 Thao tác đọc trong giao diện n8n')
picture('09_n8n_overview.jpg','Overview n8n MAIN với các workflow đang publish',maxheight=3.2)
steps(['Mở http://127.0.0.1:5679 và đăng nhập bằng tài khoản n8n được cấp. Tài khoản n8n owner không phải một PM token để thay quyền actor.',
 'Vào Overview → Workflows, tìm mã WF01 đến WF16. Published/active chỉ xác nhận đăng ký, chưa chứng minh business thành công.',
 'Mở workflow → Executions, chọn execution đúng thời điểm/ID. Kiểm trigger mode, published version và terminal state.',
 'Mở node cuối để đọc output. So sánh business state, run/receipt ID, idempotency key, ready/targets hoặc health checks.',
 'Khi điều tra, lưu execution ID và sanitized output. Không bấm Execute, Retry, Copy to editor, Delete hoặc đổi credential chỉ để tạo kết quả giống ảnh.'])
para('Nhánh adapter có thể chuyển tiếp HTTP lỗi Gateway qua Respond to Webhook. Vì vậy workflow technical success vẫn có thể chứa HTTP4xx/5xx hoặc business blocked. WF07/WF12 có validator COMPLETED/READY riêng; WF16 lưu DEGRADED như một kết quả monitoring có ý nghĩa.')
para('Execution history có thể chứa các lỗi qualification/lịch sử hợp lệ. Hãy kiểm thời điểm, actor và nguồn; không replay hàng loạt unknown-outcome writes hoặc xóa history để giảm failed count.')

page('23 Preview và phê duyệt thay đổi')
picture('approval_flow.png','Quy trình ghi dữ liệu có human decision và Native readback',maxheight=1.75)
picture('11_proposal_preview.jpg','Preview before/after của một proposal lịch sử',maxheight=2.6)
steps(['Người yêu cầu mô tả đúng thay đổi và scope. Đọc preview before/after: target, nội dung, parent, loại công việc, ngày hoặc relation.',
 'Người có quyền quyết định kiểm exact hash, expiry, source version và các bằng chứng cần thiết. Mỗi proposal chỉ áp dụng cho nội dung đã xem.',
 'Nếu proposal còn pending và hợp lệ, dùng Duyệt và thực hiện thay đổi trên hoặc Từ chối đề xuất. Việc chấp thuận một draft không tự chấp thuận mutation ngoài scope.',
 'Sau khi ghi, kiểm receipt và Native readback. Nếu kết quả không rõ, dừng gửi lại và nhờ operator đối soát đúng request/proposal.'])
para('Proposal lịch sử này đã có kết quả khi đối chiếu trên trang. Một proposal đã xử lý không được gửi lại. Bản preview chỉ là ví dụ; không nhấn approve để nghiệm thu cẩm nang hoặc thay đổi công việc thật.')

page('24 Quy trình WBS từ yêu cầu tới Native')
picture('wbs_flow.png','WBS đi qua draft bất biến và proposal theo từng bước',maxheight=2)
steps(['BA phân tích nguồn hiện hành và tạo structured output có requirement IDs, nodes và quan hệ. Người kiểm tra đọc chất lượng nội dung trước khi sử dụng.',
 'from_ba tham chiếu completed run và exact output_hash; backend kiểm actor/project, BA step provenance, schema và source references.',
 'Draft lưu id/hash/spec bất biến. Đọc wbs_get để xem DRAFT_NON_EXECUTABLE và tiến độ; một draft chưa phải các Native tasks đã tồn tại.',
 'PM/Owner có quyền adopt đúng hash, rồi gọi next theo quy trình. Mỗi bước tạo proposal riêng và chờ quyết định hợp lệ.',
 'Kiểm parent trước child, receipt của node đã tạo, Native form/calendar và quan hệ được phép. Sau readback, Second Brain được refresh theo pipeline.'])
table(['Kiểm tra','Điều kiện'],[
 ('Cấu trúc','Epic → Task → Subtask; khóa duy nhất; parent/dependency tham chiếu đúng; không cycle/dangling refs.'),
 ('Ngày và người nhận','start_date/due_date phải đủ cặp, ISO và đúng thứ tự; assignee role, priority, calendar phải hợp lệ.'),
 ('Quan hệ','depends_on trong metadata không mặc nhiên ghi Native relation; explicit relations/steps có guard và approval riêng.'),
 ('Nguồn thay đổi','Version/hash/BA output khác → hold hoặc draft mới; không sửa raw model output để che lỗi.'),
 ('Lost ACK','Đối chiếu own receipt để tránh duplicate create; không retry unknown Native write bằng request mới.')],[1.3,5.76])
para('Ví dụ wbs_get id530cb443… hiển thị ba node và DRAFT_NON_EXECUTABLE. Nó minh họa cách đọc một WBS đã lưu, không cấp quyền adopt/execute trên MAIN.')

page('25 Bug và bằng chứng QA')
picture('qa_flow.png','Evidence tự động phải qua review độc lập và Native gate',maxheight=1.7)
picture('08_qa_detail.jpg','Evidence pending QA vẫn tách khỏi kết quả PASSED của runner; phóng lớn vùng trạng thái',maxheight=3.8)
steps(['Ghi lỗi với expected/actual, bước tái hiện, môi trường, severity, source version và evidence. Dùng Bug triage để hỗ trợ phân loại, không tự suy ra approval.',
 'Runner chỉ thực hiện assertion Native được hỗ trợ. Tiêu chí văn xuôi không hỗ trợ phải bị chặn hoặc cần test khác, không tự đánh PASS.',
 'QA độc lập đọc artifact/hash/source, xác nhận checkbox trách nhiệm rồi Chấp nhận bằng chứng hoặc Từ chối bằng chứng. Manager chỉ review automated proof sau QA hợp lệ.',
 'PM/Owner quản lý kiểm điều kiện hiện hành rồi prepare transition proposal; Native workflow vẫn kiểm riêng trước khi ghi.'])
para('Ví dụ evidence fc0479a8… cho Bug #371/v4 có automated PASSED nhưng trạng thái review vẫn pending_qa. Producer/assignee không được tự review. accepted evidence cũng chưa tự biến công việc thành DONE; các gate khác có thể còn thiếu.')

page('26 Native Task và điều kiện chuyển trạng thái')
picture('task_states.png','Luồng chính mười trạng thái Task của MAIN',maxheight=1.65)
table(['Chuyển tới','Điều kiện chính trong Native gate'],[
 ('IN ANALYSIS','Story evidence, AC, scope evidence và scope approval.'),('READY FOR DEV','AC, analysis evidence/approval và scope approval còn revision.'),
 ('IN PROGRESS','Từ READY FOR DEV phải có development Subtask; từ IN TESTING phải có bug evidence/Fix Bug khi áp dụng.'),
 ('CODE REVIEW','Checklist đầy đủ, implementation evidence và reviewer độc lập được cấu hình.'),
 ('READY FOR TEST','Code approval, test_build, test_cases và đúng reviewer theo policy.'),('IN TESTING','Có test_cases; giữ scope và quyền Native hiện tại.'),
 ('REVIEW','Test evidence/approval, không blocking bug; QA child bắt buộc đã DONE.'),
 ('READY FOR RELEASE','Code, BA, PM approvals và retest evidence/approval hoặc retest_not_needed hợp lệ.'),
 ('DONE','Các child DONE, checklist đầy đủ, không blocking bug; deployment Test, smoke passed và approvals hiện hành.')],[1.6,5.46],size=10)
para('Đây là tóm tắt GatePolicy đang triển khai; danh sách lỗi Native trên thao tác hiện tại là căn cứ quyết định. Gateway/Native có thể chỉ cho PM hoặc AI System Owner thực hiện thay đổi dù tài liệu trách nhiệm BA/Dev/QA mô tả ai tạo bằng chứng.')
para('Reopen, trả lại trạng thái hoặc hủy cần lý do và reference gắn đúng from/to, actor và revision. Không tự đổi status để bỏ qua missing evidence; code/revision mới có thể vô hiệu approvals cũ. READY FOR RELEASE và REVIEW không phải DONE.')

page('27 Native Epic và Subtask')
sub('Epic')
picture('epic_states.png','Luồng giao việc và nghiệm thu Epic',maxheight=.64)
para('NEW → READY cần owner, AC, ít nhất một Task, scope evidence/approval. READY → IN PROGRESS cần child đã bắt đầu. REVIEW/DONE yêu cầu children tồn tại và đều DONE. DONE còn cần checklist, integration/handover evidence, handover approval và không blocking bug.')
para('Epic còn có CANCELLED. Hủy, mở lại và restore cần lý do/reference đúng revision. Hủy Epic không phải quyền tự xóa hoặc nghiệm thu Task con; DONE không có nghĩa có thể bỏ lịch sử bàn giao.')
sub('Subtask Native')
picture('subtask_states.png','Bốn trạng thái Native Subtask với nghĩa vụ evidence vẫn giữ',maxheight=.64)
para('Subtask có stream development hoặc business. Bốn trạng thái không làm mất nghĩa vụ code review, test hoặc completion. Development Native khi vào REVIEW/DONE vẫn cần implementation, test_cases, test_build, test evidence, code/test approval và reviewer độc lập theo policy.')
para('REVIEW yêu cầu checklist và test/completion evidence theo stream; DONE cần checklist, completion approval và reviewer hợp lệ. Các child QA/Fix Bug không được đánh DONE khi còn blocking bug. Sửa scope, implementation, test/build hay checklist có thể làm approvals cũ hết hiệu lực.')
sub('Workflow gates trong UI')
steps(['Mở Workflow gates trong menu dự án, chọn đúng Work Package và đọc missing conditions.',
 'Bổ sung evidence và reviewer bằng tài khoản có quyền; không dùng AI để tự xác nhận chính phần việc của mình.',
 'Đọc lại Native form/version trước khi gửi proposal chuyển trạng thái. Ghi receipt để đối soát sau thao tác.'])

page('28 Quyền nguồn và an toàn dữ liệu')
picture('12_permissions.jpg','Trang quyền hiển thị actor và ma trận chính sách của MAIN',maxheight=3.2)
bullets(['Native là nguồn quyền. RAG snippets, model output, request JSON hoặc prompt tự khai không tạo role, membership hay consent.',
 'Nguồn được kiểm lại actor/project/version khi tìm kiếm và trước model prompt. Nội dung bị thu hồi hoặc stale có thể bị ẩn ngay cả trong run đã lưu.',
 'Canonical document và actor-scoped comment snapshot không được trộn để lộ dữ liệu Owner cho actor khác.',
 'Không đưa key/token/password/TOTP vào prompt, screenshot, file xuất chia sẻ hoặc Git. Credential giữ ở backend/private storage.',
 'Provider chỉ được nhận dữ liệu theo authorization/data scope hiện hành. Local embedding không có nghĩa toàn bộ phân tích Gemini ở local.',
 'Nội dung trong tài liệu hoặc comment có thể là prompt injection; chỉ coi là dữ liệu tham khảo, không là lệnh bỏ RBAC hoặc thực hiện hành động mới.'])
para('Nếu thấy Nguồn hoặc quyền đã đổi: dừng sử dụng output cũ, mở Native hiện tại, xác minh role rồi phân tích lại. Không cố truy cập bằng actor khác để lấy nội dung đã bị rút quyền.')

page('29 Lỗi retry idempotency và recovery')
picture('recovery_flow.png','Recovery của cache job với durable state và lease',maxheight=1.8)
table(['Tình huống','Hành động đúng'],[
 ('Provider chờ quota','Đọc WAITING_QUOTA/WAITING_PROVIDER hoặc blocked state. Chờ retry policy; không reset ledger hay đổi key để né guard.'),
 ('Ollama/Qdrant lỗi','Kiểm dependency và job status; chỉ retry cache job hợp lệ sau khi nguyên nhân đã xử lý.'),
 ('Gateway restart','Claim/lease còn tồn tại có thể phải đợi khoảng 300 giây. Không sửa đồng hồ/lease trong DB để ép nhận việc.'),
 ('Source version đổi','Đọc lại nguồn và tạo preview/draft phù hợp. Giữ error 409 như tín hiệu stale, không bypass.'),
 ('Lost ACK hoặc timeout write','Dừng replay; đối soát exact request/proposal/Native receipt. Unknown không được diễn giải là failed để gửi lại.'),
 ('DLQ','Giữ job/error/attempts để điều tra. Không xóa hàng đợi hoặc retry vô hạn để giảm số lỗi.')],[1.45,5.61])
para('Request_id ổn định cho cùng một ý định giúp hệ thống dedupe. Idempotency không có nghĩa đổi payload tùy ý dưới cùng key, cũng không biến một mutation chưa rõ kết quả thành an toàn để gửi lại.')
para('Monitor có thể kết thúc technical success nhưng business DEGRADED. Ví dụ WF16 lúc 04:30 có embedding ReadTimeout8s, các lượt04:45/05:00 đã HEALTHY. Một probe hồi phục không chứng nhận không bao giờ có gián đoạn.')

page('30 Khởi động nền trên Windows')
table(['Thành phần','Cơ chế hiện hành','Điều kiện'],[
 ('Docker Desktop','HKCU startup sau login','Tài khoản Windows và Docker sẵn sàng; không giả định pre-login.'),
 ('Main containers','restart policy unless-stopped','Container đã được cấu hình; operator không cố ý stop.'),
 ('Gateway workers','Application lifespan','Gateway khởi động thành công; config, Native credentials và storage đúng.'),
 ('n8n schedules','Active published workflows','n8n chạy, timezone Asia/Bangkok và cron được khôi phục.'),
 ('Ollama health task','Logon/mỗi 5 phút, mutex và valid listener','Một daemon trên 11434, model BGE-M3 có sẵn; không tự pull khi thiếu.'),
 ('Backup và observer','TaskScheduler limited interactive LUIM','Action WindowStyle Hidden; battery flags cho chạy/không dừng khi chuyển pin.')],[1.3,2.6,3.16],size=10)
steps(['Khi bắt đầu phiên làm việc, kiểm Docker/Main health và một Ollama listener. Không cần mở terminal để giữ daemon nếu task hoạt động đúng.',
 'Kiểm LastTaskResult, scanner observed_at và last-success backup. Result0/NOT_DUE là launcher thành công, không chứng minh một snapshot mới đã tạo.',
 'Sau Docker restart thực tế, đọc lại IDs/images, readiness, scanner và natural execution tiếp theo. Sau Windows login/reboot cần bằng chứng riêng.'])
para('Máy ngủ/hibernate/tắt có thể làm lịch local bị lỡ; WakeToRun hiện không được bật. Interactive tasks vẫn phụ thuộc LUIM đăng nhập. Không tự chuyển sang SYSTEM, đổi power policy hoặc reboot toàn bộ máy chỉ để làm một checklist xanh.')
para('Đã có bằng chứng phục hồi sau Docker restart do người dùng thực hiện. Physical reboot, trước login và lần Windows login mới chưa được qualify; hidden action được cấu hình nhưng không đồng nghĩa đã quan sát mọi khả năng cửa sổ lóe lên.')

page('31 Backup và khôi phục có kiểm soát')
para('QLDAPM-Main-Daily-Backup kiểm tra mỗi giờ/logon và tạo snapshot khi đủ 24 giờ từ last-success. Backup có PostgreSQL, Gateway/Knowledge SQLite cùng n8n/assets/config theo cơ chế hiện hữu. Các kho được snapshot nhất quán riêng; không phải một transaction atomic xuyên toàn bộ dịch vụ.')
table(['Mức chứng minh','Ý nghĩa'],[
 ('Task result 0','Launcher đã hoàn tất; có thể chỉ NOT_DUE.'),('last-success và manifest','Có snapshot hoàn tất và hashes/metadata; kiểm đúng thời điểm/phạm vi.'),
 ('Isolated restore','Kiểm bản sao trong môi trường cô lập; không ghi đè MAIN.'),('Qdrant full restore','Chưa được qualify trong gate hiện hành; task daily không sao lưu collection Qdrant.'),
 ('Cross service DR','Chưa chứng minh phục hồi atomic toàn hệ thống; không gom chung thành một PASS.')],[1.65,5.41])
sub('Kiểm tra thông thường')
steps(['Xem private operator/main-scheduled-backups/last-success.json và last-attempt.json, đối chiếu thời gian và status.',
 'Kiểm dung lượng đĩa; task cần ít nhất 5 GiB trống. Giữ các backup cũ và artifacts lỗi để điều tra.',
 'Khi cần restore, chuẩn bị isolated copy, exact image/key/config/manifest và rollback plan. Chỉ operator được phép mới thực hiện restore đúng scope.'])
para('Không mở live SQLite bằng Windows trong khi container Linux đang dùng WAL. Đọc trong owning container; Windows chỉ mở completed snapshot theo chế độ read-only phù hợp. Không xóa WAL/SHM, sửa header hoặc restore đè production để sửa lỗi đọc.')
para('Backup chứa dữ liệu nhạy cảm và có thể gồm private credentials; giữ trong private ACL, không đính kèm nguyên thư mục vào chat/Git hay phát hành kèm cẩm nang.')

page('32 Công nghệ và địa chỉ truy cập')
table(['Thành phần','Công nghệ thực tế','Truy cập hoặc vai trò'],[
 ('OpenProject','Community Core, Ruby on Rails','127.0.0.1:18088; UI/Native API/gates.'),('Dữ liệu nghiệp vụ',versions['postgres'],'PostgreSQL trong private Docker network.'),
 ('AI Gateway','Python, Starlette '+versions['gateway_packages']['starlette']+', Uvicorn '+versions['gateway_packages']['uvicorn'],'127.0.0.1:18089; auth, tools, queue, Supervisor.'),
 ('Validation','Pydantic '+versions['gateway_packages']['pydantic'],'Typed schemas, giới hạn payload và allowlists.'),('n8n',versions['n8n'],'127.0.0.1:5679; 16 published workflows.'),
 ('Knowledge text','SQLite và FTS5','Metadata, chunks, full text search và durable ledger.'),('Vector database','Qdrant '+versions['qdrant']['version'],'127.0.0.1:6333; vector 1024D và payload provenance.'),
 ('Local embedding','Ollama '+versions['ollama']['version']+' và BGE-M3','127.0.0.1:11434; không phải Gemini.'),
 ('Gemini integration','google-genai'+versions['gateway_packages']['google-genai'],'Model cấu hình gemini-3.5-flash-lite; Free-only guard.'),
 ('Tools và protocol','REST/OpenAPI và MCP SDK '+versions['gateway_packages']['mcp'],'Cùng server-side RBAC/scope; không cấp tool viết rộng hơn.'),
 ('PDF parser','pypdf '+versions['gateway_packages']['pypdf'],'Pinned file parser; không OCR.'),('Vận hành','Docker Desktop, Windows Task Scheduler','Container restart, background health, observer và backup.')],[1.25,3.05,2.76],size=10)
para('Version được đọc từ runtime ngày 29/10/2026. Cẩm nang không tự cập nhật khi nâng cấp; hãy kiểm release và config hiện hành trước khi thay image hoặc áp dụng lệnh kỹ thuật. Các cổng trên là loopback, không phải endpoint public đã được phê duyệt.')

page('33 Tích hợp API MCP và webhook')
para('API Gateway có /api/v1/commands và schema /api/v1/openapi.json; MCP cung cấp các tool được lọc theo actor và policy. REST, MCP và Core signed UI bridge dùng cùng ranh giới nghiệp vụ, không phải ba cách để né approval.')
table(['Đường gọi','Thông tin cần có','Điều không được giả định'],[
 ('Core UI','Phiên đăng nhập và signed bridge từ server','Browser gửi actor_id tự khai không cấp authority.'),('Actor webhook n8n','Webhook header credential và actor bearer','Credential n8n owner không bằng quyền PM của người gọi.'),
 ('Gateway command','action, arguments, idempotency_key khi cần','Một HTTP200 không chứng minh Native mutation đã xác nhận.'),('Machine schedule','Fixed route/key/HMAC/nonce/issued_at','Machine không được thực hiện Native writes hoặc human QA/PM decisions.'),
 ('MCP client','Authenticated session và discovered tool schema','Số tool và tên được phép tùy actor; không dùng catalog static làm bằng chứng mọi tool đều usable.')],[1.35,2.65,3.06],size=10)
sub('Mẫu chỉ đọc cho người tích hợp')
code('{\n  "action": "knowledge_incremental_status",\n  "arguments": {}\n}')
para('Chỉ dùng mẫu này qua client đã được cấp credential theo cơ chế hiện hữu; không dán token vào tài liệu. Với write, cần đọc schema live, chuẩn bị scope/hash/request ID và quy trình approval tương ứng. Không gọi trực tiếp database để bỏ API gate.')
para('Các path webhook của từng workflow và published version ID tại ngày biên soạn được ghi ở phụ lục tra cứu. Không sử dụng /webhook-test/ hoặc Execute Workflow làm production scheduled evidence.')

page('34 Bảng xử lý sự cố thường gặp')
table(['Dấu hiệu','Kiểm tra trước','Hành động tiếp theo'],[
 ('Assistant không dùng được','Login/project, Gateway và Native auth','Đăng nhập đúng tài khoản; giữ mã lỗi/run; không reset account tùy tiện.'),
 ('Đếm 57 khác 339','Task chưa hoàn thành hay tổng Work Package','Đối chiếu type/status/actor/time; tách hai câu hỏi.'),
 ('Owner chưa có Daily','Target daily có loại Owner hay không','Đọc collector READY/targets; kiểm tài khoản nghiệp vụ được cấu hình.'),
 ('Search trả nguồn cũ/thiếu','Native version, scanner timestamp, sync job','Chờ bounded sync hoặc xử lý lỗi cache; không xóa nguồn lịch sử.'),
 ('Provider blocked/chờ','Free/data consent/quota/circuit/readiness','Chờ hoặc operator kiểm cấu hình; không bỏ guard/đổi key để né quota.'),
 ('QA PASSED nhưng pending','Automated result khác review state','QA độc lập review rồi manager theo stage; không tự ký.'),
 ('Proposal409/expired','Hash, lockVersion, lifecycle','Đọc nguồn và tạo preview mới; không đổi hash bằng tay.'),
 ('n8n xanh nhưng PARTIAL','Output cuối và receipt','Xử lý business failure; không đánh PASS dựa vào nhãn Success.'),
 ('Job running sau restart','lease_until và actor job','Đợi lease/hỏi operator; không chỉnh clock/SQL để ép nhận.'),
 ('Không có execution lịch','Máy thức, LUIM/Docker/n8n active','Ghi missing observation; không chạy tay để giả natural trigger.'),
 ('Backup 0 nhưng file không mới','last-attempt NOT_DUE và last-success','Kiểm tuổi backup/thời điểm 24h, dung lượng và task trigger.'),
 ('Unknown Native outcome','Request/proposal/Native receipt','Hold và đối soát exact operation; không blind retry.')],[1.65,2.35,3.06],size=10)
para('Một báo lỗi hữu ích gồm thời điểm Asia/Bangkok, actor/role, project, run/trace/execution/job ID, target/version, expected/actual và ảnh không chứa secret. Không gửi password/token/2FA hoặc full private backup.')

page('35 Thuật ngữ và quy tắc đọc trạng thái')
table(['Thuật ngữ','Cách hiểu trong QLDAPM'],[
 ('Native','Dữ liệu, API và workflow gốc của OpenProject; nguồn nghiệp vụ cần đối soát.'),('RAG','Lấy context liên quan đã kiểm quyền/freshness để hỗ trợ câu trả lời có nguồn.'),
 ('Second Brain','Kho tài liệu/chunks/index và provenance; không tự tạo quyền hay consent.'),('Embedding','Biểu diễn vector của text; BGE-M3 hiện tạo 1024D, không phải final answer.'),
 ('FTS5','Tìm từ khóa trên SQLite; bổ trợ semantic retrieval của Qdrant.'),('Actor và scope','Danh tính được xác minh và giới hạn tài nguyên/thao tác của một yêu cầu.'),
 ('lockVersion','Phiên bản optimistic concurrency Native; đổi phiên bản có thể làm preview/context stale.'),('Hash','Dấu vân tay nội dung/spec/proposal/receipt; không phải mật khẩu hoặc quyền thực thi.'),
 ('Idempotency key','Khóa chống thực thi lặp cho cùng ý định; không cho phép thay payload tùy tiện.'),('Receipt','Bản ghi bền vững để đối soát operation/outcome; không tự là human approval.'),
 ('DRAFT NON EXECUTABLE','Draft metadata chưa được thực thi Native; cần các bước tiếp theo và approval.'),('verified','Cache job đã có kiểm chứng index/readback theo contract; không là QA nghiệm thu.'),
 ('READY COMPLETED','Business result của một collector/run; kiểm đúng namespace và nguồn.'),('HEALTHY DEGRADED','Kết quả probe tại observed_at với phạm vi đo được ghi rõ.'),
 ('Unknown outcome','Chưa biết chính xác write đã xảy ra hay chưa; giữ để đối soát, không blind replay.'),('Human UAT','Người dùng thực nghiệm thu và ký chấp nhận; browser automation không ký thay.')],[1.65,5.41],size=10)

page('36 Giới hạn hiện hành và checklist sử dụng')
para('Core automation đang vận hành với verdict AUTOMATION_CORE_E2E_PASS_WITH_LIMITATIONS. Main live UI/RAG/Gemini đã có bằng chứng riêng; fresh isolated Native change xuyên suốt tới Gemini thật vẫn thiếu TEST credential/proof được phép. Hai phần này không được ghép thành một continuous clone PASS.')
table(['Điểm đã có bằng chứng','Giới hạn cần giữ khi sử dụng'],[
 ('Main UI đọc và live PM run','Một số ảnh dùng Owner; không suy ra mọi role đều thấy cùng dữ liệu hoặc mọi specialist vừa được live-test.'),
 ('WF07 tự chạy29/10 08:00','WF12 natural30/10 17:00 vẫn chưa tới; chỉ cập nhật sau observation thật.'),('Automatic source sync','Comments bounded20/750, edit/clear audit khoảng 11 phút với snapshot 339 WPs.'),
 ('Docker restart recovery','Không suy ra Windows physical reboot/pre-login PASS.'),('Per store backup','Chưa full Qdrant/cross-service DR; không restore production để kiểm thử.'),
 ('Local delivery metadata','Chưa external SMTP/chat destination/credentials hợp lệ; BLOCKED_EXTERNAL_CONFIGURATION.'),('Automated tests và UI checks','Human UAT/sign-off vẫn là một bước riêng.')],[2.25,4.81])
sub('Checklist trước khi dựa vào một kết quả')
bullets(['Đúng tài khoản, project và scope; thời điểm dữ liệu được ghi rõ.', 'Nguồn/citation và lockVersion hiện hành; không có stale/withdrawn warning.',
 'Phân biệt deterministic/model, technical/business state và automated/human review.', 'Write có preview/hash/approval đúng quyền, receipt và Native readback.',
 'Lỗi hoặc unknown outcome được giữ để đối soát; không blind retry hay dọn lịch sử.'])
para('Các records đang được bảo toàn như WP #376 test2, Bug #371 và evidence pending_qa là dữ liệu thật/lịch sử. Hướng dẫn này không cấp phép sửa/xóa chúng để thử workflow.')

page('37 Gemini và quản lý quota')
para('Gemini sử dụng API key được giữ tại backend; người dùng nghiệp vụ không nhập key trong Assistant. Model hiện cấu hình là gemini-3.5-flash-lite, đi qua Free-only policy, data-scope authorization, central limiter và audit. Tên model trên registry không tự chứng minh một lượt gọi đã thành công; phải đọc provider receipt.')
table(['Thông tin trên Control Center','Cách sử dụng'],[
 ('Model và LIVE_SUCCESS gần nhất','Chỉ là kết quả được ghi nhận gần nhất; không phải provider đang chạy hay vừa được probe lại.'),
 ('RPM TPM RPD','Giới hạn cấu hình hiện tại 15/250000/500; backend giữ safety margin và budget. Không sửa quota để tạo PASS.'),
 ('Reserved calls/input tokens','Ledger local có countTokens/generateContent và các reservation; không thay bảng usage toàn bộ Google project.'),
 ('Provider remaining quota unavailable','Không có số dư quota được xác minh trực tiếp. Ledger không bao gồm mọi client khác hoặc mọi output token.'),
 ('WAITING QUOTA hoặc WAITING PROVIDER','Đọc run và retry policy; tránh gửi nhiều yêu cầu trùng nhau.'),
 ('BLOCKED KEY OR MODEL','Operator kiểm credential, exact proof/model/data consent và readiness; không bypass guard hoặc dùng key khác không được phép.')],[2.5,4.56],size=10.3)
para('Multi-agent không nhất thiết gọi nhiều model: ví dụ run minh họa chỉ PM gọi Gemini một lần, Supervisor/Reviewer/tổng hợp chạy local. Mỗi run vẫn có giới hạn agent count, model calls, context, token, timeout và retry được server enforce.')
para('Provider có thể nhận nội dung nghiệp vụ được phép của project để phân tích. BGE-M3 local chỉ đảm nhiệm embedding; nó không biến toàn bộ pipeline Gemini thành offline. Mọi việc cấp quyền nội dung, project/quota hoặc thay key phải qua operator hợp lệ, không qua model.')
para('Fresh continuous clone-to-Gemini cần TEST credential và proof riêng phù hợp data scope/quota. Không copy/giải mã production key sang clone hoặc mượn Staging key. Free-tier/billing dựa trên cấu hình và bằng chứng đã được chấp thuận; tài liệu không xác minh billing trực tiếp từ Google Console tại mỗi lần đọc.')

page('38 Các worker nền và bằng chứng vận hành')
table(['Tác vụ nền','Cơ chế và điều kiện','Bằng chứng nên đọc'],[
 ('AI dispatcher','Nhận durable queue, xử lý theo actor/budget; không replay tool khi interrupted outcome chưa rõ.','ai_queue, run state, trace và provider receipts.'),
 ('Knowledge consumer','Xử lý cache-refresh outbox; vòng lặp nghỉ 1 giây sau cycle, thời lượng job phụ thuộc dependency.','knowledge_sync state/attempts/error/lease_until.'),
 ('Native scanner','Cùng worker, due khoảng 60 giây khi vòng lặp có thể chạy; source/inventory/activity audit có giới hạn.','native_index_scans generation/observed_at, cursor/hash.'),
 ('Local notification delivery','process_pending trong worker; chỉ metadata/hash theo policy, có attempts/error.','Control Center counts và private receipt files; không coi là email đã gửi.'),
 ('Canonical và actor index','Sau cache job, cả canonical và actor-scoped index phải readback đúng.','document/source/chunk identity, provenance và vector_indexed.'),
 ('Delete synchronization','Chỉ signed Native delete proof/exact scope mới cho cleanup cache hợp lệ. Visibility withdrawn giữ dữ liệu.','Native receipt, delete ledger/outbox; không xóa theo source label.'),
 ('Report collectors','Daily/weekly idempotent theo ngày/tuần; source và role đọc lại.','automation_runs receipt, peractor report/hash và validator.'),
 ('Windows tasks','Health, backup và one-shotobserver đã đăng ký; interactive LUIM, hidden action.','LastTaskResult, last-success/attempt, observer latest JSON.')],[1.42,3.25,2.39],size=10)
para('Các đường private dành cho operator nằm dưới %LOCALAPPDATA%/QLDAPM/openproject-ai/operator. Natural observations ở natural-schedule-observations/*-latest.json; backup ở main-scheduled-backups/last-success.json và last-attempt.json. Chỉ đọc các file cần thiết, không chia sẻ private config/credentials.')
para('Chẩn đoán freshness phải so với observed_at, không chỉ generation lớn. Queue tăng cần xem arrival/processing/error; một snapshot không có stuck jobs không chứng minh đã chạy 24 giờ hoặc không có memory leak.')

page('39 Phụ lục path workflow và phiên bản')
para('Base n8n MAIN: http://127.0.0.1:5679. Path production webhook có prefix /webhook/. Các giá trị dưới đây là định danh, không phải secret hay authorization.')
table(['WF','Webhook path','Published version'],[(w['code'],next(n['webhook_path'] for n in live[w['code']]['nodes'] if 'webhook_path' in n),live[w['code']]['version']) for w in WORKFLOWS],[.55,2.8,3.71],size=9.4)
para('Mỗi workflow ID/version được đọc trực tiếp từ SQLite của n8n trong container sở hữu, chế độ read-only ngày 29/10/2026. Khi workflow được publish version mới, đối soát lại ID/version và contract trước khi dùng cẩm nang làm runbook kỹ thuật.')

page('40 Nguồn đối soát và bằng chứng hình ảnh')
para('Workspace triển khai: D:\\AI project\\QLDAPM chat. Nội dung hướng dẫn được đối chiếu với runtime MAIN, các module đang triển khai và tài liệu hiện hành dưới đây. Các path gateway/ và automation/ dưới đây nằm trong openproject/ai/. Tài liệu lịch sử không ghi đè contract hiện tại.')
table(['Nguồn','Nội dung được sử dụng'],[
 ('docs/ai/CODEX_FINAL_STABILIZATION_20261029.json','21 gate, live Main run/citation, Windows task limits và preservation.'),
 ('docs/ai/CODEX_AUTOMATION_STABILITY_20261029_RESULT.md','Actual clone qualification,16 workflow business contracts, bounded recovery.'),
 ('docs/ai/CODEX_FULL_PROJECT_OPERATOR_GUIDE.md','Main operations, daily backup, private observer locations và điều kiện an toàn.'),
 ('automation/deploy_real_n8n_workflows.py và live inventory','Nhánh secure_workflows, route, input validation, validators và schedules thật.'),
 ('gateway/native_incremental.py và openproject_loader.py','Scanner, source/comment freshness và actor snapshots.'),
 ('gateway/agent_registry.py, gemini.py, permissions.py','Agent roles, shared provider guard, scope và giới hạn quyền.'),
 ('gateway/native_wbs.py và Native GatePolicy','Immutable WBS/source validation, parent/calendar và transition obligations.'),
 ('gateway/daily_brief.py, weekly_report.py, monitoring.py','Target roles, daily/weekly window/dedupe và health receipt.'),
 ('Natural observer output WF07 ngày 29/10','Execution2646, version c2a7a82c…, COMPLETED/READY 5/5, receipt e9bdf13b…')],[3.1,3.96],size=10)
para('Ảnh được chụp trực tiếp từ MAIN OpenProject/n8n ngày 29/10/2026; không dựng lại giao diện, không chứa credential. Sơ đồ khối là diễn giải từ các đường gọi và gate hiện hành, không phải telemetry tự phát hiện toàn bộ kiến trúc.')
para('Bộ ảnh minh họa gồm Assistant dashboard/form, Second Brain/search/citation, Monitor và PM output, proposal preview, QA detail, permissions, n8n overview và execution graph. Các ảnh có thể hiển thị dữ liệu lịch sử đã lưu; caption và phần mô tả phân biệt với thao tác mới.')

# Table of contents links use verified PDF page numbers on the second build.
tocmap_path=ROOT/'qa/toc_pages.json';tocmap=json.loads(tocmap_path.read_text(encoding='utf-8')) if tocmap_path.exists() else {}
toc_rows=pages[2:]
parent=toc_placeholder._p.getparent();idx=parent.index(toc_placeholder._p);parent.remove(toc_placeholder._p)
for item in toc_rows:
    p=doc.add_paragraph();p.paragraph_format.space_after=Pt(2);p.paragraph_format.line_spacing=Pt(11.5)
    h=OxmlElement('w:hyperlink');h.set(qn('w:anchor'),item['bookmark']);r=OxmlElement('w:r');t=OxmlElement('w:t')
    props=OxmlElement('w:rPr');sz=OxmlElement('w:sz');sz.set(qn('w:val'),'21');props.append(sz);r.append(props)
    t.text=item['title']+'    '+str(tocmap.get(item['title'],pages.index(item)+1));r.append(t);h.append(r);p._p.append(h)
    parent.insert(idx,p._p);idx+=1
(ROOT/'source/chapters.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'source/figures.json').write_text(json.dumps(figures,ensure_ascii=False,indent=2),encoding='utf-8')
for border in list(doc.element.xpath('.//w:pBdr')):
    border.getparent().remove(border)
for border in list(doc.styles.element.xpath('.//w:pBdr')):
    border.getparent().remove(border)
doc.save(OUT)
assert len(WORKFLOWS)==16 and len({w['code'] for w in WORKFLOWS})==16
print(json.dumps({'docx':str(OUT),'planned_pages':len(pages),'figures':len(figures)},ensure_ascii=False))


