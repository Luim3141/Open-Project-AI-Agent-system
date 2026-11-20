"""Exact read intents only; mixed instructions stay on the bounded assistant path."""
import re
import time
import json
from urllib.parse import urlencode

from .gemini import Gemini
from .presentation import execution_report
from .store import canonical, digest
from .native import NativeError


def match_query(prompt):
    text = " ".join(prompt.casefold().strip().rstrip("?.!").split())
    text = re.sub(r'[?.!]\s*chỉ đọc số liệu,\s*không tạo đề xuất$', '', text)
    if text in {"đếm công việc", "đếm tổng số công việc", "có bao nhiêu công việc", "dự án có bao nhiêu công việc", "count work packages"}:
        return "count", "analyze", {}
    if text in {"thống kê công việc theo trạng thái", "thống kê số lượng công việc theo trạng thái", "thống kê trạng thái công việc"}:
        return "statuses", "analyze", {}
    if text in {"liệt kê công việc", "danh sách công việc", "liệt kê công việc trong dự án"}:
        return "list", "list_work_packages", {"limit": 30}
    if text in {"liệt kê công việc quá hạn", "danh sách công việc quá hạn"}:
        return "overdue", "analyze", {}
    if text in {'báo cáo tuần', 'báo cáo tuần này', 'tóm tắt tuần', 'weekly report'}:
        return 'weekly', 'weekly_summary', {}
    match=re.fullmatch(r"(?:hiện (?:tại|nay)\s+)?(?:dự án\s+)?(?:đang\s+)?(?:có\s+)?(?:đếm\s+)?(?:tổng\s+số\s+)?(?:bao nhiêu\s+)?(?:công việc (?:thuộc )?loại )?(công việc|task|subtask|epic|bug) (?:chưa hoàn thành|chưa xong|còn mở|đang mở|chưa đóng)",text)
    if match or text in {'count uncompleted work packages','open work packages','open tasks'}:
        noun=match[1] if match else 'task' if text=='open tasks' else 'công việc'
        return 'uncompleted','native_open_count',{'kind':{'công việc':'WorkPackage','task':'Task','subtask':'Subtask','epic':'Epic','bug':'Bug'}[noun]}
    match = re.fullmatch(r"(?:đọc|xem) công việc #?([1-9][0-9]{0,8})", text)
    if match:
        return "read", "get_work_package", {"id": int(match[1])}
    return None


