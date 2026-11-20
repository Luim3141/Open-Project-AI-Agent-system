from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
view_path = ROOT / 'openproject' / 'ai' / 'core' / 'overlay' / 'app' / 'views' / 'qldapm_ai' / '_engineering_command_center.html.erb'
content = view_path.read_text(encoding='utf-8')

# 1. Add format_vn_time and iso_tooltip lambdas after quota_model = ...
target_quota = "quota_model = quota_info['model'] || 'gemini-3.5-flash-lite'"
helpers_code = """quota_model = quota_info['model'] || 'gemini-3.5-flash-lite'

  format_vn_time = ->(val) {
    return 'Chưa có dữ liệu' if val.blank?
    t = nil
    if val.is_a?(Numeric)
      t = Time.at(val)
    elsif val.is_a?(String)
      t = (val =~ /\\A\\d+(\\.\\d+)?\\z/) ? Time.at(val.to_f) : (Time.parse(val) rescue nil)
    elsif val.respond_to?(:in_time_zone)
      t = val
    end
    return 'Chưa có dữ liệu' unless t
    t.in_time_zone('Asia/Ho_Chi_Minh').strftime('%d/%m/%Y %H:%M:%S')
  }

  iso_tooltip = ->(val) {
    return '' if val.blank?
    t = nil
    if val.is_a?(Numeric)
      t = Time.at(val)
    elsif val.is_a?(String)
      t = (val =~ /\\A\\d+(\\.\\d+)?\\z/) ? Time.at(val.to_f) : (Time.parse(val) rescue nil)
    elsif val.respond_to?(:utc)
      t = val
    end
    t ? t.utc.iso8601 : ''
  }"""

if target_quota in content:
    content = content.replace(target_quota, helpers_code, 1)

# 2. Update fallback github_prs
old_fallback = """      { 'number' => 2, 'wp_id' => 381, 'title' => 'Edit/delete/status/search and usable web interface', 'state' => 'closed', 'branch' => 'codex/openclaw-crud-search-web-v1', 'base_ref' => 'codex/openclaw-create-list-persistence-v1', 'is_merged' => true, 'merge_target' => 'FEATURE_BRANCH (PR #1)', 'head_sha' => '29ff0ec1' },
      { 'number' => 1, 'wp_id' => 380, 'title' => 'Create and list tasks with SQLite persistence', 'state' => 'open', 'branch' => 'codex/openclaw-create-list-persistence-v1', 'base_ref' => 'main', 'is_merged' => false, 'merge_target' => 'UNMERGED', 'head_sha' => '1aa7c395' }"""

new_fallback = """      { 'number' => 2, 'wp_id' => 381, 'title' => 'Edit/delete/status/search and usable web interface', 'state' => 'closed', 'branch' => 'codex/openclaw-crud-search-web-v1', 'base_ref' => 'codex/openclaw-create-list-persistence-v1', 'is_merged' => true, 'merge_target' => 'FEATURE_BRANCH (PR #1)', 'head_sha' => '29ff0ec1', 'created_at' => '2026-10-29T14:00:00Z', 'merged_at' => '2026-10-30T05:29:13Z' },
      { 'number' => 1, 'wp_id' => 380, 'title' => 'Create and list tasks with SQLite persistence', 'state' => 'closed', 'branch' => 'codex/openclaw-create-list-persistence-v1', 'base_ref' => 'main', 'is_merged' => true, 'merge_target' => 'MAIN', 'head_sha' => '1aa7c395', 'created_at' => '2026-10-29T10:00:00Z', 'merged_at' => '2026-10-31T05:45:27Z' }"""

if old_fallback in content:
    content = content.replace(old_fallback, new_fallback, 1)

# 3. Update Execution Center Table Header & Rows
old_exec_header = """                <tr>
                  <th>Run ID</th>
                  <th>Hàng đợi</th>
                  <th>Giai đoạn</th>
                  <th>Task / Unit</th>
                  <th>Trạng thái Review</th>
                  <th>Kết quả</th>
                  <th>Hành động</th>
                </tr>"""

new_exec_header = """                <tr>
                  <th>Run ID</th>
                  <th>Thời điểm chạy</th>
                  <th>Hàng đợi</th>
                  <th>Giai đoạn</th>
                  <th>Task / Unit</th>
                  <th>Trạng thái Review</th>
                  <th>Kết quả</th>
                  <th>Hành động</th>
                </tr>"""

if old_exec_header in content:
    content = content.replace(old_exec_header, new_exec_header, 1)

old_exec_empty = """<tr><td colspan="7" class="text-center text-slate">Chưa có lịch sử thực thi nào</td></tr>"""
new_exec_empty = """<tr><td colspan="8" class="text-center text-slate">Chưa có lịch sử thực thi nào</td></tr>"""
if old_exec_empty in content:
    content = content.replace(old_exec_empty, new_exec_empty, 1)

