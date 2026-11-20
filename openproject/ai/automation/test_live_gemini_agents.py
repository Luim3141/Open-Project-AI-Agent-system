"""Test real Gemini Multi-Agent supervisor execution."""
import os
import sys
import pathlib
import json
import time
import uuid
import requests

sys.path.insert(0, str(pathlib.Path("openproject/ai").resolve()))
from gateway.store import Store

def main():
    root = pathlib.Path(os.environ["LOCALAPPDATA"]) / "QLDAPM" / "openproject-ai" / "gateway"
    creds = json.loads((root / "credentials.json").read_text())
    store = Store(root)
    pm_token = store.issue_token(19, "PM", creds["19"])

    prompt = "Phân tích kỹ thuật và kịch bản kiểm thử cho chức năng đăng nhập AUTH-02 #50"
    idempotency_key = f"live-test-{uuid.uuid4()}"
    
    print(f"Submitting AI Run with prompt: '{prompt}'")
    res = requests.post(
        "http://localhost:8090/api/v1/ai-runs",
        headers={
            "Authorization": f"Bearer {pm_token}",
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key
        },
        json={"prompt": prompt}
    )
    print("Start run response:", res.status_code, res.json())
    resp_data = res.json()
    run_id = resp_data.get("id") or resp_data.get("result", {}).get("id")
    if not run_id:
        return

    print(f"Polling AI Run ID: {run_id} ...")
    for i in range(40):
        time.sleep(3)
        poll = requests.get(
            f"http://localhost:8090/api/v1/ai-runs/{run_id}",
            headers={"Authorization": f"Bearer {pm_token}"}
        ).json()
        state = poll.get("state")
        res_obj = poll.get("result") or {}
        msg = res_obj.get("message", "N/A")
        mode = res_obj.get("execution_mode", "N/A")
        print(f"  [{i*3}s] state={state} | mode={mode} | message={msg}")
        if state in ("done", "failed_or_unknown", "cancelled"):
            print("\n=== FINAL AI RUN RESULT ===")
            print("Engine:", res_obj.get("engine"))
            print("Execution Mode:", res_obj.get("execution_mode"))
            print("Model Used:", res_obj.get("model_used"))
            print("Summary / Text:", (res_obj.get("text") or "")[:400])
            agent_outputs = res_obj.get("agent_outputs", [])
            print(f"Total Agent Outputs: {len(agent_outputs)}")
            for out in agent_outputs:
                agent_name = out.get("agent")
                step_id = out.get("step_id")
                result_data = out.get("result", {})
                print(f"  -> Agent '{agent_name}' (Step {step_id}):")
                print(f"     Status: {result_data.get('status')}")
                print(f"     Citations: {result_data.get('citations')}")
                findings = result_data.get("findings", [])
                if findings:
                    print(f"     Findings ({len(findings)}): {findings[:2]}")
            
            # Trace verification
            trace_res = requests.get(
                f"http://localhost:8090/api/v1/agent-runs/{run_id}/trace",
                headers={"Authorization": f"Bearer {pm_token}"}
            )
            print(f"\nTrace endpoint status: {trace_res.status_code}")
            if trace_res.status_code == 200:
                events = trace_res.json().get("result", {}).get("events", [])
                print(f"Trace events recorded: {len(events)}")
                for ev in events[:5]:
                    print(f"  Event: {ev.get('event')} agent={ev.get('agent')} phase={ev.get('phase')}")
            break

if __name__ == "__main__":
    main()
