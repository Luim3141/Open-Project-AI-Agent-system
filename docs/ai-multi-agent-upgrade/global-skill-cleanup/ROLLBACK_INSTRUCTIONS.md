# ROLLBACK INSTRUCTIONS — GLOBAL SKILLS CLEANUP
**Backup Location:** `D:\AI_Backups\antigravity_global_skills_precleanup_20261017_215106`  
**Backup Timestamp:** `20261017_215106`  
**Total Verified Skills in Backup:** `1463`

## 1. Quick Rollback of All Deleted Skills
If you ever want to restore all deleted skills exactly to their original state:

### Using PowerShell:
```powershell
# Restore all deleted skills from backup
$backupDir = "D:\AI_Backups\antigravity_global_skills_precleanup_20261017_215106"
$targetDir = "C:\Users\LUIM\.gemini\config\skills"

Get-ChildItem -Path $backupDir -Directory | ForEach-Object {
    $dest = Join-Path $targetDir $_.Name
    if (-not (Test-Path $dest)) {
        Write-Host "Restoring: $($_.Name)"
        Copy-Item -Path $_.FullName -Destination $dest -Recurse -Force
    }
}
```

### Using Python:
```python
import shutil
from pathlib import Path

backup_dir = Path(r"D:\AI_Backups\antigravity_global_skills_precleanup_20261017_215106")
target_dir = Path(r"C:\Users\LUIM\.gemini\config\skills")

for d in backup_dir.iterdir():
    if d.is_dir():
        dest = target_dir / d.name
        if not dest.exists():
            print(f"Restoring: {d.name}")
            shutil.copytree(d, dest)
```

## 2. Selective Rollback of a Single Skill
To restore a specific skill (e.g. `azure-cosmos-db-py`):
```powershell
Copy-Item -Path "D:\AI_Backups\antigravity_global_skills_precleanup_20261017_215106\azure-cosmos-db-py" -Destination "C:\Users\LUIM\.gemini\config\skills\azure-cosmos-db-py" -Recurse -Force
```

## 3. Backup Integrity Verification
All 1463 skill folders in `D:\AI_Backups\antigravity_global_skills_precleanup_20261017_215106` were verified with SHA-256 tree checksums prior to deletion.
See [`BACKUP_VERIFICATION.json`](file:///D:/AI project/QLDAPM chat/docs/ai-multi-agent-upgrade/global-skill-cleanup/results/20261017_215312/BACKUP_VERIFICATION.json) for the full cryptographic manifest.
