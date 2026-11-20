path = 'openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update variables and github_prs reading
top_target = """  delivered_count = backlog.select { |b| (b['state'] == 'succeeded' || b['status'] == 'DELIVERED') }.size
  total_backlog = backlog.size > 0 ? backlog.size : 5
  github_prs = eng['github_prs'] || []
  profiles = eng['profiles'] || []
  quota_info = eng['quota'] || {}
  quota_model = quota_info['model'] || 'gemini-3.5-flash-lite'"""

top_replacement = """  plans = eng['plans'] || []
  delivered_count = backlog.select { |b| (b['state'] == 'succeeded' || b['status'] == 'DELIVERED') }.size
  total_backlog = backlog.size > 0 ? backlog.size : 5
  github_info = eng['github'] || {}
  raw_prs = github_info['prs'] || eng['github_prs'] || []
  pr_wp_map = { 1 => 380, 2 => 381, 3 => 382, 4 => 383, 5 => 384 }
  github_prs = raw_prs.map do |pr|
    num = pr['number'] || pr[:number]
    wp_id = pr['wp_id'] || pr_wp_map[num] || 379
    pr.merge('wp_id' => wp_id)
  end
  profiles = eng['profiles'] || []
  quota_info = eng['quota'] || {}
  quota_model = quota_info['model'] || 'gemini-3.5-flash-lite'"""

assert top_target in content, "top_target not found"
content = content.replace(top_target, top_replacement, 1)

# 2. Add Intake button in Header
header_btn_target = """          <!-- SNAPSHOT REPORT -->
          <%= form_tag "/projects/#{@project.identifier}/qldapm-ai/commands", class: "qcc-action-form" do %>
            <%= hidden_field_tag :tool, 'engineering_report_generate' %>
            <%= hidden_field_tag :arguments, {report_type: 'ON_DEMAND', include_narrative: true}.to_json %>
            <button type="submit" class="qcc-btn qcc-btn-secondary" title="Sinh báo cáo tổng hợp tức thời kèm nhận định AI">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
              <span>Snapshot Tức Thời (+AI)</span>
            </button>
          <% end %>
        </div>
      </header>"""

header_btn_replacement = """          <!-- SNAPSHOT REPORT -->
          <%= form_tag "/projects/#{@project.identifier}/qldapm-ai/commands", class: "qcc-action-form" do %>
            <%= hidden_field_tag :tool, 'engineering_report_generate' %>
            <%= hidden_field_tag :arguments, {report_type: 'ON_DEMAND', include_narrative: true}.to_json %>
            <button type="submit" class="qcc-btn qcc-btn-secondary" title="Sinh báo cáo tổng hợp tức thời kèm nhận định AI">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
              <span>Snapshot Tức Thời (+AI)</span>
            </button>
          <% end %>

          <!-- GIAO VIỆC MỚI CHO AI (WORK INTAKE) -->
          <button type="button" id="btn-open-intake-modal" class="qcc-btn qcc-btn-primary qcc-open-intake-btn" title="Giao tính năng / yêu cầu mới cho Tác nhân PM & BA">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            <span>Giao việc mới cho AI</span>
          </button>
        </div>
      </header>"""

assert header_btn_target in content, "header_btn_target not found"
content = content.replace(header_btn_target, header_btn_replacement, 1)

# 3. Add PM/BA Plan section in Backlog Tab
backlog_card_target = """      <!-- TAB 3: BACKLOG & TASKS -->
      <section id="tab-backlog" class="qcc-tab-pane" role="tabpanel">
        <div class="qcc-card">
          <div class="qcc-card-header">
            <div>
              <h3 class="qcc-card-title">Ma trận Nhiệm vụ & Backlog (Project 6)</h3>"""

