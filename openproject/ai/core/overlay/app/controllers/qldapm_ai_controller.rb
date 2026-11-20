class QldapmAIController < ApplicationController

  before_action :require_login

  before_action :load_project

  authorize_with_permission :view_work_packages



  def observer
    response.headers["Cache-Control"] = "no-store"
    response.cache_control.merge!(no_store: true)
    response.headers["X-Robots-Tag"] = "noindex"
    return render :observer unless request.format.json?

    packet = if params[:task_id].present?
               args = {task_id: Integer(params[:task_id], 10)}
               args[:view] = params[:view].to_s if params[:view].present?
               if params[:view] == 'details'
                 args.merge!(section: params[:section].to_s, offset: Integer(params[:offset].presence || '0', 10), limit: Integer(params[:limit].presence || '25', 10))
                 args[:stage] = params[:stage].to_s if params[:stage].present?
               end
               Qldapm::AiBridge.call(@project, User.current, 'command', {action: 'observer_task_progress', arguments: args}, request_id: request.request_id)
             elsif params[:run_id].present?
               Qldapm::AiBridge.call(@project, User.current, 'command', {action: 'observer_run_details', arguments: {run_id: params[:run_id].to_s}}, request_id: request.request_id)
             else
                 limit = Integer(params[:limit].presence || "20", 10)
                 raise ::ArgumentError unless (1..50).cover?(limit)
                 args = {limit: limit, query: params[:query].to_s, state: params[:state].presence || "ALL"}
                 args.merge!(view: params[:view].to_s, offset: Integer(params[:offset].presence || '0', 10)) if params[:view].present?
                 Qldapm::AiBridge.call(@project, User.current, 'command', {action: 'observer_active', arguments: args}, request_id: request.request_id)
             end
    transport = packet['_transport'] || {}
    response.headers['X-Qldapm-Request-Id'] = transport[:request_id].to_s if transport[:request_id]
    response.headers['Server-Timing'] = [transport[:server_timing], "rails_bridge;dur=#{transport[:duration_ms].to_f.round(3)}"].compact.join(',')
    render json: packet['result']
  rescue Qldapm::AiBridge::RequestError => error
    render json: {error: error.code || 'OBSERVER_UNAVAILABLE', message: error.message, request_id: request.request_id}, status: bridge_error_status(error)
  rescue ::ArgumentError, ::KeyError
    render json: {error: "OBSERVER_INVALID_REQUEST"}, status: :unprocessable_entity
  end

  def executions

    response.headers["Cache-Control"] = "no-store"
    response.cache_control.merge!(no_store: true)

    offset = Integer(params[:offset].presence || 0, exception: false)
    return render json: {error: 'EXECUTION_HISTORY_INVALID_FILTER'}, status: :unprocessable_entity if offset.nil? || offset.negative?

    @filters = {limit: 10, offset: offset, search: params[:search].to_s,

                state: params[:state].presence || "ALL", order: params[:order].presence || "desc"}

    @executions = bridge("list_execution_monitors", @filters)["result"]

    respond_to do |format|

      format.html

      format.json { render json: @executions }

    end

  rescue ::ArgumentError => error

    @error = error.message
    status = error.is_a?(Qldapm::AiBridge::RequestError) ? bridge_error_status(error) : :service_unavailable

    respond_to do |format|

      format.html { render :executions, status: status }

      format.json { render json: {error: "EXECUTION_HISTORY_UNAVAILABLE"}, status: status }

    end

  end



  def execution
    response.headers["Cache-Control"] = "no-store"
    response.cache_control.merge!(no_store: true)
    response.headers["X-Robots-Tag"] = "noindex"
    run_id = params[:run_id].presence || params[:id].presence
    raise ::KeyError, "run_id required" unless run_id

    if request.format.json? || params[:format] == "json" || request.headers["Accept"].to_s.include?("application/json")
      result = bridge("get_execution_monitor", {id: run_id})["result"]
      return render json: result
    end
    render :execution

  rescue ::ArgumentError, ::KeyError, ::StandardError => error
    status = error.is_a?(Qldapm::AiBridge::RequestError) ? bridge_error_status(error) : (error.message.match?(/403|không có quyền/) ? :forbidden : (error.message.match?(/404|Không tìm thấy|AI_RUN_NOT_FOUND/) ? :not_found : :service_unavailable))
    render json: {error: [403,:forbidden].include?(status) ? "EXECUTION_ACCESS_DENIED" : ([404,:not_found].include?(status) ? "EXECUTION_NOT_FOUND" : "EXECUTION_UNAVAILABLE"), message: error.message}, status: status
  end

  def report
    response.headers["Cache-Control"] = "no-store"
    response.cache_control.merge!(no_store: true)
    response.headers["X-Robots-Tag"] = "noindex"
    report_id = params[:id].presence || params[:report_id].presence
    raise ::KeyError, "report_id required" unless report_id

    result = bridge("engineering_report_get", {id: report_id})["result"]
    result = result.merge('reader' => helpers.qldapm_report_document(result))
    render json: result
  rescue Qldapm::AiBridge::RequestError => error
    status = bridge_error_status(error)
    render json: {error: status == 404 ? "REPORT_NOT_FOUND" : "REPORT_UNAVAILABLE", message: error.message}, status: status
  rescue ::KeyError => error
    render json: {error: "REPORT_NOT_FOUND", message: error.message}, status: :not_found
  rescue ::StandardError => error
    render json: {error: "REPORT_UNAVAILABLE", message: error.message}, status: :service_unavailable
  end



  def show

    return render_engineering if engineering_project?

    @proposal = bridge("get_proposal", {id: params[:proposal_id]})["result"] if params[:proposal_id].present?

    @run = bridge("get_ai_run", {id: params[:run_id]})["result"] if params[:run_id].present?

    load_assistant_context

  rescue ::ArgumentError => error

    @error = error.message

  end



  def permissions

    return head :forbidden unless Qldapm::Rbac.pm?(@project, User.current)

    @permissions = bridge("get_permissions", {})["result"]

    @history = bridge("get_action_history", {})["result"]

  rescue ::ArgumentError => error

    @error = error.message

  end

  def qa_evidence
    response.headers["Cache-Control"] = "no-store"
    response.cache_control.merge!(no_store: true)
    return head :forbidden if User.current.admin? && !Qldapm::Rbac.ai_system_owner?(@project, User.current, fresh: true)
    return head :forbidden unless %w[PM AI_SYSTEM_OWNER QA].include?(Qldapm::Rbac.role(@project, User.current, fresh: true))
    @qa_evidence = bridge("qa_evidence_get", {id: params[:id]})["result"] if params[:id].present?
    @qa_run = bridge("qa_test_get", {id: params[:run_id]})["result"] if params[:run_id].present?
    @qa_inbox = bridge("qa_evidence_list", {})["result"]
    render :qa_evidence
  rescue ::ArgumentError, ::KeyError => error
    @error = error.message
    render :qa_evidence, status: error.is_a?(Qldapm::AiBridge::RequestError) ? error.status : :unprocessable_entity
  end

  def qa_decision
    response.headers["Cache-Control"] = "no-store"
    response.cache_control.merge!(no_store: true)
    return head :forbidden if User.current.admin? && !Qldapm::Rbac.ai_system_owner?(@project, User.current, fresh: true)
    return head :forbidden unless Qldapm::Rbac.pm?(@project, User.current, fresh: true)
    review_qa_evidence
  end

  def phases
    response.headers["Cache-Control"] = "no-store"
    response.cache_control.merge!(no_store: true)
    return head :forbidden unless phase_access?
    @phase = bridge("phase_get", {id: params[:id]})["result"] if params[:id].present?
    @phase_inbox = bridge("phase_list", {})["result"]
    render :phases
  rescue ::ArgumentError, ::KeyError => error
    @error = error.message
    render :phases, status: error.is_a?(Qldapm::AiBridge::RequestError) ? error.status : :unprocessable_entity
  end

  def phase_decision
    response.headers["Cache-Control"] = "no-store"
    response.cache_control.merge!(no_store: true)
    return head :forbidden unless phase_access? && Qldapm::Rbac.pm?(@project, User.current, fresh: true)
    raise ::ArgumentError, "Hãy xác nhận đã đọc nguồn, phạm vi approval và đúng hash." unless params[:acknowledge] == "1"
    @phase = Qldapm::AiBridge.call(@project, User.current, "phase_review",
      {id: params.fetch(:id), hash: params.fetch(:hash), decision: params.fetch(:decision)})["result"]
    @review_completed = true
    render :phases
  rescue ::ArgumentError, ::KeyError => error
    @error = error.message
    render :phases, status: error.is_a?(Qldapm::AiBridge::RequestError) ? error.status : :unprocessable_entity
  end

  private def phase_access?
    return false if User.current.admin? && !Qldapm::Rbac.ai_system_owner?(@project, User.current, fresh: true)
    %w[PM AI_SYSTEM_OWNER BA-PM BA].include?(Qldapm::Rbac.role(@project, User.current, fresh: true))
  end

  def qa_test_decision
    response.headers["Cache-Control"] = "no-store"
    response.cache_control.merge!(no_store: true)
    return head :forbidden if User.current.admin?
    return head :forbidden unless Qldapm::Rbac.role(@project, User.current, fresh: true) == "QA"
    review_qa_evidence
  end

  private def review_qa_evidence
    raise ::ArgumentError, "Hãy xác nhận đã đọc bằng chứng và hash trước khi quyết định." unless params[:acknowledge] == "1"
    @qa_evidence = Qldapm::AiBridge.call(@project, User.current, "qa_review",
      {id: params.fetch(:id), hash: params.fetch(:hash), decision: params.fetch(:decision)})["result"]
    @review_completed = true
    render :qa_evidence
  rescue ::ArgumentError, ::KeyError => error
    @error = error.message
    render :qa_evidence, status: error.is_a?(Qldapm::AiBridge::RequestError) ? error.status : :unprocessable_entity
  end



  def command
    @role = Qldapm::Rbac.role(@project, User.current, fresh: true)
    if User.current.admin? && !Qldapm::Rbac.ai_system_owner?(@project, User.current, fresh: true)
      if engineering_project?
        @error = "Chỉ AI System Owner mới có quyền thực thi lệnh trong Engineering Command Center."
        return render_engineering(status: :forbidden)
      else
        return head :forbidden
      end
    end

    action = params[:prompt].present? ? "start_ai_run" : params.fetch(:tool)
    if engineering_project?
      allowed_actions = %w[delegated_status delegated_control delegated_preview engineering_status engineering_run_once engineering_control engineering_plan engineering_cancel engineering_resume engineering_github_sync engineering_report_generate engineering_report_list engineering_report_get engineering_report_schedule_get engineering_report_schedule_update engineering_notifications_list engineering_notifications_dismiss knowledge_search knowledge_file_ingest knowledge_file_search knowledge_file_read bug_triage sprint_risks]
      unless %w[PM AI_SYSTEM_OWNER].include?(@role) && allowed_actions.include?(action)
        @error = "Từ chối quyền truy cập: Bạn không có quyền thực thi tác vụ '#{action}' trong Engineering Project (yêu cầu vai trò PM hoặc AI System Owner)."
        return render_engineering(status: :forbidden)
      end

      begin
        if %w[knowledge_search knowledge_file_search].include?(action)
          arguments = {
            'query' => (params[:knowledge_query].presence || (params[:arguments].present? ? (JSON.parse(params[:arguments])['query'] rescue '') : '')).to_s,
            'limit' => 5,
            'mode' => params[:knowledge_mode].presence || 'search'
          }
          arguments['source_key'] = params[:source_key].to_s if action == 'knowledge_file_search'
          if params[:native_ids].present?
            arguments['native_ids'] = Array(params[:native_ids]).map(&:to_i)
          end
        else
          arguments = JSON.parse(params.fetch(:arguments))
          raise ::ArgumentError, 'Arguments JSON phải là object' unless arguments.is_a?(Hash)
        end
        if action == 'knowledge_file_ingest'
          arguments = {'source_key' => params[:source_key].to_s}
        elsif action == 'knowledge_file_read'
          arguments = {'source_key' => params[:source_key].to_s, 'document_id' => params[:document_id].to_s}
        elsif action == 'bug_triage'
          arguments = {'id' => Integer(params[:bug_native_id].to_s, 10)}
          raise ::ArgumentError, 'Cần Work Package ID dương' unless arguments['id'].positive?
        elsif action == 'engineering_run_once' && params[:engineering_unit].present?
          current = bridge('engineering_status', {})['result']
          unit = Array(current['backlog']).find { |row| row['unit'] == params[:engineering_unit] && row['native_id'].to_s == params[:engineering_task] }
          unless unit
            @error = "Không tìm thấy Engineering Unit '#{params[:engineering_unit]}' trong backlog."
            return render_engineering(status: :not_found)
          end
          source = Array(current['tasks']).find { |row| row['id'] == unit['native_id'] }
          raise ::ArgumentError, 'Task không còn đọc được trong Project 6' unless source
          arguments = {native_id: source['id'], lock_version: source['lock_version'], unit: unit['unit']}
        elsif action == 'engineering_github_sync'
          arguments = {}
        elsif action == 'engineering_report_schedule_update'
          raise ::ArgumentError, 'Chưa nhận được các trường cấu hình lịch. Tải lại AI Command Center rồi mở cấu hình và lưu lại.' if arguments.empty?
        elsif action == 'engineering_plan'
          arguments['feedback'] = params[:engineering_feedback].to_s if params.key?(:engineering_feedback)
        end
        request_key = params[:request_id].presence || SecureRandom.uuid
        raise ::ArgumentError, 'Mã yêu cầu không hợp lệ' unless request_key.match?(/\A[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\z/i)
        if action == 'engineering_control' && params[:expected_revision].present?
          arguments['expected_revision'] = Integer(params[:expected_revision])
        end
        bridge_resp = bridge(action, arguments, request_key)
        @command_correlation_id = bridge_resp['correlation_id']
        @result = bridge_resp['result'] || bridge_resp
        if @result.is_a?(Hash) && @result['accepted'] == false
          @error = @result['reason_code'] || 'COMMAND_REJECTED'
          return render_engineering(status: @error == 'ENGINEERING_STATE_REVISION_CONFLICT' ? :conflict : :unprocessable_entity)
        end
        if %w[knowledge_search knowledge_file_search].include?(action)
          @knowledge = @result
        end
        if @result.is_a?(Hash) && @result['message'].blank?
          case action
          when 'delegated_preview'
            @result['message'] = "Proposal #{@result['id']}: #{@result['state']}. Xem quyết định WF05 và Native read-back WF06 trong Approval automation."
          when 'delegated_control'
            @result['message'] = "Delegated Project6: #{@result['enabled'] ? 'ON' : 'OFF'}; revision #{@result['revision']}."
          when 'engineering_run_once'
            run_id = @result['id'] || @result['run_id']
            if @result['deduplicated']
              @result['message'] = "Run #{run_id} đã được tiếp nhận trước đó; xem receipt/trạng thái hiện tại, không tạo run mới."
            elsif run_id.present?
              @result['message'] = "Đã tiếp nhận yêu cầu chạy đơn lẻ: Run ID #{run_id}."
            else
              @result['message'] = "NO_ELIGIBLE_WORK — không có engineering unit mới đủ điều kiện chạy."
            end
          when 'engineering_control'
            target_mode = arguments['mode']
            if target_mode == 'AUTO' && @result.dig('scheduled', 'reason') == 'ALL_DELIVERED'
              @result['message'] = @result.dig('scheduled', 'explanation') || "NO_ELIGIBLE_WORK — các unit đã hoàn tất; AUTO không khởi chạy việc mới. Xem effective state trong receipt."
            elsif target_mode == 'AUTO' && @result.dig('scheduled', 'scheduled') == true
              @result['message'] = "Đã kích hoạt chế độ AUTO: Đang điều phối Unit '#{@result.dig('scheduled', 'unit')}' (Run ID: #{@result.dig('scheduled', 'run_id')})."
            elsif target_mode == 'PAUSED'
              @result['message'] = @result['active_worker_must_checkpoint'] ? "Đã yêu cầu PAUSED; worker đang chạy cần hoàn tất checkpoint." : "Đã chuyển hệ thống sang PAUSED; không nhận thêm việc mới."
            else
              @result['message'] = "Đã cập nhật chế độ điều khiển hệ thống sang: #{target_mode}."
            end
          when 'engineering_plan'
            plan_id = @result['id'] || @result['run_id']
            if @result['deduplicated']
              @result['message'] = "Yêu cầu tính năng này đã được tiếp nhận và xử lý (Run ID: #{plan_id})."
            else
              @result['message'] = "Đã chuyển yêu cầu tính năng mới tới Tác nhân PM & BA (Run ID: #{plan_id}). Đang tạo đặc tả kỹ thuật và Backlog Unit mới."
            end
          when 'engineering_github_sync'
            pr_count = @result['total_prs_synced'] || 0
            if @result['status'] == 'SUCCESS'
              @result['message'] = "Đã đối soát thành công #{pr_count} Pull Requests trên kho GitHub."
            else
              @error = "Đồng bộ GitHub #{@result['status'] || 'UNKNOWN'}: #{pr_count} PR đã đối soát. #{@result['error']}"
            end
          when 'engineering_report_generate'
            rtype = arguments['report_type'] || 'Báo cáo'
            rep_id = @result['id'] || @result['report_id']
            @result['message'] = "Đã tạo thành công #{rtype} (Report ID: #{rep_id}). Bấm 'Xem toàn văn' trên thẻ báo cáo để đọc nội dung chi tiết."
            @generated_report_id = rep_id
          when 'engineering_report_schedule_update'
            @result['message'] = "Đã lưu cấu hình lịch trình báo cáo tự động (Asia/Ho_Chi_Minh UTC+7) thành công."
          when 'engineering_cancel'
            @result['message'] = case @result['state']
                                 when 'cancelling' then "Đã yêu cầu hủy; worker đang dừng và checkpoint."
                                 when 'cancelled' then "Đã hủy phiên trước khi thực thi."
                                 else "Phiên đã kết thúc; không thực hiện hủy."
                                 end
          when 'engineering_resume'
            @result['message'] = "Đã nhận yêu cầu tiếp tục; chờ worker claim và xác nhận checkpoint."
          end
        end
      rescue Qldapm::AiBridge::RequestError => error
        @error = error.message
        return render_engineering(status: bridge_error_status(error))
      rescue ::ArgumentError => error
        @error = error.message
        return render_engineering(status: :unprocessable_entity)
      rescue StandardError => error
        @error = "Lỗi thực thi lệnh: #{error.message}"
        return render_engineering(status: :internal_server_error)
      end
      return render_engineering
    end
    if %w[qa_application_proof_verify qa_application_proof_admit].include?(action)
      return head :forbidden unless Qldapm::Rbac.ai_system_owner?(@project, User.current, fresh: true)
    end

    raise ::ArgumentError, "Tool không được phép" unless %w[delete_work_package update_dependency delete_dependency create_dependency get_assistant_status get_action_history analyze list_work_packages start_ai_run get_proposal get_ai_run get_job identity get_work_package get_project_options get_gate create_work_package update_work_package comment transition change_gate knowledge_ingest knowledge_search knowledge_deindex cancel_agent_run owner_inspect knowledge_integrity knowledge_file_ingest knowledge_file_search knowledge_file_read knowledge_incremental_sync knowledge_incremental_status knowledge_feedback_submit knowledge_feedback_get knowledge_feedback_apply bug_triage bug_propose wbs_draft wbs_get wbs_adopt wbs_next wbs_from_ba qa_evidence_capture qa_evidence_get qa_transition_prepare qa_test_run qa_test_get qa_evidence_from_run qa_evidence_list phase_draft phase_get phase_list phase_transition_prepare qa_application_proof_verify qa_application_proof_admit].include?(action)

    arguments = params[:prompt].present? ? {"prompt" => params[:prompt], "allow_routine_writes" => params[:allow_routine_writes] == "1",
      "write_scope_ids" => parse_write_scope(params[:write_scope_ids])} : JSON.parse(params.fetch(:arguments))

    arguments["engine"] = params[:engine].presence || "gemini" if action == "start_ai_run"

    arguments = {"id" => Integer(params.fetch(:native_id))} if %w[knowledge_ingest knowledge_deindex].include?(action) && params[:native_id].present?
    arguments = {"native_id" => Integer(params.fetch(:native_id))} if action == "qa_test_run" && params[:native_id].present?
    arguments = {"id" => params.fetch(:proof_id)} if %w[qa_application_proof_verify qa_application_proof_admit].include?(action) && params[:proof_id].present?
    arguments = {"native_id" => Integer(params.fetch(:native_id)), "kind" => params.fetch(:kind)} if action == "phase_draft" && params[:native_id].present?
    arguments = {"id" => params.fetch(:phase_id), "hash" => params.fetch(:phase_hash), "status_id" => Integer(params.fetch(:status_id))} if action == "phase_transition_prepare" && params[:phase_id].present?

    arguments = {"query" => params[:knowledge_query], "mode" => params[:knowledge_mode].presence || 'search'} if action == "knowledge_search" && params[:knowledge_query].present?

    raise ::ArgumentError, "Arguments JSON phải là object" unless arguments.is_a?(Hash)

    request_key = params[:request_id].presence || SecureRandom.uuid
    raise ::ArgumentError, "Mã yêu cầu không hợp lệ" unless request_key.match?(/\A[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\z/i)

    @result = Qldapm::AiBridge.call(@project, User.current, "command", {action:, arguments:,

        idempotency_key: request_key, auto_execute: false})
    if action == "phase_draft" && @result.dig("result", "id").present?
      return redirect_to project_qldapm_ai_phases_path(@project.identifier, id: @result["result"]["id"])
    end
    if %w[qa_test_run qa_evidence_from_run qa_application_proof_admit].include?(action) && @result.dig("result", "id").present?
      target = action == "qa_test_run" ? {run_id: @result["result"]["id"]} : {id: @result["result"]["id"]}
      return redirect_to project_qldapm_ai_qa_evidence_path(@project.identifier, **target)
    end

    @proposal = @result["result"] if @result.dig("result", "human_confirmation_required")

    @run = @result["result"] if action == "start_ai_run"

    @knowledge = @result["result"] if action == "knowledge_search"

    return redirect_to project_qldapm_ai_path(@project.identifier, run_id: @run.fetch("id")) if action == "start_ai_run"

    render_assistant

  rescue JSON::ParserError

    @error = "Arguments JSON không hợp lệ; chưa thực hiện thao tác."

    render_assistant(status: :unprocessable_entity)

  rescue ::ArgumentError, ::KeyError => error
    @error = error.message
    status = if error.is_a?(Qldapm::AiBridge::RequestError)
               error.status
             elsif error.message.match?(/từ chối|không có quyền|403/)
               :forbidden
             elsif error.message.match?(/chưa sẵn sàng|gián đoạn|503|Timeout/)
               :service_unavailable
             else
               :unprocessable_entity
             end
    render_assistant(status:)
  end



  def confirm

    proposal = bridge("get_proposal", {id: params.fetch(:proposal_id)})["result"]

    @completed_action = helpers.qldapm_preview(proposal)[:title] + " — OpenProject đã xác nhận kết quả."

    @result = Qldapm::AiBridge.call(@project, User.current, "confirm", {id: params.fetch(:proposal_id), hash: params.fetch(:hash)})

    render_assistant

  rescue ::ArgumentError, ::KeyError => error
    @error = error.message
    status = if error.message.match?(/từ chối|không có quyền|403/)
               :forbidden
             elsif error.message.match?(/chưa sẵn sàng|gián đoạn|503|Timeout/)
               :service_unavailable
             else
               :unprocessable_entity
             end
    render_assistant(status:)
  end



  def reject

    @result = bridge("reject_proposal", {id: params.fetch(:proposal_id), hash: params.fetch(:hash)}, SecureRandom.uuid)

    redirect_to project_qldapm_ai_path(@project.identifier, proposal_id: params[:proposal_id])

  rescue ::ArgumentError, ::KeyError => error
    @error = error.message
    status = if error.message.match?(/từ chối|không có quyền|403/)
               :forbidden
             elsif error.message.match?(/chưa sẵn sàng|gián đoạn|503|Timeout/)
               :service_unavailable
             else
               :unprocessable_entity
             end
    render_assistant(status:)
  end



  def insights

    @subject = Integer((params[:user_id].presence || User.current.id).to_s)

    @days = Integer((params[:days].presence || 30).to_s)

    @report = Qldapm::Insights.new(@project, User.current).report(@subject, @days)

    @snapshots = Qldapm::InsightSnapshot.where(project: @project, user_id: @subject, days: @days).order(created_at: :desc).limit(10)

  rescue ::ArgumentError => error

    @error = error.message

  end



  def respond

    engine = Qldapm::Insights.new(@project, User.current)

    snapshot = Qldapm::InsightSnapshot.where(project: @project).find(params[:snapshot_id])

    engine.report(snapshot.user_id, snapshot.days)

    snapshot.responses.create!(user: User.current, body: params.fetch(:body))

    redirect_to project_qldapm_insights_path(@project.identifier, user_id: snapshot.user_id, days: snapshot.days)

  rescue ::ArgumentError, ::KeyError, ActiveRecord::RecordInvalid => error

    @error = error.is_a?(ActiveRecord::RecordInvalid) ? "Giải trình không hợp lệ; chưa lưu." : error.message

    render :insights, formats: [:html], status: :unprocessable_entity

  end



  private

  def load_assistant_context
    offset = Integer(params[:cc_offset].presence || 0)
    if @run || @proposal
      @control_center = bridge("get_control_center", {limit: 10, offset: offset})["result"]
    else
      @connection = bridge("get_assistant_status", {})["result"]
      @history = bridge("get_action_history", {})["result"]
      @dashboard = bridge("analyze", {})["result"]
      @control_center = offset.zero? ? @dashboard["control_center"] : bridge("get_control_center", {limit: 10, offset: offset})["result"]
    end
  end

  def render_assistant(status: :ok)
    return render_engineering(status:) if engineering_project?
    begin
      load_assistant_context
    rescue ::ArgumentError => error
      # A failed refresh must never hide the submitted result or resend the command.
      @context_error = error.message
    end
    render :show, formats: [:html], status: status
  end



  def load_project

    @project = Project.visible(User.current).find_by!(identifier: params[:project_id])

    raise ActiveRecord::RecordNotFound unless {5 => 'qldapm-local', 6 => 'ai-dev-demo'}[@project.id] == @project.identifier
    if engineering_project?
      @role = Qldapm::Rbac.role(@project, User.current, fresh: true)
      return deny_access unless %w[PM AI_SYSTEM_OWNER].include?(@role)
      return deny_access unless %w[show command executions execution report observer].include?(action_name)
      @tools = %w[delegated_status delegated_control delegated_preview engineering_status engineering_run_once engineering_control engineering_plan engineering_cancel engineering_resume engineering_github_sync engineering_report_generate engineering_report_list engineering_report_get engineering_report_schedule_get engineering_report_schedule_update engineering_notifications_list engineering_notifications_dismiss knowledge_search knowledge_file_ingest knowledge_file_search knowledge_file_read bug_triage sprint_risks]
      return
    end

    item = WorkPackage.visible(User.current).where(project: @project).first

    raise ActiveRecord::RecordNotFound unless item

    actor_info = item.qldapm_actor(User.current)

    return deny_access unless actor_info && actor_info["role"].present?

    @role = Qldapm::Rbac.role(@project, User.current)

    @tools = %w[identity list_work_packages analyze get_assistant_status get_action_history start_ai_run get_work_package get_project_options get_gate get_job get_proposal get_ai_run comment knowledge_file_search knowledge_file_read knowledge_incremental_status knowledge_feedback_submit knowledge_feedback_get bug_triage wbs_draft wbs_get wbs_from_ba]

    @tools += %w[update_dependency delete_dependency create_dependency create_work_package update_work_package transition change_gate knowledge_file_ingest knowledge_incremental_sync knowledge_feedback_apply bug_propose wbs_adopt wbs_next qa_transition_prepare] if Qldapm::Rbac.pm?(@project, User.current)
    @tools << 'delete_work_package' if Qldapm::Rbac.pm?(@project, User.current) && User.current.allowed_in_project?(:delete_work_packages,@project)
    @tools += %w[qa_evidence_get qa_test_run qa_test_get qa_evidence_from_run qa_evidence_list] if %w[PM AI_SYSTEM_OWNER QA].include?(@role)
    @tools += %w[phase_draft phase_get phase_list] if %w[PM AI_SYSTEM_OWNER BA BA-PM].include?(@role)
    @tools += %w[phase_transition_prepare] if Qldapm::Rbac.pm?(@project, User.current)
    @tools += %w[qa_evidence_capture] if @role == "QA"
    @tools += %w[owner_inspect knowledge_integrity] if @role == Qldapm::Rbac::AI_SYSTEM_OWNER
    @tools += %w[qa_application_proof_verify qa_application_proof_admit] if @role == Qldapm::Rbac::AI_SYSTEM_OWNER

  end



  def bridge_error_status(error)
    response.headers['X-Qldapm-Request-Id'] = error.request_id.to_s if error.request_id
    response.headers['Retry-After'] = error.retry_after.to_s if error.retry_after
    (400..599).cover?(error.status) ? error.status : 503
  end

  def bridge(action, arguments, key = nil)

    Qldapm::AiBridge.call(@project, User.current, "command", {action:, arguments:, idempotency_key: key})


  end

  def engineering_project?
    @project&.id == 6 && @project.identifier == 'ai-dev-demo'
  end

  def render_engineering(status: :ok)
    @role ||= Qldapm::Rbac.role(@project, User.current, fresh: true)
    response.headers['Cache-Control'] = 'no-store'
    response.cache_control.merge!(no_store: true)
    if request.post? && (request.format.json? || params[:format] == 'json')
      # A persisted command receipt must not wait for GitHub/Native full-page refresh.
      if @knowledge
        format_time = ->(value) do
          next 'Chưa có dữ liệu' if value.blank?
          parsed = value.is_a?(Numeric) || value.to_s.match?(/\A\d+(\.\d+)?\z/) ? Time.at(value.to_f) : Time.parse(value.to_s)
          parsed.in_time_zone('Asia/Bangkok').strftime('%d/%m/%Y %H:%M:%S')
        rescue ::ArgumentError, ::TypeError
          'Chưa có dữ liệu'
        end
        knowledge_html = render_to_string(partial: 'qldapm_ai/engineering_knowledge_results', formats: [:html], locals: {format_vn_time: format_time})
      end
      return render json: {result: @result, error: @error, correlation_id: @command_correlation_id,
                           knowledge_html: knowledge_html}, status: status
    end
    if request.post?
      flash[:error] = @error if @error.present?
      flash[:notice] = @result&.dig('message').presence || 'Thao tác đã xử lý; đối chiếu trạng thái và receipt trong AI Command Center.' unless @error.present?
      return redirect_to "/projects/#{@project.identifier}/qldapm-ai", status: :see_other
    end
    begin
      @engineering = bridge('engineering_status', {})['result']
      parent = Array(@engineering['tasks']).find { |row| row['id'] == 379 }
      @engineering_wp = parent && parent.merge('lockVersion' => parent['lock_version'])
      @reports = @engineering['recent_reports']
      @schedule = @engineering['reporting_schedule']
      @notifications = @engineering['notifications']
      if params[:ui].present?
        session[:qldapm_ui_mode] = params[:ui]
      end
      @ui_mode = params[:ui].presence || session[:qldapm_ui_mode].presence || 'modern'
    rescue ::ArgumentError => error
      @error ||= error.message
    end
    if request.format.json? || params[:format] == 'json'
      fragments = {}
      knowledge_html = nil
      if @engineering
        html = render_to_string(partial: 'qldapm_ai/engineering_command_center', formats: [:html])
        document = Nokogiri::HTML.fragment(html)
        document.css('[data-qcc-live]').each { |node| fragments[node['id']] = node.inner_html }
        knowledge_html = document.at_css('#qcc-knowledge-results')&.inner_html if @knowledge
      end
      return render json: {
        engineering: @engineering,
        fragments: fragments,
        knowledge_html: knowledge_html,
        correlation_id: @command_correlation_id,
        reports: @reports,
        schedule: @schedule,
        notifications: @notifications,
        result: @result,
        error: @error
      }, status:
    end
    render :engineering, formats: [:html], status:
  end

  def parse_write_scope(value)
    text = value.to_s.strip
    return [] if text.empty?
    raise ::ArgumentError, "Phạm vi chỉ nhận ID nguyên dương, cách nhau bằng dấu phẩy hoặc khoảng trắng." unless text.match?(/\A#?[1-9]\d*(?:[\s,]+#?[1-9]\d*)*[\s,]*\z/)
    text.scan(/\d+/).map(&:to_i).uniq
  end

end

