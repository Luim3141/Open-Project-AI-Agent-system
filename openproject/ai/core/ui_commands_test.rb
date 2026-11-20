raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
require "action_controller/test_case"
ActionCable.server.config.cable = {"adapter" => "test"}

class QldapmUICommandsTest < ActionController::TestCase
  tests QldapmAIController

  def setup
    super
    @routes = Rails.application.routes
    @request.host = "localhost:18091"
    @actor = User.find(8)
    raise "WRONG_SYNTHETIC_ACTOR" unless Project.find_by!(identifier: "qldapm-local").work_packages.first!.qldapm_actor(@actor)["role"] == "BE"
    @request.session[:user_id] = @actor.id
    @request.session[:updated_at] = Time.current
    @request.env["HTTP_ACCEPT"] = "text/vnd.turbo-stream.html, text/html"
  end

  def submit(action, arguments)
    get :show, params: {project_id: "qldapm-local"}
    assert_equal 200, @response.status, "Authenticated fixture could not open AI Assistant"
    token = @controller.send(:form_authenticity_token)
    @controller.commit_csrf_token(@request)
    post action, session: @request.session.to_hash, params: {project_id: "qldapm-local", authenticity_token: token}.merge(arguments)
  end

  def assert_alert
    assert_equal 422, @response.status
    assert @response.body.include?('role="alert"'), "AI error alert missing"
    assert_equal "text/html", @response.media_type
    refute @response.body.include?("<title>500"), "Unexpected internal error page"
  end

  def test_rejected_prompt_renders_alert_not_500
    submit :command, {prompt: "Synthetic UI rejection: employee@example.invalid must not be sent to Google."}
    assert_alert
    assert @response.body.include?("Gemini OFF:") || @response.body.include?("Câu hỏi ngoài phạm vi Gemini"), "Gemini refusal did not explain its scope/verification"
  end

  def test_valid_native_identity_read
    submit :command, {tool: "identity", arguments: "{}"}
    assert_equal 200, @response.status
    assert_equal "text/html", @response.media_type
    assert @response.body.include?('&quot;user_id&quot;: 8'), "Wrong identity receipt"
  end

  def test_project_sidebar_exposes_ai_and_insights_to_authorized_member
    @request.env["HTTP_ACCEPT"] = "text/html"
    get :show, params: {project_id: "qldapm-local"}
    assert_equal 200, @response.status
    assert_select 'a.qldapm-ai-menu-item[href="http://localhost:18091/projects/qldapm-local/qldapm-ai"]', count: 1
    assert_select 'a.qldapm-insights-menu-item[href="http://localhost:18091/projects/qldapm-local/qldapm-insights"]', count: 1
  end

  def test_ai_submission_redirects_to_get_run_instead_of_refreshing_post
    identifier = "11111111-2222-4333-8444-555555555555"
    body = JSON.generate(result: {id: identifier, state: "running"})
    response = Struct.new(:code, :body).new("200", body)
    response.define_singleton_method(:read_body) { |&block| block.call(body) }
    http = Object.new
    http.define_singleton_method(:request) { |_request, &block| block.call(response) }
    original = Net::HTTP.method(:start)
    Net::HTTP.define_singleton_method(:start) { |*_, **_, &block| block.call(http) }
    submit :command, {prompt: "Giải thích ngắn gọn bằng tiếng Việt: Sprint trong Scrum là gì?"}
    assert_redirected_to project_qldapm_ai_path("qldapm-local", run_id: identifier)
  ensure
    Net::HTTP.define_singleton_method(:start, original) if original
  end

  def test_chat_consent_and_selected_ids_are_signed_but_do_not_grant_top_level_auto_execute
    body = JSON.generate(result: {id: "11111111-2222-4333-8444-555555555555", state: "running"})
    response = Struct.new(:code, :body).new("200", body)
    response.define_singleton_method(:read_body) { |&block| block.call(body) }
    sent = []
    http = Object.new
    http.define_singleton_method(:request) { |request, &block| sent << JSON.parse(request.body); block.call(response) }
    original = Net::HTTP.method(:start)
    Net::HTTP.define_singleton_method(:start) { |*_, **_, &block| block.call(http) }
    submit :command, {prompt: "Synthetic scoped request", allow_routine_writes: "1", write_scope_ids: "12, 35, 36, 37, 38, 39, 40, 41"}
    assert_equal 302, @response.status
    command = sent.last.fetch("command")
    assert_equal true, command.dig("arguments", "allow_routine_writes")
    assert_equal [12, 35, 36, 37, 38, 39, 40, 41], command.dig("arguments", "write_scope_ids")
    assert_equal false, command.fetch("auto_execute")
  ensure
    Net::HTTP.define_singleton_method(:start, original) if original
  end

  def test_completed_run_links_to_owned_proposal_preview_not_auto_confirmation
    identifier = "11111111-2222-4333-8444-555555555555"
    body = JSON.generate(result: {id: identifier, state: "done", result: {text: "Synthetic proposal", tools: [
      {action: "update_work_package", result: {result: {id: identifier, human_confirmation_required: true}}}]}})
    response = Struct.new(:code, :body).new("200", body)
    response.define_singleton_method(:read_body) { |&block| block.call(body) }
    http = Object.new
    http.define_singleton_method(:request) { |_request, &block| block.call(response) }
    original = Net::HTTP.method(:start)
    Net::HTTP.define_singleton_method(:start) { |*_, **_, &block| block.call(http) }
    @request.env["HTTP_ACCEPT"] = "text/html"
    get :show, params: {project_id: "qldapm-local", run_id: identifier}
    assert_equal 200, @response.status
    assert_select 'a.qldapm-ai-proposal', count: 1 do |links|
      assert_equal project_qldapm_ai_path("qldapm-local", proposal_id: identifier), links.first["href"]
    end
    assert_select 'form[action="/projects/qldapm-local/qldapm-ai/confirm"]', count: 0
  ensure
    Net::HTTP.define_singleton_method(:start, original) if original
  end

  def test_running_answer_uses_standard_meta_refresh_for_same_get_run
    identifier = "11111111-2222-4333-8444-555555555555"
    http = Object.new
    http.define_singleton_method(:request) do |request, &block|
      action = JSON.parse(request.body).dig("command", "action")
      body = JSON.generate(result: action == "get_ai_run" ? {id: identifier, state: "running",
        result: {text: "Chưa có dữ liệu đủ để trả lời. Hãy nêu rõ công việc hoặc yêu cầu bạn muốn thực hiện."}} : {})
      response = Struct.new(:code, :body).new("200", body)
      response.define_singleton_method(:read_body) { |&reader| reader.call(body) }
      block.call(response)
    end
    original = Net::HTTP.method(:start)
    Net::HTTP.define_singleton_method(:start) { |*_, **_, &block| block.call(http) }
    @request.env["HTTP_ACCEPT"] = "text/html"
    get :show, params: {project_id: "qldapm-local", run_id: identifier}
    assert_equal 200, @response.status
    assert_select 'meta[http-equiv="refresh"]', count: 1 do |elements|
      assert_equal "2;url=#{project_qldapm_ai_path('qldapm-local', run_id: identifier)}", elements.first["content"]
    end
    assert_select 'meta[http_equiv]', count: 0
    assert_select '.qldapm-ai-answer', count: 0
  ensure
    Net::HTTP.define_singleton_method(:start, original) if original
  end

  def test_malformed_json
    submit :command, {tool: "identity", arguments: '{"secret":"synthetic-not-a-real-secret",'}
    assert_alert
    refute @response.body.include?("unexpected token"), "Raw parser error exposed"
  end

  def test_non_object_json
    submit :command, {tool: "identity", arguments: "[]"}
    assert_alert
  end

  def test_tool_allowlist
    submit :command, {tool: "shell", arguments: "{}"}
    assert_alert
  end

  def test_missing_arguments
    submit :command, {tool: "identity"}
    assert_alert
  end

  def test_rejected_confirmation
    submit :confirm, {proposal_id: "synthetic-unknown-proposal", hash: "0" * 64}
    assert_alert
  end

  def test_reject_proposal_preserves_work_package_and_hides_confirmation
    project = Project.find_by!(identifier: "qldapm-local")
    item = project.work_packages.find_by!(assigned_to_id: @actor.id)
    before = item.subject
    proposal = Qldapm::AiBridge.call(project, @actor, "command", {action: "update_work_package",
      arguments: {id: item.id, lock_version: item.lock_version, changes: {subject: "Synthetic rejected UI proposal"}},
      idempotency_key: SecureRandom.uuid})["result"]
    submit :reject, {proposal_id: proposal.fetch("id"), hash: proposal.fetch("hash")}
    assert_redirected_to project_qldapm_ai_path("qldapm-local", proposal_id: proposal.fetch("id"))
    assert_equal before, item.reload.subject
    get :show, params: {project_id: "qldapm-local", proposal_id: proposal.fetch("id")}
    assert_equal 200, @response.status
    assert @response.body.include?("rejected")
    assert_select 'form[action="/projects/qldapm-local/qldapm-ai/confirm"]', count: 0
  end

  def test_dashboard_connection_and_private_history_render
    get :show, params: {project_id: "qldapm-local"}
    assert_equal 200, @response.status
    assert_select 'h3#ai-connection', count: 1
    assert_select 'h3#ai-settings', count: 1
    assert_select 'p.qldapm-ai-count', text: "329"
    assert @response.body.include?("không giới hạn số thao tác")
    refute @response.body.include?("tối đa 6")
    assert @response.body.include?("Action History / Audit Log của bạn")
  end

  def test_unowned_run_read
    get :show, params: {project_id: "qldapm-local", run_id: "synthetic-unknown-run"}
    assert_equal 200, @response.status
    assert @response.body.include?('role="alert"'), "Denied run did not display error"
  end

  def with_business_fixture(responses)
    http = Object.new
    http.define_singleton_method(:request) do |request, &block|
      action = JSON.parse(request.body).dig("command", "action")
      body = JSON.generate(result: responses.fetch(action, {}))
      response = Struct.new(:code, :body).new("200", body)
      response.define_singleton_method(:read_body) { |&reader| reader.call(body) }
      block.call(response)
    end
    original = Net::HTTP.method(:start)
    Net::HTTP.define_singleton_method(:start) { |*_, **_, &block| block.call(http) }
    yield
  ensure
    Net::HTTP.define_singleton_method(:start, original) if original
  end

  def test_preview_has_human_before_after_and_technical_details_collapsed
    proposal = {id: "11111111-2222-4333-8444-555555555555", hash: "a" * 64, state: "pending", command: {
      action: "update_work_package", arguments: {id: 58, lock_version: 1, changes: {subject: "Tên mới", start_date: "2026-10-10", due_date: "2026-10-20"}},
      preview: {before: {subject: "Tên cũ", startDate: "2026-10-08", dueDate: "2026-10-18"},
        date_adjustments: {start_date: {requested: "2026-10-10", actual: "2026-10-12"}}}}}
    with_business_fixture("get_proposal" => proposal) do
      get :show, params: {project_id: "qldapm-local", proposal_id: proposal[:id]}
      assert_equal 200, @response.status
      assert_select 'table.qldapm-ai-preview td', text: "Tên cũ"
      assert_select 'table.qldapm-ai-preview td', text: "Tên mới"
      assert_select 'table.qldapm-ai-preview th', text: "Hạn hoàn thành"
      assert_select 'table.qldapm-ai-preview th', text: "Ngày bắt đầu"
      assert_select 'table.qldapm-ai-preview td', text: /2026-10-12.*2026-10-10.*lịch làm việc/
      assert_select 'table.qldapm-ai-preview td', text: "2026-10-08"
      assert_select 'details[open]', count: 0
      assert_select 'input[type="submit"][value="Duyệt và thực hiện thay đổi trên"]', count: 1
    end
  end

  def test_partial_result_explains_failed_action_and_links_native_ticket_at_top
    run = {id: "11111111-2222-4333-8444-555555555555", state: "done", result: {status: "partial", heading: "Hoàn thành một phần",
      text: "Đã thêm bình luận. Chưa chuyển trạng thái vì workflow từ chối.", outcomes: [{title: "Thêm bình luận #58", detail: "OpenProject xác nhận.", work_package_id: 58}]}}
    with_business_fixture("get_ai_run" => run) do
      get :show, params: {project_id: "qldapm-local", run_id: run[:id]}
      assert_equal 200, @response.status
      assert_select 'section.qldapm-ai-result.-partial[role="alert"] h3', text: "Hoàn thành một phần"
      assert_select 'section.qldapm-ai-result a[href="/work_packages/58"]', count: 1
      assert @response.body.index("Hoàn thành một phần") < @response.body.index('id="ai-connection"')
      assert @response.body.include?("workflow từ chối")
    end
  end

  def test_comment_preview_shows_exact_comment_without_a_command_block
    proposal = {id: "11111111-2222-4333-8444-555555555555", hash: "b" * 64, state: "pending", command: {
      action: "comment", arguments: {id: 58, lock_version: 1, text: "Đã kiểm tra trên staging"}, preview: {before: {subject: "Công việc staging"}}}}
    with_business_fixture("get_proposal" => proposal) do
      get :show, params: {project_id: "qldapm-local", proposal_id: proposal[:id]}
      assert_equal 200, @response.status
      assert_select 'table.qldapm-ai-preview td', text: "Đã kiểm tra trên staging"
      assert_select 'section.qldapm-ai-result p strong', text: "Thêm bình luận #58"
      assert_select 'section.qldapm-ai-result > pre', count: 0
    end
  end

  def test_expired_preview_explains_why_it_cannot_be_approved
    proposal = {id: "11111111-2222-4333-8444-555555555555", hash: "a" * 64, state: "pending", expires: Time.current.to_f - 1,
      command: {action: "comment", arguments: {id: 58, text: "Expired fixture"}, preview: {before: {subject: "Staging"}}}}
    with_business_fixture("get_proposal" => proposal) do
      get :show, params: {project_id: "qldapm-local", proposal_id: proposal[:id]}
      assert_equal 200, @response.status
      assert @response.body.include?("Đề xuất đã hết hạn")
      assert_select 'form[action="/projects/qldapm-local/qldapm-ai/confirm"]', count: 0
    end
  end

  def test_model_explanation_cannot_render_remote_images_or_active_html
    run = {id: "11111111-2222-4333-8444-555555555555", state: "done", result: {status: "answered",
      text: '<img src="https://outside.invalid/probe"><script>alert(1)</script>', outcomes: []}}
    with_business_fixture("get_ai_run" => run) do
      get :show, params: {project_id: "qldapm-local", run_id: run[:id]}
      assert_equal 200, @response.status
      assert_select 'img[src="https://outside.invalid/probe"]', count: 0
      assert_select 'script', text: "alert(1)", count: 0
      assert @response.body.include?("&lt;img")
    end
  end

  def test_insights_other_user_denied
    get :insights, params: {project_id: "qldapm-local", user_id: 10, days: 30}
    assert_equal 200, @response.status
    assert @response.body.include?("PM_OR_SELF_REQUIRED"), "Privacy rejection missing"
    refute @response.body.include?("Snapshot đã lưu"), "Private report leaked"
  end

  def test_insights_invalid_window
    get :insights, params: {project_id: "qldapm-local", user_id: 8, days: 1}
    assert_equal 200, @response.status
    assert @response.body.include?("WINDOW_DENIED"), "Invalid window rejection missing"
  end

  def test_insights_malformed_subject
    get :insights, params: {project_id: "qldapm-local", user_id: [8], days: 30}
    assert_equal 200, @response.status
    assert @response.body.include?('role="alert"'), "Malformed subject should not cause 500"
  end

  def test_insights_response_privacy
    project = Project.find_by!(identifier: "qldapm-local")
    snapshot = Qldapm::Insights.new(project, User.find(7)).snapshot(10, 30)
    before = snapshot.responses.count
    submit :respond, {snapshot_id: snapshot.id, body: "Synthetic unauthorized explanation"}
    assert_equal 422, @response.status
    assert @response.body.include?("PM_OR_SELF_REQUIRED"), "Response privacy rejection missing"
    assert_equal before, snapshot.responses.count
  end

  def test_csrf_still_required
    post :command, params: {project_id: "qldapm-local", authenticity_token: "invalid", tool: "identity", arguments: "{}"}
    assert_equal 422, @response.status
    refute @response.body.include?('role="status"'), "CSRF request executed"
  end