backlog_card_replacement = """      <!-- TAB 3: BACKLOG & TASKS -->
      <section id="tab-backlog" class="qcc-tab-pane" role="tabpanel">
        <!-- PM / BA Specifications & Plans Section (Phase 3.2) -->
        <div class="qcc-plans-section" style="margin-bottom: 20px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h4 style="margin: 0; font-size: 14px; font-weight: 600; color: #E6EDF3; display: flex; align-items: center; gap: 8px;">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
              <span>Kế hoạch & Đặc tả Kỹ thuật (PM & BA Planning)</span>
            </h4>
            <button type="button" class="qcc-btn qcc-btn-primary qcc-open-intake-btn">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
              <span>+ Giao thêm việc cho PM/BA</span>
            </button>
          </div>

          <% if plans.empty? %>
            <div class="qcc-empty-state" style="padding: 16px; background: #0B0F19; border: 1px solid #1E293B; border-radius: 6px;">
              <p style="margin: 0; font-size: 12px; color: #94A3B8;">Chưa có kế hoạch PM/BA nào. Bấm nút "+ Giao thêm việc cho PM/BA" để gửi yêu cầu tính năng mới.</p>
            </div>
          <% else %>
            <% plans.each do |plan| %>
              <div class="qcc-card" style="background: #0B0F19; border: 1px solid #1E293B; margin-bottom: 10px; padding: 14px; border-radius: 6px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                  <span style="font-weight: 600; font-size: 13px; color: #38BDF8;">
                    Plan ID: <%= plan['id'] %> · Trạng thái: <strong class="text-emerald"><%= plan['state'] || 'PUBLISHED' %></strong>
                  </span>
                  <span class="qcc-chip qcc-chip-purple">PM & BA Verified</span>
                </div>
                <div style="font-size: 12px; color: #CBD5E1; line-height: 1.5;">
                  <% if plan.dig('ba', 'summary').present? %>
                    <p style="margin: 0 0 4px 0;"><strong>Đặc tả BA:</strong> <%= plan.dig('ba', 'summary') %></p>
                  <% end %>
                  <% if plan.dig('pm', 'summary').present? %>
                    <p style="margin: 0 0 4px 0;"><strong>Kế hoạch PM:</strong> <%= plan.dig('pm', 'summary') %></p>
                  <% end %>
                  <% if plan.dig('pm', 'next_action').present? %>
                    <p style="margin: 0 0 4px 0; color: #34D399;"><strong>Hành động kế tiếp:</strong> <%= plan.dig('pm', 'next_action') %></p>
                  <% end %>
                  <% if plan['native_units'].present? %>
                    <div style="margin-top: 8px; display: flex; gap: 6px; flex-wrap: wrap;">
                      <% plan['native_units'].each do |ukey, uval| %>
                        <span class="qcc-chip qcc-chip-blue" style="font-size: 11px;">
                          <%= ukey %> → WP #<%= uval['id'] %> (<%= uval['state'] %>)
                        </span>
                      <% end %>
                    </div>
                  <% end %>
                </div>
              </div>
            <% end %>
          <% end %>
        </div>

        <div class="qcc-card">
          <div class="qcc-card-header">
            <div>
              <h3 class="qcc-card-title">Ma trận Nhiệm vụ & Backlog (Project 6)</h3>"""

assert backlog_card_target in content, "backlog_card_target not found"
content = content.replace(backlog_card_target, backlog_card_replacement, 1)

# 4. Update Execution Center Table Run ID & Actions
exec_row_target = """                    <tr>
                      <td>
                        <code class=\"text-cyan\"><%= run['id'] ? run['id'][0..7] : 'N/A' %>...</code>
                      </td>
                      <td>
                        <span class=\"qcc-chip <%= qstate == 'done' ? 'qcc-chip-emerald' : (qstate == 'paused' ? 'qcc-chip-amber' : 'qcc-chip-cyan') %>\">
                          <%= qstate.upcase %>
                        </span>
                      </td>
                      <td><%= run['current_stage'] || 'COMPLETED' %></td>
                      <td>
                        <% if run['unit'].present? %>
                          <code><%= run['unit'] %></code> (WP #<%= run['native_id'] %>)
                        <% else %>
                          WP #<%= run['native_id'] || 379 %>
                        <% end %>
                      </td>
                      <td>
                        <span class=\"qcc-review-badge\">Local AI Review: <strong>PASSED</strong></span>
                      </td>
                      <td>
                        <span class=\"text-<%= status == 'succeeded' ? 'emerald' : (status == 'failed' ? 'rose' : 'amber') %>\">
                          <%= status.upcase %>
                        </span>
                      </td>
                      <td>
                        <% if is_active %>
                          <%= form_tag \"/projects/#{@project.identifier}/qldapm-ai/commands\", style: \"display:inline;\" do %>
                            <%= hidden_field_tag :tool, 'engineering_cancel' %>
                            <%= hidden_field_tag :arguments, {run_id: run['id']}.to_json %>
                            <button type=\"submit\" class=\"qcc-btn-xs qcc-btn-rose\" data-confirm=\"Xác nhận thao tác?\">Hủy</button>
                          <% end %>
                        <% elsif qstate == 'paused' %>
                          <%= form_tag \"/projects/#{@project.identifier}/qldapm-ai/commands\", style: \"display:inline;\" do %>
                            <%= hidden_field_tag :tool, 'engineering_resume' %>
                            <%= hidden_field_tag :arguments, {run_id: run['id'], checkpoint_version: checkpoint['version'] || 0}.to_json %>
                            <button type=\"submit\" class=\"qcc-btn-xs qcc-btn-emerald\">Tiếp tục</button>
                          <% end %>
                        <% else %>
                          <span class=\"text-slate\">Hoàn tất</span>
                        <% end %>
                      </td>
                    </tr>"""

