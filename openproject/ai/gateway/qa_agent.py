"""QA Agent: Quality Assurance specialist for test cases generation,
regression gaps detection, bug triage, and evidence-based test attestation reporting.
Strictly read-only / advisory: never claims tests PASS without execution evidence,
and never self-mutates OpenProject tasks.
"""
import re
from dataclasses import dataclass, field
from typing import Any

from .agent_models import AgentResult, AgentTask, NativeReference, RunScope
from .planner import is_write_intent

_REPORT_ISSUER = object()


@dataclass(frozen=True)
class VerifiedTestReport:
    """In-process result of the authenticated runner verifier; JSON flags cannot construct it."""
    issuer: object = field(repr=False)
    actor_id: int
    project_id: int
    native_id: int
    version: int
    run_id: str
    verdict: str
    runner: str
    finished_at: float
    artifact_sha256: str

    def __post_init__(self):
        if self.issuer is not _REPORT_ISSUER:
            raise PermissionError('VERIFIED_RUNNER_REPORT_REQUIRED')


def generate_test_cases(package: dict[str, Any]) -> tuple[str, NativeReference]:
    """Generates structured test cases (Positive, Negative, Boundary, Security) for a work package."""
    pkg_id = package["id"]
    lock_ver = package["lockVersion"]
    subject = package.get("subject", "").strip()

    lines = [
        f"### KỊCH BẢN KIỂM THỬ (TEST CASES) — #{pkg_id}",
        f"**Công việc mục tiêu:** {subject}",
        "",
        "#### TC-01 [Chức năng / Happy Path]: Thực hiện luồng thành công với dữ liệu hợp lệ",
        "- **Tiền điều kiện:** Người dùng đã xác thực vào hệ thống với vai trò được phép.",
        "- **Các bước:**",
        f"  1. Điều hướng đến tính năng '{subject}'.",
        "  2. Điền đầy đủ dữ liệu hợp lệ theo biểu mẫu.",
        "  3. Nhấn nút gửi/xác nhận.",
        "- **Kết quả kỳ vọng:** Thao tác thành công, hệ thống lưu bản ghi và hiển thị thông báo phản hồi.",
        "",
        "#### TC-02 [Ngoại lệ / Dữ liệu ranh giới]: Kiểm tra validation khi thiếu trường hoặc vượt giới hạn",
        "- **Tiền điều kiện:** Người dùng mở biểu mẫu nhập liệu.",
        "- **Các bước:**",
        "  1. Để trống các trường bắt buộc hoặc nhập chuỗi vượt độ dài cho phép.",
        "  2. Nhấn xác nhận.",
        "- **Kết quả kỳ vọng:** Hệ thống hiển thị thông báo lỗi tương ứng tại từng trường, ngăn chặn gửi form.",
        "",
        "#### TC-03 [Bảo mật & Phân quyền]: Truy cập trái phép không có token hoặc quyền hạn thấp hơn",
        "- **Tiền điều kiện:** Không gửi Bearer token hoặc dùng tài khoản không có vai trò hợp lệ.",
        "- **Các bước:** Gửi request đến API/chức năng.",
        "- **Kết quả kỳ vọng:** Hệ thống từ chối truy cập (HTTP 401 Unauthorized hoặc HTTP 403 Forbidden).",
        "",
        f"> Trích dẫn dữ liệu nguồn: Work Package #{pkg_id} (lock_version: {lock_ver})",
    ]
    ref = NativeReference(work_package_id=pkg_id, lock_version=lock_ver)
    return "\n".join(lines), ref


def detect_regression_gaps(packages: list[dict[str, Any]]) -> tuple[str, list[NativeReference]]:
    """Identifies work packages lacking test coverage or posing regression risks."""
    lines = ["### BÁO CÁO KHOẢNG TRỐNG KIỂM THỬ HỒI QUY (REGRESSION GAPS)"]
    ref_map: dict[int, NativeReference] = {}

    gaps = []
    for p in packages:
        desc = p.get("description", {}).get("raw", "") if isinstance(p.get("description"), dict) else str(p.get("description", ""))
        desc_lower = desc.lower()
        subject_lower = p.get("subject", "").lower()
        p_type = p.get("_links", {}).get("type", {}).get("title", "")

        is_gap = False
        reasons = []

        if "chưa có kịch bản" in desc_lower or "chưa có test" in desc_lower:
            is_gap = True
            reasons.append("Thiếu kịch bản kiểm thử đơn vị & tích hợp")
        if "chưa chạy kiểm thử" in desc_lower or "chưa chạy test" in desc_lower:
            is_gap = True
            reasons.append("Chưa thực thi kiểm thử hồi quy trước khi hợp nhất")
        if p_type == "Bug" and any(w in desc_lower or w in subject_lower for w in ["500", "sập", "crash", "critical"]):
            is_gap = True
            reasons.append("Lỗi nghiêm trọng (Crash/500) cần bổ sung regression test case để chặn tái diễn")

        if is_gap:
            ref = NativeReference(work_package_id=p["id"], lock_version=p["lockVersion"])
            ref_map[p["id"]] = ref
            gaps.append((p, reasons))

    if gaps:
        lines.append("Phát hiện các công việc có nguy cơ hồi quy cao do thiếu kiểm thử:")
        for p, reasons in gaps:
            lines.append(f"- **#{p['id']}** ({p['subject']})")
            for r in reasons:
                lines.append(f"  - Cảnh báo: {r}")
    else:
        lines.append("Không phát hiện khoảng trống kiểm thử hồi quy đáng kể trong phạm vi kiểm tra.")
        if packages:
            ref_map[packages[0]["id"]] = NativeReference(work_package_id=packages[0]["id"], lock_version=packages[0]["lockVersion"])

    return "\n".join(lines), list(ref_map.values())


