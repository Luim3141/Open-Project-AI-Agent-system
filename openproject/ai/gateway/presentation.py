"""User-facing operation facts come from receipts, never the model's claim of success."""
import re

WRITE_ACTIONS = {"delete_work_package", "update_dependency", "delete_dependency", "create_dependency", "create_work_package", "update_work_package", "comment", "transition"}
ACTION_LABELS = {"delete_work_package":"Xóa vĩnh viễn Task Native", "update_dependency":"Đổi lag dependency Native", "delete_dependency":"Xóa relation dependency Native", "create_dependency":"Tạo dependency Native", "create_work_package": "Tạo công việc", "update_work_package": "Cập nhật công việc",
                 "comment": "Thêm bình luận", "transition": "Chuyển trạng thái",
                 "get_work_package": "Đọc công việc", "list_work_packages": "Tìm công việc",
                 "analyze": "Phân tích dự án", "get_project_options": "Đọc loại công việc và workflow"}
FIELD_LABELS = {"subject": "Tên công việc", "description": "Mô tả", "start_date": "Ngày bắt đầu", "due_date": "Hạn hoàn thành",
                "assignee_id": "Người phụ trách", "assignee_role": "Vai trò phụ trách", "priority_id": "Ưu tiên",
                "status_id": "Trạng thái", "parent_id": "Công việc cha", "type_id": "Loại công việc", "text": "Bình luận"}


def requested_ids(prompt):
    # Comment text is data: an ID inside the new comment cannot expand execution scope.
    head = re.split(r"(?<=\d)\s*:\s*", prompt, maxsplit=1)[0] if re.search(r"comment|bình luận", prompt, re.I) else prompt
    ids = re.findall(r"(?:công\s*việc|work[\s_-]*packages?|tickets?|subtasks?|tasks?|epics?|\bid)\s*(?:id\s*[=:]?\s*)?#?\s*(\d+(?:\s*(?:,|và|and|&)\s*#?\d+)*)|#(\d+)|/work_packages/(\d+)", head, re.I)
    return list(dict.fromkeys(int(number) for match in ids for number in re.findall(r"\d+", next(value for value in match if value)) if int(number) > 0))


def action_requested(prompt, action):
    prefix = re.split(r"(?<=\d)\s*:\s*", prompt, maxsplit=1)[0]
    # Comment bodies and quoted ticket text cannot authorize additional actions.
    head = prefix if re.search(r"comment|bình luận|\b(đọc|xem|read|summarize)\b", prefix, re.I) else prompt
    patterns = {"create_work_package": r"\b(tạo|create|chia|tách|phân rã|lập backlog|thêm công việc|thêm task|thêm subtask)\b",
                "update_work_package": r"\b(sửa|cập nhật|update|set|đặt|gán|assign|đổi|giao|dời|gia hạn|lên lịch)\b|\bthêm\s+(deadline|hạn|ngày)\b|\bchuyển\b.*\b(BE|FE|BA|BA-PM|PM|QA|người phụ trách)\b",
                "comment": r"\b(comment|bình luận)\b", "transition": r"\b(chuyển|transition|move|đánh dấu|đổi trạng thái)\b"}
    return bool(re.search(patterns.get(action, r"(?!)"), head, re.I))


def safe_text(value, key=None):
    text = str(value or "")
    if key:
        text = text.replace(key, "[Đã ẩn API key]")
    text = re.sub(r"-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----", "[Đã ẩn private key]", text, flags=re.S)
    text = re.sub(r'''\b(?:AIza[\w-]{20,}|sk-[\w-]{20,})\b|(?:password|api.?key|(?:access|refresh)[_. -]?token|token|secret|authorization)\s*[:=]\s*(?:"[^"]*"|'[^']*'|(?:(?:Bearer|Basic)\s+)?[^\s,;]+)|\bBearer\s+[A-Za-z0-9._~+/=-]{8,}''', "[Đã ẩn thông tin xác thực]", text, flags=re.I)
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\b\d{10,19}\b", "[Đã ẩn thông tin cá nhân]", text)
    return text


