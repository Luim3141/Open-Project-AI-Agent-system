"""Run established immutable-image regressions plus schedule concurrency tests."""
from pathlib import Path
import sys
import release_buttons
legacy=Path(__file__).parent.parent/'cc-stabilization'
source=(legacy/'verify_image.py').read_text()
source=source.replace("importlib.import_module('release_reports' if reports else 'release_polish' if polish else 'release_cc')","importlib.import_module('release_buttons')")
source=source.replace("image=manifest['images']['gateway']","tests.extend(['test_engineering_schedule_contract','test_engineering','test_engineering_continuation','test_engineering_core_recovery','test_n8n_lifecycle_outbox'])\nimage=manifest['images']['gateway']")
sys.argv=[__file__,'--reports']
exec(compile(source,str(legacy/'verify_image.py'),'exec'))
