"""Reuse the qualified Telegram image-only operator with this phase's baseline/evidence directory."""
from pathlib import Path
OUT=Path(__file__).resolve().parent
original=OUT.parent/'functional-audit/bot_release.py'
exec(compile(original.read_text(encoding='utf-8'),str(original),'exec'),{'__name__':'__main__','__file__':str(OUT/'bot_release.py')})
