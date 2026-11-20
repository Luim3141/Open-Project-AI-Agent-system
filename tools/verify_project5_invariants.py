"""Deep verification of Project 5 Invariants against baseline."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_FILE = ROOT / "docs/ai/engineering/project5_invariants_baseline.json"

def main():
    print("=================================================================")
    print("VERIFYING PROJECT 5 INVARIANTS (FINDING E)")
    print("=================================================================\n")

    baseline = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))

    # Query current live state from PostgreSQL
    psql_cmd = [
        "docker", "exec", "qldapm-openproject-db-1", "psql",
        "-U", "postgres", "-d", "openproject", "-t", "-A", "-F", ",",
        "-c", """
        SELECT 
            count(*),
            min(id),
            max(id),
            max(lock_version),
            to_char(max(updated_at) AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"')
        FROM work_packages 
        WHERE project_id = 5;
        """
    ]
    res = subprocess.run(psql_cmd, capture_output=True, text=True, check=True)
    parts = res.stdout.strip().split(",")
    live_count = int(parts[0])
    live_min_id = int(parts[1])
    live_max_id = int(parts[2])
    live_max_lock = int(parts[3])
    live_latest_updated = parts[4]

    # Query status distribution
    res_status = subprocess.run([
        "docker", "exec", "qldapm-openproject-db-1", "psql",
        "-U", "postgres", "-d", "openproject", "-t", "-A", "-F", ":",
        "-c", "SELECT status_id, count(*) FROM work_packages WHERE project_id = 5 GROUP BY status_id ORDER BY status_id;"
    ], capture_output=True, text=True, check=True)
    live_status_dist = {}
    for line in res_status.stdout.strip().splitlines():
        if line:
            sid, cnt = line.split(":")
            live_status_dist[sid] = int(cnt)

    # Query members
    res_members = subprocess.run([
        "docker", "exec", "qldapm-openproject-db-1", "psql",
        "-U", "postgres", "-d", "openproject", "-t", "-A", "-F", ":",
        "-c", """
        SELECT m.user_id, r.name 
        FROM members m 
        JOIN member_roles mr ON m.id = mr.member_id 
        JOIN roles r ON mr.role_id = r.id 
        WHERE m.project_id = 5 
        ORDER BY m.user_id;
        """
    ], capture_output=True, text=True, check=True)
    live_members = {}
    for line in res_members.stdout.strip().splitlines():
        if line:
            uid, rname = line.split(":")
            live_members.setdefault(int(uid), []).append(rname)

    checks = []

    # Check 1: WP Count
    c1 = (live_count == baseline["work_package_count"])
    checks.append(("Work Package Count", f"{live_count} == {baseline['work_package_count']}", c1))

    # Check 2: Min ID
    c2 = (live_min_id == baseline["min_id"])
    checks.append(("Min Work Package ID", f"{live_min_id} == {baseline['min_id']}", c2))

    # Check 3: Max ID
    c3 = (live_max_id == baseline["max_id"])
    checks.append(("Max Work Package ID", f"{live_max_id} == {baseline['max_id']}", c3))

    # Check 4: Max Lock Version
    c4 = (live_max_lock == baseline["max_lock_version"])
    checks.append(("Max Lock Version (No modifications)", f"{live_max_lock} == {baseline['max_lock_version']}", c4))

    # Check 5: Latest Updated At
    c5 = (live_latest_updated == baseline["latest_updated_at"])
    checks.append(("Latest Updated At (Frozen in time)", f"{live_latest_updated} == {baseline['latest_updated_at']}", c5))

    # Check 6: Status Distribution
    c6 = (live_status_dist == baseline["status_distribution"])
    checks.append(("Status Distribution", f"{live_status_dist} == {baseline['status_distribution']}", c6))

    # Check 7: Members Count
    c7 = (len(live_members) == baseline["members_count"])
    checks.append(("Members Count", f"{len(live_members)} == {baseline['members_count']}", c7))

    for name, detail, passed in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")

    all_passed = all(c[2] for c in checks)
    print("\n-----------------------------------------------------------------")
    print(f"OVERALL INVARIANT VERIFICATION: {'>>> ALL 7 INVARIANTS HELD UNTOUCHED <<<' if all_passed else '>>> INVARIANT VIOLATION DETECTED <<<'}")
    print("-----------------------------------------------------------------")

    assert all_passed, "Project 5 invariant checks must strictly hold 100%!"

if __name__ == "__main__":
    main()
