path = 'openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """  def execution
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex"
    if request.format.json? || params[:format] == "json" || request.headers["Accept"].to_s.include?("application/json")
      return render json: bridge("get_execution_monitor", {id: params.fetch(:run_id)})["result"]
    end
    render :execution

  rescue ::ArgumentError, ::KeyError => error

    status = error.message.match?(/403|404|không có quyền|Không tìm thấy/) ? :forbidden : :service_unavailable

    render json: {error: status == :forbidden ? "EXECUTION_ACCESS_DENIED" : "EXECUTION_UNAVAILABLE"}, status:

  end"""

replacement = """  def execution
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex"
    run_id = params[:run_id].presence || params[:id].presence
    raise ::KeyError, "run_id required" unless run_id

    if request.format.json? || params[:format] == "json" || request.headers["Accept"].to_s.include?("application/json")
      result = bridge("get_execution_monitor", {id: run_id})["result"]
      return render json: result
    end
    render :execution

  rescue ::ArgumentError, ::KeyError, ::StandardError => error
    status = error.message.match?(/403|không có quyền/) ? :forbidden : (error.message.match?(/404|Không tìm thấy|AI_RUN_NOT_FOUND/) ? :not_found : :service_unavailable)
    render json: {error: status == :forbidden ? "EXECUTION_ACCESS_DENIED" : (status == :not_found ? "EXECUTION_NOT_FOUND" : "EXECUTION_UNAVAILABLE"), message: error.message}, status: status
  end"""

if target in content:
    content = content.replace(target, replacement, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('PATCH_CONTROLLER_SUCCESS')
else:
    # Try normalizing line endings
    content_norm = content.replace('\r\n', '\n')
    target_norm = target.replace('\r\n', '\n')
    replacement_norm = replacement.replace('\r\n', '\n')
    if target_norm in content_norm:
        content_norm = content_norm.replace(target_norm, replacement_norm, 1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content_norm)
        print('PATCH_CONTROLLER_SUCCESS_NORM')
    else:
        print('TARGET_NOT_FOUND')
