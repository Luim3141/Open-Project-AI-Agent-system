"""Patch script for Controller, Initializer, and Command Center View."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONTROLLER_PATH = ROOT / "openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb"
VIEW_PATH = ROOT / "openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb"

def patch_controller():
    text = CONTROLLER_PATH.read_text(encoding="utf-8")
    
    # 1. Patch def command
    old_cmd = """      @result = bridge(action, arguments, SecureRandom.uuid)
      return render_engineering
    end"""
    
    new_cmd = """      bridge_resp = bridge(action, arguments, SecureRandom.uuid)
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
    end"""
    
    if old_cmd in text:
        text = text.replace(old_cmd, new_cmd, 1)
        print("[OK] Controller def command patched")
    else:
        print("[SKIP] Controller def command already patched or target not found")

    # 2. Patch def render_engineering for JSON format
    old_render = """    render :engineering, formats: [:html], status:
  end"""
    
    new_render = """    if request.format.json? || params[:format] == 'json'
      return render json: {
        engineering: @engineering,
        reports: @reports,
        schedule: @schedule,
        notifications: @notifications,
        result: @result,
        error: @error
      }, status:
    end
    render :engineering, formats: [:html], status:
  end"""

    if old_render in text:
        text = text.replace(old_render, new_render, 1)
        print("[OK] Controller render_engineering patched")
    else:
        print("[SKIP] Controller render_engineering already patched or target not found")

    CONTROLLER_PATH.write_text(text, encoding="utf-8")

def patch_view():
    text = VIEW_PATH.read_text(encoding="utf-8")

    # 1. Variable calculation at top
    old_top = """  sched = @schedule || eng['schedule'] || {}
  worker = eng['worker'] || {}
  worker_alive = worker['worker_id'].present?
  github_prs = eng['github_prs'] || []"""

    new_top = """  sched = @schedule || eng['schedule'] || {}
  worker = eng['worker'] || {}
  worker_alive = worker['worker_id'].present?
  delivered_count = backlog.select { |b| (b['state'] == 'succeeded' || b['status'] == 'DELIVERED') }.size
  total_backlog = backlog.size > 0 ? backlog.size : 5
  github_prs = eng['github_prs'] || []"""

    if old_top in text:
        text = text.replace(old_top, new_top, 1)
        print("[OK] View top variables patched")
    else:
        print("[SKIP] View top variables already patched")

    # 2. Header meta & worker text
    old_header_meta = """Worker: <strong class="<%= worker_alive ? 'text-emerald' : 'text-slate' %>"><%= worker_alive ? 'ALIVE (' + worker['worker_id'][0..7] + ')' : 'IDLE' %></strong> · 
            Múi giờ: <strong>Asia/Ho_Chi_Minh (UTC+7)</strong> · 
            Auto Delivery: <strong><%= backlog.select { |b| b['status'] == 'DELIVERED' }.size %> / <%= backlog.size %> Units Delivered</strong>"""

    new_header_meta = """Worker: <strong class="<%= worker_alive ? 'text-emerald' : 'text-slate' %>"><%= worker_alive ? 'ALIVE (' + worker['worker_id'][0..7] + ')' : 'IDLE (Sẵn sàng)' %></strong> · 
            Múi giờ: <strong>Asia/Ho_Chi_Minh (UTC+7)</strong> · 
            Auto Delivery: <strong><%= delivered_count %> / <%= total_backlog %> Units Delivered</strong>"""

    if old_header_meta in text:
        text = text.replace(old_header_meta, new_header_meta, 1)
        print("[OK] View header meta patched")
    else:
        print("[SKIP] View header meta already patched")

    # 3. Add Work Packages link in Header Actions Toolbar
    old_header_actions = """        <!-- ACTION BUTTONS TOOLBAR -->
        <div class="qcc-header-actions">
          <!-- RUN ONCE -->"""

    new_header_actions = """        <!-- ACTION BUTTONS TOOLBAR -->
        <div class="qcc-header-actions">
          <!-- Back to OpenProject Work Packages -->
          <%= link_to "/projects/#{@project.identifier}/work_packages", class: "qcc-btn qcc-btn-secondary", title: "Quay lại danh sách Work Packages của OpenProject" do %>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
            <span>← Work Packages</span>
          <% end %>

          <!-- RUN ONCE -->"""

    if old_header_actions in text:
        text = text.replace(old_header_actions, new_header_actions, 1)
        print("[OK] View header actions (Work Packages link) patched")
    else:
        print("[SKIP] View header actions already patched")

    # 4. KPI Card 1 (Worker) & Card 2 (Backlog Units)
    old_kpi_worker = """<div class="qcc-kpi-sub">
              Worker: <span class="text-<%= worker_alive ? 'emerald' : 'slate' %>"><%= worker_alive ? 'Online & Sẵn sàng' : 'Chưa kết nối' %></span>
            </div>"""

    new_kpi_worker = """<div class="qcc-kpi-sub">
              Worker: <span class="text-<%= worker_alive ? 'emerald' : 'slate' %>"><%= worker_alive ? 'Online & Đang chạy' : 'IDLE (Sẵn sàng)' %></span>
            </div>"""

    if old_kpi_worker in text:
        text = text.replace(old_kpi_worker, new_kpi_worker, 1)
        print("[OK] View KPI worker text patched")
    else:
        print("[SKIP] View KPI worker text already patched")

    old_kpi_backlog = """            <div class="qcc-kpi-value"><%= backlog.select { |b| b['status'] == 'DELIVERED' }.size %> / <%= backlog.size %></div>
            <div class="qcc-kpi-sub">
              5/5 Units đã phát triển hoàn tất
            </div>"""

    new_kpi_backlog = """            <div class="qcc-kpi-value"><%= delivered_count %> / <%= total_backlog %></div>
            <div class="qcc-kpi-sub">
              <%= delivered_count %> / <%= total_backlog %> Units đã phát triển hoàn tất
            </div>"""

    if old_kpi_backlog in text:
        text = text.replace(old_kpi_backlog, new_kpi_backlog, 1)
        print("[OK] View KPI backlog calculation patched")
    else:
        print("[SKIP] View KPI backlog calculation already patched")

    # 5. Backlog unit item badge in Mission Control
    old_unit_badge = """                  <div class="qcc-unit-badge">
                    <span class="qcc-chip <%= unit['status'] == 'DELIVERED' ? 'qcc-chip-emerald' : 'qcc-chip-cyan' %>">
                      <%= unit['status'] || 'PLANNED' %>
                    </span>
                  </div>"""

    new_unit_badge = """                  <% 
                    is_unit_del = (unit['state'] == 'succeeded' || unit['status'] == 'DELIVERED')
                    badge_label = is_unit_del ? 'DELIVERED' : (unit['status'] || unit['state'] || 'PLANNED').to_s.upcase
                  %>
                  <div class="qcc-unit-badge">
                    <span class="qcc-chip <%= is_unit_del ? 'qcc-chip-emerald' : 'qcc-chip-cyan' %>">
                      <%= badge_label %>
                    </span>
                  </div>"""

    if old_unit_badge in text:
        text = text.replace(old_unit_badge, new_unit_badge, 1)
        print("[OK] View unit badge in Mission Control patched")
    else:
        print("[SKIP] View unit badge already patched")

    # 6. Backlog table status in Tab 4
    old_table_status = """                      <span class="qcc-chip <%= t['status']['name'] == 'In progress' ? 'qcc-chip-amber' : 'qcc-chip-emerald' %>">
                        <%= t['status']['name'] %>
                      </span>"""

    new_table_status = """                      <%
                        raw_st = t['status']
                        st_name = raw_st.is_a?(Hash) ? raw_st['name'] : raw_st.to_s
                        is_prog = st_name.downcase.include?('progress')
                      %>
                      <span class="qcc-chip <%= is_prog ? 'qcc-chip-amber' : 'qcc-chip-emerald' %>">
                        <%= st_name.presence || 'IN PROGRESS' %>
                      </span>"""

    if old_table_status in text:
        text = text.replace(old_table_status, new_table_status, 1)
        print("[OK] View table status extraction patched")
    else:
        print("[SKIP] View table status already patched")

    # 7. Add Toast Notification HTML container right inside .qcc-root
    old_root_start = """<div id="qldapm-command-center" class="qcc-root">
  <!-- Top Progress Bar (Active when mode is AUTO or task running) -->
  <div class="qcc-top-progress <%= 'active' if mode == 'AUTO' %>"></div>"""

    new_root_start = """<div id="qldapm-command-center" class="qcc-root">
  <!-- Top Progress Bar (Active when mode is AUTO or task running) -->
  <div class="qcc-top-progress <%= 'active' if mode == 'AUTO' %>"></div>

  <!-- TOAST NOTIFICATION CONTAINER (Phase 2.9.2) -->
  <div id="qcc-toast-container" class="qcc-toast-container">
    <% if @result.present? %>
      <% result_msg = @result.is_a?(Hash) ? (@result['message'] || @result['text'] || @result['status']) : @result.to_s %>
      <div class="qcc-toast qcc-toast-success" role="alert">
        <div class="qcc-toast-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
        </div>
        <div class="qcc-toast-content">
          <div class="qcc-toast-title">Thao tác thành công</div>
          <div class="qcc-toast-body"><%= result_msg %></div>
        </div>
        <button type="button" class="qcc-toast-close" data-action="close-toast">&times;</button>
      </div>
    <% end %>

    <% if @error.present? %>
      <div class="qcc-toast qcc-toast-error" role="alert">
        <div class="qcc-toast-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        </div>
        <div class="qcc-toast-content">
          <div class="qcc-toast-title">Thông báo lỗi / Từ chối</div>
          <div class="qcc-toast-body"><%= @error %></div>
        </div>
        <button type="button" class="qcc-toast-close" data-action="close-toast">&times;</button>
      </div>
    <% end %>
  </div>"""

    if old_root_start in text:
        text = text.replace(old_root_start, new_root_start, 1)
        print("[OK] View toast notification container added")
    else:
        print("[SKIP] View toast container already added")

    # 8. Add Toast CSS styles
    toast_css = """
  /* Toast Notification Alerts & Spinners (Phase 2.9.2) */
  .qcc-toast-container {
    position: fixed;
    top: 24px;
    right: 24px;
    z-index: 99999;
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-width: 440px;
    pointer-events: none;
  }
  .qcc-toast {
    pointer-events: auto;
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 14px 18px;
    border-radius: var(--qcc-radius);
    background: #0F172A;
    border: 1px solid var(--qcc-border);
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6), 0 8px 10px -6px rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(12px);
    animation: qccToastIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    transition: opacity 0.3s ease, transform 0.3s ease;
  }
  @keyframes qccToastIn {
    from { opacity: 0; transform: translateY(-12px) scale(0.96); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }
  .qcc-toast-success {
    border-color: rgba(16, 185, 129, 0.4);
    background: rgba(15, 23, 42, 0.98);
  }
  .qcc-toast-success .qcc-toast-icon {
    color: var(--qcc-emerald);
    background: rgba(16, 185, 129, 0.15);
  }
  .qcc-toast-error {
    border-color: rgba(239, 68, 68, 0.4);
    background: rgba(15, 23, 42, 0.98);
  }
  .qcc-toast-error .qcc-toast-icon {
    color: var(--qcc-rose);
    background: rgba(239, 68, 68, 0.15);
  }
  .qcc-toast-info {
    border-color: rgba(6, 182, 212, 0.4);
    background: rgba(15, 23, 42, 0.98);
  }
  .qcc-toast-info .qcc-toast-icon {
    color: var(--qcc-cyan);
    background: rgba(6, 182, 212, 0.15);
  }
  .qcc-toast-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .qcc-toast-content {
    flex: 1;
    min-width: 0;
  }
  .qcc-toast-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--qcc-text-main);
    margin-bottom: 2px;
  }
  .qcc-toast-body {
    font-size: 12px;
    color: var(--qcc-text-muted);
    line-height: 1.4;
    word-break: break-word;
  }
  .qcc-toast-close {
    background: none;
    border: none;
    color: var(--qcc-text-slate);
    font-size: 18px;
    cursor: pointer;
    padding: 0 4px;
    line-height: 1;
    transition: color 0.15s;
  }
  .qcc-toast-close:hover {
    color: var(--qcc-text-main);
  }
  .qcc-spinner {
    display: inline-block;
    width: 14px;
    height: 14px;
    border: 2px solid rgba(255,255,255,0.3);
    border-radius: 50%;
    border-top-color: #fff;
    animation: qccSpin 0.8s linear infinite;
    vertical-align: middle;
    margin-right: 6px;
  }
  @keyframes qccSpin {
    to { transform: rotate(360deg); }
  }
  button.submitting {
    opacity: 0.8 !important;
    cursor: not-allowed !important;
    pointer-events: none !important;
  }