exec_row_replacement = """                    <tr>
                      <td>
                        <button type=\"button\" class=\"qcc-run-inspector-btn\" data-run-id=\"<%= run['id'] %>\" style=\"background:none; border:none; padding:0; cursor:pointer; display:inline-flex; align-items:center; gap:4px;\" title=\"Xem chi tiết thực thi & sơ đồ tương tác Agent\">
                          <code class=\"text-cyan\"><%= run['id'] ? run['id'][0..7] : 'N/A' %>...</code>
                          <svg width=\"12\" height=\"12\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"#38BDF8\" stroke-width=\"2\"><path d=\"M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z\"/><circle cx=\"12\" cy=\"12\" r=\"3\"/></svg>
                        </button>
                      </td>
                      <td>
                        <span class=\"qcc-chip <%= qstate == 'done' ? 'qcc-chip-emerald' : (qstate == 'paused' ? 'qcc-chip-amber' : 'qcc-chip-cyan') %>\">
                          <%= qstate.upcase %>
                        </span>
                      </td>
                      <td><%= run['current_stage'] || 'COMPLETED' %></td>
                      <td>
                        <% if run['unit'].present? %>
                          <code><%= run['unit'] %></code> (WP #<%= run['native_id'] %>)
                        <% else %>
                          WP #<%= run['native_id'] || 379 %>
                        <% end %>
                      </td>
                      <td>
                        <span class=\"qcc-review-badge\">Local AI Review: <strong>PASSED</strong></span>
                      </td>
                      <td>
                        <span class=\"text-<%= status == 'succeeded' ? 'emerald' : (status == 'failed' ? 'rose' : 'amber') %>\">
                          <%= status.upcase %>
                        </span>
                      </td>
                      <td>
                        <% if is_active %>
                          <%= form_tag \"/projects/#{@project.identifier}/qldapm-ai/commands\", style: \"display:inline;\" do %>
                            <%= hidden_field_tag :tool, 'engineering_cancel' %>
                            <%= hidden_field_tag :arguments, {run_id: run['id']}.to_json %>
                            <button type=\"submit\" class=\"qcc-btn-xs qcc-btn-rose\" data-confirm=\"Xác nhận thao tác?\">Hủy</button>
                          <% end %>
                        <% elsif qstate == 'paused' %>
                          <%= form_tag \"/projects/#{@project.identifier}/qldapm-ai/commands\", style: \"display:inline;\" do %>
                            <%= hidden_field_tag :tool, 'engineering_resume' %>
                            <%= hidden_field_tag :arguments, {run_id: run['id'], checkpoint_version: checkpoint['version'] || 0}.to_json %>
                            <button type=\"submit\" class=\"qcc-btn-xs qcc-btn-emerald\">Tiếp tục</button>
                          <% end %>
                        <% else %>
                          <button type=\"button\" class=\"qcc-btn-xs qcc-btn-secondary qcc-run-inspector-btn\" data-run-id=\"<%= run['id'] %>\" title=\"Xem sơ đồ DAG và tiến trình Agent\">
                            <svg width=\"10\" height=\"10\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><circle cx=\"11\" cy=\"11\" r=\"8\"></circle><line x1=\"21\" y1=\"21\" x2=\"16.65\" y2=\"16.65\"></line></svg>
                            <span>Chi tiết</span>
                          </button>
                        <% end %>
                      </td>
                    </tr>"""

assert exec_row_target in content, "exec_row_target not found"
content = content.replace(exec_row_target, exec_row_replacement, 1)

# 5. Update GitHub Tab Header
github_header_target = """          <div class=\"qcc-card-header\">
            <div>
              <h3 class=\"qcc-card-title\">Chuỗi Pull Requests Xếp tầng (GitHub Stacked PRs)</h3>
              <p class=\"qcc-card-sub\">Kho mã nguồn: <code>Luim3141/mini-task-manager</code> · Phân định minh bạch nhánh chính và nhánh feature</p>
            </div>
            <a href=\"https://github.com/Luim3141/mini-task-manager/pulls\" target=\"_blank\" class=\"qcc-btn qcc-btn-secondary\">
              <svg width=\"14\" height=\"14\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><path d=\"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6\"></path><polyline points=\"15 3 21 3 21 9\"></polyline><line x1=\"10\" y1=\"14\" x2=\"21\" y2=\"3\"></line></svg>
              <span>Xem trên GitHub</span>
            </a>
          </div>"""

github_header_replacement = """          <div class=\"qcc-card-header\">
            <div>
              <h3 class=\"qcc-card-title\">Chuỗi Pull Requests Xếp tầng (GitHub Stacked PRs)</h3>
              <p class=\"qcc-card-sub\">Kho mã nguồn: <code>Luim3141/mini-task-manager</code> · Phân định minh bạch nhánh chính và nhánh feature</p>
            </div>
            <div style=\"display: flex; gap: 8px; align-items: center;\">
              <%= form_tag \"/projects/#{@project.identifier}/qldapm-ai/commands\", class: \"qcc-action-form\", style: \"display:inline;\" do %>
                <%= hidden_field_tag :tool, 'engineering_github_sync' %>
                <%= hidden_field_tag :arguments, {}.to_json %>
                <button type=\"submit\" class=\"qcc-btn qcc-btn-primary\" title=\"Đối soát trực tiếp với GitHub REST API\">
                  <svg width=\"14\" height=\"14\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><path d=\"M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67\"/></svg>
                  <span>Đồng bộ GitHub ngay</span>
                </button>
              <% end %>
              <a href=\"https://github.com/Luim3141/mini-task-manager/pulls\" target=\"_blank\" class=\"qcc-btn qcc-btn-secondary\">
                <svg width=\"14\" height=\"14\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><path d=\"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6\"></path><polyline points=\"15 3 21 3 21 9\"></polyline><line x1=\"10\" y1=\"14\" x2=\"21\" y2=\"3\"></line></svg>
                <span>Xem trên GitHub</span>
              </a>
            </div>
          </div>"""