old_exec_cell = """                      <td>
                        <button type="button" class="qcc-run-inspector-btn" data-run-id="<%= run['id'] %>" style="background:none; border:none; padding:0; cursor:pointer; display:inline-flex; align-items:center; gap:4px;" title="Xem chi tiết thực thi & sơ đồ tương tác Agent">
                          <code class="text-cyan"><%= run['id'] ? run['id'][0..7] : 'N/A' %>...</code>
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                        </button>
                      </td>
                      <td>
                        <span class="qcc-chip <%= qstate == 'done' ? 'qcc-chip-emerald' : (qstate == 'paused' ? 'qcc-chip-amber' : 'qcc-chip-cyan') %>">"""

new_exec_cell = """                      <td>
                        <button type="button" class="qcc-run-inspector-btn" data-run-id="<%= run['id'] %>" style="background:none; border:none; padding:0; cursor:pointer; display:inline-flex; align-items:center; gap:4px;" title="Xem chi tiết thực thi & sơ đồ tương tác Agent">
                          <code class="text-cyan"><%= run['id'] ? run['id'][0..7] : 'N/A' %>...</code>
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                        </button>
                      </td>
                      <td title="<%= iso_tooltip.call(run['created_at']) %>">
                        <span class="text-slate" style="font-size:12px;"><%= format_vn_time.call(run['created_at']) %></span>
                      </td>
                      <td>
                        <span class="qcc-chip <%= qstate == 'done' ? 'qcc-chip-emerald' : (qstate == 'paused' ? 'qcc-chip-amber' : 'qcc-chip-cyan') %>">"""

if old_exec_cell in content:
    content = content.replace(old_exec_cell, new_exec_cell, 1)

# 4. Update GitHub PR Table
old_pr_table = """            <table class="qcc-table">
              <thead>
                <tr>
                  <th>Pull Request</th>
                  <th>Task OpenProject</th>
                  <th>Base Branch (Target)</th>
                  <th>Head Branch & Commit</th>
                  <th>Reviews & CI GitHub</th>
                  <th>Đích Merge</th>
                  <th>Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                <% github_prs.each do |pr| %>
                  <tr>
                    <td>
                      <a href="https://github.com/Luim3141/mini-task-manager/pull/<%= pr['number'] %>" target="_blank" class="qcc-pr-link">
                        <strong>PR #<%= pr['number'] %></strong>: <%= pr['title'] %>
                      </a>
                    </td>
                    <td>
                      <span class="qcc-chip qcc-chip-blue">WP #<%= pr['wp_id'] %></span>
                    </td>
                    <td>
                      <code><%= pr['base_ref'] %></code>
                    </td>
                    <td>
                      <code><%= pr['head_sha'] ? pr['head_sha'][0..7] : 'N/A' %></code>
                    </td>
                    <td>
                      <div class="qcc-badge-stack">
                        <span class="qcc-chip qcc-chip-subtle" title="Chưa có reviewer người duyệt trên GitHub">NO_REVIEWS_ON_GITHUB</span>
                        <span class="qcc-chip qcc-chip-subtle" title="Chưa cấu hình GitHub Actions CI">NO_CI_CHECKS_CONFIGURED</span>
                      </div>
                    </td>
                    <td>
                      <% if pr['is_merged'] %>
                        <span class="qcc-chip qcc-chip-purple">FEATURE_BRANCH</span>
                      <% elsif pr['base_ref'] == 'main' %>
                        <span class="qcc-chip qcc-chip-amber">MAIN</span>
                      <% else %>
                        <span class="qcc-chip qcc-chip-cyan">FEATURE_STACK</span>
                      <% end %>
                    </td>
                    <td>
                      <span class="qcc-chip <%= pr['state'] == 'open' ? 'qcc-chip-emerald' : 'qcc-chip-purple' %>">
                        <%= pr['state'].upcase %>
                      </span>
                    </td>
                  </tr>
                <% end %>
              </tbody>
            </table>"""

