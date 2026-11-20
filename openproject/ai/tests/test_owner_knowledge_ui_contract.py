import json,re,subprocess,unittest
from pathlib import Path
class KnowledgeUiContract(unittest.TestCase):
 def test_native_version_uses_actual_gateway_field(self):
  source=(Path(__file__).parents[1]/'core/overlay/app/views/qldapm_ai/_engineering_knowledge_results.html.erb').read_text(encoding='utf-8')
  expr=re.search(r'Native version <%= (.*?) %>',source).group(1)
  ruby="require 'json';d=JSON.parse(STDIN.read);item={'lock_version'=>2};puts eval(d['expr'])"
  result=subprocess.run(['docker','exec','-i','qldapm-openproject-web-1','ruby','-e',ruby],input=json.dumps({'expr':expr}).encode(),capture_output=True,check=True,timeout=20)
  self.assertEqual(result.stdout.decode().strip(),'2')
if __name__=='__main__':unittest.main()
