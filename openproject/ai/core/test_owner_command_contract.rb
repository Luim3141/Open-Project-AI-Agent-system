# Actual controller command method, isolated collaborator doubles; no browser/Native writes.
require 'json'
require 'active_support/all'
class ApplicationController
  def self.before_action(*);end
  def self.authorize_with_permission(*);end
end
module Qldapm
 module Rbac
  def self.role(*,**);'AI_SYSTEM_OWNER';end
  def self.ai_system_owner?(*,**);true;end
 end
 class AiBridge;class RequestError < ArgumentError;attr_reader :status;end;end
end
class User
 def self.current;new;end
 def admin?;true;end
end
Object.class_eval { def present?; !blank?; end } unless nil.respond_to?(:present?)
eval(STDIN.read,TOPLEVEL_BINDING,'qldapm_ai_controller.rb')
class OwnerFixture < QldapmAIController
 attr_reader :calls
 def initialize(tool,arguments,extra={})
  @params={tool:tool,arguments:JSON.generate(arguments),request_id:'10000000-0000-4000-8000-000000000001'}.merge(extra)
  @calls=[]
 end
 def params;@params;end
 def engineering_project?;true;end
 def reject!;@reject=true;end
 def bridge(action,arguments,key=nil)
  @calls << [action,arguments,key]
  return {'result'=>{'backlog'=>[],'tasks'=>[]}} if action=='engineering_status'
  return {'result'=>{'accepted'=>false,'reason_code'=>'ENGINEERING_STATE_REVISION_CONFLICT'}} if @reject
  {'correlation_id'=>'trace-1','result'=>{'command_id'=>'cmd-1','message'=>'Acknowledged'}}
 end
 def render_engineering(status: :ok); {status:status,result:@result,correlation_id:@command_correlation_id,error:@error};end
end
f=OwnerFixture.new('engineering_plan',{'native_id'=>379,'lock_version'=>4,'unit'=>'feature-intake'},{engineering_feedback:'Add feature'})
r=f.command
raise 'INVALID_RUN_ONCE_CONTROL_SENT_AND_SWALLOWED' if f.calls.any?{|a,b,k|a=='engineering_control'}
raise 'REQUEST_ID_NOT_PROPAGATED' unless f.calls.find{|a,b,k|a=='engineering_plan'}[2]=='10000000-0000-4000-8000-000000000001'
raise 'CORRELATION_NOT_RETURNED' unless r[:correlation_id]=='trace-1'
f=OwnerFixture.new('engineering_control',{'mode'=>'AUTO'},{expected_revision:'7'});f.command
raise 'STALE_REVISION_NOT_FORWARDED' unless f.calls.find{|a,b,k|a=='engineering_control'}[1]['expected_revision']==7
f=OwnerFixture.new('engineering_control',{'mode'=>'AUTO'});f.reject!;r=f.command
raise 'REJECTED_COMMAND_REPORTED_SUCCESS' unless r[:status]==:conflict && r[:error]=='ENGINEERING_STATE_REVISION_CONFLICT'
f=OwnerFixture.new('engineering_report_schedule_update',{});r=f.command
raise 'EMPTY_SCHEDULE_FALSE_SUCCESS' unless f.calls.empty? && r[:error].include?('Chưa nhận được')
f=OwnerFixture.new('engineering_report_schedule_update',{'daily_minute'=>1,'expected_updated'=>123.5});f.command
raise 'SCHEDULE_VERSION_NOT_FORWARDED' unless f.calls.find{|a,b,k|a=='engineering_report_schedule_update'}[1]['expected_updated']==123.5
puts 'PASS actual controller: owner command, no swallowed mode write, stable request UUID, correlation and expected revision; auth tested separately'
