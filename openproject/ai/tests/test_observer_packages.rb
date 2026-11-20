require 'minitest/autorun'
require 'ostruct'
require ARGV.fetch(0)
class Project
  def self.visible(user);self;end
  def self.find(id);OpenStruct.new(id: id, identifier: id==6 ? 'ai-dev-demo' : 'other');end
end
module Qldapm::Rbac
  def self.role(project,user,fresh:);raise unless fresh;user.role;end
end
class ObserverPackagesTest < Minitest::Test
  def user(allowed: true,role: 'PM')
    u=OpenStruct.new(role: role)
    u.define_singleton_method(:allowed_in_project?){|*|allowed}
    u.define_singleton_method(:allowed_in_work_package?){|_,item|allowed && item.id==1}
    u
  end
  def test_current_project_and_membership_fail_closed
    assert_raises(ArgumentError){Qldapm::ObserverPackages.project_for(user,5)}
    assert_raises(ArgumentError){Qldapm::ObserverPackages.project_for(user(allowed:false),6)}
    assert_raises(ArgumentError){Qldapm::ObserverPackages.project_for(user(role:nil),6)}
    assert_equal 6,Qldapm::ObserverPackages.project_for(user,6).id
  end
  def test_ids_are_strict_and_bounded
    [[],[true],[0],[-1],(1..101).to_a].each{|ids|assert_raises(ArgumentError){Qldapm::ObserverPackages.call(user,6,ids)}}
  end
  def test_invisible_items_and_full_representers_are_excluded
    items=[1,2].map{|id|OpenStruct.new(id:id,subject:'Task',lock_version:1,status_id:2,status:OpenStruct.new(name:'NEW'),type:OpenStruct.new(name:'Task'))}
    result=Qldapm::ObserverPackages.render_items(user,Project.find(6),items)
    assert_equal [1],result.map{|r|r[:id]}
    refute result.first.key?(:description)
    assert_equal '/api/v3/projects/6',result.first['_links'][:project][:href]
  end
end
