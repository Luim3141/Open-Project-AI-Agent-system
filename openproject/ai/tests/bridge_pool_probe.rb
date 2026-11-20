require 'json'
require 'net/http'
require 'tempfile'
require 'puma'
require 'active_support/core_ext/numeric/bytes'
require ARGV.fetch(0)
# Isolated component fixture: two Puma servers model the existing callback chain.
begin
key=Tempfile.new('bridge-fixture');key.write('fixture-only-signing-key');key.flush;ENV['QLDAPM_UI_KEY_FILE']=key.path
project=Struct.new(:id).new(6);actor=Struct.new(:id).new(18)
core_app=lambda do |env|
 if env['PATH_INFO']=='/native'
  [200,{'content-type'=>'application/json'},['{}']]
 else
  begin
   result=Qldapm::AiBridge.call(project,actor,'command',{action:'observer_task_progress',arguments:{task_id:397}})
   [200,{'content-type'=>'application/json'},[JSON.generate(result)]]
  rescue Qldapm::AiBridge::RequestError=>e
   [e.status,{'content-type'=>'application/json'},[JSON.generate(error:e.code)]]
  end
 end
end
gateway_app=lambda do |_env|
 sleep 0.15
 begin
  Net::HTTP.start('127.0.0.1',8080,nil,open_timeout:1,read_timeout:0.5){|http|http.get('/native')}
  [200,{'content-type'=>'application/json'},['{"result":{}}']]
 rescue Timeout::Error
  [503,{'content-type'=>'application/json'},['{"error":"OPENPROJECT_UNAVAILABLE_OUTCOME_MAY_BE_UNKNOWN"}']]
 end
end
core=Puma::Server.new(core_app,nil,{min_threads:4,max_threads:4});core.add_tcp_listener('127.0.0.1',8080)
gateway=Puma::Server.new(gateway_app,nil,{min_threads:8,max_threads:8});gateway.add_tcp_listener('127.0.0.1',8090)
core.run;gateway.run;sleep 0.1
start=Process.clock_gettime(Process::CLOCK_MONOTONIC)
statuses=4.times.map{Thread.new{Net::HTTP.start('127.0.0.1',8080,nil,open_timeout:1,read_timeout:12){|http|http.get('/bridge').code.to_i}}}.map(&:value)
puts JSON.generate(scope:'ISOLATED PUMA CALLBACK COMPONENT, NO MAIN DATA',threads:4,concurrent_bridge_requests:4,statuses:statuses.sort,total_ms:((Process.clock_gettime(Process::CLOCK_MONOTONIC)-start)*1000).round(2))
raise 'PUMA_CALLBACK_STARVATION' unless statuses.sort==[200,200,429,429]
ensure
 core&.stop(true);gateway&.stop(true);key&.close!
end
