"""Local periodic read-only MCP collector with optional Gemini drafts (Windows)."""

import argparse
import hashlib
import json
import msvcrt
import os
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from jira_bot import PROJECT, ROOT, collect
from jira_gemini import assess, credentials, minimal_metrics

RUNTIME = ROOT / "jira-bot" / "runtime"


def member_assessment(snapshot):
    """Private current-scope delivery observations, never personnel scores."""
    if snapshot.get("readComplete") is not True or snapshot.get("projectKey") != PROJECT:
        raise ValueError("Complete QAG3 snapshot required for member assessment")
    members, excluded = {}, []
    for item in snapshot["issues"]:
        labels = set(item["labels"])
        if "qag3-wbs" not in labels or labels & {"qag3-test", "excluded-from-performance"}:
            excluded.append(item["key"])
            continue
        account = (item["assigneeAccountId"] or "UNASSIGNED") if item["assigneeKnown"] else "UNKNOWN"
        groups = members.setdefault(account, {})
        group = groups.setdefault(item["kind"], {"total": 0, "done": 0, "new": 0,
            "wip": 0, "cancelled": 0, "simulated": 0, "issueKeys": []})
        group["total"] += 1
        group["done"] += item["category"] == "done" and not item["cancelled"]
        group["new"] += item["category"] == "new"
        group["wip"] += item["category"] == "indeterminate"
        group["cancelled"] += item["cancelled"]
        group["simulated"] += "qag3-simulation" in labels
        group["issueKeys"].append(item["key"])
    for groups in members.values():
        for group in groups.values():
            group["completionPercent"] = round(100 * group["done"] / group["total"], 2)
    observations = {"scope": "qag3-wbs excluding explicit test/performance-excluded labels",
                    "members": members, "excludedIssueKeys": excluded}
    fingerprint = hashlib.sha256(json.dumps(observations, sort_keys=True).encode()).hexdigest()
    return {**observations, "fingerprint": fingerprint,
            "sourceObservedAtUtc": snapshot["observedAtUtc"], "assessmentComplete": True,
            "publication": "PRIVATE_LOCAL_AND_OWNER_CHAT", "overallScore": None,
            "overallScoreStatus": "INSUFFICIENT_EVIDENCE",
            "dimensionStatus": {key: "INSUFFICIENT_EVIDENCE" for key in
                ("deliveryReliability", "quality", "collaboration", "ownership", "contribution")},
            "limits": ["Current assignee and status are not proof of who performed the work",
                       "Epic/Task/Subtask are separate; do not sum them as productivity",
                       "Simulated worklogs/points/QA are not real-person evidence",
                       "No verified capacity, committed scope, worklog attribution or product QA"]}


def atomic_json(path, data):
    descriptor, temporary = tempfile.mkstemp(prefix="monitor-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(data, output, ensure_ascii=False)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


@contextmanager
def single_runner(directory):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "runner.lock").open("a+b") as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            yield
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


def cycle(directory, collector=collect, assessor=assess, environ=None):
    environ = os.environ if environ is None else environ
    state_path = directory / "state-QAG3.json"
    previous = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    if previous and (previous.get("owner") != "jira_monitor" or previous.get("projectKey") != PROJECT):
        raise ValueError("Runtime state ownership mismatch; refusing overwrite")
    try:
        snapshot = collector()
        metrics = minimal_metrics(snapshot)
        performance = member_assessment(snapshot)
    except Exception as error:
        return {"projectKey": PROJECT, "readComplete": False,
                "status": "MCP_READ_FAILED", "errorType": type(error).__name__}
    tracked = [{k: item[k] for k in ("key", "kind", "category", "statusId",
                                   "assigneeKnown", "assigneeAccountId", "parentKnown", "parentKey",
                                   "dueDateKnown", "dueDate", "cancelled")}
               for item in snapshot["issues"]]
    # Exclude raw text/updated timestamps: ordinary content edits are not scope/status changes.
    fingerprint = hashlib.sha256(json.dumps({"metrics": metrics, "issues": tracked,
                                            "performanceFingerprint": performance["fingerprint"]},
                                           sort_keys=True).encode()).hexdigest()
    changed = fingerprint != previous.get("fingerprint")
    gemini_status = "UNCHANGED"
    assessment = previous.get("lastAssessment")
    assessed_fingerprint = previous.get("lastAssessedFingerprint")
    try:
        credentials(environ)
        enabled = True
    except ValueError:
        enabled = False
    if not enabled:
        gemini_status = "DISABLED_CONFIG"
    elif not metrics["functionalTotal"]:
        gemini_status = "NO_FUNCTIONAL_SCOPE"
    elif fingerprint != assessed_fingerprint:
        try:
            candidate = assessor(snapshot, environ=environ)
            if candidate.get("assessmentComplete") is not True:
                raise ValueError("Assessment not complete")
            assessment = candidate
            assessed_fingerprint = fingerprint
            gemini_status = "DRAFT_COMPLETE"
        except Exception:
            gemini_status = "UNAVAILABLE"
    state = {"owner": "jira_monitor", "schemaVersion": 1, "projectKey": PROJECT,
             "observedAtUtc": snapshot["observedAtUtc"], "readComplete": True,
             "route": "official_atlassian_mcp", "fingerprint": fingerprint,
             "metrics": metrics, "issues": tracked, "geminiStatus": gemini_status,
             "memberAssessment": performance,
             "lastAssessment": assessment, "lastAssessedFingerprint": assessed_fingerprint,
             "scheduledExecutionVerified": False}
    atomic_json(state_path, state)
    return {"projectKey": PROJECT, "readComplete": True, "status": "COLLECTED",
            "sourceObservedAtUtc": snapshot["observedAtUtc"], "scopeChanged": changed,
            "metrics": metrics, "geminiStatus": gemini_status}


def run(directory=RUNTIME, interval=3600, cycles=0, collector=collect):
    if interval < 60 or cycles < 0:
        raise ValueError("Interval must be at least 60 seconds; cycles cannot be negative")
    run_id = str(uuid.uuid4())
    with single_runner(directory):
        number = 0
        while cycles == 0 or number < cycles:
            number += 1
            start = time.monotonic()
            event = cycle(directory, collector=collector)
            timestamp = datetime.now(timezone.utc)
            event.update({"runId": run_id, "pid": os.getpid(), "cycle": number,
                          "completedAtUtc": timestamp.isoformat(), "intervalSeconds": interval,
                          "execution": "local_runner_cycle_not_codex_scheduled_run"})
            with (directory / f"events-{timestamp.date()}.jsonl").open("a", encoding="utf-8") as log:
                log.write(json.dumps(event, ensure_ascii=False) + "\n")
            print(json.dumps(event, ensure_ascii=False), flush=True)
            if cycles and number >= cycles:
                break
            # shortcut: Windows logon supervisor cannot run while logged off/asleep; use an always-on host for 24/7.
            time.sleep(max(0, interval - (time.monotonic() - start)))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=int, default=3600, help="Seconds between cycle starts (>=60)")
    parser.add_argument("--cycles", type=int, default=0, help="Stop after N cycles; 0 means until stopped")
    options = parser.parse_args()
    try:
        run(interval=options.interval, cycles=options.cycles)
    except KeyboardInterrupt:
        pass
    except Exception as error:
        print(json.dumps({"status": "RUNNER_STOPPED", "errorType": type(error).__name__,
                          "message": "Check configuration/storage/other runner; no Jira writes occurred."}))
        sys.exit(1)
