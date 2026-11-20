"""Reviewer Agent: Independent validator for evidence citations, consistency,
cross-agent conflict detection, and RBAC compliance.
Strictly rejects unsupported assumptions and enforces NO blind auto-approval.
"""
import re
from typing import Any

from .agent_models import AgentResult, AgentTask, NativeReference, RunScope

AUTO_APPROVE_KEYWORDS = re.compile(
    r"(?i)\b(tự động phê duyệt|auto approve|tự duyệt|áp dụng ngay không cần duyệt|bỏ qua phê duyệt)\b"
)


def review_agent_result(
    result: AgentResult,
    native_packages: list[dict[str, Any]],
) -> tuple[bool, str, list[NativeReference]]:
    """Validates citations in an agent result against native packages and lock versions."""
    pkg_map = {p["id"]: p for p in native_packages}
    valid_refs = []
    issues = []

    # 1. Verify existing references
    for ref in result.references:
        pid = ref.work_package_id
        if pid not in pkg_map:
            issues.append(f"Work package #{pid} không tồn tại trong dự án native.")
        elif pkg_map[pid]["lockVersion"] != ref.lock_version:
            issues.append(
                f"Work package #{pid} sai lệch lock_version: trích dẫn phiên bản {ref.lock_version}, "
                f"nhưng dữ liệu native hiện tại là {pkg_map[pid]['lockVersion']}."
            )
        else:
            valid_refs.append(ref)

    # 2. Check for uncited work packages mentioned in summary text
    mentioned_ids = [int(m) for m in re.findall(r"#(\d+)", result.summary)]
    cited_ids = {r.work_package_id for r in result.references}
    for mid in mentioned_ids:
        if mid not in pkg_map:
            issues.append(f"Nhận định đề cập công việc #{mid} nhưng không có bằng chứng native tồn tại.")
        elif mid not in cited_ids:
            issues.append(f"Công việc #{mid} được nhắc tới nhưng thiếu trích dẫn native reference có lock_version.")

    if issues:
        reason = "Phát hiện sai lệch hoặc nhận định không có bằng chứng:\n- " + "\n- ".join(issues)
        return False, reason, valid_refs

    detail = "ID và lock_version của các trích dẫn khớp nguồn" if valid_refs else "Chưa có trích dẫn cụ thể để đối chiếu"
    return True, detail + "; nội dung phân tích/dự thảo vẫn cần người dùng thẩm định.", valid_refs


def detect_agent_conflicts(results: list[AgentResult]) -> list[str]:
    """Detects semantic and status contradictions between outputs of different agents."""
    conflicts = []
    if len(results) < 2:
        return conflicts

    # Look for conflicting claims on same package IDs
    pkg_claims: dict[int, list[tuple[str, str]]] = {}
    for r in results:
        for ref in r.references:
            pid = ref.work_package_id
            pkg_claims.setdefault(pid, []).append((r.summary, r.state))

    for pid, claims in pkg_claims.items():
        if len(claims) >= 2:
            # shortcut: detects explicit per-ID status assertions; semantic draft review remains human-owned.
            statements = [re.findall(rf"#{pid}\b\s*(?:hiện\s+|hiện tại\s+|is\s+)?([^.;\n]*)", c[0].lower()) for c in claims]
            positive = {i for i, parts in enumerate(statements) if any(re.match(r"(?:đã hoàn tất|đã xong|đã sẵn sàng|sẵn sàng bàn giao|ready\b|completed?\b)", p) for p in parts)}
            negative = {i for i, parts in enumerate(statements) if any(re.match(r"(?:còn\s+(?:\d+\s+)?lỗi|chưa thể hoàn thành|chưa hoàn thành|(?:đang )?bị chặn|blocked\b|has\s+.*blocker)", p) for p in parts)}
            if any(a != b for a in positive for b in negative):
                conflicts.append(
                    f"Xung đột nhận định về công việc #{pid}: Một tác nhân báo cáo đã sẵn sàng/hoàn tất "
                    f"trong khi tác nhân khác báo cáo còn lỗi hoặc bị chặn."
                )

    return conflicts