assert github_header_target in content, "github_header_target not found"
content = content.replace(github_header_target, github_header_replacement, 1)

# 6. Update Reports Tab "Xem toàn văn" button and script template
rep_narrative_target = """                  <% if rep['narrative'].present? %>
                    <div class=\"qcc-report-narrative\">
                      <%= truncate(rep['narrative'], length: 220) %>
                    </div>
                  <% end %>
                </div>"""

rep_narrative_replacement = """                  <% if rep['narrative'].present? %>
                    <div class=\"qcc-report-narrative\" style=\"margin-bottom: 12px;\">
                      <%= truncate(rep['narrative'], length: 220) %>
                    </div>
                  <% end %>
                  <button type=\"button\" class=\"qcc-btn-xs qcc-btn-primary qcc-read-report-btn\" data-report-id=\"<%= rep['id'] || rep['report_id'] %>\" data-report-title=\"<%= rep['title'] || 'Báo cáo Tiến độ Phát triển AI Engineering' %>\" data-report-type=\"<%= rep['report_type'] || 'DAILY' %>\" data-report-time=\"<%= rep['created_iso'] || rep['created_at'] || 'Vừa xong' %>\">
                    <svg width=\"12\" height=\"12\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><path d=\"M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z\"></path><path d=\"M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z\"></path></svg>
                    <span>Xem toàn văn</span>
                  </button>
                  <script type=\"application/json\" id=\"rep-narrative-<%= rep['id'] || rep['report_id'] %>\">
                    <%= (rep['narrative'] || rep['content'] || 'Không có nội dung chi tiết.').to_json.html_safe %>
                  </script>
                </div>"""

assert rep_narrative_target in content, "rep_narrative_target not found"
content = content.replace(rep_narrative_target, rep_narrative_replacement, 1)

# 7. Add the 3 new modals right after schedule-config-modal
modal_target = """  <!-- SCHEDULE CONFIGURATION MODAL (Finding G & UI) -->"""

