"""Read-only protected scope hashes, independent of previous phase snapshots."""
from pathlib import Path
import os
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/button-audit'
private.mkdir(exist_ok=True)
legacy=Path(__file__).parent.parent/'cc-stabilization/native_integrity.py'
source=legacy.read_text().replace("operator/cc-stabilization'","operator/button-audit'")
exec(compile(source,str(legacy),'exec'))
