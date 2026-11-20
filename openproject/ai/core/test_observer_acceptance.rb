require 'ostruct'
require 'minitest/autorun'
require_relative 'overlay/app/services/qldapm/observer_acceptance'

class ObserverAcceptanceTest < Minitest::Test
  class JournalAssociation
    def initialize(rows); @rows = rows; end
    def includes(*); self; end
    # Rails association already orders ASC; order(DESC) appends and does not replace it.
    def order(**); self; end
    def reorder(**); @rows = @rows.sort_by(&:version).reverse; self; end
    def limit(*); self; end
    def to_a; @rows; end
  end

  def test_native_association_default_order_does_not_hide_final_owner_transition
    rows = [1, 9, 9, 41, 35].each_with_index.map do |status, index|
      OpenStruct.new(id: 100 + index, version: index + 1, user_id: 18,
        created_at: Time.at(1000 + index), cause_type: nil, data: OpenStruct.new(status_id: status))
    end
    item = OpenStruct.new(id: 397, lock_version: 11, status_id: 35,
      project: OpenStruct.new(id: 6, identifier: 'ai-dev-demo'),
      status: OpenStruct.new(name: 'DONE', :is_closed? => true),
      :qldapm_managed? => false, journals: JournalAssociation.new(rows))
    packages = Object.new
    packages.define_singleton_method(:visible) { |_| packages }
    packages.define_singleton_method(:find) { |_| item }
    users = Object.new
    users.define_singleton_method(:active) { users }
    users.define_singleton_method(:find_by) { |**| OpenStruct.new(id: 18) }
    role = Object.new
    role.define_singleton_method(:role) { |*args, **kwargs| 'AI_SYSTEM_OWNER' }
    Object.const_set(:WorkPackage, packages)
    Object.const_set(:User, users)
    Qldapm.const_set(:Rbac, role)
    reader = Object.new
    reader.define_singleton_method(:allowed_in_work_package?) { |*| true }
    result = Qldapm::ObserverAcceptance.call(reader, 397)
    assert result['verified']
    assert_equal 104, result['status_change']['journal_id']
    assert_equal 18, result['status_change']['actor_id']
  ensure
    Object.send(:remove_const, :WorkPackage) if Object.const_defined?(:WorkPackage)
    Object.send(:remove_const, :User) if Object.const_defined?(:User)
    Qldapm.send(:remove_const, :Rbac) if Qldapm.const_defined?(:Rbac)
  end

  def journal(id, status)
    OpenStruct.new(id: id, data: OpenStruct.new(status_id: status))
  end
  def test_uses_actual_final_transition_not_latest_comment_or_initial_status
    rows=[journal(1, 1), journal(2, 25), journal(3, 25)]
    pair=Qldapm::ObserverAcceptance.last_transition(rows, 25)
    assert_equal 2, pair.last.id
    assert_nil Qldapm::ObserverAcceptance.last_transition([journal(1,25)],25)
  end
  def test_reopening_removes_prior_completion_and_later_completion_replaces_it
    rows=[journal(1,1),journal(2,25),journal(3,1)]
    assert_nil Qldapm::ObserverAcceptance.last_transition(rows,25)
    rows << journal(4,25)
    assert_equal 4,Qldapm::ObserverAcceptance.last_transition(rows,25).last.id
  end
end
