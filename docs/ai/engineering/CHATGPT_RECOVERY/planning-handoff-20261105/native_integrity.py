"""Reuse protected read-only scope checks with independent incident snapshot paths."""
from pathlib import Path
import os
OUT=Path(__file__).parent
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/planning-handoff-20261105'
private.mkdir(exist_ok=True)
legacy=OUT.parent/'cc-stabilization/native_integrity.py'
source=legacy.read_text().replace("operator/cc-stabilization'","operator/planning-handoff-20261105'")
exec(compile(source,str(legacy),'exec'))
