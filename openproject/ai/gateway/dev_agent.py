"""DEV Agent: Technical requirements analyst for QLDAPM work packages.
Provides FE/BE task breakdown, technical dependencies, and architecture/concurrency risks.
Strictly prohibited from running shell commands or GitHub web research,
and never self-mutates OpenProject tasks.
"""
import re
from typing import Any

from .agent_models import AgentResult, AgentTask, NativeReference, RunScope
from .planner import is_write_intent

FORBIDDEN_KEYWORDS = re.compile(
    r"(?i)\b(shell|bash|sh|cmd|powershell|terminal|git clone|clone repo|github\.com|curl|wget|exec|eval)\b"
)


def breakdown_fe_be(package: dict[str, Any]) -> tuple[str, NativeReference]:
    """Decomposes a work package into distinct Frontend (FE) and Backend (BE) technical tasks."""
    pkg_id = package["id"]
    lock_ver = package["lockVersion"]
    subject = package.get("subject", "").strip()

    lines = [
        f"### PHÂN RÃ KỸ THUẬT FE / BE (TECHNICAL BREAKDOWN) — #{pkg_id}",
        f"**Công việc mục tiêu:** {subject}",
        "",
        "#### 1. FRONTEND (FE) — Trách nhiệm triển khai giao diện & tương tác:",
        f"- **Component & Giao diện:** Thiết kế màn hình, component hiển thị cho '{subject}' tuân thủ Design Tokens.",
        "- **Form Validation & State:** Xử lý kiểm tra dữ liệu đầu vào phía client và quản lý trạng thái tải/lỗi.",
        "- **Tích hợp API:** Kết nối API client, xử lý hiển thị feedback và retry khi gặp lỗi mạng.",
        "",
        "#### 2. BACKEND (BE) — Trách nhiệm dịch vụ & lưu trữ dữ liệu:",
        "- **API Endpoint:** Định nghĩa RESTful API endpoint, xác thực Bearer token và kiểm tra RBAC người gọi.",
        "- **Service & Nghiệp vụ:** Triển khai tầng xử lý logic nghiệp vụ, bảo đảm tính toàn vẹn dữ liệu.",
        "- **Database & Migration:** Thiết kế schema, khóa lạc quan (lock_version) ngăn chặn race condition.",
        "",
        f"> Trích dẫn dữ liệu nguồn: Work Package #{pkg_id} (lock_version: {lock_ver})",
    ]
    ref = NativeReference(work_package_id=pkg_id, lock_version=lock_ver)
    return "\n".join(lines), ref


def identify_technical_dependencies(package: dict[str, Any]) -> tuple[str, NativeReference]:
    """Maps technical dependencies, API schema contracts, and migration sequencing."""
    pkg_id = package["id"]
    lock_ver = package["lockVersion"]
    subject = package.get("subject", "").strip()

    lines = [
        f"### PHỤ THUỘC KỸ THUẬT & HỢP ĐỒNG API (TECHNICAL DEPENDENCIES) — #{pkg_id}",
        f"**Công việc:** {subject}",
        "",
        "#### Thứ tự triển khai kỹ thuật (Sequencing):",
        "1. **Tầng Database / Schema:** Áp dụng migration DB trước khi deploy code mới.",
        "2. **Tầng Backend API Contract:** Hoàn thành và bàn giao OpenAPI / schema hợp đồng REST API.",
        "3. **Tầng Frontend Client:** Triển khai UI dựa trên API contract đã thống nhất.",
        "",
        "#### Ràng buộc hợp đồng API (API Contract Guidelines):",
        "- Định dạng dữ liệu: Chuẩn JSON với HTTP status codes rõ ràng (200, 201, 400, 401, 403, 409, 422, 500).",
        "- Kiểm soát khóa lạc quan: Mọi thao tác cập nhật (PATCH/PUT) bắt buộc truyền `lock_version`.",
        "",
        f"> Trích dẫn dữ liệu nguồn: Work Package #{pkg_id} (lock_version: {lock_ver})",
    ]
    ref = NativeReference(work_package_id=pkg_id, lock_version=lock_ver)
    return "\n".join(lines), ref


def evaluate_technical_risks(package: dict[str, Any]) -> tuple[str, NativeReference]:
    """Analyzes technical risks such as concurrency conflicts, locking, and performance bounds."""
    pkg_id = package["id"]
    lock_ver = package["lockVersion"]
    subject = package.get("subject", "").strip()
    desc = package.get("description", {}).get("raw", "") if isinstance(package.get("description"), dict) else str(package.get("description", ""))

    lines = [
        f"### ĐÁNH GIÁ RỦI RO KỸ THUẬT (TECHNICAL RISKS) — #{pkg_id}",
        f"**Công việc:** {subject}",
        "",
        "#### 1. Rủi ro xử lý đồng thời & Xung đột khóa (Concurrency Conflict / HTTP 409):",
        "- **Phân tích:** Khi nhiều người dùng hoặc tiến trình cập nhật cùng một work package, có nguy cơ xung đột `lock_version` (HTTP 409).",
        "- **Giải pháp:** Sử dụng cơ chế khóa lạc quan (optimistic locking), yêu cầu client đọc lại (readback) dữ liệu mới nhất trước khi thử lại.",
        "",
        "#### 2. Rủi ro hiệu năng & Giới hạn tài nguyên (Performance Bounds):",
        "- Tránh các truy vấn N+1 khi duyệt danh sách công việc lớn; tận dụng collection batching và pagination tối đa 30-50 items.",
        "- Đảm bảo transaction thời gian ngắn, không giữ connection database trong khi chờ xử lý LLM.",
        "",
        f"> Trích dẫn dữ liệu nguồn: Work Package #{pkg_id} (lock_version: {lock_ver})",
    ]
    ref = NativeReference(work_package_id=pkg_id, lock_version=lock_ver)
    return "\n".join(lines), ref