new_pr_table = """            <table class="qcc-table">
              <thead>
                <tr>
                  <th>Pull Request</th>
                  <th>Task OpenProject</th>
                  <th>Tạo lúc</th>
                  <th>Merge lúc</th>
                  <th>Base Branch (Target)</th>
                  <th>Head Branch & Commit</th>
                  <th>Reviews & CI GitHub</th>
                  <th>Đích Merge</th>
                  <th>Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                <% github_prs.each do |pr| %>
                  <tr>
                    <td>
                      <a href="https://github.com/Luim3141/mini-task-manager/pull/<%= pr['number'] %>" target="_blank" class="qcc-pr-link">
                        <strong>PR #<%= pr['number'] %></strong>: <%= pr['title'] %>
                      </a>
                    </td>
                    <td>
                      <span class="qcc-chip qcc-chip-blue">WP #<%= pr['wp_id'] %></span>
                    </td>
                    <td title="<%= iso_tooltip.call(pr['created_at']) %>">
                      <span class="text-slate" style="font-size:11px;"><%= format_vn_time.call(pr['created_at']) %></span>
                    </td>
                    <td title="<%= iso_tooltip.call(pr['merged_at']) %>">
                      <span class="text-slate" style="font-size:11px;"><%= pr['is_merged'] ? format_vn_time.call(pr['merged_at']) : '—' %></span>
                    </td>
                    <td>
                      <code><%= pr['base_ref'] %></code>
                    </td>
                    <td>
                      <code><%= pr['head_sha'] ? pr['head_sha'][0..7] : 'N/A' %></code>
                    </td>
                    <td>
                      <div class="qcc-badge-stack">
                        <span class="qcc-chip qcc-chip-subtle" title="Chưa có reviewer người duyệt trên GitHub">NO_REVIEWS_ON_GITHUB</span>
                        <span class="qcc-chip qcc-chip-subtle" title="Chưa cấu hình GitHub Actions CI">NO_CI_CHECKS_CONFIGURED</span>
                      </div>
                    </td>
                    <td>
                      <% if pr['is_merged'] %>
                        <% if pr['base_ref'] == 'main' || pr['merge_target'] == 'MAIN' %>
                          <span class="qcc-chip qcc-chip-emerald">MERGED TO MAIN</span>
                        <% else %>
                          <span class="qcc-chip qcc-chip-purple">MERGED TO BRANCH</span>
                        <% end %>
                      <% elsif pr['base_ref'] == 'main' %>
                        <span class="qcc-chip qcc-chip-amber">MAIN</span>
                      <% else %>
                        <span class="qcc-chip qcc-chip-cyan">FEATURE_STACK</span>
                      <% end %>
                    </td>
                    <td>
                      <span class="qcc-chip <%= pr['state'] == 'open' ? 'qcc-chip-emerald' : 'qcc-chip-purple' %>">
                        <%= pr['state'].upcase %>
                      </span>
                    </td>
                  </tr>
                <% end %>
              </tbody>
            </table>"""

assert old_pr_table in content, "old_pr_table not found"
content = content.replace(old_pr_table, new_pr_table, 1)

# 5. Update Reports time
old_rep_time = """<span class="qcc-report-time"><%= rep['created_iso'] ? rep['created_iso'][0..18] : (rep['created_at'] ? rep['created_at'][0..18] : 'Vừa xong') %></span>"""
new_rep_time = """<span class="qcc-report-time" title="<%= iso_tooltip.call(rep['created_at'] || rep['created_iso']) %>"><%= format_vn_time.call(rep['created_at'] || rep['created_iso']) %></span>"""
if old_rep_time in content:
    content = content.replace(old_rep_time, new_rep_time, 1)

# 6. Update Tokens label in Quick Metrics Strip
old_metrics_strip = """        <div><span class="text-slate">Tokens:</span> <strong id="qcc-run-metric-tokens" class="text-white">--</strong></div>"""
new_metrics_strip = """        <div><span class="text-slate">Tokens (Lượt chạy này):</span> <strong id="qcc-run-metric-tokens" class="text-white" title="Tokens tiêu thụ trong riêng Run ID này. Quota tích lũy toàn hệ thống xem tại KPI Header">--</strong></div>"""
if old_metrics_strip in content:
    content = content.replace(old_metrics_strip, new_metrics_strip, 1)

# 7. Add formatVNDateTime in JavaScript and update Timeline events
old_events_render = """      eventsHtml += '<td style="color:#94A3B8;">' + (ev.timestamp ? (new Date(ev.timestamp * 1000).toLocaleTimeString()) : '--') + '</td>';"""
new_events_render = """      var isoTooltip = ev.timestamp ? new Date(ev.timestamp < 10000000000 ? ev.timestamp * 1000 : ev.timestamp).toISOString() : '';
      eventsHtml += '<td style="color:#94A3B8;" title="' + isoTooltip + '">' + formatVNDateTime(ev.timestamp) + '</td>';"""

if old_events_render in content:
    content = content.replace(old_events_render, new_events_render, 1)

old_render_fn = "  function renderExecutionData(data) {"
new_render_fn = """  function formatVNDateTime(ts) {
    if (!ts) return 'Chưa có dữ liệu';
    var d;
    if (typeof ts === 'number') {
      d = new Date(ts < 10000000000 ? ts * 1000 : ts);
    } else if (typeof ts === 'string') {
      var num = Number(ts);
      if (!isNaN(num) && num > 0) {
        d = new Date(num < 10000000000 ? num * 1000 : num);
      } else {
        d = new Date(ts);
      }
    } else {
      d = new Date(ts);
    }
    if (isNaN(d.getTime())) return 'Chưa có dữ liệu';
    var parts = new Intl.DateTimeFormat('en-GB', {
      timeZone: 'Asia/Ho_Chi_Minh',
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      hour12: false
    }).formatToParts(d);
    var p = {};
    parts.forEach(function(part) { p[part.type] = part.value; });
    return p.day + '/' + p.month + '/' + p.year + ' ' + p.hour + ':' + p.minute + ':' + p.second;
  }

  function renderExecutionData(data) {"""

if old_render_fn in content:
    content = content.replace(old_render_fn, new_render_fn, 1)

view_path.write_text(content, encoding='utf-8')
print("Successfully patched _engineering_command_center.html.erb")