end

class QldapmUIGatesTest < ActionController::TestCase
  tests QldapmGatesController

  def setup
    super
    @routes = Rails.application.routes
    @request.host = "localhost:18091"
    @request.session[:user_id] = 8
    @request.session[:updated_at] = Time.current
    @request.env["HTTP_ACCEPT"] = "text/vnd.turbo-stream.html, text/html"
    @item = Project.find_by!(identifier: "qldapm-local").work_packages.find_by!(assigned_to_id: 8)
    @baseline = @item.attributes
  end

  def reject(operation, value, expected)
    get :show, params: {id: @item.id}
    assert_equal 200, @response.status
    token = @controller.send(:form_authenticity_token)
    @controller.commit_csrf_token(@request)
    post :update, session: @request.session.to_hash, params: {id: @item.id, operation:, value:,
      lock_version: @item.lock_version, authenticity_token: token}
    assert_equal 302, @response.status
    assert @controller.flash[:error].to_s.include?(expected), "Expected gate rejection missing"
    assert @item.reload.attributes == @baseline, "Rejected gate request changed source"
  end

  def test_self_approval
    reject "approve", {key: "code", reference: "ui:synthetic-self-review"}, "SELF_APPROVAL"
  end

  def test_reviewer_requires_pm
    reject "reviewer", {user_id: 9}, "PM_REQUIRED"
  end

  def test_malformed_receipt
    reject "evidence", {key: "test", verification: "automatic", job_receipt: "{"}, "JSON"
  end

  def test_non_object_gate_value
    reject "evidence", ["invalid"], "object"
  end

  def test_missing_transition_status
    reject "transition", {}, "status_id"
  end