class DEVAgent:
    """DEV Agent specialist providing technical analysis, FE/BE breakdown,

    technical dependency mapping, and concurrency risk assessment for QLDAPM.
    Strictly prohibited from running shell commands or GitHub web research,
    and never self-mutates OpenProject tasks.
    """

    def __init__(self, agent='dev'):
        if agent not in {'dev','fe','be'}:
            raise ValueError('TECHNICAL_AGENT_UNKNOWN')
        self.agent = agent

    def run(
        self,
        task: AgentTask,
        scope: RunScope,
        packages: list[dict[str, Any]],
        provider=None,
    ) -> AgentResult:
        if provider is not None:
            if FORBIDDEN_KEYWORDS.search(task.instruction):
                raise PermissionError('BUSINESS_OPERATOR_TOOL_DENIED')
            return provider.run_agent(self.agent,task,scope,packages)
        instruction = task.instruction
        pkg_map = {p["id"]: p for p in packages}

        # STRICT SECURITY RULE: Prohibit shell, terminal, git clone, and GitHub web research
        if FORBIDDEN_KEYWORDS.search(instruction):
            summary = (
                "Yêu cầu bị từ chối: DEV Business Agent trong hệ thống QLDAPM hoạt động hoàn toàn "
                "trong ranh giới dự án cục bộ, nghiêm cấm thực thi lệnh shell, terminal, git clone hoặc "
                "research GitHub bên ngoài. Mọi phân tích kỹ thuật được giới hạn trong phạm vi dữ liệu "
                "Work Package và tài liệu kiến trúc nội bộ của QLDAPM."
            )
            return AgentResult(
                run_id=scope.run_id,
                task_id=scope.task_id,
                actor_id=scope.actor_id,
                project_id=scope.project_id,
                trace_id=scope.trace_id,
                state="COMPLETED",
                summary=summary,
                references=[],
                receipt_ids=[],
                model_used=False,
            )

        # STRICT RULE: Refuse direct task creation or code mutation
        if is_write_intent(instruction):
            cited_ids = [int(m) for m in re.findall(r"#(\d+)", instruction)]
            references = []
            for cid in cited_ids:
                if cid in pkg_map:
                    references.append(NativeReference(work_package_id=cid, lock_version=pkg_map[cid]["lockVersion"]))
            if not references and task.references:
                references = list(task.references)

            summary = (
                "DEV Agent chỉ phân tích kỹ thuật và lập kế hoạch phân rã FE/BE; "
                "tuyệt đối KHÔNG tự ý tạo task, subtask hay chỉnh sửa trực tiếp dữ liệu trong OpenProject. "
                "Nội dung phân rã đã được ghi nhận dưới dạng bản dự thảo đề xuất (Proposal Draft) cần phê duyệt "
                "bởi PM theo chính sách PM-only-write trước khi tạo các đầu việc thực tế.\n"
                f"- Các công việc liên quan: {', '.join(f'#{r.work_package_id} (lock_version: {r.lock_version})' for r in references)}"
            )

            return AgentResult(
                run_id=scope.run_id,
                task_id=scope.task_id,
                actor_id=scope.actor_id,
                project_id=scope.project_id,
                trace_id=scope.trace_id,
                state="REVIEW",
                summary=summary,
                references=references,
                receipt_ids=[],
                model_used=False,
            )

        # READ / ANALYSIS FLOW
        instr_lower = instruction.lower()
        target_ids = [int(m) for m in re.findall(r"#(\d+)", instruction)]
        target_pkg = pkg_map.get(target_ids[0]) if target_ids else (packages[0] if packages else None)

        if "chia" in instr_lower or "breakdown" in instr_lower or "fe" in instr_lower or "be" in instr_lower:
            if target_pkg:
                summary, ref = breakdown_fe_be(target_pkg)
                references = [ref]
            else:
                summary = "Không tìm thấy công việc mục tiêu để phân rã kỹ thuật FE/BE."
                references = []

        elif "phụ thuộc" in instr_lower or "contract" in instr_lower or "api" in instr_lower:
            if target_pkg:
                summary, ref = identify_technical_dependencies(target_pkg)
                references = [ref]
            else:
                summary = "Không tìm thấy công việc mục tiêu để xác định phụ thuộc kỹ thuật."
                references = []

        elif "rủi ro" in instr_lower or "đồng thời" in instr_lower or "xung đột" in instr_lower or "concurrency" in instr_lower:
            if target_pkg:
                summary, ref = evaluate_technical_risks(target_pkg)
                references = [ref]
            else:
                summary = "Không tìm thấy công việc mục tiêu để đánh giá rủi ro kỹ thuật."
                references = []

        else:
            if target_pkg:
                s1, ref = breakdown_fe_be(target_pkg)
                s2, _ = evaluate_technical_risks(target_pkg)
                summary = f"{s1}\n\n{s2}"
                references = [ref]
            else:
                summary = "Không có công việc hợp lệ để phân tích kỹ thuật."
                references = []

        return AgentResult(
            run_id=scope.run_id,
            task_id=scope.task_id,
            actor_id=scope.actor_id,
            project_id=scope.project_id,
            trace_id=scope.trace_id,
            state="COMPLETED",
            summary=summary,
            references=references,
            receipt_ids=[],
            model_used=False,
        )