def execute_query(service,who,native,route):
    if route[0] == 'weekly':
        if route[1] != 'weekly_summary' or route[2] != {}:
            raise ValueError('WEEKLY_READ_ROUTE_INVALID')
        from .weekly_report import generate_weekly_report
        users = {int(actor): {'name': f'User {actor}', 'role': role} for actor, role in service.config['users'].items()}
        return generate_weekly_report(native.packages(), users, who['user_id'], who['role'],
                                      project_id=native.project_id, with_ai_summary=False)
    if route[1]!='native_open_count':return service.perform(who,native,route[1],route[2])
    if route[0]!='uncompleted' or set(route[2])!={'kind'} or route[2]['kind'] not in {'WorkPackage','Task','Subtask','Epic','Bug'}:
        raise ValueError('NATIVE_OPEN_COUNT_ROUTE_INVALID')
    kind=route[2]['kind'];filters=[{'status':{'operator':'o','values':[]}}]
    if kind=='Bug':
        from .bug_lifecycle import mapping
        mapping(service)
    identifiers=[]
    if kind!='WorkPackage':
        types=native.collection(f'/api/v3/projects/{native.project_id}/types')
        if not isinstance(types,list) or any(not isinstance(row,dict) or type(row.get('id')) is not int or row['id']<=0 or not isinstance(row.get('name'),str) for row in types):
            raise NativeError(502,'NATIVE_TYPE_METADATA_INVALID')
        identifiers=[str(row['id']) for row in types if row['name'].casefold()==('task' if kind=='Bug' else kind.casefold())]
        if kind=='Bug' and identifiers!=['1']:raise NativeError(409,'APPROVED_BUG_TYPE_MAPPING_CHANGED')
        if not identifiers:return {'count':0,'kind':kind,'project_id':native.project_id,'filters':filters,'type_present':False}
        filters.append({'type':{'operator':'=','values':identifiers}})
    base=f'/api/v3/projects/{native.project_id}/work_packages?'
    if kind=='Bug':
        filters.append({'subject':{'operator':'~','values':['[Bug]']}})
        rows=native.collection(base+urlencode({'filters':json.dumps(filters)}))
        if not isinstance(rows,list) or any(not isinstance(row,dict) for row in rows):raise NativeError(502,'NATIVE_COUNT_METADATA_INVALID')
        count=len([row for row in rows if row.get('subject','').startswith('[Bug] ')])
        if len({row.get('id') for row in rows})!=len(rows):raise NativeError(409,'NATIVE_COUNT_SOURCE_CHANGED')
    else:
        result=native.call(base+urlencode({'filters':json.dumps(filters),'pageSize':1,'offset':1}))
        count=result.get('total');rows=result.get('_embedded',{}).get('elements')
        if type(count) is not int or count<0 or not isinstance(rows,list) or len(rows)!=min(count,1):
            raise NativeError(502,'NATIVE_COUNT_METADATA_INVALID')
    for row in rows:
        if not isinstance(row,dict):raise NativeError(502,'NATIVE_COUNT_METADATA_INVALID')
        links=row.get('_links',{})
        if (type(row.get('id')) is not int or row['id']<=0 or links.get('project',{}).get('href')!=f'/api/v3/projects/{native.project_id}' or
                identifiers and links.get('type',{}).get('href') not in {'/api/v3/types/'+value for value in identifiers}):
            raise NativeError(502,'NATIVE_COUNT_SCOPE_INVALID')
    return {'count':count,'kind':kind,'project_id':native.project_id,'filters':filters,'type_present':True}


def read_result(who, project, route, document):
    kind, action, args = route
    # Reuse the existing redacted source projection; full native responses never enter read receipts.
    projected = {'result':document} if action=='native_open_count' or kind=='weekly' else Gemini.business_result(action, {"result": document})
    data = projected["result"]
    if kind == "count":
        text = f"Dự án có {data['count']} công việc bạn được phép xem."
    elif kind == "uncompleted":
        if action!='native_open_count':raise ValueError('LEGACY_OPEN_COUNT_REQUIRES_FRESH_QUERY')
        label='công việc' if data['kind']=='WorkPackage' else data['kind']
        text = f"Dự án có {data['count']} {label} chưa hoàn thành bạn được phép xem."
    elif kind == "statuses":
        text = "Số công việc theo trạng thái: " + "; ".join(f"{name}: {count}" for name, count in sorted(data["by_status"].items())) + "."
    elif kind == "overdue":
        ids = data.get("overdue_ids", [])
        text = f"Có {len(ids)} công việc quá hạn bạn được phép xem" + (": " + ", ".join(f"#{identifier}" for identifier in ids) if ids else "") + "."
    elif kind == "list":
        text = f"Hiển thị {len(data['items'])}/{data['total']} công việc bạn được phép xem:\n" + "\n".join(f"#{row['id']}: {row['subject']}" for row in data["items"])
    elif kind == 'weekly':
        text = data['ai_summary']['text'] + '\nGiới hạn: ' + '; '.join(data['limitations'])
    else:
        text = f"Công việc #{data['id']}: {data['subject']}\nTrạng thái: {data.get('status', '')}\n{data.get('description', '')}"
    calls = [{"action": action, "arguments": args, "result": projected}]
    source_identity = projected["result"] if isinstance(projected, dict) and "result" in projected else document
    fingerprint = digest(canonical({"actor": who["user_id"], "role": who["role"], "project": project, "route": route, "source": source_identity}))
    return {**execution_report(calls), "status": "answered", "heading": "Dữ liệu trực tiếp từ OpenProject",
            "text": text, "tools": calls, "source": "native", "model_used": False, "observed_at": time.time(),
            "source_fingerprint": fingerprint, "read_route": route,
            "cache_policy": "same-request-only-after-fresh-native-ACL-and-source-match"}