end

class QldapmBridgeContractTest < Minitest::Test
  def reject(code, body)
    response = Struct.new(:code, :body).new(code, body)
    response.define_singleton_method(:read_body) { |&block| block.call(self.body) }
    http = Object.new
    http.define_singleton_method(:request) { |_request, &block| block.call(response) }
    original = Net::HTTP.method(:start)
    Net::HTTP.define_singleton_method(:start) { |*_, **_, &block| block.call(http) }
    assert_raises(::ArgumentError) do
      Qldapm::AiBridge.call(Project.find_by!(identifier: "qldapm-local"), User.find(8), "command", {action: "identity", arguments: {}})
    end.message
  ensure
    Net::HTTP.define_singleton_method(:start, original) if original
  end

  def test_known_error_has_no_raw_suffix
    message = reject("503", JSON.generate(error: "GEMINI_QUOTA_429; synthetic-private-marker"))
    assert message.include?("Google từ chối do quota"), "Known quota message missing"
    refute message.include?("synthetic-private-marker"), "Upstream metadata exposed"
  end

  def test_unknown_error_redacted
    message = reject("403", JSON.generate(error: "synthetic-private-marker"))
    assert message.include?("(403)"), "HTTP status missing"
    refute message.include?("synthetic-private-marker"), "Upstream error exposed"
  end

  def test_response_size_limit
    message = reject("503", "x" * (2.megabytes + 1))
    assert message.include?("quá lớn"), "Error response limit not enforced"
  end

  def test_success_requires_object
    message = reject("200", "[]")
    assert message.include?("không hợp lệ"), "Malformed success was accepted"
  end
end

failures = []
count = 0
[QldapmUICommandsTest, QldapmUIGatesTest, QldapmBridgeContractTest].each do |test_class|
  names = test_class.instance_methods.grep(/^test_/).sort
  names.select! { |name| ARGV.empty? || ARGV.include?(name.to_s) }
  count += names.size
  names.each do |name|
    # Native CSRF rejection can revoke the actor's sessions; fixture transactions must not persist that.
    ActiveRecord::Base.transaction do
      result = test_class.new(name).run
      result.failures.each { |failure| failures << "#{name}: #{failure.message}" }
      raise ActiveRecord::Rollback
    end
  end
end
failures.each { |failure| puts "UI_POST_RED: #{failure}" }
raise "UI_POST_REGRESSION_FAILED" unless failures.empty?
puts "Native AI/Gates UI and bounded bridge #{count} cases PASS (synthetic session/HTTP fixtures; real browser tested separately)."