def triage_bug(package: dict[str, Any]) -> tuple[str, NativeReference]:
    """Triages a defect, evaluating severity, impact, reproduction steps, and blast radius."""
    pkg_id = package["id"]
    lock_ver = package["lockVersion"]
    subject = package.get("subject", "").strip()
    desc = package.get("description", {}).get("raw", "") if isinstance(package.get("description"), dict) else str(package.get("description", ""))
    desc_lower = f"{subject} {desc}".lower()

    if any(k in desc_lower for k in ["sập", "crash", "500", "mất dữ liệu", "data loss", "deadlock"]):
        severity = "CRITICAL (NGHIÊM TRỌNG CAO)"
        priority_rec = "Immediate (Ưu tiên xử lý ngay)"
    elif any(k in desc_lower for k in ["lỗi logic", "không lưu", "sai số", "không hiển thị"]):
        severity = "HIGH (CAO)"
        priority_rec = "High (Xử lý trong Sprint hiện tại)"
    else:
        severity = "MEDIUM (TRUNG BÌNH)"
        priority_rec = "Normal (Xử lý theo kế hoạch backlog)"

    lines = [
        f"### KẾT QUẢ PHÂN LOẠI VÀ ĐÁNH GIÁ LỖI (BUG TRIAGE) — #{pkg_id}",
        f"**Tiêu đề lỗi:** {subject}",
        f"- **Mức độ nghiêm trọng (Severity):** {severity}",
        f"- **Đề xuất mức ưu tiên (Recommended Priority):** {priority_rec}",
        "",
        "#### Phân tích nguyên nhân và phạm vi ảnh hưởng:",
        f"- **Mô tả hành vi lỗi:** {desc[:200] if desc else 'Không có mô tả chi tiết'}",
        "- **Phạm vi tác động (Blast Radius):** Rủi ro gián đoạn dịch vụ hoặc gây lỗi lan truyền sang các module phụ thuộc.",
        "- **Kế hoạch kiểm thử xác minh:** Cần viết bài kiểm thử tự động tái hiện lỗi (reproduction test) trước khi áp dụng bản vá.",
        "",
        f"> Trích dẫn dữ liệu nguồn: Work Package #{pkg_id} (lock_version: {lock_ver})",
    ]
    ref = NativeReference(work_package_id=pkg_id, lock_version=lock_ver)
    return "\n".join(lines), ref


def evaluate_test_attestation(package: dict[str, Any], attestation: VerifiedTestReport | dict[str, Any] | None = None) -> tuple[str, NativeReference]:
    """Strictly verifies test status: refuses to claim PASS without verified execution attestation."""
    pkg_id = package["id"]
    lock_ver = package["lockVersion"]
    subject = package.get("subject", "").strip()

    lines = [
        f"### BÁO CÁO XÁC MINH KIỂM THỬ (TEST VERIFICATION REPORT) — #{pkg_id}",
        f"**Công việc:** {subject}",
        "",
    ]

    if not isinstance(attestation, VerifiedTestReport) or (attestation.native_id, attestation.version) != (pkg_id, lock_ver):
        lines.append("- **Trạng thái kiểm thử:** **CHƯA CHẠY (NOT_RUN) / CHƯA CÓ BẰNG CHỨNG THỰC THI**")
        lines.append("- **Kết luận:** **KHÔNG THỂ XÁC NHẬN PASS**")
        lines.append("")
        lines.append("> [!IMPORTANT]")
        lines.append("> **Quy tắc bảo đảm chất lượng nghiêm ngặt:** QA Agent tuyệt đối KHÔNG xác nhận hoặc tuyên bố "
                     "kết quả kiểm thử đạt 'PASS' khi chưa có log thực thi thực tế từ Test Runner hoặc biên bản attestation hợp lệ.")
        lines.append("Cần kích hoạt runner kiểm thử tự động hoặc cung cấp log kiểm thử thực tế để xác minh.")
    else:
        status_val = attestation.verdict
        lines.append(f"- **Trạng thái kiểm thử:** {status_val}")
        lines.append(f"- **Runner:** {attestation.runner} / {attestation.run_id}")
        lines.append(f"- **Thời gian thực thi:** {attestation.finished_at}")
        lines.append(f"- **Artifact SHA256:** {attestation.artifact_sha256}")
        if attestation.runner == 'qldapm-wbs-application-v1':
            lines.append("- Đây là qualification application WBS trong môi trường cô lập; không phải human QA review hoặc approval Native.")
        else:
            lines.append("- Đây là automated Native readback; không phải human QA review hoặc approval Native.")

    ref = NativeReference(work_package_id=pkg_id, lock_version=lock_ver)
    return "\n".join(lines), ref


