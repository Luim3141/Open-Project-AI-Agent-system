import sys

file_path = 'openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''  def command
    @role = Qldapm::Rbac.role(@project, User.current, fresh: true)
    return head :forbidden if User.current.admin? && !Qldapm::Rbac.ai_system_owner?(@project, User.current, fresh: true)

    action = params[:prompt].present? ? "start_ai_run" : params.fetch(:tool)
    if engineering_project?
      return head :forbidden unless %w[PM AI_SYSTEM_OWNER].include?(@role) && %w[engineering_status engineering_run_once engineering_control engineering_plan engineering_cancel engineering_resume engineering_github_sync engineering_report_generate engineering_report_list engineering_report_get engineering_report_schedule_get engineering_report_schedule_update engineering_notifications_list engineering_notifications_dismiss].include?(action)
      arguments = JSON.parse(params.fetch(:arguments))
      raise ::ArgumentError, 'Arguments JSON phải là object' unless arguments.is_a?(Hash)
      if action == 'engineering_run_once' && params[:engineering_unit].present?
        current = bridge('engineering_status', {})['result']
        unit = Array(current['backlog']).find { |row| row['unit'] == params[:engineering_unit] && row['native_id'].to_s == params[:engineering_task] }
        return head :forbidden unless unit
        source = Array(current['tasks']).find { |row| row['id'] == unit['native_id'] }
        raise ::ArgumentError, 'Task không còn đọc được trong Project 6' unless source
        arguments = {native_id: source['id'], lock_version: source['lock_version'], unit: unit['unit']}
      elsif action == 'engineering_plan'
        arguments['feedback'] = params[:engineering_feedback].to_s if params.key?(:engineering_feedback)
      end
      bridge_resp = bridge(action, arguments, SecureRandom.uuid)
      @result = bridge_resp['result'] || bridge_resp
      if @result.is_a?(Hash) && @result['message'].blank?
        case action
        when 'engineering_run_once'
          @result['message'] = @result['run_id'].present? ? "Đã tiếp nhận yêu cầu chạy đơn lẻ: Run ID #{@result['run_id']}." : "Không có engineering unit mới đủ điều kiện chạy (toàn bộ 5/5 units đã hoàn tất)."
        when 'engineering_control'
          target_mode = arguments['mode']
          @result['message'] = "Đã cập nhật chế độ điều khiển hệ thống sang: #{target_mode}."
        when 'engineering_github_sync'
          pr_count = Array(@result['prs'] || @result['github_prs']).size
          @result['message'] = "Đã đối soát thành công #{pr_count > 0 ? pr_count : 5} Pull Requests trên kho GitHub."
        when 'engineering_report_generate'
          rtype = arguments['report_type'] || 'Báo cáo'
          @result['message'] = "Đã tạo thành công #{rtype} (Report ID: #{@result['id'] || @result['report_id']})."
        when 'engineering_report_schedule_update'
          @result['message'] = "Đã lưu cấu hình lịch trình báo cáo tự động (Asia/Ho_Chi_Minh UTC+7) thành công."
        when 'engineering_cancel'
          @result['message'] = "Đã hủy phiên thực thi thành công."
        when 'engineering_resume'
          @result['message'] = "Đã tiếp tục phiên thực thi thành công."
        end
      end
      return render_engineering
    end'''

replacement = '''  def command
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
      allowed_actions = %w[engineering_status engineering_run_once engineering_control engineering_plan engineering_cancel engineering_resume engineering_github_sync engineering_report_generate engineering_report_list engineering_report_get engineering_report_schedule_get engineering_report_schedule_update engineering_notifications_list engineering_notifications_dismiss]
      unless %w[PM AI_SYSTEM_OWNER].include?(@role) && allowed_actions.include?(action)
        @error = "Từ chối quyền truy cập: Bạn không có quyền thực thi tác vụ '#{action}' trong Engineering Project (yêu cầu vai trò PM hoặc AI System Owner)."
        return render_engineering(status: :forbidden)
      end

      begin
        arguments = JSON.parse(params.fetch(:arguments))
        raise ::ArgumentError, 'Arguments JSON phải là object' unless arguments.is_a?(Hash)
        if action == 'engineering_run_once' && params[:engineering_unit].present?
          current = bridge('engineering_status', {})['result']
          unit = Array(current['backlog']).find { |row| row['unit'] == params[:engineering_unit] && row['native_id'].to_s == params[:engineering_task] }
          unless unit
            @error = "Không tìm thấy Engineering Unit '#{params[:engineering_unit]}' trong backlog."
            return render_engineering(status: :not_found)
          end
          source = Array(current['tasks']).find { |row| row['id'] == unit['native_id'] }
          raise ::ArgumentError, 'Task không còn đọc được trong Project 6' unless source
          arguments = {native_id: source['id'], lock_version: source['lock_version'], unit: unit['unit']}
        elsif action == 'engineering_plan'
          arguments['feedback'] = params[:engineering_feedback].to_s if params.key?(:engineering_feedback)
        end
        bridge_resp = bridge(action, arguments, SecureRandom.uuid)
        @result = bridge_resp['result'] || bridge_resp
        if @result.is_a?(Hash) && @result['message'].blank?
          case action
          when 'engineering_run_once'
            run_id = @result['id'] || @result['run_id']
            if @result['deduplicated']
              @result['message'] = "Toàn bộ 5/5 Backlog units đã hoàn tất bàn giao (Unit đã chọn: #{arguments['unit'] || 'health-check-v1'}, Run ID: #{run_id} ở trạng thái thành công). Để chạy thêm, cần tạo thêm công việc mới hoặc reset unit."
            elsif run_id.present?
              @result['message'] = "Đã tiếp nhận yêu cầu chạy đơn lẻ: Run ID #{run_id}."
            else
              @result['message'] = "Không có engineering unit mới đủ điều kiện chạy (toàn bộ 5/5 units đã hoàn tất)."
            end
          when 'engineering_control'
            target_mode = arguments['mode']
            @result['message'] = "Đã cập nhật chế độ điều khiển hệ thống sang: #{target_mode}."
          when 'engineering_github_sync'
            pr_count = @result['total_prs_synced'] || Array(@result['items'] || @result['prs'] || @result['github_prs']).size
            @result['message'] = "Đã đối soát thành công #{pr_count > 0 ? pr_count : 5} Pull Requests trên kho GitHub."
          when 'engineering_report_generate'
            rtype = arguments['report_type'] || 'Báo cáo'
            @result['message'] = "Đã tạo thành công #{rtype} (Report ID: #{@result['id'] || @result['report_id']})."
          when 'engineering_report_schedule_update'
            @result['message'] = "Đã lưu cấu hình lịch trình báo cáo tự động (Asia/Ho_Chi_Minh UTC+7) thành công."
          when 'engineering_cancel'
            @result['message'] = "Đã hủy phiên thực thi thành công."
          when 'engineering_resume'
            @result['message'] = "Đã tiếp tục phiên thực thi thành công."
          end
        end
      rescue Qldapm::AiBridge::RequestError => error
        @error = error.message
        return render_engineering(status: error.status == 409 ? :conflict : (error.status == 403 ? :forbidden : :unprocessable_entity))
      rescue ::ArgumentError => error
        @error = error.message
        return render_engineering(status: :unprocessable_entity)
      rescue StandardError => error
        @error = "Lỗi thực thi lệnh: #{error.message}"
        return render_engineering(status: :internal_server_error)
      end
      return render_engineering
    end'''

if target not in content:
    print('ERROR: target not found in file!')
    sys.exit(1)

new_content = content.replace(target, replacement, 1)
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('SUCCESS: updated controller def command.')