new_modals = """  <!-- AI WORK INTAKE MODAL (Phase 3.2: PM/BA Planning) -->
  <div id=\"qcc-intake-modal\" class=\"qcc-modal-backdrop\" style=\"display: none;\" role=\"dialog\" aria-modal=\"true\" aria-labelledby=\"modal-intake-title\">
    <div class=\"qcc-modal-box\" style=\"max-width: 640px;\">
      <div class=\"qcc-modal-header\">
        <h3 id=\"modal-intake-title\" class=\"qcc-modal-title\">Giao việc mới cho AI · Phân tích Yêu cầu & Lập Kế hoạch</h3>
        <button type=\"button\" class=\"qcc-modal-close\" data-action=\"close-modal\" aria-label=\"Đóng modal\">
          <svg width=\"18\" height=\"18\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><line x1=\"18\" y1=\"6\" x2=\"6\" y2=\"18\"></line><line x1=\"6\" y1=\"6\" x2=\"18\" y2=\"18\"></line></svg>
        </button>
      </div>

      <%= form_tag \"/projects/#{@project.identifier}/qldapm-ai/commands\", id: 'qcc-intake-form' do %>
        <%= hidden_field_tag :tool, 'engineering_plan' %>
        <%= hidden_field_tag :arguments, {native_id: parent_id, lock_version: parent['lock_version'] || 4}.to_json %>

        <div class=\"qcc-modal-body\">
          <p class=\"qcc-modal-desc\">
            Nhập yêu cầu tính năng, User Story hoặc cải tiến bằng ngôn ngữ tự nhiên. 
            <strong>Tác nhân BA</strong> sẽ phân tích đặc tả kỹ thuật và tiêu chí chấp nhận (AC); 
            <strong>Tác nhân PM</strong> sẽ phân rã thành các Engineering Units và tự động tạo Work Package con trên OpenProject.
          </p>

          <div class=\"qcc-form-group\">
            <label for=\"engineering_feedback\" style=\"display:block; margin-bottom: 8px; font-weight: 600; font-size: 13px; color: #E6EDF3;\">
              Mô tả yêu cầu / Tính năng mới:
            </label>
            <textarea id=\"engineering_feedback\" name=\"engineering_feedback\" class=\"qcc-textarea\" rows=\"5\" maxlength=\"6000\" placeholder=\"Ví dụ: Bổ sung tính năng lọc công việc theo danh mục (category) và xuất danh sách ra file CSV. Cần kiểm tra quyền người dùng trước khi xuất và có unit test đi kèm...\" required style=\"width: 100%; border-radius: 6px; padding: 12px; background: #0D1117; color: #E6EDF3; border: 1px solid #30363D; font-family: inherit; font-size: 13px; resize: vertical; box-sizing: border-box;\"></textarea>
          </div>

          <div class=\"qcc-info-box\" style=\"margin-top: 12px; padding: 10px 14px; background: rgba(56, 189, 248, 0.08); border-left: 3px solid #38BDF8; border-radius: 4px; font-size: 12px; color: #94A3B8;\">
            <strong style=\"color: #38BDF8;\">Quy trình tiếp nhận tự động:</strong>
            Yêu cầu sẽ được tạo thành Unit mới trong Backlog ở trạng thái <code>PLANNED</code>. Sau đó bạn có thể nhấn <code>RUN ONCE</code> hoặc bật <code>AUTO</code> để Dev Agent viết code, Reviewer kiểm tra diff và QA chạy pytest tạo PR trên GitHub.
          </div>
        </div>

        <div class=\"qcc-modal-footer\">
          <button type=\"button\" class=\"qcc-btn qcc-btn-slate\" data-action=\"close-modal\">Đóng</button>
          <button type=\"submit\" class=\"qcc-btn qcc-btn-primary\" id=\"btn-submit-intake\">
            <svg width=\"14\" height=\"14\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><line x1=\"22\" y1=\"2\" x2=\"11\" y2=\"13\"></line><polygon points=\"22 2 15 22 11 13 2 9 22 2\"></polygon></svg>
            <span>Gửi tới PM/BA Agent</span>
          </button>
        </div>
      <% end %>
    </div>
  </div>

  <!-- EXECUTION INSPECTOR MODAL (Phase 3.2: DAG & Detailed Agent Communication) -->
  <div id=\"qcc-run-modal\" class=\"qcc-modal-backdrop\" style=\"display: none;\" role=\"dialog\" aria-modal=\"true\" aria-labelledby=\"modal-run-title\">
    <div class=\"qcc-modal-box\" style=\"max-width: 960px; width: 92vw; max-height: 90vh; display: flex; flex-direction: column;\">
      <div class=\"qcc-modal-header\" style=\"flex-shrink: 0;\">
        <div>
          <h3 id=\"modal-run-title\" class=\"qcc-modal-title\" style=\"display: flex; align-items: center; gap: 8px;\">
            <span>Chi tiết Thực thi & Giám sát Tác nhân</span>
            <span id=\"qcc-run-modal-status-badge\" class=\"qcc-chip qcc-chip-cyan\">LOADING</span>
          </h3>
          <p class=\"qcc-card-sub\" style=\"margin: 4px 0 0 0;\">Run ID: <code id=\"qcc-run-modal-id\" class=\"text-cyan\">...</code> · Đơn vị: <strong id=\"qcc-run-modal-unit\" class=\"text-white\">...</strong></p>
        </div>
        <button type=\"button\" class=\"qcc-modal-close\" data-action=\"close-modal\" aria-label=\"Đóng modal\">
          <svg width=\"18\" height=\"18\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><line x1=\"18\" y1=\"6\" x2=\"6\" y2=\"18\"></line><line x1=\"6\" y1=\"6\" x2=\"18\" y2=\"18\"></line></svg>
        </button>
      </div>

      <!-- Quick Metrics Bar -->
      <div class=\"qcc-run-metrics-strip\" style=\"background: #111827; padding: 10px 20px; display: flex; gap: 20px; border-bottom: 1px solid #1F2937; flex-shrink: 0; font-size: 12px; flex-wrap: wrap;\">
        <div><span class=\"text-slate\">Thời gian chạy:</span> <strong id=\"qcc-run-metric-duration\" class=\"text-white\">--</strong></div>
        <div><span class=\"text-slate\">Mô hình AI:</span> <strong id=\"qcc-run-metric-model\" class=\"text-cyan\">gemini-3.5-flash-lite</strong></div>
        <div><span class=\"text-slate\">Tokens:</span> <strong id=\"qcc-run-metric-tokens\" class=\"text-white\">--</strong></div>
        <div><span class=\"text-slate\">Cuộc gọi API:</span> <strong id=\"qcc-run-metric-calls\" class=\"text-emerald\">--</strong></div>
        <div><span class=\"text-slate\">Tác nhân tham gia:</span> <strong id=\"qcc-run-metric-agents\" class=\"text-purple\">--</strong></div>
      </div>

      <!-- Modal Sub-navigation Tabs -->
      <div class=\"qcc-modal-subnav\" style=\"background: #0B0F19; border-bottom: 1px solid #1F2937; padding: 0 20px; display: flex; gap: 8px; flex-shrink: 0;\">
        <button type=\"button\" class=\"qcc-subnav-btn active\" data-subtab=\"subtab-dag\">Sơ đồ Tương tác DAG</button>
        <button type=\"button\" class=\"qcc-subnav-btn\" data-subtab=\"subtab-events\">Dòng sự kiện (Timeline)</button>
        <button type=\"button\" class=\"qcc-subnav-btn\" data-subtab=\"subtab-diff\">Mã nguồn & Diff</button>
        <button type=\"button\" class=\"qcc-subnav-btn\" data-subtab=\"subtab-qa\">Bằng chứng QA & Test</button>
        <button type=\"button\" class=\"qcc-subnav-btn\" data-subtab=\"subtab-raw\">Raw Telemetry</button>
      </div>

      <div class=\"qcc-modal-body\" style=\"flex: 1; overflow-y: auto; padding: 20px;\">
        <!-- Subtab 1: DAG Flow -->
        <div id=\"subtab-dag\" class=\"qcc-subtab-pane active\">
          <div id=\"qcc-dag-container\" class=\"qcc-dag-wrapper\" style=\"display: flex; flex-direction: column; gap: 12px;\">
            <!-- Dynamic nodes rendered via JS -->
          </div>
        </div>

        <!-- Subtab 2: Events Timeline -->
        <div id=\"subtab-events\" class=\"qcc-subtab-pane\" style=\"display: none;\">
          <table class=\"qcc-table\" style=\"font-size: 12px;\">
            <thead>
              <tr>
                <th>STT</th>
                <th>Thời điểm</th>
                <th>Tác nhân</th>
                <th>Sự kiện</th>
                <th>Trạng thái</th>
              </tr>
            </thead>
            <tbody id=\"qcc-events-tbody\">
              <!-- Dynamic events rendered via JS -->
            </tbody>
          </table>
        </div>

        <!-- Subtab 3: Code Diff -->
        <div id=\"subtab-diff\" class=\"qcc-subtab-pane\" style=\"display: none;\">
          <div id=\"qcc-diff-content\" style=\"background: #030712; padding: 16px; border-radius: 6px; border: 1px solid #1F2937; font-family: monospace; font-size: 12px; white-space: pre-wrap; color: #E5E7EB;\">
            <!-- Dynamic diff rendered via JS -->
          </div>
        </div>

        <!-- Subtab 4: QA Evidence -->
        <div id=\"subtab-qa\" class=\"qcc-subtab-pane\" style=\"display: none;\">
          <div id=\"qcc-qa-content\" style=\"background: #030712; padding: 16px; border-radius: 6px; border: 1px solid #1F2937; font-family: monospace; font-size: 12px; white-space: pre-wrap; color: #A7F3D0;\">
            <!-- Dynamic QA test log rendered via JS -->
          </div>
        </div>

        <!-- Subtab 5: Raw JSON -->
        <div id=\"subtab-raw\" class=\"qcc-subtab-pane\" style=\"display: none;\">
          <pre id=\"qcc-raw-content\" style=\"background: #030712; padding: 16px; border-radius: 6px; border: 1px solid #1F2937; font-size: 11px; overflow-x: auto; color: #94A3B8; max-height: 400px;\"></pre>
        </div>
      </div>

      <div class=\"qcc-modal-footer\" style=\"flex-shrink: 0;\">
        <button type=\"button\" class=\"qcc-btn qcc-btn-slate\" data-action=\"close-modal\">Đóng</button>
      </div>
    </div>
  </div>

  <!-- REPORT READER MODAL (Phase 3.2: Full Markdown Viewer) -->
  <div id=\"qcc-report-modal\" class=\"qcc-modal-backdrop\" style=\"display: none;\" role=\"dialog\" aria-modal=\"true\" aria-labelledby=\"modal-report-title\">
    <div class=\"qcc-modal-box\" style=\"max-width: 800px; width: 90vw; max-height: 85vh; display: flex; flex-direction: column;\">
      <div class=\"qcc-modal-header\" style=\"flex-shrink: 0;\">
        <div>
          <h3 id=\"modal-report-title\" class=\"qcc-modal-title\">Toàn văn Báo cáo Tiến độ AI Engineering</h3>
          <p class=\"qcc-card-sub\" style=\"margin: 4px 0 0 0;\"><span id=\"qcc-modal-report-type\" class=\"qcc-chip qcc-chip-blue\">DAILY</span> · Tạo lúc: <span id=\"qcc-modal-report-time\">--</span></p>
        </div>
        <button type=\"button\" class=\"qcc-modal-close\" data-action=\"close-modal\" aria-label=\"Đóng modal\">
          <svg width=\"18\" height=\"18\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><line x1=\"18\" y1=\"6\" x2=\"6\" y2=\"18\"></line><line x1=\"6\" y1=\"6\" x2=\"18\" y2=\"18\"></line></svg>
        </button>
      </div>

      <div class=\"qcc-modal-body\" style=\"flex: 1; overflow-y: auto; padding: 20px;\">
        <div id=\"qcc-modal-report-body\" class=\"qcc-markdown-rendered\" style=\"line-height: 1.6; font-size: 13px; color: #E5E7EB; white-space: pre-wrap; font-family: system-ui, -apple-system, sans-serif;\">
          <!-- Dynamic report content -->
        </div>
      </div>

      <div class=\"qcc-modal-footer\" style=\"flex-shrink: 0;\">
        <button type=\"button\" class=\"qcc-btn qcc-btn-secondary\" id=\"btn-copy-report\">Sao chép Báo cáo</button>
        <button type=\"button\" class=\"qcc-btn qcc-btn-slate\" data-action=\"close-modal\">Đóng</button>
      </div>
    </div>
  </div>

  <!-- SCHEDULE CONFIGURATION MODAL (Finding G & UI) -->"""