def error_info(error):
    code = str(error)
    status = getattr(error, "status", None)
    unknown = (status in {502, 503, 504} or "READBACK" in code) and getattr(error, "source", None) in {"gateway", "openproject"}
    if unknown or "OUTCOME_UNKNOWN" in code:
        message = "Chưa xác định được kết quả do kết nối/readback lỗi. Kiểm tra công việc trước khi gửi lại để tránh ghi trùng."
    elif "OUTSIDE_USER_SCOPE" in code:
        message = "ID công việc chưa nằm trong phạm vi bạn cho phép. Ghi rõ ID trong câu lệnh hoặc ô phạm vi."
    elif "NOT_REQUESTED" in code:
        message = "Thao tác này chưa được bạn yêu cầu rõ ràng; AI không tự thực hiện."
    elif "ADMIN_TOKEN" in code or "USER_NOT_REGISTERED" in code:
        message = "Tài khoản này chưa được đăng ký để thao tác AI. Hãy dùng tài khoản thành viên dự án."
    elif "STALE" in code or status == 409:
        message = "Công việc vừa được thay đổi. Đọc lại phiên bản mới trước khi duyệt hoặc sửa."
    elif status == 404:
        message = "Không tìm thấy công việc trong dự án bạn được phép truy cập."
    elif isinstance(error, PermissionError) or status in {401, 403}:
        message = "Quyền hiện tại không cho phép thao tác này. AI không thay quyền hoặc bỏ qua workflow."
    elif "DATA_SCOPE" in code:
        message = "Nội dung chứa dữ liệu ngoài phạm vi được phép, thông tin cá nhân hoặc thông tin xác thực."
    elif "QUOTA" in code or "EXHAUSTED" in code or "CIRCUIT" in code:
        message = "Gemini đang chờ quota hoặc cooldown. Các thao tác đã có receipt vẫn được giữ, không tự gửi lại."
    elif "AI_BUSY" in code:
        message = "Một yêu cầu AI đang chạy. Chờ kết quả hiện tại trước khi gửi yêu cầu mới."
    elif "DISABLED" in code:
        message = "Gemini chưa được bật hoặc quyền sử dụng/key chưa hợp lệ."
    elif code == "OPENPROJECT_FORM_REJECTED":
        labels = {"parent": "Công việc cha", "type": "Loại công việc", "subject": "Tên công việc",
                  "status": "Trạng thái", "assignee": "Người phụ trách", "description": "Mô tả"}
        message = "OpenProject chưa chấp nhận: " + "; ".join(labels.get(field, field) + " — " + safe_text(row.get("message", "Không hợp lệ"))
            for field, row in (getattr(error, "details", None) or {}).items())
        if "PropertyIsReadOnly" in str(getattr(error, "details", "")) and "parent" in (error.details or {}):
            message += " Tài khoản cần quyền quản lý Subtask để đặt công việc cha."
    elif "INVALID_ARGUMENTS" in code:
        message = "Tham số công cụ chưa đúng. Dùng đúng các trường được mô tả trong tool, không tự thêm trường."
    elif "SOURCE_ID_REQUIRED" in code:
        message = "Mã nguồn chỉ nhận chữ, số, gạch dưới/gạch ngang, tối đa 80 ký tự; có thể bỏ trống để hệ thống tự sinh."
    elif "DUE_DATE_INVALID" in code:
        message = "Hạn hoàn thành cần có định dạng YYYY-MM-DD hoặc null để xóa hạn."
    elif "START_DATE_INVALID" in code:
        message = "Ngày bắt đầu cần có định dạng YYYY-MM-DD hoặc null để xóa ngày."
    elif "DATE_RANGE_INVALID" in code:
        message = "Ngày bắt đầu phải trước hoặc bằng hạn hoàn thành; chưa ghi thay đổi."
    elif "CHANGES_REQUIRED" in code:
        message = "Cần chỉ rõ thông tin muốn sửa: tên, mô tả, người phụ trách, hạn hoàn thành hoặc ưu tiên."
    elif "ASSIGNEE_ROLE" in code or "ASSIGNEE_DENIED" in code:
        message = "Người phụ trách phải là thành viên dự án; vai trò hỗ trợ: BA-PM, PM, BE, FE, QA."
    elif status == 422 and getattr(error, "source", None) == "openproject":
        message = "OpenProject không chấp nhận thay đổi: " + safe_text(code.removeprefix("OPENPROJECT_422: "))
    elif "DEADLINE" in code or "TIMEOUT" in code:
        message = "Yêu cầu đã hết thời gian chờ. Receipt đã nhận được vẫn được giữ; kiểm tra kết quả trước khi gửi lại."
    elif "CLAIM_SOURCE_INVALID" in code:
        message = "Gemini trả thông tin không khớp dẫn chứng nên câu trả lời bị từ chối. Kết quả thao tác đã có receipt vẫn được giữ."
    elif getattr(error, "source", None) == "gemini":
        message = "Gemini chưa hoàn tất câu trả lời do lỗi dịch vụ hoặc định dạng. Kết quả thao tác đã có receipt vẫn được giữ."
    else:
        message = "Không thực hiện được vì dữ liệu hoặc điều kiện workflow chưa hợp lệ. Xem chi tiết để kiểm tra."
    info = {"error": type(error).__name__, "message": message, "outcome_unknown": unknown,
            "source": getattr(error, "source", "gateway"), "status": status}
    if code == "OPENPROJECT_FORM_REJECTED":
        info["details"] = {field: {"message": safe_text(row.get("message", "")), "code": safe_text(row.get("errorIdentifier", ""))}
                           for field, row in (error.details or {}).items()}
    return info


