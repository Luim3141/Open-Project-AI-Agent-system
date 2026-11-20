require 'json'
require 'active_support/all'
require ARGV.fetch(0)
module Qldapm::Rbac
  def self.role(*,**);'AI_SYSTEM_OWNER';end
end
class User
  def self.current;new;end
  def admin?;false;end
end
source=JSON.parse(STDIN.read).fetch('controller')
method=source.split("  def command\n",2).last.split("  def confirm\n",2).first
klass=Class.new do
 attr_reader :status
 def engineering_project?;true;end
 def params;{tool:'engineering_status',arguments:'{}',request_id:'11111111-1111-4111-8111-111111111111'};end
 def bridge(*);raise Qldapm::AiBridge::RequestError.new('not sent',429,code:'AI_BRIDGE_BUSY',retry_after:1);end
 def render_engineering(status:);@status=status;end
 def response;self;end
 def headers;@headers||={};end
end
klass.class_eval("def command\n"+method)
klass.class_eval("def bridge_error_status(error)\n"+source.split("  def bridge_error_status(error)\n",2).last.split("\n  end",2).first+"\nend")
c=klass.new;c.command
raise 'BUSY_STATUS_LOST' unless c.status==429
raise 'RETRY_AFTER_LOST' unless c.headers['Retry-After']=='1'
puts 'PASS command rejects busy before Gateway without remapping429 or retrying mutation'
