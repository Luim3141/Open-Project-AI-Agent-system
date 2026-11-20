raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
require "action_controller/test_case"
ActionCable.server.config.cable = {"adapter" => "test"}

class QldapmHierarchyTest < ActionController::TestCase
  tests WorkPackagesController

  def setup
    super
    @routes = Rails.application.routes
    @request.host = "localhost:18091"
    @request.session[:user_id] = 8
    @request.session[:updated_at] = Time.current
    @request.env["HTTP_ACCEPT"] = "text/html"
  end

  def test_default_tree_contains_complete_branches_and_starts_collapsed
    get :index, params: {project_id: "qldapm-local"}
    assert_equal 200, @response.status
    assert_select '[data-tree-root]', count: 11
    assert_select '[data-work-package-id]', count: 329
    assert_select 'details[open]', count: 0
    assert_select 'details[data-work-package-id="38"] details[data-work-package-id="49"] [data-work-package-id]', count: 5
    assert_select 'details[data-work-package-id="38"] [data-work-package-id="54"]', count: 0
    assert_select 'a', text: "Bảng / bộ lọc nâng cao"
  end

  def test_pagination_keeps_whole_branches_in_stable_order
    root_ids, all_ids = [], []
    (1..3).each do |page|
      get :index, params: {project_id: "qldapm-local", page:, per_page: 5}
      assert_equal 200, @response.status
      assert_select '[data-tree-root]' do |nodes|
        root_ids.concat(nodes.map { |node| node['data-work-package-id'].to_i })
      end
      assert_select '[data-work-package-id]' do |nodes|
        all_ids.concat(nodes.map { |node| node['data-work-package-id'].to_i })
      end
      assert_select 'details[open]', count: 0
    end
    assert_equal (38..48).to_a, root_ids
    assert_equal 329, all_ids.uniq.size
    assert_equal 329, all_ids.size
  end

  def test_native_table_remains_available
    get :index, params: {project_id: "qldapm-local", native_table: "1"}
    assert_equal 200, @response.status
    assert_select '[data-tree-root]', count: 0
    assert_select 'openproject-base', count: 1
    assert @response.body.include?('event.stopImmediatePropagation()'), "Native editor/table must retain the route back to the Rails tree"
  end

  def test_anonymous_cannot_read_tree
    @request.session.delete(:user_id)
    get :index, params: {project_id: "qldapm-local"}
    assert_includes [302, 403], @response.status
    refute @response.body.include?("AUTH-01")
  end
end

failures = []
Minitest.seed = 1
QldapmHierarchyTest.runnable_methods.each do |name|
  ActiveRecord::Base.transaction do
    result = QldapmHierarchyTest.new(name).run
    result.failures.each { |failure| failures << "#{name}: #{failure.message}" }
    raise ActiveRecord::Rollback
  end
end
failures.each { |failure| puts "HIERARCHY_RED: #{failure}" }
raise "HIERARCHY_REGRESSION_FAILED" unless failures.empty?
puts "Native Work Packages hierarchy, pagination, table fallback and authorization PASS."
