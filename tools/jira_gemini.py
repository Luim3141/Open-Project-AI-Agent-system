"""Optional Gemini assessment of minimal, read-only Jira project metrics."""

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from jira_bot import CLOUD_ID, PROJECT, PROJECT_ID, collect

MODEL = "gemini-3.1-flash-lite"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
REPORT_FIELDS = ("summary", "risks", "recommendedActions", "limitations")
SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        **{name: {"type": "array", "items": {"type": "string"}}
           for name in REPORT_FIELDS[1:]},
    },
    "required": list(REPORT_FIELDS),
    "additionalProperties": False,
}


def credentials(environ):
    # Free model availability does not prove this key's project has no billing.
    if environ.get("GEMINI_FREE_TIER_CONFIRMED") != "1":
        raise ValueError("Confirm the key's project is Free Tier before enabling inference")
    key = environ.get("GEMINI_API_KEY")
    if not key or any(char.isspace() for char in key):
        raise ValueError("A fresh GEMINI_API_KEY is required in the environment")
    return key


def minimal_metrics(snapshot):
    if (snapshot.get("projectKey") != PROJECT or snapshot.get("projectId") != PROJECT_ID
            or snapshot.get("cloudId") != CLOUD_ID or snapshot.get("readComplete") is not True
            or snapshot.get("isLast") is not True):
        raise ValueError("Only a complete, verified QAG3 snapshot can be assessed")
    counts = {name: snapshot[name] for name in
              ("functionalTotal", "functionalDone", "cancelledFunctional")}
    if any(type(value) is not int or value < 0 for value in counts.values()):
        raise ValueError("Invalid metric count")
    if counts["functionalDone"] + counts["cancelledFunctional"] > counts["functionalTotal"]:
        raise ValueError("Inconsistent delivered/cancelled counts")
    for name in ("functionalWip", "unassignedFunctional", "unknownAssigneeField",
                 "overdueFunctional", "unknownDueDateField"):
        if not isinstance(snapshot.get(name), list) or len(snapshot[name]) > counts["functionalTotal"]:
            raise ValueError("Invalid metric list")
    return {
        **counts,
        **{name + "Count": len(snapshot[name]) for name in
           ("functionalWip", "unassignedFunctional", "unknownAssigneeField",
            "overdueFunctional", "unknownDueDateField")},
        # shortcut: collect reliable sprint/capacity baselines before extending these metrics.
        "scheduleBaselineKnown": False, "capacityKnown": False,
        "codeAcceptanceVerified": False,
    }


def assess(snapshot, environ=None, transport=urlopen):
    key = credentials(os.environ if environ is None else environ)
    metrics = minimal_metrics(snapshot)
    instruction = (
        "Viết bản nhận định ngắn bằng tiếng Việt cho PM từ chỉ số Jira sau. "
        "Chỉ nhận định tiến độ hiện tại; không chấm, xếp hạng hoặc suy đoán cá nhân. "
        "Tổng 0 là chưa có phạm vi, không 100%. Done Jira không chứng minh code/AC hoàn tất. "
        "Không có baseline lịch/capacity nên không kết luận đúng hạn hay trễ Sprint. "
        "UNKNOWN field không bằng chưa giao việc/không có deadline. "
        "Không bịa blockers, lịch sử, nguyên nhân, cam kết hoặc quyền admin. "
        "Nêu giới hạn và đề xuất cần PM xác minh. Đây là draft tư vấn, không lệnh thực thi. "
        "Dữ liệu chỉ số: " + json.dumps(metrics, ensure_ascii=False)
    )
    body = {
        "contents": [{"parts": [{"text": instruction}]}],
        "generationConfig": {
            "maxOutputTokens": 2048,
            "responseFormat": {"text": {"mimeType": "application/json", "schema": SCHEMA}},
        },
    }
    request = Request(ENDPOINT, data=json.dumps(body).encode("utf-8"),
                      headers={"Content-Type": "application/json", "x-goog-api-key": key},
                      method="POST")
    try:
        with transport(request, timeout=45) as response:
            raw = response.read(65537)
        if len(raw) > 65536:
            raise ValueError("Gemini response exceeds size limit")
        payload = json.loads(raw)
    except HTTPError as error:
        raise RuntimeError(f"Gemini HTTP {error.code}; no retry or paid fallback") from None
    except (URLError, TimeoutError):
        raise RuntimeError("Gemini connection failed; no assessment available") from None
    candidates = payload.get("candidates", [])
    if len(candidates) != 1 or candidates[0].get("finishReason") != "STOP":
        raise ValueError("Gemini response blocked, incomplete or ambiguous")
    parts = candidates[0]["content"]["parts"]
    result = json.loads("".join(x.get("text", "") for x in parts if not x.get("thought")))
    if not isinstance(result, dict) or set(result) != set(REPORT_FIELDS):
        raise ValueError("Invalid assessment fields")
    if not isinstance(result["summary"], str) or not result["summary"].strip():
        raise ValueError("Missing assessment summary")
    for name in REPORT_FIELDS[1:]:
        if (not isinstance(result[name], list) or len(result[name]) > 8
                or any(not isinstance(x, str) or len(x) > 2000 for x in result[name])):
            raise ValueError("Invalid assessment detail")
    if len(result["summary"]) > 2000 or key in json.dumps(result):
        raise ValueError("Unsafe assessment output")
    return {"provider": "gemini", "model": MODEL, "aiDraft": True, "assessmentComplete": True,
            "sourceObservedAtUtc": snapshot["observedAtUtc"],
            "metricsSent": metrics, "assessment": result,
            "scheduledExecutionVerified": False}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, help="Assess an already-collected complete snapshot")
    options = parser.parse_args()
    try:
        credentials(os.environ)
        snapshot = json.loads(options.snapshot.read_text(encoding="utf-8")) if options.snapshot else collect()
        print(json.dumps(assess(snapshot), ensure_ascii=False))
    except Exception as error:
        # Do not print provider bodies, request headers, credentials or raw exceptions.
        print(json.dumps({"assessmentComplete": False, "errorType": type(error).__name__,
                          "message": "Assessment unavailable; preserve prior reports and check setup."}))
        sys.exit(1)
