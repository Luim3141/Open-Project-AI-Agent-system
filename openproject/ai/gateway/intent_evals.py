"""Evaluation module for QLDAPM: Multi-intent, ambiguity detection, and stale reference resolution.
Provides a golden evaluation set and runner for bilingual (Vietnamese/English) prompt understanding.
"""
from dataclasses import dataclass, field
import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from .agent_models import AgentTask
from .conversation_memory import NativeObjectRef, PRONOUN_PATTERN
from .planner import (
    COMPLEX_ANALYSIS_KEYWORDS,
    DETERMINISTIC_KEYWORDS,
    ROLE_AGENT_MAP,
    WRITE_KEYWORDS,
    is_deterministic_intent,
    is_write_intent,
    resolve_target_agent,
)

WP_ID_PATTERN = re.compile(r"(?:#|wp\s*|task\s*|package\s*|ticket\s*)(\d+)", re.IGNORECASE)
COMPOUND_DELIMITER_PATTERN = re.compile(r"\s*(?:\b(?:v\u00e0|and|sau \u0111\u00f3|then)\b|\+|;|\.\s+)\s*", re.IGNORECASE)


@dataclass
class SubIntent:
    intent_type: str  # DETERMINISTIC_READ, COMPLEX_READ, PROPOSAL_WRITE, AMBIGUOUS
    target_agent: str
    instruction: str
    target_id: Optional[int] = None
    operation_type: str = "READ_ONLY"  # READ_ONLY or PROPOSAL_WRITE


@dataclass
class IntentEvaluationResult:
    original_instruction: str
    is_multi_intent: bool
    sub_intents: List[SubIntent]
    is_ambiguous: bool
    ambiguity_reason: Optional[str]
    is_stale_reference: bool
    resolved_ref: Optional[NativeObjectRef]
    accuracy_matched: bool = False


@dataclass
class EvalSummary:
    total: int
    passed: int
    failed: int
    accuracy_rate: float
    results: List[Dict[str, Any]] = field(default_factory=list)


def extract_wp_id(text: str) -> Optional[int]:
    match = WP_ID_PATTERN.search(text)
    return int(match.group(1)) if match else None


