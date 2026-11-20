# Real Rails/controller/view regression on an isolated restored Main database only.
raise "QUALIFICATION_ONLY" unless ENV["QLDAPM_QUALIFICATION"] == "codex-main-20261020"
raise "WRONG_DATABASE" unless ActiveRecord::Base.connection_db_config.configuration_hash[:host] == "qa-db"
require "action_controller/test_case"
ActionCable.server.config.cable = {"adapter" => "test"}

class MainAssistantContextUAT < ActionController::TestCase
  tests QldapmAIController

  def setup
    super
    @routes = Rails.application.routes
    @request.host = "localhost:18088"
    actor = User.find_by!(login: "ba-pm")
    project = Project.find_by!(identifier: "qldapm-local")
    raise "WRONG_ROLE" unless Qldapm::Rbac.role(project, actor) == "PM"
    @request.session[:user_id] = actor.id
    @request.session[:updated_at] = Time.current
    @request.env["HTTP_ACCEPT"] = "text/html"
    @bridge_original = Qldapm::AiBridge.method(:call)
    @calls=[]
    calls=@calls
    Qldapm::AiBridge.define_singleton_method(:call) do |_p, a, _operation, command|
      raise "WRONG_ACTOR" unless a.id == actor.id
      action=command.fetch(:action);calls << action
      raise ArgumentError,"SYNTHETIC_COMMAND_DENIED" if action=="get_work_package"
      result=case action
      when "identity" then {"user_id" => actor.id,"role" => "PM"}
      when "get_assistant_status" then {"gateway" => "ok","openproject" => "authenticated","gateway_mode" => "native","gemini" => {"state" => "OFF"}}
      when "get_action_history" then {"runs" => [],"proposals" => [],"audit" => []}
      when "analyze" then {"count" => 329,"by_status" => {"NEW" => 329},"overdue_ids" => [],"control_center" => {"progress" => {"total" => 0}}}
      else {}
      end
      {"result" => result}
    end
  end

  def teardown
    Qldapm::AiBridge.define_singleton_method(:call,@bridge_original)
    super
  end

  def submit(tool, arguments="{}")
    get :show, params: {project_id: "qldapm-local"}
    assert_response :success
    token=@controller.send(:form_authenticity_token)
    @controller.commit_csrf_token(@request)
    # Controller tests reuse the instance; a real POST starts without the previous GET's assigns.
    %i[@connection @dashboard @history @control_center].each do |name|
      @controller.remove_instance_variable(name) if @controller.instance_variable_defined?(name)
    end
    post :command, session: @request.session.to_hash, params: {project_id: "qldapm-local",authenticity_token: token,tool: tool,arguments: arguments}
  end

  def assert_dashboard
    assert_select '#ai-progress + p.qldapm-ai-count',text: "329"
    assert_includes @response.body,"Gateway: ok"
    refute_includes @response.body,"Chưa tải được Control Center"
    assert_includes @response.body,"Agent registry"
  end

  def test_successful_post_keeps_actual_cards
    submit("identity")
    assert_response :success
    assert_dashboard
    assert_equal 1,@calls.count("identity")
  end

  def test_denied_post_keeps_error_and_actual_cards
    submit("get_work_package")
    assert_equal 422,@response.status
    assert_includes @response.body,"SYNTHETIC_COMMAND_DENIED"
    assert_dashboard
    assert_equal 1,@calls.count("get_work_package")
  end

  def test_invalid_json_keeps_cards_without_submitting_command
    submit("identity","{")
    assert_equal 422,@response.status
    assert_includes @response.body,"Arguments JSON"
    assert_dashboard
    assert_equal 0,@calls.count("identity")
  end
end

Minitest.seed=0
failures=[];assertions=0
MainAssistantContextUAT.runnable_methods.each do |name|
  ActiveRecord::Base.transaction do
    result=MainAssistantContextUAT.new(name).run
    assertions+=result.assertions
    failures.concat(result.failures.map { |f| "#{name}: #{f.message}" })
    raise ActiveRecord::Rollback
  end
end
puts JSON.generate(tests: 3,assertions: assertions,failures: failures,real_rails_views: true,bridge: "synthetic",native_business_writes: 0,provider_calls: 0)
raise "MAIN_CONTEXT_UAT_FAILED" unless failures.empty?
