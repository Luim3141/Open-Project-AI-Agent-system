"""BA Agent: Business Analyst specialist for User Stories, Acceptance Criteria (AC),
ambiguity detection, and business dependency drafting.
Strictly read-only / advisory: never self-writes or mutates OpenProject tasks.
"""
import re
from typing import Any

from .agent_models import AgentResult, AgentTask, NativeReference, RunScope
from .planner import is_write_intent

VAGUE_PATTERNS = [
    (r"\b(thật nhanh|rất nhanh|nhanh chóng|càng nhanh càng tốt)\b", "Tiêu chí tốc độ/hiệu năng chưa được định lượng (cần quy định rõ thời gian phản hồi: ví dụ < 500ms hay < 2s)."),
    (r"\b(giao diện đẹp|đẹp mắt|hiện đại|thân thiện)\b", "Tiêu chí giao diện mang tính cảm tính (cần tham chiếu Design System hoặc Figma mockup cụ thể)."),
    (r"\b(tự hiểu|tự động|thông minh)\b", "Quy tắc nghiệp vụ tự động hóa chưa có điều kiện kích hoạt và logic xử lý rõ ràng."),
    (r"\b(xử lý tốt|tối ưu|ổn định)\b", "Chưa xác định ngưỡng tải hoặc dung sai lỗi chấp nhận được."),
]


def _get_pkg_by_id(packages: list[dict[str, Any]], pkg_id: int) -> dict[str, Any] | None:
    for p in packages:
        if p.get("id") == pkg_id:
            return p
    return None


def draft_user_story(package: dict[str, Any]) -> tuple[str, NativeReference]:
    """Formats requirement into standard User Story format with native citation."""
    pkg_id = package["id"]
    lock_ver = package["lockVersion"]
    subject = package.get("subject", "").strip()
    desc = package.get("description", {}).get("raw", "") if isinstance(package.get("description"), dict) else str(package.get("description", ""))

    role = "Người dùng hệ thống"
    if "kế toán" in desc.lower():
        role = "Kế toán viên"
    elif "quản trị" in desc.lower() or "admin" in desc.lower():
        role = "Quản trị viên"
    elif "khách hàng" in desc.lower():
        role = "Khách hàng"

    lines = [
        f"### USER STORY: #{pkg_id} — {subject}",
        f"- **Là [Vai trò]:** {role}",
        f"- **Tôi muốn [Tính năng]:** {subject.lower() if subject else 'thực hiện thao tác trên hệ thống'}",
        f"- **Để [Mục đích/Giá trị]:** đảm bảo nhu cầu nghiệp vụ được đáp ứng chính xác, minh bạch và an toàn.",
        "",
        f"> Trích dẫn dữ liệu nguồn: Work Package #{pkg_id} (lock_version: {lock_ver})",
    ]
    ref = NativeReference(work_package_id=pkg_id, lock_version=lock_ver)
    return "\n".join(lines), ref


def draft_acceptance_criteria(package: dict[str, Any]) -> tuple[str, NativeReference]:
    """Drafts structured, testable Acceptance Criteria for a work package."""
    pkg_id = package["id"]
    lock_ver = package["lockVersion"]
    subject = package.get("subject", "").strip()

    lines = [
        f"### TIÊU CHÍ CHẤP NHẬN (ACCEPTANCE CRITERIA) — #{pkg_id}",
        f"**Công việc:** {subject}",
        "",
        "**AC1 — Điều kiện tiên quyết & Giao diện:**",
        f"- **Given:** Người dùng đã đăng nhập vào hệ thống với quyền hạn hợp lệ.",
        f"- **When:** Người dùng truy cập màn hình '{subject}'.",
        f"- **Then:** Hệ thống hiển thị đầy đủ các trường thông tin cần thiết và các nút thao tác tương ứng.",
        "",
        "**AC2 — Luồng xử lý chính (Happy Path):**",
        "- **When:** Người dùng nhập dữ liệu hợp lệ và bấm xác nhận.",
        "- **Then (dự thảo):** Hệ thống lưu dữ liệu hợp lệ và phản hồi; SLA cần được chủ yêu cầu xác định, chưa có bằng chứng về ngưỡng hiệu năng.",
        "",
        "**AC3 — Xử lý ngoại lệ & Bảo mật:**",
        "- **When:** Dữ liệu đầu vào sai định dạng hoặc phiên đăng nhập hết hạn.",
        "- **Then:** Hệ thống hiển thị thông báo lỗi rõ ràng tại vị trí tương ứng và không lưu bản ghi lỗi.",
        "",
        f"> Trích dẫn dữ liệu nguồn: Work Package #{pkg_id} (lock_version: {lock_ver})",
    ]
    ref = NativeReference(work_package_id=pkg_id, lock_version=lock_ver)
    return "\n".join(lines), ref