def evaluate_instruction_intent(
    instruction: str,
    conversation_ref: Optional[NativeObjectRef] = None,
    current_native_lock_version: Optional[int] = None,
) -> IntentEvaluationResult:
    """Analyzes a bilingual instruction for multi-intent, ambiguity, and stale references."""
    clean_text = instruction.strip()

    # 1. Check Pronoun & Reference Resolution
    has_pronoun = bool(PRONOUN_PATTERN.search(clean_text))
    is_stale = False
    resolved_ref = None

    if has_pronoun:
        if conversation_ref is None:
            is_stale = True
        else:
            if current_native_lock_version is not None and current_native_lock_version != conversation_ref.lock_version:
                is_stale = True
            else:
                resolved_ref = conversation_ref

    # 2. Check Ambiguity: Write / modify action without explicit ID or resolvable pronoun
    has_write = bool(WRITE_KEYWORDS.search(clean_text))
    extracted_id = extract_wp_id(clean_text)

    is_ambiguous = False
    ambiguity_reason = None

    # Needs explicit target if action is mutating an existing item (update, close, assign, delete, edit)
    mutating_existing = bool(
        re.search(
            r"(?i)\b(c\u1eadp nh\u1eadt|s\u1eeda|thay \u0111\u1ed5i|g\u00e1n|ph\u00e2n c\u00f4ng|x\u00f3a|\u0111\u1ed5i tr\u1ea1ng th\u00e1i|\u0111\u00f3ng|update|edit|modify|change|assign|delete|close|transition)\b",
            clean_text,
        )
    )

    if mutating_existing and not extracted_id and not resolved_ref:
        is_ambiguous = True
        ambiguity_reason = "MISSING_TARGET_WORK_PACKAGE_ID: Hành động sửa đổi yêu cầu ID công việc hoặc ngữ cảnh gần nhất."

    # General extremely underspecified input
    if len(clean_text.split()) < 3 and not extracted_id and not resolved_ref and not DETERMINISTIC_KEYWORDS.search(clean_text):
        is_ambiguous = True
        ambiguity_reason = ambiguity_reason or "UNDERSPECIFIED_REQUEST: Yêu cầu quá ngắn hoặc thiếu thông tin định danh."

    # 3. Decompose Compound / Multi-Intent
    # Split by conjunctions ("và", "and", "sau đó", ";")
    parts = [p.strip() for p in COMPOUND_DELIMITER_PATTERN.split(clean_text) if len(p.strip()) > 3]

    sub_intents: List[SubIntent] = []
    if len(parts) > 1 and any(WRITE_KEYWORDS.search(p) or DETERMINISTIC_KEYWORDS.search(p) or COMPLEX_ANALYSIS_KEYWORDS.search(p) for p in parts):
        for part in parts:
            part_write = bool(WRITE_KEYWORDS.search(part))
            part_det = is_deterministic_intent(part)
            part_agent = resolve_target_agent(part, "pm")
            part_id = extract_wp_id(part) or (resolved_ref.native_id if resolved_ref else None)

            if part_write:
                i_type = "PROPOSAL_WRITE"
                op_type = "PROPOSAL_WRITE"
            elif part_det:
                i_type = "DETERMINISTIC_READ"
                op_type = "READ_ONLY"
            else:
                i_type = "COMPLEX_READ"
                op_type = "READ_ONLY"

            sub_intents.append(
                SubIntent(
                    intent_type=i_type,
                    target_agent=part_agent,
                    instruction=part,
                    target_id=part_id,
                    operation_type=op_type,
                )
            )
        is_multi = len(sub_intents) > 1
    else:
        is_multi = False
        target_agent = resolve_target_agent(clean_text, "pm")
        target_id = extracted_id or (resolved_ref.native_id if resolved_ref else None)
        if is_ambiguous:
            i_type = "AMBIGUOUS"
            op_type = "READ_ONLY"
        elif has_write:
            i_type = "PROPOSAL_WRITE"
            op_type = "PROPOSAL_WRITE"
        elif is_deterministic_intent(clean_text):
            i_type = "DETERMINISTIC_READ"
            op_type = "READ_ONLY"
        else:
            i_type = "COMPLEX_READ"
            op_type = "READ_ONLY"

        sub_intents.append(
            SubIntent(
                intent_type=i_type,
                target_agent=target_agent,
                instruction=clean_text,
                target_id=target_id,
                operation_type=op_type,
            )
        )

    return IntentEvaluationResult(
        original_instruction=clean_text,
        is_multi_intent=is_multi,
        sub_intents=sub_intents,
        is_ambiguous=is_ambiguous,
        ambiguity_reason=ambiguity_reason,
        is_stale_reference=is_stale,
        resolved_ref=resolved_ref,
    )