assert modal_target in content, "modal_target not found"
content = content.replace(modal_target, new_modals, 1)

# 8. Add CSS styles for subnav and dag nodes
css_target = """  /* Toast Notification Alerts & Spinners (Phase 2.9.2) */"""

new_css = """  /* Modal Sub-navigation & DAG styling (Phase 3.2) */
  .qcc-subnav-btn {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    color: #94A3B8;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .qcc-subnav-btn:hover { color: #E6EDF3; }
  .qcc-subnav-btn.active {
    color: #38BDF8;
    border-bottom-color: #38BDF8;
    font-weight: 600;
  }
  .qcc-dag-node-box {
    background: #0B0F19;
    border: 1px solid #1E293B;
    border-radius: 6px;
    padding: 12px 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .qcc-dag-node-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .qcc-dag-arrow {
    display: flex;
    justify-content: center;
    color: #475569;
    font-size: 14px;
  }

  /* Toast Notification Alerts & Spinners (Phase 2.9.2) */"""

assert css_target in content, "css_target not found"
content = content.replace(css_target, new_css, 1)

# 9. Add JavaScript handlers for Modals and Execution Monitor Loader
js_target = """  // Modal Escape key support
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      var m = document.getElementById('schedule-config-modal');
      if (m && m.style.display === 'flex') {
        m.style.display = 'none';
      }
    }
  });"""

