"""Script to patch engineering.html.erb with dynamic reporting schedule binding and configuration modal."""
from pathlib import Path

path = Path("openproject/ai/core/overlay/app/views/qldapm_ai/engineering.html.erb")
content = path.read_text(encoding="utf-8")

old_section = """    <%# Engineering Progress Reports Section (Milestone 7) %>
    <div class="qldapm-section">
      <div class="qldapm-section-header">
        <h2 class="qldapm-section-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          Báo cáo tiến độ kỹ thuật (Automated Reporting System)
        </h2>
        <span style="font-size: 12px; color: #64748b; margin-left: 12px;">Lịch tự động: <strong>Daily (08:00)</strong> · <strong>Weekly (Thứ 2, 09:00)</strong> (Độc lập với Engineering AUTO)</span>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <%= form_tag project_qldapm_ai_command_path(@project.identifier), style: 'display: inline;' do %>
            <%= hidden_field_tag :tool, 'engineering_report_generate' %>
            <%= hidden_field_tag :arguments, {report_type: 'DAILY', include_narrative: false}.to_json %>
            <button type="submit" class="qldapm-btn qldapm-btn-secondary" style="padding: 4px 10px; font-size: 12px; cursor: pointer;">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 14 14"/></svg>
              Tạo Daily Report
            </button>
          <% end %>

          <%= form_tag project_qldapm_ai_command_path(@project.identifier), style: 'display: inline;' do %>
            <%= hidden_field_tag :tool, 'engineering_report_generate' %>
            <%= hidden_field_tag :arguments, {report_type: 'WEEKLY', include_narrative: false}.to_json %>
            <button type="submit" class="qldapm-btn qldapm-btn-secondary" style="padding: 4px 10px; font-size: 12px; cursor: pointer;">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              Tạo Weekly Report
            </button>
          <% end %>

          <%= form_tag project_qldapm_ai_command_path(@project.identifier), style: 'display: inline;' do %>
            <%= hidden_field_tag :tool, 'engineering_report_generate' %>
            <%= hidden_field_tag :arguments, {report_type: 'ON_DEMAND', include_narrative: true}.to_json %>
            <button type="submit" class="qldapm-btn qldapm-btn-primary" style="padding: 4px 10px; font-size: 12px; cursor: pointer;">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              Snapshot Tức Thời (+AI)
            </button>
          <% end %>
        </div>
      </div>"""