class ReviewerAgent:
    """Reviewer Agent specialist providing objective cross-verification of evidence,

    consistency, RBAC policy compliance, and conflict detection.
    Enforces strict rules: rejects unsupported assumptions and prohibits blind auto-approval.
    """

    def run(
        self,
        task: AgentTask,
        scope: RunScope,
        agent_results: list[AgentResult],
        native_packages: list[dict[str, Any]],
    ) -> AgentResult:
        instruction = task.instruction
        if any(any(getattr(result,key) != getattr(scope,key) for key in ('run_id','actor_id','project_id','task_id','trace_id')) for result in agent_results):
            raise PermissionError('REVIEWER_RESULT_SCOPE_MISMATCH')

        # STRICT RULE: No blind auto-approval under any circumstances
        if AUTO_APPROVE_KEYWORDS.search(instruction):
            summary = (
                "YÊU CẦU BỊ TỪ CHỐI TỰ ĐỘNG PHÊ DUYỆT: Theo chính sách quản trị của QLDAPM, "
                "Reviewer Agent tuyệt đối KHÔNG TỰ ĐỘNG PHÊ DUYỆT bất kỳ đề xuất thay đổi hay thao tác ghi nào. "
                "Mọi đề xuất (proposals) bắt buộc phải được người dùng giữ vai trò PM (Project Manager) kiểm tra, "
                "xác nhận và phê duyệt thủ công qua giao diện UI hoặc kênh điều hành có thẩm quyền."
            )
            # Collect any available references for tracking
            all_refs = []
            for r in agent_results:
                all_refs.extend(r.references)
            return AgentResult(
                run_id=scope.run_id,
                task_id=scope.task_id,
                actor_id=scope.actor_id,
                project_id=scope.project_id,
                trace_id=scope.trace_id,
                state="COMPLETED",
                summary=summary,
                references=all_refs,
                receipt_ids=[],
                model_used=False,
            )

        # Standard Review & Verification Flow
        lines = ["### BÁO CÁO ĐỐI CHIẾU VÀ KIỂM ĐỊNH TÍNH NHẤT QUÁN (REVIEWER REPORT)"]
        all_valid_refs: dict[int, NativeReference] = {}
        all_passed = True
        has_proposal = any(r.state == "REVIEW" for r in agent_results)

        # 1. Evidence Verification
        lines.append("#### 1. Kết quả đối chiếu bằng chứng native:")
        for idx, r in enumerate(agent_results, 1):
            passed, detail, valid_refs = review_agent_result(r, native_packages)
            for ref in valid_refs:
                all_valid_refs[ref.work_package_id] = ref

            ref_str = f" (Công việc liên quan: {', '.join(f'#{r.work_package_id}' for r in valid_refs)})" if valid_refs else ""
            if passed:
                lines.append(f"- Tác vụ {idx}: **TRÍCH DẪN HỢP LỆ**{ref_str} — {detail}")
            else:
                all_passed = False
                lines.append(f"- Tác vụ {idx}: **TỪ CHỐI / CẢNH BÁO KHÔNG HỢP LỆ**{ref_str} — {detail}")

        # 2. Cross-Agent Conflicts
        conflicts = detect_agent_conflicts(agent_results)
        if conflicts:
            all_passed = False
            lines.append("\n#### 2. Phát hiện mâu thuẫn / Xung đột giữa các tác nhân (Conflicts):")
            for c in conflicts:
                lines.append(f"- [CẢNH BÁO MÂU THUẪN]: {c}")
        else:
            lines.append("\n#### 2. Kiểm tra xung đột đa tác nhân: Nhất quán, không phát hiện mâu thuẫn.")

        # 3. RBAC & PM Approval Policy Enforcement
        lines.append("\n#### 3. Rà soát ranh giới thẩm quyền RBAC:")
        if has_proposal:
            lines.append(
                "- **Chính sách RBAC:** Phát hiện đề xuất thay đổi dữ liệu (Proposal). "
                "Theo chính sách PM-only-write, chỉ người dùng giữ vai trò **PM (Project Manager)** mới có thẩm quyền "
                "phê duyệt và kích hoạt ghi dữ liệu vào hệ thống OpenProject."
            )
        else:
            lines.append("- Các tác vụ đều thuộc phạm vi ĐỌC (Read-Only) hợp lệ, tuân thủ đúng phân quyền của vai trò.")

        # 4. Final Verdict
        lines.append("\n#### 4. Kết luận kiểm định (Final Verdict):")
        if not all_passed:
            lines.append("**KẾT QUẢ: CẦN ĐIỀU CHỈNH / TỪ CHỐI NHẬN ĐỊNH THIẾU BẰNG CHỨNG.**")
        elif has_proposal:
            lines.append("**KẾT QUẢ: ĐÃ ĐỐI CHIẾU THAM CHIẾU ĐƯỢC CUNG CẤP — ĐỀ XUẤT CHỜ PM DUYỆT.**")
        else:
            lines.append("**KẾT QUẢ: ĐÃ KIỂM TRA THAM CHIẾU/PHẠM VI; NỘI DUNG DỰ THẢO CHƯA ĐƯỢC CON NGƯỜI NGHIỆM THU.**")

        summary = "\n".join(lines)
        return AgentResult(
            run_id=scope.run_id,
            task_id=scope.task_id,
            actor_id=scope.actor_id,
            project_id=scope.project_id,
            trace_id=scope.trace_id,
            state="COMPLETED" if all_passed else "FAILED",
            summary=summary,
            references=list(all_valid_refs.values()),
            receipt_ids=[],
            model_used=False,
            error_code=None if all_passed else 'AGENT_EVIDENCE_REJECTED',
        )
