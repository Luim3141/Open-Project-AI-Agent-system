path = 'openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update execution method to be more resilient with json
target1 = '''  def execution

    response.headers["Cache-Control"] = "no-store"

    response.headers["X-Robots-Tag"] = "noindex"

    return render :execution unless request.format.json?



    render json: bridge("get_execution_monitor", {id: params.fetch(:run_id)})["result"]'''

replacement1 = '''  def execution
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex"
    if request.format.json? || params[:format] == "json" || request.headers["Accept"].to_s.include?("application/json")
      return render json: bridge("get_execution_monitor", {id: params.fetch(:run_id)})["result"]
    end
    render :execution'''

# 2. Update case statement in command
target2 = '''          when \'engineering_control\'
            target_mode = arguments[\'mode\']
            @result[\'message\'] = "Đã cập nhật chế độ điều khiển hệ thống sang: #{target_mode}."'''

replacement2 = '''          when \'engineering_control\'
            target_mode = arguments[\'mode\']
            if target_mode == \'AUTO\' && @result.dig(\'scheduled\', \'reason\') == \'ALL_DELIVERED\'
              @result[\'message\'] = "Tất cả 5/5 Backlog units hiện tại đã hoàn tất giao hàng. Chế độ AUTO tự động ngắt an toàn (OFF) để bảo vệ hệ thống. Nhấn \'Giao việc mới cho AI\' để lập kế hoạch cho tính năng tiếp theo."
            elsif target_mode == \'AUTO\' && @result.dig(\'scheduled\', \'scheduled\') == true
              @result[\'message\'] = "Đã kích hoạt chế độ AUTO: Đang điều phối Unit \'#{@result.dig(\'scheduled\', \'unit\')}\' (Run ID: #{@result.dig(\'scheduled\', \'run_id\')})."
            elsif target_mode == \'PAUSED\'
              @result[\'message\'] = "Đã tạm dừng hệ thống (PAUSED). Mọi tác vụ đang chạy sẽ checkpoint an toàn và không nhận thêm việc mới."
            else
              @result[\'message\'] = "Đã cập nhật chế độ điều khiển hệ thống sang: #{target_mode}."
            end
          when \'engineering_plan\'
            plan_id = @result[\'id\'] || @result[\'run_id\']
            if @result[\'deduplicated\']
              @result[\'message\'] = "Yêu cầu tính năng này đã được tiếp nhận và xử lý (Run ID: #{plan_id})."
            else
              @result[\'message\'] = "Đã chuyển yêu cầu tính năng mới tới Tác nhân PM & BA (Run ID: #{plan_id}). Đang tạo đặc tả kỹ thuật và Backlog Unit mới."
            end'''

target3 = '''          when \'engineering_report_generate\'
            rtype = arguments[\'report_type\'] || \'Báo cáo\'
            @result[\'message\'] = "Đã tạo thành công #{rtype} (Report ID: #{@result[\'id\'] || @result[\'report_id\']})."'''

replacement3 = '''          when \'engineering_report_generate\'
            rtype = arguments[\'report_type\'] || \'Báo cáo\'
            rep_id = @result[\'id\'] || @result[\'report_id\']
            @result[\'message\'] = "Đã tạo thành công #{rtype} (Report ID: #{rep_id}). Bấm \'Xem toàn văn\' trên thẻ báo cáo để đọc nội dung chi tiết."
            @generated_report_id = rep_id'''

if target1 in code:
    code = code.replace(target1, replacement1, 1)
else:
    print("Warning: target1 not matched directly")

if target2 in code:
    code = code.replace(target2, replacement2, 1)
else:
    print("Warning: target2 not matched directly")

if target3 in code:
    code = code.replace(target3, replacement3, 1)
else:
    print("Warning: target3 not matched directly")

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated qldapm_ai_controller.rb successfully")