def detect_ambiguity(package: dict[str, Any]) -> tuple[str, NativeReference]:
    """Analyzes text for vague phrases and flags clarifying questions."""
    pkg_id = package["id"]
    lock_ver = package["lockVersion"]
    subject = package.get("subject", "").strip()
    desc = package.get("description", {}).get("raw", "") if isinstance(package.get("description"), dict) else str(package.get("description", ""))
    full_text = f"{subject} {desc}"

    found_vague = []
    for pattern, explanation in VAGUE_PATTERNS:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            found_vague.append((match.group(0), explanation))

    lines = [
        f"### BÁO CÁO PHÂN TÍCH MỨC ĐỘ MƠ HỒ (AMBIGUITY REPORT) — #{pkg_id}",
        f"**Công việc:** {subject}",
        "",
    ]

    if found_vague:
        lines.append("#### 1. Các thuật ngữ mơ hồ cần chuẩn hóa:")
        for phrase, expl in found_vague:
            lines.append(f"- Cụm từ: **\"{phrase}\"**")
            lines.append(f"  - Đánh giá: {expl}")

        lines.append("\n#### 2. Câu hỏi làm rõ cho Stakeholders / PM:")
        lines.append(f"1. Tiêu chí định lượng chính xác cho '{found_vague[0][0]}' trong ngữ cảnh #{pkg_id} là gì?")
        lines.append("2. Có kịch bản ngoại lệ cụ thể nào khi điều kiện tự động hóa không thỏa mãn không?")
    else:
        lines.append("Không phát hiện thuật ngữ mơ hồ nghiêm trọng trong mô tả công việc hiện tại.")

    ref = NativeReference(work_package_id=pkg_id, lock_version=lock_ver)
    return "\n".join(lines), ref


def draft_dependencies(packages: list[dict[str, Any]]) -> tuple[str, list[NativeReference]]:
    """Analyzes business dependencies across work packages."""
    lines = ["### BÁO CÁO PHỤ THUỘC NGHIỆP VỤ (BUSINESS DEPENDENCIES)"]
    ref_map: dict[int, NativeReference] = {}

    auth_pkgs = [p for p in packages if any(k in p.get("subject", "").lower() for k in ["đăng nhập", "xác thực", "auth", "2fa"])]
    feature_pkgs = [p for p in packages if p not in auth_pkgs]

    lines.append("#### Phụ thuộc luồng xác thực & phân quyền:")
    for fp in feature_pkgs:
        desc = fp.get("description", {}).get("raw", "") if isinstance(fp.get("description"), dict) else str(fp.get("description", ""))
        desc_lower = desc.lower()
        if "đăng nhập" in desc_lower or "quyền" in desc_lower:
            for ap in auth_pkgs:
                lines.append(f"- **#{fp['id']}** ({fp['subject']}) **PHỤ THUỘC VÀO** **#{ap['id']}** ({ap['subject']})")
                ref_map[fp["id"]] = NativeReference(work_package_id=fp["id"], lock_version=fp["lockVersion"])
                ref_map[ap["id"]] = NativeReference(work_package_id=ap["id"], lock_version=ap["lockVersion"])

    if not ref_map:
        for p in packages[:3]:
            ref_map[p["id"]] = NativeReference(work_package_id=p["id"], lock_version=p["lockVersion"])
        lines.append("- Các công việc đang hoạt động độc lập hoặc chưa ghi nhận ràng buộc trực tiếp.")

    return "\n".join(lines), list(ref_map.values())


class BAAgent:
    """BA Agent specialist providing User Story structuring, Acceptance Criteria drafting,

    ambiguity analysis, and business dependency mapping.
    Enforces strict read-only/advisory contract: never self-writes to OpenProject.
    """

    def run(
        self,
        task: AgentTask,
        scope: RunScope,
        packages: list[dict[str, Any]],
        provider=None,
    ) -> AgentResult:
        if provider is not None:
            return provider.run_agent('ba',task,scope,packages)
        instruction = task.instruction
        pkg_map = {p["id"]: p for p in packages}

        # STRICT RULE: Refuse direct task modification/writing; strictly advisory
        if is_write_intent(instruction):
            cited_ids = [int(m) for m in re.findall(r"#(\d+)", instruction)]
            references = []
            for cid in cited_ids:
                if cid in pkg_map:
                    references.append(NativeReference(work_package_id=cid, lock_version=pkg_map[cid]["lockVersion"]))
            if not references and task.references:
                references = list(task.references)

            summary = (
                "BA Agent chỉ phân tích và soạn thảo tài liệu nghiệp vụ (User Story, AC, Ambiguity, Phụ thuộc), "
                "tuyệt đối KHÔNG tự ý ghi hoặc cập nhật trực tiếp dữ liệu vào OpenProject. "
                "Nội dung đã được biên soạn dưới dạng bản dự thảo đề xuất (Proposal Draft) và chuyển giao để PM "
                "phê duyệt theo chính sách PM-only-write trước khi áp dụng.\n"
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

        if "user story" in instr_lower or "story" in instr_lower:
            if target_pkg:
                summary, ref = draft_user_story(target_pkg)
                references = [ref]
            else:
                summary = "Không tìm thấy công việc mục tiêu để soạn thảo User Story."
                references = []

        elif "ac" in instr_lower or "tiêu chí" in instr_lower or "acceptance" in instr_lower:
            if target_pkg:
                summary, ref = draft_acceptance_criteria(target_pkg)
                references = [ref]
            else:
                summary = "Không tìm thấy công việc mục tiêu để soạn thảo tiêu chí chấp nhận."
                references = []

        elif "mơ hồ" in instr_lower or "làm rõ" in instr_lower or "ambiguity" in instr_lower:
            if target_pkg:
                summary, ref = detect_ambiguity(target_pkg)
                references = [ref]
            else:
                summary = "Không tìm thấy công việc mục tiêu để phân tích độ mơ hồ."
                references = []

        elif "phụ thuộc" in instr_lower or "dependency" in instr_lower:
            summary, references = draft_dependencies(packages)

        else:
            if target_pkg:
                s1, r1 = draft_user_story(target_pkg)
                s2, _ = draft_acceptance_criteria(target_pkg)
                summary = f"{s1}\n\n{s2}"
                references = [r1]
            else:
                summary, references = draft_dependencies(packages)

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