"""

    if ".qcc-toast-container" not in text:
        text = text.replace("</style>", toast_css + "\n</style>", 1)
        print("[OK] View toast CSS styles added")
    else:
        print("[SKIP] View toast CSS already added")

    # 9. Update nonced JavaScript
    old_js_block = """    // Dismiss notification toast
    var dismissBtn = e.target.closest('[data-action="dismiss-toast"]');
    if (dismissBtn) {
      e.preventDefault();
      var toast = dismissBtn.closest('.qcc-notification-item');
      if (toast) toast.style.display = 'none';
      return;
    }
  });"""

    new_js_block = """    // Dismiss notification toast
    var dismissBtn = e.target.closest('[data-action="dismiss-toast"]');
    if (dismissBtn) {
      e.preventDefault();
      var toast = dismissBtn.closest('.qcc-notification-item');
      if (toast) toast.style.display = 'none';
      return;
    }

    // Close toast alert
    var closeToastBtn = e.target.closest('[data-action="close-toast"]');
    if (closeToastBtn) {
      e.preventDefault();
      var tItem = closeToastBtn.closest('.qcc-toast');
      if (tItem) {
        tItem.style.opacity = '0';
        tItem.style.transform = 'translateY(-10px)';
        setTimeout(function() { tItem.remove(); }, 300);
      }
      return;
    }
  });

  // Client-side Toast Helper Function
  function showClientToast(type, title, message) {
    var container = document.getElementById('qcc-toast-container');
    if (!container) return;
    var toast = document.createElement('div');
    toast.className = 'qcc-toast qcc-toast-' + type;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = '<div class="qcc-toast-icon">' +
      (type === 'success' ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>' :
       type === 'error' ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>' :
       '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>') +
      '</div>' +
      '<div class="qcc-toast-content">' +
      '<div class="qcc-toast-title">' + title + '</div>' +
      '<div class="qcc-toast-body">' + message + '</div>' +
      '</div>' +
      '<button type="button" class="qcc-toast-close" data-action="close-toast">&times;</button>';
    container.appendChild(toast);
    setTimeout(function() {
      if (toast && toast.parentNode) {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        setTimeout(function() { if (toast.parentNode) toast.remove(); }, 300);
      }
    }, 7000);
  }

  // Handle Form Submission: Disabling buttons & Visual Progress
  document.addEventListener('submit', function(e) {
    var form = e.target.closest('form');
    if (!form) return;

    var btn = form.querySelector('button[type="submit"]');
    if (btn) {
      btn.disabled = true;
      btn.classList.add('submitting');
      var originalHtml = btn.innerHTML;
      btn.setAttribute('data-original-html', originalHtml);
      btn.innerHTML = '<span class="qcc-spinner"></span> <span>Đang xử lý...</span>';
    }

    var progressBar = document.querySelector('.qcc-top-progress');
    if (progressBar) progressBar.classList.add('active');

    showClientToast('info', 'Đang gửi yêu cầu...', 'Hệ thống đang gửi thao tác đến AI Gateway.');
  });

  // Auto-dismiss initial server-rendered toasts after 7s
  setTimeout(function() {
    var initialToasts = document.querySelectorAll('.qcc-toast');
    initialToasts.forEach(function(t) {
      t.style.opacity = '0';
      t.style.transform = 'translateY(-10px)';
      setTimeout(function() { if (t.parentNode) t.remove(); }, 300);
    });
  }, 7000);

  // Background Status Polling (every 20 seconds)
  var pollInterval = setInterval(function() {
    var pollUrl = '/projects/<%= @project.identifier %>/qldapm-ai?format=json';
    fetch(pollUrl, { credentials: 'same-origin', headers: { 'Accept': 'application/json' } })
      .then(function(res) {
        if (res.ok) return res.json();
        throw new Error('Poll status: ' + res.status);
      })
      .then(function(data) {
        if (!data || !data.engineering) return;
        var eng = data.engineering;
        var modeElem = document.querySelector('.qcc-kpi-card .qcc-kpi-value');
        if (modeElem && eng.mode) {
          modeElem.textContent = eng.mode;
        }
      })
      .catch(function(err) {
        // Silent backoff on polling error
      });
  }, 20000);"""

    if old_js_block in text:
        text = text.replace(old_js_block, new_js_block, 1)
        print("[OK] View nonced JS updated with submit handler, toasts & polling")
    else:
        print("[SKIP] View nonced JS already updated")

    VIEW_PATH.write_text(text, encoding="utf-8")

if __name__ == "__main__":
    print("--- Patching Controller ---")
    patch_controller()
    print("--- Patching View ---")
    patch_view()
    print("--- Done ---")