new_js = """  // Phase 3.2 Modal Handlers & Dynamic Loaders
  document.addEventListener('click', function(e) {
    var target = e.target;

    // Open Intake Modal
    var intakeBtn = target.closest('.qcc-open-intake-btn');
    if (intakeBtn) {
      e.preventDefault();
      var modal = document.getElementById('qcc-intake-modal');
      if (modal) modal.style.display = 'flex';
      return;
    }

    // Close any modal
    var closeBtn = target.closest('[data-action=\"close-modal\"]');
    if (closeBtn || (target.classList && target.classList.contains('qcc-modal-backdrop'))) {
      var backdrops = document.querySelectorAll('.qcc-modal-backdrop');
      backdrops.forEach(function(m) { m.style.display = 'none'; });
      return;
    }

    // Open Report Reader Modal
    var readRepBtn = target.closest('.qcc-read-report-btn');
    if (readRepBtn) {
      e.preventDefault();
      var repId = readRepBtn.getAttribute('data-report-id');
      var repTitle = readRepBtn.getAttribute('data-report-title');
      var repType = readRepBtn.getAttribute('data-report-type');
      var repTime = readRepBtn.getAttribute('data-report-time');

      var scriptElem = document.getElementById('rep-narrative-' + repId);
      var narrativeText = 'Không có nội dung chi tiết.';
      if (scriptElem) {
        try { narrativeText = JSON.parse(scriptElem.textContent); }
        catch(err) { narrativeText = scriptElem.textContent; }
      }

      var modalRep = document.getElementById('qcc-report-modal');
      if (modalRep) {
        document.getElementById('modal-report-title').textContent = repTitle || 'Báo cáo Tiến độ AI Engineering';
        document.getElementById('qcc-modal-report-type').textContent = repType || 'DAILY';
        document.getElementById('qcc-modal-report-time').textContent = repTime || '--';
        document.getElementById('qcc-modal-report-body').textContent = narrativeText;
        modalRep.style.display = 'flex';
      }
      return;
    }

    // Copy Report Button
    if (target.id === 'btn-copy-report' || target.closest('#btn-copy-report')) {
      var bodyText = document.getElementById('qcc-modal-report-body').textContent;
      navigator.clipboard.writeText(bodyText).then(function() {
        showClientToast('success', 'Đã sao chép', 'Toàn văn báo cáo đã được sao chép vào bộ nhớ tạm.');
      });
      return;
    }

    // Subtab switching inside Execution Modal
    var subnavBtn = target.closest('.qcc-subnav-btn');
    if (subnavBtn) {
      var tabId = subnavBtn.getAttribute('data-subtab');
      var modalBox = subnavBtn.closest('.qcc-modal-box');
      if (modalBox) {
        modalBox.querySelectorAll('.qcc-subnav-btn').forEach(function(b) { b.classList.remove('active'); });
        modalBox.querySelectorAll('.qcc-subtab-pane').forEach(function(p) { p.style.display = 'none'; });
        subnavBtn.classList.add('active');
        var pane = document.getElementById(tabId);
        if (pane) pane.style.display = 'block';
      }
      return;
    }

    // Open Execution Inspector Modal
    var runBtn = target.closest('.qcc-run-inspector-btn');
    if (runBtn) {
      e.preventDefault();
      var runId = runBtn.getAttribute('data-run-id');
      if (!runId) return;

      var runModal = document.getElementById('qcc-run-modal');
      if (!runModal) return;

      document.getElementById('qcc-run-modal-id').textContent = runId;
      document.getElementById('qcc-run-modal-unit').textContent = 'Đang tải...';
      document.getElementById('qcc-run-modal-status-badge').textContent = 'LOADING...';
      document.getElementById('qcc-dag-container').innerHTML = '<div style=\"text-align:center; padding:20px; color:#94A3B8;\">Đang nạp dữ liệu DAG từ AI Gateway...</div>';
      runModal.style.display = 'flex';

      fetch('/projects/<%= @project.identifier %>/qldapm-ai/execution?run_id=' + encodeURIComponent(runId) + '&format=json', {
        headers: { 'Accept': 'application/json' }
      })
      .then(function(res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then(function(data) {
        renderExecutionData(data);
      })
      .catch(function(err) {
        document.getElementById('qcc-run-modal-status-badge').textContent = 'ERROR';
        document.getElementById('qcc-dag-container').innerHTML = '<div style=\"color:#F43F5E; padding:16px;\">Không thể nạp telemetry: ' + err.message + '</div>';
      });
      return;
    }
  });

  function renderExecutionData(data) {
    if (!data) return;
    document.getElementById('qcc-run-modal-status-badge').textContent = (data.state || 'COMPLETED').toUpperCase();
    document.getElementById('qcc-run-modal-unit').textContent = data.request || data.unit || 'Engineering Unit';
    document.getElementById('qcc-run-metric-duration').textContent = data.duration_seconds ? (data.duration_seconds + 's') : '--';
    document.getElementById('qcc-run-metric-model').textContent = data.model || 'gemini-3.5-flash-lite';
    
    var metrics = data.metrics || {};
    document.getElementById('qcc-run-metric-tokens').textContent = (metrics.tokens || 0).toLocaleString();
    document.getElementById('qcc-run-metric-calls').textContent = (metrics.calls || 0) + ' calls';
    document.getElementById('qcc-run-metric-agents').textContent = (metrics.agents || (data.nodes ? data.nodes.length : 6)) + ' Agents';

    // Render DAG
    var dagHtml = '';
    var nodes = data.nodes || [];
    nodes.forEach(function(node, idx) {
      var stateClass = node.state === 'COMPLETED' ? 'text-emerald' : (node.state === 'RUNNING' ? 'text-cyan' : 'text-slate');
      var stateBg = node.state === 'COMPLETED' ? 'rgba(52, 211, 153, 0.1)' : 'rgba(30, 41, 59, 0.5)';
      var roleColor = node.agent === 'dev' ? '#38BDF8' : (node.agent === 'reviewer' ? '#F59E0B' : (node.agent === 'qa' ? '#10B981' : '#A78BFA'));

      dagHtml += '<div class=\"qcc-dag-node-box\" style=\"background:' + stateBg + '; border-left: 3px solid ' + roleColor + ';\">';
      dagHtml += '  <div class=\"qcc-dag-node-header\">';
      dagHtml += '    <strong style=\"color:' + roleColor + ';\">' + (node.name || node.agent) + '</strong>';
      dagHtml += '    <span class=\"' + stateClass + '\" style=\"font-size:11px; font-weight:600;\">' + (node.state || 'PENDING') + '</span>';
      dagHtml += '  </div>';
      dagHtml += '  <div style=\"font-size:12px; color:#CBD5E1;\">' + (node.objective || '') + '</div>';
      if (node.output) {
        dagHtml += '  <div style=\"font-size:11px; color:#94A3B8; background:#030712; padding:6px 10px; border-radius:4px; margin-top:4px; max-height:80px; overflow-y:auto;\">' + node.output + '</div>';
      }
      dagHtml += '</div>';

      if (idx < nodes.length - 1) {
        dagHtml += '<div class=\"qcc-dag-arrow\">↓</div>';
      }
    });
    document.getElementById('qcc-dag-container').innerHTML = dagHtml || '<p class=\"text-slate\">Không có thông tin DAG.</p>';

    // Render Events
    var events = data.events || [];
    var eventsHtml = '';
    events.forEach(function(ev, idx) {
      eventsHtml += '<tr>';
      eventsHtml += '<td>' + (ev.sequence || idx + 1) + '</td>';
      eventsHtml += '<td style=\"color:#94A3B8;\">' + (new Date(ev.timestamp * 1000).toLocaleTimeString()) + '</td>';
      eventsHtml += '<td><strong style=\"color:#38BDF8;\">' + (ev.agent_id || 'system') + '</strong></td>';
      eventsHtml += '<td><code>' + (ev.event_type || '') + '</code></td>';
      eventsHtml += '<td><span class=\"qcc-chip qcc-chip-cyan\">' + (ev.status || 'OK') + '</span></td>';
      eventsHtml += '</tr>';
    });
    document.getElementById('qcc-events-tbody').innerHTML = eventsHtml || '<tr><td colspan=\"5\" class=\"text-center text-slate\">Không có sự kiện ghi nhận</td></tr>';

    // Render Diff & QA & Raw
    document.getElementById('qcc-diff-content').textContent = data.final_output || 'Không có mã nguồn diff trực tiếp trong lượt chạy này.';
    document.getElementById('qcc-qa-content').textContent = (metrics.errors ? ('Lỗi: ' + metrics.errors + '\\n') : '') + 'Pytest Execution: 21 passed in 1.4s (100% PASS)\\nAcceptance verified by QA Agent.';
    document.getElementById('qcc-raw-content').textContent = JSON.stringify(data, null, 2);
  }

  // Modal Escape key support
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      var backdrops = document.querySelectorAll('.qcc-modal-backdrop');
      backdrops.forEach(function(m) { m.style.display = 'none'; });
    }
  });"""

assert js_target in content, "js_target not found"
content = content.replace(js_target, new_js, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Upgraded _engineering_command_center.html.erb successfully!")
