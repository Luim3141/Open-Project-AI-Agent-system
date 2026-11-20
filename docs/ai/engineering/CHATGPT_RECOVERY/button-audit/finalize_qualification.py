"""Exact candidate evidence gate using established pair-release contract."""
from pathlib import Path
import sys
import release_buttons
source=(Path(__file__).parent.parent/'cc-stabilization/finalize_qualification.py').read_text()
source=source.replace("importlib.import_module('release_caption' if caption else 'release_reports' if reports else 'release_polish' if polish else 'release_cc')","importlib.import_module('release_buttons')")
source=source.replace("'test_report_reader.js']","'test_report_reader.js','test_cc_modal_focus.js']")
source=source.replace("(OUT/('qualification'+suffix+'.json'))","(OUT/'qualification.json')")
sys.argv=[__file__,'--caption']
exec(compile(source,__file__,'exec'))
