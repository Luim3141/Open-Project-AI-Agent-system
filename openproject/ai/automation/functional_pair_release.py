"""Exact-source completion release from the already deployed integration baseline."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from automation import integration_pair_release as release

release.BASE_IMAGES={'gateway':'sha256:e9af9565b3af52d2b2184bef144aa22cbdab019ecae15f2ccb0b48526f060ed7',
                     'core':'sha256:b5f3913ae8a74e4d37aaba9a5a6a12c14ddbe6d75d885359175a0a5d1f6a3db7'}
release.SOURCES.update({'openproject/ai/gateway/'+name:('gateway','/app/gateway/'+name) for name in (
    'workflow_status.py','workflow_commands.py','knowledge_answer.py','bug_lifecycle.py','native_wbs.py','engineering_planning.py')})
release.SOURCES.update({'openproject/ai/core/overlay/'+path:('core','/app/'+path) for path in (
    'app/controllers/qldapm_ai_controller.rb','app/views/qldapm_ai/_engineering_workflows.html.erb',
    'app/views/qldapm_ai/_engineering_knowledge_results.html.erb')})

if __name__=='__main__':release.main()