def execution_report(calls, explanation="", claims=None, in_progress=False):
    outcomes = []
    for call in calls:
        action, args, document = call["action"], call.get("arguments", {}), call.get("result", {})
        source = document.get("result") if isinstance(document, dict) else None
        identifier = args.get("id")
        if action == "create_work_package" and isinstance(source, dict):
            identifier = source.get("id") if type(source.get("id")) is int else None
        title = ACTION_LABELS.get(action, action) + (f" #{identifier}" if type(identifier) is int else "")
        if document.get("error"):
            state = "unknown" if document.get("outcome_unknown") else "failed"
            detail = document.get("message", "Thao tác chưa thành công.")
        elif isinstance(source, dict) and source.get("human_confirmation_required") is True:
            state, detail = "proposed", "Đã chuẩn bị thay đổi; chưa ghi. Bạn cần xem trước và duyệt."
        elif action in WRITE_ACTIONS:
            if isinstance(source, dict) and source.get("native_confirmed") is True:
                state, detail = "succeeded", "OpenProject đã xác nhận kết quả."
                if action == "comment":
                    detail += " Bình luận: “" + safe_text(args.get("text")) + "”."
                elif action == "create_work_package":
                    detail += " Đã tạo “" + safe_text(source.get("subject") or args.get("subject")) + "”."
                    if args.get("parent_id"):
                        detail += f" Công việc cha: #{args['parent_id']}."
                elif action == "transition":
                    detail += " Trạng thái mới: " + safe_text(source.get("status") or f"ID {args.get('status_id')}") + "."
                elif action == "update_work_package":
                    fields = []
                    for name, value in args.get("changes", {}).items():
                        adjustment = source.get("date_adjustments", {}).get(name)
                        shown = safe_text(value)[:600]
                        if adjustment:
                            shown = safe_text(adjustment["actual"]) + " (OpenProject điều chỉnh từ " + safe_text(adjustment["requested"]) + " theo lịch làm việc)"
                        fields.append(FIELD_LABELS.get(name, name) + ": " + shown)
                    for name, adjustment in source.get("date_adjustments", {}).items():
                        if name not in args.get("changes", {}):
                            fields.append(FIELD_LABELS.get(name, name) + ": " + safe_text(adjustment["actual"]) + " (OpenProject tự tính theo lịch và thời lượng công việc)")
                    detail += " Đã cập nhật: " + "; ".join(fields) + "."
            else:
                state, detail = "unknown", "Chưa có xác nhận kết quả từ OpenProject; không báo đã thực hiện."
        else:
            state, detail = "read", "Đã đọc dữ liệu theo quyền của bạn."
        outcomes.append({"action": action, "title": title, "state": state, "detail": detail,
                         "work_package_id": identifier if type(identifier) is int else None,
                         "proposal_id": source.get("id") if state == "proposed" else None})
    writes = [row for row in outcomes if row["action"] in WRITE_ACTIONS]
    failed = [row for row in outcomes if row["state"] in {"failed", "unknown"}]
    succeeded = [row for row in writes if row["state"] == "succeeded"]
    proposed = [row for row in writes if row["state"] == "proposed"]
    state = "partial" if failed and (succeeded or proposed) else "failed" if failed else "proposed" if proposed else "succeeded" if succeeded else "answered"
    headings = {"partial": "Hoàn thành một phần", "failed": "Chưa thực hiện được", "proposed": "Có thay đổi chờ bạn duyệt",
                "succeeded": "Đã thực hiện thành công", "answered": "Đã đọc và phân tích"}
    if writes or failed:
        text = "\n".join(row["title"] + ": " + row["detail"] for row in outcomes if row["action"] in WRITE_ACTIONS or row["state"] in {"failed", "unknown"})
    else:
        text = safe_text(explanation)
        if not text:
            lines = []
            for claim in claims or []:
                label = "Số công việc" if claim["path"] == ["result", "count"] else "Công việc quá hạn" if claim["path"] == ["result", "overdue_count"] else ACTION_LABELS.get(claim["action"], "Dữ liệu đã đọc")
                lines.append(f"{label}: {claim['value']} [nguồn #{claim['tool']}]")
            text = "\n".join(lines) or ("Đang xử lý yêu cầu; dữ liệu đã đọc được giữ để thực hiện bước tiếp theo." if in_progress else "Gemini chưa cung cấp kết luận cho yêu cầu này.")
    return {"status": state, "heading": headings[state], "text": text, "outcomes": outcomes}