# ---------------------------------------------------------------------------
# Golden Evaluation Set: 32 comprehensive bilingual scenarios
# ---------------------------------------------------------------------------
GOLDEN_EVALS_SET: List[Dict[str, Any]] = [
    # 1-6: Pure Deterministic Read (VN & EN)
    {
        "id": "DET_01",
        "instruction": "Đếm số lượng work package quá hạn trong sprint",
        "expected_intent": "DETERMINISTIC_READ",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "DET_02",
        "instruction": "Liệt kê danh sách các task đang ở trạng thái In Progress",
        "expected_intent": "DETERMINISTIC_READ",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "DET_03",
        "instruction": "Count overdue work packages for FE team",
        "expected_intent": "DETERMINISTIC_READ",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "DET_04",
        "instruction": "List all open bugs in current milestone",
        "expected_intent": "DETERMINISTIC_READ",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "DET_05",
        "instruction": "Kiểm tra trạng thái của task #42",
        "expected_intent": "DETERMINISTIC_READ",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "DET_06",
        "instruction": "Show summary count of finished tasks",
        "expected_intent": "DETERMINISTIC_READ",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },

    # 7-12: Complex Analysis / Read (VN & EN)
    {
        "id": "ANA_01",
        "instruction": "Phân tích rủi ro chậm tiến độ của sprint hiện tại",
        "expected_intent": "COMPLEX_READ",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "ANA_02",
        "instruction": "Đánh giá chất lượng các acceptance criteria của User Story #105",
        "expected_intent": "COMPLEX_READ",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "ANA_03",
        "instruction": "Analyze architecture bottlenecks for the database migration",
        "expected_intent": "COMPLEX_READ",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "ANA_04",
        "instruction": "Suggest regression test cases for authentication module",
        "expected_intent": "COMPLEX_READ",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "ANA_05",
        "instruction": "So sánh workload giữa các thành viên BE và FE",
        "expected_intent": "COMPLEX_READ",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "ANA_06",
        "instruction": "Review test coverage for QA agent tickets",
        "expected_intent": "COMPLEX_READ",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },

    # 13-18: Write Proposal (VN & EN)
    {
        "id": "WRT_01",
        "instruction": "Tạo task mới cho BE: Xây dựng API xác thực JWT",
        "expected_intent": "PROPOSAL_WRITE",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "WRT_02",
        "instruction": "Cập nhật trạng thái của task #88 sang In Progress",
        "expected_intent": "PROPOSAL_WRITE",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "WRT_03",
        "instruction": "Gán work package #50 cho thành viên QA",
        "expected_intent": "PROPOSAL_WRITE",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "WRT_04",
        "instruction": "Create new story: Responsive design for mobile dashboard",
        "expected_intent": "PROPOSAL_WRITE",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "WRT_05",
        "instruction": "Update ticket #92 description with new security guidelines",
        "expected_intent": "PROPOSAL_WRITE",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "WRT_06",
        "instruction": "Đóng bug #33 vì đã pass kiểm thử staging",
        "expected_intent": "PROPOSAL_WRITE",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },

    # 19-24: Multi-Intent Compound Instructions (VN & EN)
    {
        "id": "MULTI_01",
        "instruction": "Đếm số task quá hạn và tạo task mới cho PM rà soát",
        "expected_intent": "MULTI",
        "is_multi": True,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "MULTI_02",
        "instruction": "Liệt kê các bug open và cập nhật trạng thái của ticket #12 sang In Progress",
        "expected_intent": "MULTI",
        "is_multi": True,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "MULTI_03",
        "instruction": "Count open defects and create a new QA test plan task",
        "expected_intent": "MULTI",
        "is_multi": True,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "MULTI_04",
        "instruction": "Kiểm tra tiến độ sprint sau đó tạo user story cho tính năng thanh toán",
        "expected_intent": "MULTI",
        "is_multi": True,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "MULTI_05",
        "instruction": "Show overdue items and assign task #77 to FE developer",
        "expected_intent": "MULTI",
        "is_multi": True,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "MULTI_06",
        "instruction": "List all blockers and notify the team about sprint deadline",
        "expected_intent": "MULTI",
        "is_multi": True,
        "is_ambiguous": False,
        "is_stale": False,
    },

    # 25-28: Ambiguity / Missing Target
    {
        "id": "AMB_01",
        "instruction": "Cập nhật trạng thái sang Done",
        "expected_intent": "AMBIGUOUS",
        "is_multi": False,
        "is_ambiguous": True,
        "is_stale": False,
    },
    {
        "id": "AMB_02",
        "instruction": "Update it immediately",
        "expected_intent": "AMBIGUOUS",
        "is_multi": False,
        "is_ambiguous": True,
        "is_stale": False,
    },
    {
        "id": "AMB_03",
        "instruction": "Sửa lỗi đi",
        "expected_intent": "AMBIGUOUS",
        "is_multi": False,
        "is_ambiguous": True,
        "is_stale": False,
    },
    {
        "id": "AMB_04",
        "instruction": "Assign to QA",
        "expected_intent": "AMBIGUOUS",
        "is_multi": False,
        "is_ambiguous": True,
        "is_stale": False,
    },

    # 29-32: Stale / Active Chat References
    {
        "id": "REF_01_STALE",
        "instruction": "Cập nhật mô tả của task đó",
        "conversation_ref": None,  # No context exists -> stale
        "expected_intent": "AMBIGUOUS",
        "is_multi": False,
        "is_ambiguous": True,
        "is_stale": True,
    },
    {
        "id": "REF_02_VALID",
        "instruction": "Cập nhật mô tả của task đó",
        "conversation_ref": NativeObjectRef("work_package", 99, 1),
        "current_lock_version": 1,  # Same lock version -> valid
        "expected_intent": "PROPOSAL_WRITE",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },
    {
        "id": "REF_03_LOCK_MISMATCH",
        "instruction": "Đóng cái task vừa rồi",
        "conversation_ref": NativeObjectRef("work_package", 99, 1),
        "current_lock_version": 2,  # Lock version changed -> stale
        "expected_intent": "AMBIGUOUS",
        "is_multi": False,
        "is_ambiguous": True,
        "is_stale": True,
    },
    {
        "id": "REF_04_VALID_EN",
        "instruction": "Assign that ticket to backend dev",
        "conversation_ref": NativeObjectRef("work_package", 77, 3),
        "current_lock_version": 3,
        "expected_intent": "PROPOSAL_WRITE",
        "is_multi": False,
        "is_ambiguous": False,
        "is_stale": False,
    },
]


