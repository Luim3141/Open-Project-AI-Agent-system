import urllib.request
import json
import os
import sys

def get_token():
    env_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if env_token:
        return env_token.strip()
    
    from pathlib import Path
    for p in [
        Path("C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/gateway/config.json"),
        Path("/state/config.json")
    ]:
        if p.is_file():
            try:
                cfg = json.loads(p.read_text(encoding="utf-8"))
                tok = cfg.get("engineering", {}).get("github_token") or cfg.get("github_token")
                if tok:
                    return str(tok).strip()
            except Exception:
                pass
    return None

def audit_github():
    token = get_token()
    url = 'https://api.github.com/repos/Luim3141/mini-task-manager/pulls?state=all'
    headers = {
        'User-Agent': 'QLDAPM-Audit/1.0',
        'Accept': 'application/vnd.github+json'
    }
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req, timeout=15) as resp:
        prs = json.loads(resp.read().decode('utf-8'))

    print(f"Total PRs returned: {len(prs)}")
    audit_data = []
    for pr in sorted(prs, key=lambda x: x['number']):
        num = pr['number']
        title = pr['title']
        state = pr['state']
        merged_at = pr.get('merged_at')
        merged_by = pr.get('merged_by', {}).get('login') if pr.get('merged_by') else None
        base = pr['base']['ref']
        head = pr['head']['ref']
        created_at = pr['created_at']
        updated_at = pr['updated_at']
        merge_sha = pr.get('merge_commit_sha')
        is_merged = merged_at is not None
        
        info = {
            "pr_number": num,
            "title": title,
            "state": state,
            "is_merged": is_merged,
            "merged_at": merged_at,
            "merged_by": merged_by,
            "base_ref": base,
            "head_ref": head,
            "merge_commit_sha": merge_sha,
            "created_at": created_at,
            "updated_at": updated_at
        }
        audit_data.append(info)
        print(f"PR #{num}: [{state.upper()}] \"{title}\"")
        print(f"  Base: {base} <- Head: {head}")
        print(f"  Created: {created_at} | Updated: {updated_at}")
        print(f"  Merged: {merged_at} by {merged_by} | Merge SHA: {merge_sha}")
        print("-" * 60)
        
    return audit_data

if __name__ == '__main__':
    audit_github()
