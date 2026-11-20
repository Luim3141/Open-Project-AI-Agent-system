raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
require "action_controller/test_case"
ActionCable.server.config.cable = {"adapter" => "test"}

class QldapmRbacUITest < ActionController::TestCase
  tests QldapmAIController

  def setup
    super
    @routes = Rails.application.routes
    @request.host = "localhost:18091"
    @request.env["HTTP_ACCEPT"] = "text/html"
  end

  def login(login)
    @request.session[:user_id] = User.find_by!(login:).id
    @request.session[:updated_at] = Time.current
  end

  def test_tool_select_matches_real_project_role
    original = Qldapm::AiBridge.method(:call)
    Qldapm::AiBridge.define_singleton_method(:call) { |*| {"result" => {}} }
    %w[pm ba-pm be fe qa].each do |role|
      login(role)
      get :show, params: {project_id: "qldapm-local"}
      assert_response :success
      assert_select 'select[name="tool"] option[value="comment"]', count: 1
      assert_select 'select[name="tool"] option[value="update_work_package"]', count: role == "pm" ? 1 : 0
      assert_select 'select[name="tool"] option[value="create_work_package"]', count: role == "pm" ? 1 : 0
      assert_select 'a[href$="qldapm-ai/permissions"]', count: role == "pm" ? 1 : 0
      assert_select '[role="status"]', minimum: 1 unless role == "pm"
    end
  ensure
    Qldapm::AiBridge.define_singleton_method(:call, original) if original
  end

  def test_permission_monitor_is_pm_only_and_has_no_mutation_form
    %w[ba-pm be fe qa].each do |role|
      login(role)
      get :permissions, params: {project_id: "qldapm-local"}
      assert_response :forbidden
    end
    login("pm")
    get :permissions, params: {project_id: "qldapm-local"}
    assert_response :success
    assert_select 'h2', text: "Role & AI Permissions"
    assert_select 'form[action*="qldapm-ai/permissions"]', count: 0
    assert_includes @response.body, "PM-only"
    refute_match(/AIza[\w-]{20,}/, @response.body)
  end
end

failures = []
assertions = 0
Minitest.seed = 0
QldapmRbacUITest.runnable_methods.each do |name|
  ActiveRecord::Base.transaction do
    result = QldapmRbacUITest.new(name).run
    assertions += result.assertions
    failures.concat(result.failures.map { |failure| "#{name}: #{failure.message}" })
    raise ActiveRecord::Rollback
  end
end
failures.each { |failure| puts failure }
raise "RBAC_UI_FAILED" unless failures.empty?
puts "RBAC native UI: #{QldapmRbacUITest.runnable_methods.size} tests / #{assertions} assertions PASS"
