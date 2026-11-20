require 'active_support/core_ext/hash'
require 'active_support/core_ext/object/deep_dup'
require 'digest'
require 'time'
require_relative 'test_owner_ui_tool_routes'
require_relative 'overlay/app/services/qldapm/gate_actions'
class User
  def self.active = self
  def self.where(id:) = OpenStruct.new(exists?: registry[id]&.active?)
  def self.find(id) = registry.fetch(id)
  def self.execute_as(*) = yield
  def allowed_in_work_package?(*) = true
end
class GateActionFixture
  attr_accessor :project,:qldapm_gate,:lock_version,:assigned_to_id,:status
  def initialize
    @project=OpenStruct.new(id:5,identifier:'qldapm-local');@qldapm_gate={};@lock_version=0;@assigned_to_id=21;@status=OpenStruct.new(name:'NEW')
  end
  def self.transaction = yield
  def id = 999
  def qldapm_managed? = true
  def qldapm_lock_projects = nil
  def reload = self
  def qldapm_actor(user) = {'id'=>user.id,'role'=>Qldapm::Rbac.role(project,user,fresh:true)}
  def save = (@lock_version+=1; true)
end
actors={18=>User.new(18,'op-owner',true),19=>User.new(19,'ba-pm'),20=>User.new(20,'pm'),21=>User.new(21,'be'),22=>User.new(22,'fe'),23=>User.new(23,'qa'),99=>User.new(99,'other-admin',true)}
actors.each { |id,user| User.registry[id]=user }
operations={'acceptance_criteria'=>{'text'=>'Explicit verified fixture criteria'},'checklist_add'=>{'text'=>'Check verified fixture result'},
  'classification'=>{'stream'=>'development','kind'=>'work','reference'=>'fixture:requirement-1'},'reviewer'=>{'user_id'=>19}}
[18,19].each do |id|
  operations.each do |operation,value|
    item=GateActionFixture.new;value=value.merge('user_id'=>18) if id==19 && operation=='reviewer'
    Qldapm::GateActions.new(item,actors[id]).call(operation,value,0)
    check(item.lock_version==1,"MANAGER_GATE_OPERATION_DENIED_#{id}_#{operation}")
  end
  item=GateActionFixture.new;actions=Qldapm::GateActions.new(item,actors[id]);actions.call('checklist_add',{'text'=>'Explicit checklist fixture'},0)
  key=item.qldapm_gate['checklist'][0]['id'];actions.call('checklist',{'id'=>key,'done'=>true,'reference'=>'fixture:checklist-1'},1)
  check(item.qldapm_gate['checklist'][0]['done'],"OWNER_OR_PM_CHECKLIST_DENIED_#{id}")
end
[20,21,22,23,99].each do |id|
  operations.each do |operation,value|
    item=GateActionFixture.new
    begin
      Qldapm::GateActions.new(item,actors[id]).call(operation,value,0)
      raise "GATE_ROLE_ESCALATED_#{id}_#{operation}"
    rescue ArgumentError => error
      check(error.message=='PM_REQUIRED',"UNEXPECTED_ROLE_POLICY_#{id}");check(item.lock_version==0,'DENIED_GATE_PERSISTED')
    end
  end
end
[18,19].each do |id|
  item=GateActionFixture.new;item.assigned_to_id=18
  begin
    Qldapm::GateActions.new(item,actors[id]).call('reviewer',{'user_id'=>18},0)
    raise 'SELF_REVIEWER_ALLOWED'
  rescue ArgumentError => error
    check(error.message=='MEMBER_REVIEWER_REQUIRED','WRONG_SELF_REVIEW_POLICY')
  end
end
puts 'Owner/PM GateActions positive operations, six-role negative matrix and independent reviewer policy PASS (isolated fixtures)'
