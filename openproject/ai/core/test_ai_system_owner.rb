# Pure Ruby policy qualification; no Rails boot, database or Native writes.
require "ostruct"
require_relative "overlay/app/models/qldapm/gate_policy"
require_relative "overlay/app/models/qldapm/rbac"

class User
  attr_accessor :id, :login, :enabled, :administrator
  def initialize(id, login, admin = false)
    @id, @login, @administrator, @enabled = id, login, admin, true
  end
  def active? = enabled
  def admin? = administrator
  def self.find_by(id:) = registry[id]
  def self.registry = (@registry ||= {})
end

def check(value, label)
  raise label unless value
end

project = OpenStruct.new(id: 5, identifier: "qldapm-local")
owner = User.new(18, "op-owner", true)
User.registry[18] = owner
check(Qldapm::Rbac.ai_system_owner?(project, owner), "OWNER_CAPABILITY_MISSING")
check(Qldapm::Rbac.role(project, owner) == "AI_SYSTEM_OWNER", "OWNER_MUST_NOT_BECOME_PM")
check(Qldapm::Rbac.pm?(project, owner), "OWNER_BUSINESS_MANAGER_MISSING")
check(!Qldapm::Rbac.ai_system_owner?(project, User.new(19, "ba-pm", true)), "OTHER_ADMIN_ESCALATED")
check(!Qldapm::Rbac.ai_system_owner?(project, User.new(18, "renamed-admin", true)), "WRONG_LOGIN_ESCALATED")
check(!Qldapm::Rbac.ai_system_owner?(OpenStruct.new(id: 3, identifier: "qldapm-local"), owner), "OTHER_PROJECT_ESCALATED")
User.registry[18] = User.new(18, "op-owner", false)
check(!Qldapm::Rbac.ai_system_owner?(project, owner, fresh: true), "STALE_ADMIN_STILL_AUTHORIZED")
User.registry[18] = owner
owner.enabled = false
check(!Qldapm::Rbac.ai_system_owner?(project, owner), "INACTIVE_OWNER_ESCALATED")
owner.enabled = true

policy = Qldapm::GatePolicy.new
item = {"type" => "Task", "assignee" => 18, "data" => {"reviewer_id" => 18, "contributors" => []}, "children" => []}
check(!policy.can_approve?(item, {"id" => 18, "role" => "AI_SYSTEM_OWNER"}, "test"), "OWNER_SELF_APPROVAL_ESCAPED")
item["assignee"] = 21
check(policy.can_approve?(item, {"id" => 18, "role" => "AI_SYSTEM_OWNER"}, "test"), "OWNER_INDEPENDENT_APPROVAL_MISSING")
%w[BA BA-PM BE FE QA].each do |role|
  check(!policy.can_approve?(item, {"id" => 20, "role" => role}, "test"), "LEGACY_ROLE_ESCALATED")
end
puts "AI_SYSTEM_OWNER: identity/revocation/project/other-admin/independence policy PASS"