new_section = """    <%# Engineering Progress Reports Section (Milestone 7 & Phase 2.8 Finding B/G) %>
    <% sched = @engineering&.dig('reporting_schedule') || {} %>
    <% weekly_days = {1 => 'Thứ 2 (Thứ Hai)', 2 => 'Thứ 3', 3 => 'Thứ 4', 4 => 'Thứ 5', 5 => 'Thứ 6', 6 => 'Thứ 7', 7 => 'Chủ Nhật'} %>
    <div class="qldapm-section">
      <div class="qldapm-section-header">
        <h2 class="qldapm-section-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          Báo cáo tiến độ kỹ thuật (Automated Reporting System)
        </h2>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <button type="button" class="qldapm-btn qldapm-btn-secondary" style="padding: 4px 10px; font-size: 12px; cursor: pointer;" onclick="document.getElementById('qldapm-schedule-modal').style.display='flex';">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
            Cấu hình Lịch
          </button>

          <%= form_tag project_qldapm_ai_command_path(@project.identifier), style: 'display: inline;' do %>
            <%= hidden_field_tag :tool, 'engineering_report_generate' %>
            <%= hidden_field_tag :arguments, {report_type: 'DAILY', include_narrative: false}.to_json %>
            <button type="submit" class="qldapm-btn qldapm-btn-secondary" style="padding: 4px 10px; font-size: 12px; cursor: pointer;">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 14 14"/></svg>
              Tạo Daily Report
            </button>
          <% end %>

          <%= form_tag project_qldapm_ai_command_path(@project.identifier), style: 'display: inline;' do %>
            <%= hidden_field_tag :tool, 'engineering_report_generate' %>
            <%= hidden_field_tag :arguments, {report_type: 'WEEKLY', include_narrative: false}.to_json %>
            <button type="submit" class="qldapm-btn qldapm-btn-secondary" style="padding: 4px 10px; font-size: 12px; cursor: pointer;">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              Tạo Weekly Report
            </button>
          <% end %>

          <%= form_tag project_qldapm_ai_command_path(@project.identifier), style: 'display: inline;' do %>
            <%= hidden_field_tag :tool, 'engineering_report_generate' %>
            <%= hidden_field_tag :arguments, {report_type: 'ON_DEMAND', include_narrative: true}.to_json %>
            <button type="submit" class="qldapm-btn qldapm-btn-primary" style="padding: 4px 10px; font-size: 12px; cursor: pointer;">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              Snapshot Tức Thời (+AI)
            </button>
          <% end %>
        </div>
      </div>

      <%# Dynamic Schedule Status Banner (Finding G) %>
      <div style="font-size: 12px; color: #334155; margin: 0 0 14px 0; background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px 14px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
        <div>
          <span style="font-weight: 600; color: #0f172a;">Lịch Tự Động Định Kỳ (<%= sched['timezone'] || 'Asia/Ho_Chi_Minh' %>):</span>
          <span style="margin-left: 8px;">
            Daily: <strong><%= sched['daily_enabled'] != false ? sprintf('%02d:%02d', sched['daily_hour'] || 8, sched['daily_minute'] || 0) : 'TẮT' %></strong>
            <% if sched['last_daily_run_iso'].present? %><span style="color: #64748b;">(gần nhất: <%= sched['last_daily_run_iso'] %>)</span><% end %>
          </span>
          <span style="margin: 0 6px; color: #cbd5e1;">|</span>
          <span>
            Weekly: <strong><%= sched['weekly_enabled'] != false ? "#{weekly_days[sched['weekly_day'] || 1]}, #{sprintf('%02d:%02d', sched['weekly_hour'] || 9, sched['weekly_minute'] || 0)}" : 'TẮT' %></strong>
            <% if sched['last_weekly_run_iso'].present? %><span style="color: #64748b;">(gần nhất: <%= sched['last_weekly_run_iso'] %>)</span><% end %>
          </span>
        </div>
        <div style="font-size: 11px; color: #64748b; font-style: italic;">
          Background Worker tự động kích hoạt độc lập với Engineering AUTO
        </div>
      </div>

      <%# Modal Cấu hình Lịch Báo Cáo %>
      <div id="qldapm-schedule-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(15, 23, 42, 0.45); z-index: 9999; justify-content: center; align-items: center;">
        <div style="background: #ffffff; border-radius: 8px; width: 480px; max-width: 90vw; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04); overflow: hidden; border: 1px solid #cbd5e1;">
          <div style="padding: 14px 20px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0; font-size: 15px; font-weight: 600; color: #0f172a;">Cấu hình Lịch Báo cáo Tiến độ (Project 6)</h3>
            <button type="button" style="background: none; border: none; font-size: 18px; cursor: pointer; color: #64748b;" onclick="document.getElementById('qldapm-schedule-modal').style.display='none';">&times;</button>
          </div>
          <div style="padding: 20px;">
            <%= form_tag project_qldapm_ai_command_path(@project.identifier), id: 'qldapm-schedule-form' do %>
              <%= hidden_field_tag :tool, 'engineering_report_schedule_update' %>
              <%= hidden_field_tag :arguments, '', id: 'qldapm-schedule-args' %>

              <div style="margin-bottom: 16px;">
                <label style="display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 13px; color: #1e293b; cursor: pointer;">
                  <input type="checkbox" id="cfg-daily-en" <%= 'checked' if sched['daily_enabled'] != false %>>
                  Bật Báo Cáo Daily Tự Động
                </label>
                <div style="margin-top: 8px; margin-left: 24px; display: flex; align-items: center; gap: 8px; font-size: 13px;">
                  <span>Giờ chạy (Giờ:Phút):</span>
                  <input type="number" id="cfg-daily-h" min="0" max="23" value="<%= sched['daily_hour'] || 8 %>" style="width: 60px; padding: 4px 6px; border: 1px solid #cbd5e1; border-radius: 4px;"> :
                  <input type="number" id="cfg-daily-m" min="0" max="59" value="<%= sched['daily_minute'] || 0 %>" style="width: 60px; padding: 4px 6px; border: 1px solid #cbd5e1; border-radius: 4px;">
                </div>
              </div>

              <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 16px 0;">

              <div style="margin-bottom: 16px;">
                <label style="display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 13px; color: #1e293b; cursor: pointer;">
                  <input type="checkbox" id="cfg-weekly-en" <%= 'checked' if sched['weekly_enabled'] != false %>>
                  Bật Báo Cáo Weekly Tự Động
                </label>
                <div style="margin-top: 8px; margin-left: 24px; display: flex; flex-direction: column; gap: 8px; font-size: 13px;">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <span>Ngày trong tuần:</span>
                    <select id="cfg-weekly-d" style="padding: 4px 8px; border: 1px solid #cbd5e1; border-radius: 4px;">
                      <% weekly_days.each do |day_idx, day_label| %>
                        <option value="<%= day_idx %>" <%= 'selected' if (sched['weekly_day'] || 1) == day_idx %>><%= day_label %></option>
                      <% end %>
                    </select>
                  </div>
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <span>Giờ chạy (Giờ:Phút):</span>
                    <input type="number" id="cfg-weekly-h" min="0" max="23" value="<%= sched['weekly_hour'] || 9 %>" style="width: 60px; padding: 4px 6px; border: 1px solid #cbd5e1; border-radius: 4px;"> :
                    <input type="number" id="cfg-weekly-m" min="0" max="59" value="<%= sched['weekly_minute'] || 0 %>" style="width: 60px; padding: 4px 6px; border: 1px solid #cbd5e1; border-radius: 4px;">
                  </div>
                </div>
              </div>

              <div style="font-size: 12px; color: #64748b; background: #f1f5f9; padding: 8px; border-radius: 4px; margin-bottom: 16px;">
                Múi giờ thực thi: <strong>Asia/Ho_Chi_Minh (UTC+7)</strong>.
              </div>

              <div style="display: flex; justify-content: flex-end; gap: 10px;">
                <button type="button" class="qldapm-btn qldapm-btn-secondary" style="padding: 6px 14px; cursor: pointer;" onclick="document.getElementById('qldapm-schedule-modal').style.display='none';">Hủy</button>
                <button type="button" class="qldapm-btn qldapm-btn-primary" style="padding: 6px 14px; cursor: pointer;" onclick="saveScheduleConfig();">Lưu Lịch Trình</button>
              </div>
            <% end %>
          </div>
        </div>
      </div>
      <script>
        function saveScheduleConfig() {
          var payload = {
            daily_enabled: document.getElementById('cfg-daily-en').checked,
            daily_hour: parseInt(document.getElementById('cfg-daily-h').value, 10) || 0,
            daily_minute: parseInt(document.getElementById('cfg-daily-m').value, 10) || 0,
            weekly_enabled: document.getElementById('cfg-weekly-en').checked,
            weekly_day: parseInt(document.getElementById('cfg-weekly-d').value, 10) || 1,
            weekly_hour: parseInt(document.getElementById('cfg-weekly-h').value, 10) || 0,
            weekly_minute: parseInt(document.getElementById('cfg-weekly-m').value, 10) || 0,
            timezone: 'Asia/Ho_Chi_Minh'
          };
          document.getElementById('qldapm-schedule-args').value = JSON.stringify(payload);
          document.getElementById('qldapm-schedule-form').submit();
        }
      </script>"""

assert old_section in content, "old_section not found"
content = content.replace(old_section, new_section, 1)

path.write_text(content, encoding="utf-8")
print("SUCCESSFULLY PATCHED engineering.html.erb")
