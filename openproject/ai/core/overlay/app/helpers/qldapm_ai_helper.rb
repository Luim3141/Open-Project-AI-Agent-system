module QldapmAIHelper
  ACTIONS = {"delete_work_package"=>"Xóa vĩnh viễn Task Native", "update_dependency"=>"Đổi lag dependency Native", "delete_dependency"=>"Xóa relation dependency Native", "create_dependency"=>"Tạo dependency Native", "create_work_package" => "Tạo công việc", "update_work_package" => "Cập nhật công việc",
             "comment" => "Thêm bình luận", "transition" => "Chuyển trạng thái", "write_code" => "Sửa nội dung file"}.freeze
  FIELDS = {"subject" => "Tên công việc", "description" => "Mô tả", "start_date" => "Ngày bắt đầu", "due_date" => "Hạn hoàn thành",
            "assignee_id" => "Người phụ trách", "assignee_role" => "Vai trò phụ trách", "priority_id" => "Ưu tiên",
            "status_id" => "Trạng thái", "parent_id" => "Công việc cha", "type_id" => "Loại công việc", "text" => "Bình luận"}.freeze

  def qldapm_preview(proposal)
    command = proposal.fetch("command", {})
    action, args = command["action"], command.fetch("arguments", {})
    before = command.dig("preview", "before") || {}
    changes = action == "update_work_package" ? args.fetch("changes", {}) : args
    changes = changes.merge((command.dig("preview", "date_adjustments") || {}).transform_values { |row| row["actual"] })
    title = ACTIONS.fetch(action, "Thay đổi công việc")
    if action=='delete_work_package'
      return {title:"#{title} ##{args['id']}",subject:command.dig('preview','subject'),
        rows:[{label:'Xóa vĩnh viễn',before:"Task NEW v#{args['lock_version']}",after:'Xóa đúng Task độc lập này và nội dung Native thuộc Task; không cascade. Giữ signed tombstone và audit.'}]}
    end
    if %w[create_dependency update_dependency delete_dependency].include?(action)
      prior_lag=action=='create_dependency' ? '—' : command.dig('preview','before','lag')
      prior_lag='Không đặt (Native)' if prior_lag.nil?
      rows = [{label:'Lag (ngày làm việc)',before:prior_lag,after:action=='delete_dependency' ? 'Gỡ relation; không xóa công việc' : args['lag']}]
      rows += command.fetch('preview').fetch('possible_affected').map do |item|
        {label:"Phạm vi có thể đổi lịch ##{item['id']}",before:"v#{item['lockVersion']}: #{item['startDate']} → #{item['dueDate']}",
         after:'Native có thể tính lại lịch trong phạm vi này; không phải dự đoán ngày mới.'}
      end
      relation=args['relation_id'] ? " (relation ##{args['relation_id']})" : ''
      return {title:"#{title}#{relation}: ##{args['predecessor_id']} → ##{args['successor_id']}",subject:nil,rows:}
    end
    title += " ##{args['id']}" if args["id"].is_a?(Integer)
    if action == "write_code"
      return {title: title + " “#{args['path']}”", subject: nil,
              rows: [{label: "Nội dung file", before: before["content"].presence || "File mới", after: args["content"]}]}
    end
    rows = changes.filter_map do |field, value|
      next unless FIELDS.key?(field)
      old = case field
            when "start_date" then before["startDate"]
            when "due_date" then before["dueDate"]
            when "description" then before.dig("description", "raw")
            when "assignee_id", "assignee_role" then before.dig("_links", "assignee", "title")
            when "priority_id" then before.dig("_links", "priority", "title")
            when "status_id" then before.dig("_links", "status", "title")
            else before[field]
            end
      label = case field
              when "status_id" then Status.find_by(id: value)&.name
              when "type_id" then Type.find_by(id: value)&.name
              when "priority_id" then IssuePriority.find_by(id: value)&.name
              when "parent_id" then "Công việc ##{value}"
              when "assignee_id" then "Thành viên ##{value}"
              else value
              end
      if adjustment = command.dig("preview", "date_adjustments", field)
        label = if adjustment["automatic"]
                  "#{adjustment['actual']} (OpenProject tự tính theo lịch và thời lượng công việc)"
                else
                  "#{adjustment['actual']} (OpenProject điều chỉnh từ #{adjustment['requested']} theo lịch làm việc)"
                end
      end
      {label: FIELDS[field], before: old.presence || "—", after: label.nil? ? "Bỏ giá trị" : label}
    end
    {title:, subject: before["subject"], rows:}
  end

  def qldapm_state(state)
    {"pending" => "Chờ duyệt", "confirmed" => "Đã thực hiện", "rejected" => "Đã từ chối",
     "reconciled_success" => "Đã đối soát Native thành công", "running" => "Đang xử lý", "done" => "Đã có kết quả", "failed_or_unknown" => "Cần kiểm tra kết quả"}.fetch(state, state)
  end
end
