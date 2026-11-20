// Superseded native-submit/mode-only harness now exercises real Phase3 JSON transport.
require('./test_owner_live_transport.js');
const fs=require('node:fs'),assert=require('node:assert/strict');
const source=fs.readFileSync(require('node:path').join(__dirname,'../core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb'),'utf8');
for(const fake of ['2,132 Vector Points Active','2,132 Points','● ACTIVE (16/16)','● ONLINE (HTTP 200)','0 LLM Calls','No LLM Reasoning','PM & BA Verified'])assert(!source.includes(fake),'unverified status: '+fake);
assert(source.includes('data-qcc-mode'));
