"""Reuse actual isolated Native clone; Core HTTP proof is unchanged exact image."""
from pathlib import Path
OUT=Path(__file__).parent
script=(OUT.parent/'button-audit/qualify_buttons.py').read_text().replace('release_buttons','release_planning')
marker="source=source.replace('clone-qualification-v9.json','core-reuse-proof.json')"
assert script.count(marker)==1
script=script.replace(marker,marker+"\nsource=source.replace(\"OUT/'core-reuse-proof.json'\",\"OUT.parent/'button-audit/core-reuse-proof.json'\")")
exec(compile(script,str(OUT/'qualify_planning.py'),'exec'))
