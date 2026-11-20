class QldapmGatesController < ApplicationController
  before_action :require_login
  before_action :load_item, only: %i[show update]
  before_action :load_project, only: :index
  authorize_with_permission :view_work_packages

  def index
    @items = WorkPackage.visible(User.current).where(project: @project).order(:id)
  end

  def show
    @policy = Qldapm::GatePolicy.new
    @snapshot = @item.qldapm_snapshot
  end

  def update
    begin
      raise ::ArgumentError, "PM_REQUIRED: chỉ PM/AI System Owner được thay đổi gate hoặc trạng thái" unless Qldapm::Rbac.pm?(@project, User.current)
      if params[:operation] == "transition"
        result = WorkPackages::UpdateService.new(user: User.current, model: @item).call(
          status_id: Integer(params.fetch(:status_id).to_s), lock_version: Integer(params.fetch(:lock_version).to_s))
        raise ::ArgumentError, result.errors.full_messages.join("; ") unless result.success?
      else
        raise ::ArgumentError, "Gate value phải là object" unless params[:value].is_a?(ActionController::Parameters)
        value = params.fetch(:value).to_unsafe_h.deep_stringify_keys
        value["done"] = ActiveModel::Type::Boolean.new.cast(value["done"]) if params[:operation] == "checklist"
        value["job_receipt"] = JSON.parse(value["job_receipt"]) if value["verification"] == "automatic" && value["job_receipt"].is_a?(String)
        Qldapm::GateActions.new(@item, User.current).call(params[:operation], value, params[:lock_version])
      end
      flash[:notice] = "Saved. Evidence is an assertion, not proof that tests actually passed."
    rescue JSON::ParserError
      flash[:error] = "Job receipt JSON không hợp lệ; chưa lưu."
    rescue ::ArgumentError, ActiveRecord::RecordInvalid, ::KeyError => error
      flash[:error] = error.message
    end
    redirect_to qldapm_gate_path(@item.id)
  end

  private

  def load_project
    @project = Project.visible(User.current).find_by!(identifier: params[:project_id])
    render_404 unless @project.identifier == "qldapm-local"
  end

  def load_item
    @item = WorkPackage.visible(User.current).find(params[:id])
    render_404 unless @item.qldapm_managed?
    @project = @item.project
  end
end
