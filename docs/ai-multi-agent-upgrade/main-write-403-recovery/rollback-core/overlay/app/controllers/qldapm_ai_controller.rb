class QldapmAIController < ApplicationController

  before_action :require_login

  before_action :load_project

  authorize_with_permission :view_work_packages



  def executions

    response.headers["Cache-Control"] = "no-store"

    @filters = {limit: 10, offset: Integer(params[:offset].presence || 0), search: params[:search].to_s,

                state: params[:state].presence || "ALL", order: params[:order].presence || "desc"}

    @executions = bridge("list_execution_monitors", @filters)["result"]

    respond_to do |format|

      format.html

      format.json { render json: @executions }

    end

  rescue ::ArgumentError => error

    @error = error.message

    respond_to do |format|

      format.html { render :executions, status: :service_unavailable }

      format.json { render json: {error: "EXECUTION_HISTORY_UNAVAILABLE"}, status: :service_unavailable }

    end

  end



  def execution

    response.headers["Cache-Control"] = "no-store"

    response.headers["X-Robots-Tag"] = "noindex"

    return render :execution unless request.format.json?



    render json: bridge("get_execution_monitor", {id: params.fetch(:run_id)})["result"]

  rescue ::ArgumentError, ::KeyError => error

    status = error.message.match?(/403|404|không có quyền|Không tìm thấy/) ? :forbidden : :service_unavailable

    render json: {error: status == :forbidden ? "EXECUTION_ACCESS_DENIED" : "EXECUTION_UNAVAILABLE"}, status:

  end



  def show

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



  def command

    return head :forbidden if User.current.admin?

    action = params[:prompt].present? ? "start_ai_run" : params.fetch(:tool)

    raise ::ArgumentError, "Tool không được phép" unless %w[get_assistant_status get_action_history analyze list_work_packages start_ai_run get_proposal get_ai_run get_job identity get_work_package get_project_options get_gate create_work_package update_work_package comment transition change_gate knowledge_ingest knowledge_search knowledge_deindex cancel_agent_run].include?(action)

    arguments = params[:prompt].present? ? {"prompt" => params[:prompt], "allow_routine_writes" => params[:allow_routine_writes] == "1",
      "write_scope_ids" => params[:write_scope_ids].to_s.scan(/\d+/).map(&:to_i)} : JSON.parse(params.fetch(:arguments))

    arguments["engine"] = params[:engine].presence || "gemini" if action == "start_ai_run"

    arguments = {"id" => Integer(params.fetch(:native_id))} if %w[knowledge_ingest knowledge_deindex].include?(action) && params[:native_id].present?

    arguments = {"query" => params[:knowledge_query]} if action == "knowledge_search" && params[:knowledge_query].present?

    raise ::ArgumentError, "Arguments JSON phải là object" unless arguments.is_a?(Hash)

    @result = Qldapm::AiBridge.call(@project, User.current, "command", {action:, arguments:,

        idempotency_key: SecureRandom.uuid, auto_execute: params[:auto_execute] == "1"})

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
    status = if error.message.match?(/từ chối|không có quyền|403/)
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

    raise ActiveRecord::RecordNotFound unless @project.identifier == "qldapm-local"

    item = WorkPackage.visible(User.current).where(project: @project).first

    raise ActiveRecord::RecordNotFound unless item

    actor_info = item.qldapm_actor(User.current)

    return deny_access unless actor_info && actor_info["role"].present?

    @role = Qldapm::Rbac.role(@project, User.current)

    @tools = %w[identity list_work_packages analyze get_assistant_status get_action_history start_ai_run get_work_package get_project_options get_gate get_job get_proposal get_ai_run comment]

    @tools += %w[create_work_package update_work_package transition change_gate] if @role == "PM"

  end



  def bridge(action, arguments, key = nil)

    Qldapm::AiBridge.call(@project, User.current, "command", {action:, arguments:, idempotency_key: key})


  end

end