def run_intent_evaluations(golden_set: Optional[List[Dict[str, Any]]] = None) -> EvalSummary:
    """Executes the benchmark suite and produces a structured pass/fail evaluation report."""
    dataset = golden_set or GOLDEN_EVALS_SET
    total = len(dataset)
    passed = 0
    results: List[Dict[str, Any]] = []

    for item in dataset:
        instruction = item["instruction"]
        conv_ref = item.get("conversation_ref")
        lock_ver = item.get("current_lock_version")

        t0 = time.perf_counter()
        res = evaluate_instruction_intent(
            instruction=instruction,
            conversation_ref=conv_ref,
            current_native_lock_version=lock_ver,
        )
        latency_ms = round((time.perf_counter() - t0) * 1000, 3)

        # Match check
        expected_intent = item["expected_intent"]
        expected_multi = item["is_multi"]
        expected_ambig = item["is_ambiguous"]
        expected_stale = item["is_stale"]

        if expected_multi:
            match = res.is_multi_intent == expected_multi
        elif expected_ambig:
            match = res.is_ambiguous == expected_ambig
        else:
            primary_intent = res.sub_intents[0].intent_type if res.sub_intents else "NONE"
            match = (
                primary_intent == expected_intent
                and res.is_multi_intent == expected_multi
                and res.is_ambiguous == expected_ambig
                and res.is_stale_reference == expected_stale
            )

        if match:
            passed += 1

        results.append(
            {
                "id": item["id"],
                "instruction": instruction,
                "expected": {
                    "intent": expected_intent,
                    "multi": expected_multi,
                    "ambiguous": expected_ambig,
                    "stale": expected_stale,
                },
                "actual": {
                    "primary_intent": res.sub_intents[0].intent_type if res.sub_intents else None,
                    "multi": res.is_multi_intent,
                    "ambiguous": res.is_ambiguous,
                    "stale": res.is_stale_reference,
                    "sub_intents_count": len(res.sub_intents),
                },
                "match": match,
                "latency_ms": latency_ms,
            }
        )

    rate = round((passed / total) * 100, 2) if total > 0 else 0.0
    return EvalSummary(
        total=total,
        passed=passed,
        failed=total - passed,
        accuracy_rate=rate,
        results=results,
    )