class QAAgent:
    """QA Agent specialist providing test case generation, regression gap detection,

    bug triage, and truthful test attestation reporting.
    Enforces strict rules: never claims tests PASS without execution evidence,
    and never self-mutates OpenProject tasks.
    """

    def run(
        self,
        task: AgentTask,
        scope: RunScope,
        packages: list[dict[str, Any]],
        attestation: VerifiedTestReport | dict[str, Any] | None = None,
        provider=None,
        verified_report=None,
    ) -> AgentResult:
        if provider is not None:
            return provider.run_agent('qa',task,scope,packages)
        instruction = task.instruction
        if isinstance(attestation, VerifiedTestReport) and (attestation.actor_id, attestation.project_id) != (scope.actor_id, scope.project_id):
            attestation = None
        pkg_map = {p["id"]: p for p in packages}

        # STRICT RULE: Refuse direct task updates / status transitions
        if is_write_intent(instruction):
            cited_ids = [int(m) for m in re.findall(r"#(\d+)", instruction)]
            references = []
            for cid in cited_ids:
                if cid in pkg_map:
                    references.append(NativeReference(work_package_id=cid, lock_version=pkg_map[cid]["lockVersion"]))
            if not references and task.references:
                references = list(task.references)

            summary = (
                "QA Agent chỉ phân tích chất lượng, thiết kế ca kiểm thử và đánh giá lỗi; "
                "tuyệt đối KHÔNG tự ý cập nhật trạng thái, đóng task hay chỉnh sửa dữ liệu trong OpenProject. "
                "Yêu cầu đã được chuyển thành bản dự thảo đề xuất (Proposal Draft) cần phê duyệt bởi PM "
                "theo chính sách PM-only-write trước khi thực hiện bất kỳ thao tác nào.\n"
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

        if "kịch bản" in instr_lower or "test case" in instr_lower or "test cases" in instr_lower:
            if target_pkg:
                summary, ref = generate_test_cases(target_pkg)
                references = [ref]
            else:
                summary = "Không tìm thấy công việc mục tiêu để thiết kế kịch bản kiểm thử."
                references = []

        elif "hồi quy" in instr_lower or "khoảng trống" in instr_lower or "gap" in instr_lower:
            summary, references = detect_regression_gaps(packages)

        elif "triage" in instr_lower or "phân loại lỗi" in instr_lower or "nghiêm trọng" in instr_lower or "bug" in instr_lower:
            if target_pkg:
                summary, ref = triage_bug(target_pkg)
                references = [ref]
            else:
                summary = "Không tìm thấy công việc lỗi mục tiêu để phân loại triage."
                references = []

        elif "kết quả" in instr_lower or "chạy test" in instr_lower or "xác minh" in instr_lower:
            if target_pkg:
                if verified_report is not None:
                    attestation=verified_report(target_pkg['id'],target_pkg['lockVersion'])
                    if not isinstance(attestation,VerifiedTestReport) or (attestation.actor_id,attestation.project_id)!=(scope.actor_id,scope.project_id):
                        attestation=None
                summary, ref = evaluate_test_attestation(target_pkg, attestation)
                references = [ref]
            else:
                summary = "Không tìm thấy công việc mục tiêu để kiểm tra kết quả kiểm thử."
                references = []

        else:
            if target_pkg and target_pkg.get("_links", {}).get("type", {}).get("title") == "Bug":
                summary, ref = triage_bug(target_pkg)
                references = [ref]
            elif target_pkg:
                summary, ref = generate_test_cases(target_pkg)
                references = [ref]
            else:
                summary, references = detect_regression_gaps(packages)

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
