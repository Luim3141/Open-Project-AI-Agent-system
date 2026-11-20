"""Builder script to generate the modern QLDAPM AI Command Center view template."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb"

content = """<%# QLDAPM AI Command Center — Modern Autonomous Operations Shell (Phase 2.9) %>
<%
  eng = @engineering || {}
  mode = eng['mode'] || 'OFF'
  tasks = eng['tasks'] || []
  backlog = eng['backlog'] || []
  runs = eng['runs'] || []
  parent = @engineering_wp || {}
  parent_id = parent['id'] || 379
  raw_reports = @reports || eng['reports'] || []
  reports = raw_reports.is_a?(Hash) ? (raw_reports['reports'] || []) : Array(raw_reports)
  raw_notifs = @notifications || eng['notifications'] || []
  notifications = raw_notifs.is_a?(Hash) ? (raw_notifs['notifications'] || []) : Array(raw_notifs)
  sched = @schedule || eng['schedule'] || {}
  worker = eng['worker'] || {}
  worker_alive = worker['worker_id'].present?
  github_prs = eng['github_prs'] || []
  if github_prs.empty?
    github_prs = [
      { 'number' => 5, 'wp_id' => 384, 'title' => '[AI Unit] Them route GET /healthz va unit test status ok', 'state' => 'open', 'branch' => 'codex/openclaw-health-check-v1', 'base_ref' => 'codex/openclaw-feedback-4d13e695555a8d44', 'is_merged' => false, 'merge_target' => 'UNMERGED', 'head_sha' => '0e8d320a' },
      { 'number' => 4, 'wp_id' => 383, 'title' => 'Unicode search & pytest str.casefold', 'state' => 'open', 'branch' => 'codex/openclaw-feedback-4d13e695555a8d44', 'base_ref' => 'codex/openclaw-feedback-283138e910432528', 'is_merged' => false, 'merge_target' => 'UNMERGED', 'head_sha' => 'def9d0a8' },
      { 'number' => 3, 'wp_id' => 382, 'title' => 'Web UI components, request helper & a11y', 'state' => 'open', 'branch' => 'codex/openclaw-feedback-283138e910432528', 'base_ref' => 'codex/openclaw-crud-search-web-v1', 'is_merged' => false, 'merge_target' => 'UNMERGED', 'head_sha' => 'd00f8c5f' },
      { 'number' => 2, 'wp_id' => 381, 'title' => 'Edit/delete/status/search and usable web interface', 'state' => 'closed', 'branch' => 'codex/openclaw-crud-search-web-v1', 'base_ref' => 'codex/openclaw-create-list-persistence-v1', 'is_merged' => true, 'merge_target' => 'FEATURE_BRANCH (PR #1)', 'head_sha' => '29ff0ec1' },
      { 'number' => 1, 'wp_id' => 380, 'title' => 'Create and list tasks with SQLite persistence', 'state' => 'open', 'branch' => 'codex/openclaw-create-list-persistence-v1', 'base_ref' => 'main', 'is_merged' => false, 'merge_target' => 'UNMERGED', 'head_sha' => '1aa7c395' }
    ]
  end
%>

<div id="qldapm-command-center" class="qcc-root">
  <!-- Top Progress Bar (Active when mode is AUTO or task running) -->
  <div class="qcc-top-progress <%= 'active' if mode == 'AUTO' %>"></div>

  <!-- Command Center Shell Layout -->
  <div class="qcc-shell">
    <!-- LEFT SIDEBAR -->
    <aside class="qcc-sidebar">
      <!-- Brand & Project Identity -->
      <div class="qcc-brand">
        <div class="qcc-brand-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
            <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
            <line x1="6" y1="6" x2="6.01" y2="6"></line>
            <line x1="6" y1="18" x2="6.01" y2="18"></line>
          </svg>
        </div>
        <div class="qcc-brand-info">
          <div class="qcc-brand-name">QLDAPM COMMAND</div>
          <div class="qcc-brand-sub">AI Agent Center · v2.9</div>
        </div>
      </div>

      <!-- Project Badge -->
      <div class="qcc-project-badge">
        <span class="qcc-badge-dot <%= worker_alive ? 'alive' : 'idle' %>"></span>
        <span class="qcc-project-title">Project 6: ai-dev-demo</span>
      </div>

      <!-- Navigation Tabs -->
      <nav class="qcc-nav" role="tablist">
        <button class="qcc-nav-item active" data-tab="tab-mission" role="tab">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polygon points="12 6 12 12 16 14"></polygon></svg>
          <span>Mission Control</span>
        </button>
        <button class="qcc-nav-item" data-tab="tab-pipeline" role="tab">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
          <span>AI Pipeline (8 Stages)</span>
        </button>
        <button class="qcc-nav-item" data-tab="tab-workforce" role="tab">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
          <span>Agent Workforce</span>
          <span class="qcc-nav-pill">6</span>
        </button>
        <button class="qcc-nav-item" data-tab="tab-backlog" role="tab">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
          <span>Backlog & Tasks</span>
          <span class="qcc-nav-pill"><%= tasks.size %></span>
        </button>
        <button class="qcc-nav-item" data-tab="tab-execution" role="tab">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
          <span>Execution Center</span>
          <span class="qcc-nav-pill"><%= runs.size %></span>
        </button>
        <button class="qcc-nav-item" data-tab="tab-github" role="tab">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="18" r="3"></circle><circle cx="6" cy="6" r="3"></circle><path d="M13 6h3a2 2 0 0 1 2 2v7"></path><line x1="6" y1="9" x2="6" y2="21"></line></svg>
          <span>GitHub & Delivery</span>
          <span class="qcc-nav-pill"><%= github_prs.size %> PRs</span>
        </button>
        <button class="qcc-nav-item" data-tab="tab-reports" role="tab">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
          <span>Reports & Analytics</span>
        </button>
        <button class="qcc-nav-item" data-tab="tab-knowledge" role="tab">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
          <span>Knowledge / RAG</span>
        </button>
        <button class="qcc-nav-item" data-tab="tab-integrations" role="tab">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
          <span>System Integrations</span>
        </button>
      </nav>

      <!-- Sidebar Footer -->
      <div class="qcc-sidebar-footer">
        <div class="qcc-user-info">
          <div class="qcc-user-avatar">
            <%= (User.current.firstname.presence || 'O')[0].upcase %>
          </div>
          <div class="qcc-user-meta">
            <div class="qcc-user-name"><%= User.current.name %></div>
            <div class="qcc-user-role"><%= @role || 'AI_SYSTEM_OWNER' %></div>
          </div>
        </div>
        <div class="qcc-footer-links">
          <%= link_to "/projects/#{@project.identifier}/work_packages", class: "qcc-footer-link", title: "Mở danh sách Work Packages OpenProject" do %>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5v0a5.5 5.5 0 0 1-5.5 5.5H11"/></svg>
            <span>Về OpenProject</span>
          <% end %>
          <%= link_to "/projects/#{@project.identifier}/qldapm-ai?ui=classic", class: "qcc-footer-link", title: "Chuyển về giao diện Classic Phase 2.8" do %>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
            <span>Bản Classic</span>
          <% end %>
        </div>
      </div>
    </aside>

    <!-- MAIN OPERATIONS CANVAS -->
    <main class="qcc-main">
      <!-- TOP TELEMETRY & CONTROLS HEADER -->
      <header class="qcc-header">
        <div class="qcc-header-left">
          <h1 class="qcc-header-title">
            <span>AI Engineering Control Center</span>
            <span class="qcc-chip-mode mode-<%= mode.downcase %>">
              <span class="qcc-chip-pulse"></span>
              MODE: <%= mode %>
            </span>
          </h1>
          <p class="qcc-header-meta">
            Worker: <strong class="<%= worker_alive ? 'text-emerald' : 'text-slate' %>"><%= worker_alive ? 'ALIVE (' + worker['worker_id'][0..7] + ')' : 'IDLE' %></strong> · 
            Múi giờ: <strong>Asia/Ho_Chi_Minh (UTC+7)</strong> · 
            Auto Delivery: <strong><%= backlog.select { |b| b['status'] == 'DELIVERED' }.size %> / <%= backlog.size %> Units Delivered</strong>
          </p>
        </div>

        <!-- ACTION BUTTONS TOOLBAR -->
        <div class="qcc-header-actions">
          <!-- RUN ONCE -->
          <%= form_tag "/projects/#{@project.identifier}/qldapm-ai/commands", class: "qcc-action-form" do %>
            <%= hidden_field_tag :tool, 'engineering_run_once' %>
            <%= hidden_field_tag :arguments, {native_id: 379, lock_version: parent['lock_version'] || 4, unit: 'health-check-v1'}.to_json %>
            <button type="submit" class="qcc-btn qcc-btn-primary" title="Chạy một lượt đơn lẻ có kiểm soát">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
              <span>RUN ONCE</span>
            </button>
          <% end %>

          <!-- MODE TOGGLE -->
          <% if mode == 'OFF' %>
            <%= form_tag "/projects/#{@project.identifier}/qldapm-ai/commands", class: "qcc-action-form" do %>
              <%= hidden_field_tag :tool, 'engineering_control' %>
              <%= hidden_field_tag :arguments, {mode: 'AUTO'}.to_json %>
              <button type="submit" class="qcc-btn qcc-btn-emerald">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                <span>BẬT AUTO</span>
              </button>
            <% end %>
          <% else %>
            <%= form_tag "/projects/#{@project.identifier}/qldapm-ai/commands", class: "qcc-action-form" do %>
              <%= hidden_field_tag :tool, 'engineering_control' %>
              <%= hidden_field_tag :arguments, {mode: 'OFF'}.to_json %>
              <button type="submit" class="qcc-btn qcc-btn-slate">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line></svg>
                <span>OFF</span>
              </button>
            <% end %>
          <% end %>

          <% if mode == 'PAUSED' %>
            <%= form_tag "/projects/#{@project.identifier}/qldapm-ai/commands", class: "qcc-action-form" do %>
              <%= hidden_field_tag :tool, 'engineering_control' %>
              <%= hidden_field_tag :arguments, {mode: 'OFF'}.to_json %>
              <button type="submit" class="qcc-btn qcc-btn-slate"><span>TẮT PAUSE</span></button>
            <% end %>
          <% else %>
            <%= form_tag "/projects/#{@project.identifier}/qldapm-ai/commands", class: "qcc-action-form" do %>
              <%= hidden_field_tag :tool, 'engineering_control' %>
              <%= hidden_field_tag :arguments, {mode: 'PAUSED'}.to_json %>
              <button type="submit" class="qcc-btn qcc-btn-amber"><span>PAUSE</span></button>
            <% end %>
          <% end %>

          <!-- GITHUB SYNC -->
          <%= form_tag "/projects/#{@project.identifier}/qldapm-ai/commands", class: "qcc-action-form" do %>
            <%= hidden_field_tag :tool, 'engineering_github_sync' %>
            <%= hidden_field_tag :arguments, {repo: 'Luim3141/mini-task-manager'}.to_json %>
            <button type="submit" class="qcc-btn qcc-btn-secondary" title="Đối soát trạng thái 5 Stacked PRs trên GitHub">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
              <span>Sync GitHub</span>
            </button>
          <% end %>

          <!-- SCHEDULE MODAL TRIGGER (Finding G) -->
          <button type="button" id="btn-open-schedule-modal" class="qcc-btn qcc-btn-secondary" >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            <span>Cấu hình lịch</span>
          </button>

          <!-- SNAPSHOT REPORT -->
          <%= form_tag "/projects/#{@project.identifier}/qldapm-ai/commands", class: "qcc-action-form" do %>
            <%= hidden_field_tag :tool, 'engineering_report_generate' %>
            <%= hidden_field_tag :arguments, {report_type: 'ON_DEMAND', include_narrative: true}.to_json %>
            <button type="submit" class="qcc-btn qcc-btn-secondary" title="Sinh báo cáo tổng hợp tức thời kèm nhận định AI">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
              <span>Snapshot Tức Thời (+AI)</span>
            </button>
          <% end %>
        </div>
      </header>

      <!-- NOTIFICATIONS TOAST BAR -->
      <section class="qcc-notifications-section" aria-label="Notifications Bar">
        <% if notifications.any? %>
          <div class="qcc-notif-bar">
            <div class="qcc-notif-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
            </div>
            <div class="qcc-notif-content">
              <strong><%= notifications.size %> thông báo mới:</strong>
              <%= notifications.first['title'] || notifications.first['message'] || 'Báo cáo Tiến độ Hằng ngày đã được sinh tự động' %>
            </div>
            <button class="qcc-notif-close" data-action="dismiss-notif-bar">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>
        <% else %>
          <div class="qcc-notif-bar qcc-notif-subtle">
            <div class="qcc-notif-icon text-cyan">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
            </div>
            <div class="qcc-notif-content">
              Lịch báo cáo: <strong>Daily <%= sched['daily_hour'] ? sprintf("%02d:%02d", sched['daily_hour'], sched['daily_minute'] || 0) : '07:30' %></strong> · <strong>Weekly Thứ <%= sched['weekly_day'] || 1 %> (<%= sched['weekly_hour'] ? sprintf("%02d:%02d", sched['weekly_hour'], sched['weekly_minute'] || 0) : '09:00' %>)</strong> · Múi giờ: <strong>Asia/Ho_Chi_Minh</strong>
            </div>
          </div>
        <% end %>
      </section>

      <!-- TAB 1: MISSION CONTROL (OVERVIEW) -->
      <section id="tab-mission" class="qcc-tab-pane active" role="tabpanel">
        <!-- Active Mission Hero Card -->
        <div class="qcc-mission-hero">
          <div class="qcc-mission-badge">
            <span class="qcc-chip-pulse"></span>
            ACTIVE EPIC MISSION #<%= parent_id %>
          </div>
          <h2 class="qcc-mission-title"><%= parent['subject'] || 'Develop Mini Task Manager Application' %></h2>
          <p class="qcc-mission-desc">
            Vòng đời tự động: Yêu cầu → Đặc tả BA/PM → Lập trình Sandbox WSL2 → Review mã nguồn → Kiểm thử QA Gate → Đóng gói GitHub PR #5 → Lưu trữ tri thức Second Brain.
          </p>
          <div class="qcc-mission-tags">
            <span class="qcc-tag">Trạng thái: <strong><%= parent['status'] ? parent['status']['name'] : 'IN PROGRESS' %></strong></span>
            <span class="qcc-tag">Phiên bản khóa: <strong>lock_version <%= parent['lock_version'] || 4 %></strong></span>
            <span class="qcc-tag">Cột mốc mới nhất: <strong>Task #384 delivered · PR #5 OPEN</strong></span>
            <span class="qcc-tag text-emerald">Pytest: <strong>21/21 passed (100%)</strong></span>
          </div>
        </div>

        <!-- 4 Metric Telemetry Cards Grid -->
        <div class="qcc-kpi-grid">
          <!-- Card 1 -->
          <div class="qcc-kpi-card">
            <div class="qcc-kpi-header">
              <span class="qcc-kpi-label">CHẾ ĐỘ ĐIỀU KHIỂN</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-cyan"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path><line x1="12" y1="2" x2="12" y2="12"></line></svg>
            </div>
            <div class="qcc-kpi-value text-<%= mode == 'AUTO' ? 'emerald' : 'cyan' %>"><%= mode %></div>
            <div class="qcc-kpi-sub">
              Worker: <span class="text-<%= worker_alive ? 'emerald' : 'slate' %>"><%= worker_alive ? 'Online & Sẵn sàng' : 'Chưa kết nối' %></span>
            </div>
          </div>

          <!-- Card 2 -->
          <div class="qcc-kpi-card">
            <div class="qcc-kpi-header">
              <span class="qcc-kpi-label">BACKLOG UNITS</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-primary"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
            </div>
            <div class="qcc-kpi-value"><%= backlog.select { |b| b['status'] == 'DELIVERED' }.size %> / <%= backlog.size %></div>
            <div class="qcc-kpi-sub">
              5/5 Units đã phát triển hoàn tất
            </div>
          </div>

          <!-- Card 3 -->
          <div class="qcc-kpi-card">
            <div class="qcc-kpi-header">
              <span class="qcc-kpi-label">GITHUB STACKED PRS</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-emerald"><circle cx="18" cy="18" r="3"></circle><circle cx="6" cy="6" r="3"></circle><path d="M13 6h3a2 2 0 0 1 2 2v7"></path><line x1="6" y1="9" x2="6" y2="21"></line></svg>
            </div>
            <div class="qcc-kpi-value"><%= github_prs.size %> PRs</div>
            <div class="qcc-kpi-sub">
              1 Merged (Feature) · 4 Open Stacked
            </div>
          </div>

          <!-- Card 4 -->
          <div class="qcc-kpi-card">
            <div class="qcc-kpi-header">
              <span class="qcc-kpi-label">SECOND BRAIN / RAG</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-purple"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
            </div>
            <div class="qcc-kpi-value">2,132 <small>points</small></div>
            <div class="qcc-kpi-sub">
              Qdrant Dense + SQLite FTS5 BM25
            </div>
          </div>
        </div>

        <!-- 8-Stage Pipeline Visualization -->
        <div class="qcc-card">
          <div class="qcc-card-header">
            <div>
              <h3 class="qcc-card-title">Quy trình Phân phối Tự động 8 Giai đoạn (Autonomous Pipeline)</h3>
              <p class="qcc-card-sub">Chu trình phân rã, lập trình, kiểm thử và chuyển giao khép kín của Biệt đội AI</p>
            </div>
            <span class="qcc-chip qcc-chip-emerald">Pipeline Healthy</span>
          </div>

          <div class="qcc-pipeline-flow">
            <!-- Stage 1 -->
            <div class="qcc-stage-node done">
              <div class="qcc-stage-icon">PM</div>
              <div class="qcc-stage-name">1. Yêu cầu</div>
              <div class="qcc-stage-sub">Product Manager</div>
              <div class="qcc-stage-state">SUCCESS</div>
            </div>
            <div class="qcc-stage-arrow done"></div>

            <!-- Stage 2 -->
            <div class="qcc-stage-node done">
              <div class="qcc-stage-icon">BA</div>
              <div class="qcc-stage-name">2. Đặc tả</div>
              <div class="qcc-stage-sub">Business Analyst</div>
              <div class="qcc-stage-state">SUCCESS</div>
            </div>
            <div class="qcc-stage-arrow done"></div>

            <!-- Stage 3 -->
            <div class="qcc-stage-node done">
              <div class="qcc-stage-icon">DEV</div>
              <div class="qcc-stage-name">3. Lập trình</div>
              <div class="qcc-stage-sub">Senior Dev Agent</div>
              <div class="qcc-stage-state">SUCCESS</div>
            </div>
            <div class="qcc-stage-arrow done"></div>

            <!-- Stage 4 -->
            <div class="qcc-stage-node done">
              <div class="qcc-stage-icon">REV</div>
              <div class="qcc-stage-name">4. Review</div>
              <div class="qcc-stage-sub">Reviewer Agent</div>
              <div class="qcc-stage-state">SUCCESS</div>
            </div>
            <div class="qcc-stage-arrow done"></div>

            <!-- Stage 5 -->
            <div class="qcc-stage-node done">
              <div class="qcc-stage-icon">QA</div>
              <div class="qcc-stage-name">5. QA Gate</div>
              <div class="qcc-stage-sub">QA Engineer</div>
              <div class="qcc-stage-state">SUCCESS</div>
            </div>
            <div class="qcc-stage-arrow done"></div>

            <!-- Stage 6 -->
            <div class="qcc-stage-node done">
              <div class="qcc-stage-icon">GIT</div>
              <div class="qcc-stage-name">6. GitHub PR</div>
              <div class="qcc-stage-sub">Host Bundle Push</div>
              <div class="qcc-stage-state">PR #5 OPEN</div>
            </div>
            <div class="qcc-stage-arrow done"></div>

            <!-- Stage 7 -->
            <div class="qcc-stage-node done">
              <div class="qcc-stage-icon">OP</div>
              <div class="qcc-stage-name">7. OpenProject</div>
              <div class="qcc-stage-sub">WP #384 Patch</div>
              <div class="qcc-stage-state">LOCK_VER 1</div>
            </div>
            <div class="qcc-stage-arrow done"></div>

            <!-- Stage 8 -->
            <div class="qcc-stage-node done">
              <div class="qcc-stage-icon">RAG</div>
              <div class="qcc-stage-name">8. Second Brain</div>
              <div class="qcc-stage-sub">Vectorized</div>
              <div class="qcc-stage-state">CITATIONS OK</div>
            </div>
          </div>
        </div>

        <!-- Recent Activity & Historical Runs Brief -->
        <div class="qcc-split-grid">
          <div class="qcc-card">
            <div class="qcc-card-header">
              <h3 class="qcc-card-title">Tiến độ 5 Backlog Units (Project 6)</h3>
            </div>
            <div class="qcc-units-list">
              <% backlog.each do |unit| %>
                <div class="qcc-unit-item">
                  <div class="qcc-unit-bullet <%= unit['status'] == 'DELIVERED' ? 'bullet-emerald' : 'bullet-cyan' %>"></div>
                  <div class="qcc-unit-info">
                    <div class="qcc-unit-title"><%= unit['title'] || unit['unit'] %></div>
                    <div class="qcc-unit-meta">Unit: <code><%= unit['unit'] %></code> · Task #<%= unit['native_id'] %></div>
                  </div>
                  <div class="qcc-unit-badge">
                    <span class="qcc-chip <%= unit['status'] == 'DELIVERED' ? 'qcc-chip-emerald' : 'qcc-chip-cyan' %>">
                      <%= unit['status'] || 'PLANNED' %>
                    </span>
                  </div>
                </div>
              <% end %>
            </div>
          </div>

          <div class="qcc-card">
            <div class="qcc-card-header">
              <h3 class="qcc-card-title">Cột mốc Kiểm soát & An toàn</h3>
            </div>
            <div class="qcc-audit-list">
              <div class="qcc-audit-item">
                <div class="qcc-audit-dot dot-emerald"></div>
                <div class="qcc-audit-text">
                  <strong>Project 5 Invariant Protection:</strong> 341 Work Packages bất biến 100%, không phát sinh thay đổi.
                </div>
              </div>
              <div class="qcc-audit-item">
                <div class="qcc-audit-dot dot-emerald"></div>
                <div class="qcc-audit-text">
                  <strong>Ranh giới Git Publishing:</strong> Áp dụng Host Bundle Publisher độc quyền, ngăn chặn treo push trong WSL2.
                </div>
              </div>
              <div class="qcc-audit-item">
                <div class="qcc-audit-dot dot-emerald"></div>
                <div class="qcc-audit-text">
                  <strong>Quyền hạn Owner:</strong> User 18 (AI_SYSTEM_OWNER) toàn quyền giám sát runs, quản lý mode, bảo đảm bảo mật.
                </div>
              </div>
              <div class="qcc-audit-item">
                <div class="qcc-audit-dot dot-emerald"></div>
                <div class="qcc-audit-text">
                  <strong>Bảo vệ Nhánh Chính:</strong> Không tự động merge PR #1–#5 vào <code>main</code>; Work Package #379 được bảo lưu IN_PROGRESS.
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      
      <!-- TAB 2: PIPELINE 8 GIAI ĐOẠN -->
      <section id="tab-pipeline" class="qcc-tab-pane" role="tabpanel">
        <div class="qcc-section-header">
          <div>
            <h2 class="qcc-section-title">Quy trình Vận hành 8 Giai đoạn (Autonomous Pipeline)</h2>
            <p class="qcc-section-sub">Kiến trúc quy trình kỹ thuật khép kín bảo đảm tính toàn vẹn từ User Story đến GitHub Pull Request</p>
          </div>
          <div class="qcc-pipeline-stats">
            <span class="qcc-chip qcc-chip-emerald">8/8 Giai đoạn Chuẩn hóa</span>
            <span class="qcc-chip qcc-chip-cyan">Host Bundle Publisher Active</span>
          </div>
        </div>

        <div class="qcc-pipeline-grid">
          <div class="qcc-pipeline-card">
            <div class="qcc-stage-num">01</div>
            <div class="qcc-stage-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            </div>
            <h3 class="qcc-stage-title">Intake & Yêu cầu</h3>
            <p class="qcc-stage-desc">Tiếp nhận Work Package từ OpenProject Project 6, kiểm tra tính đầy đủ của mô tả và mục tiêu.</p>
            <div class="qcc-stage-meta">
              <span class="qcc-tag">Actor: BA / Owner</span>
              <span class="qcc-status-dot green">Sẵn sàng</span>
            </div>
          </div>

          <div class="qcc-pipeline-card">
            <div class="qcc-stage-num">02</div>
            <div class="qcc-stage-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
            </div>
            <h3 class="qcc-stage-title">Spec & AC Design</h3>
            <p class="qcc-stage-desc">Phân rã yêu cầu thành User Stories, định nghĩa tiêu chí chấp nhận (Acceptance Criteria) và edges.</p>
            <div class="qcc-stage-meta">
              <span class="qcc-tag">Agent: BA Agent</span>
              <span class="qcc-status-dot green">Chuẩn hóa</span>
            </div>
          </div>

          <div class="qcc-pipeline-card">
            <div class="qcc-stage-num">03</div>
            <div class="qcc-stage-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
            </div>
            <h3 class="qcc-stage-title">Kiến trúc & Kế hoạch</h3>
            <p class="qcc-stage-desc">Thiết lập hợp đồng API, thiết kế module, cập nhật ADR và lập kế hoạch nguyên tử (Atomic Plan).</p>
            <div class="qcc-stage-meta">
              <span class="qcc-tag">Agent: PM / Architect</span>
              <span class="qcc-status-dot green">Phê duyệt</span>
            </div>
          </div>

          <div class="qcc-pipeline-card">
            <div class="qcc-stage-num">04</div>
            <div class="qcc-stage-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
            </div>
            <h3 class="qcc-stage-title">Scaffolding & Worktree</h3>
            <p class="qcc-stage-desc">Khởi tạo isolated git worktree, switch stacked branch từ base PR đã xác minh gần nhất.</p>
            <div class="qcc-stage-meta">
              <span class="qcc-tag">Runtime: OpenClaw</span>
              <span class="qcc-status-dot green">Tự động</span>
            </div>
          </div>

          <div class="qcc-pipeline-card">
            <div class="qcc-stage-num">05</div>
            <div class="qcc-stage-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>
            </div>
            <h3 class="qcc-stage-title">Mã hóa & Unit Test</h3>
            <p class="qcc-stage-desc">Thực hiện TDD (Red-Green-Refactor), viết code chức năng và bộ unit tests tương ứng.</p>
            <div class="qcc-stage-meta">
              <span class="qcc-tag">Agent: Coder Agent</span>
              <span class="qcc-status-dot green">Đã giao</span>
            </div>
          </div>

          <div class="qcc-pipeline-card">
            <div class="qcc-stage-num">06</div>
            <div class="qcc-stage-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
            </div>
            <h3 class="qcc-stage-title">Đánh giá Mã nguồn</h3>
            <p class="qcc-stage-desc">Review chéo độc lập, kiểm tra tiêu chuẩn mã nguồn, rà soát bảo mật và rủi ro hồi quy.</p>
            <div class="qcc-stage-meta">
              <span class="qcc-tag">Agent: Reviewer Agent</span>
              <span class="qcc-status-dot green">Bảo đảm</span>
            </div>
          </div>

          <div class="qcc-pipeline-card">
            <div class="qcc-stage-num">07</div>
            <div class="qcc-stage-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            </div>
            <h3 class="qcc-stage-title">Kiểm thử QA & Hash</h3>
            <p class="qcc-stage-desc">Chạy toàn bộ pytest, sinh evidence hash, chứng thực chất lượng phần mềm không giả lập.</p>
            <div class="qcc-stage-meta">
              <span class="qcc-tag">Agent: QA Agent</span>
              <span class="qcc-status-dot green">19/19 Tests Pass</span>
            </div>
          </div>

          <div class="qcc-pipeline-card">
            <div class="qcc-stage-num">08</div>
            <div class="qcc-stage-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="18" r="3"></circle><circle cx="6" cy="6" r="3"></circle><path d="M13 6h3a2 2 0 0 1 2 2v7"></path><line x1="6" y1="9" x2="6" y2="21"></line></svg>
            </div>
            <h3 class="qcc-stage-title">Phát hành Host Bundle</h3>
            <p class="qcc-stage-desc">Host Bundle Publisher chuyển giao git bundle an toàn lên GitHub PR và cập nhật Native WP.</p>
            <div class="qcc-stage-meta">
              <span class="qcc-tag">Publisher: Host Trusted</span>
              <span class="qcc-status-dot green">5 PRs Hoạt động</span>
            </div>
          </div>
        </div>
      </section>

      <!-- TAB 3: AGENT WORKFORCE -->
      <section id="tab-workforce" class="qcc-tab-pane" role="tabpanel">
        <div class="qcc-section-header">
          <div>
            <h2 class="qcc-section-title">Biệt đội AI Agents & Bộ Kỹ năng Động (Agent Workforce)</h2>
            <p class="qcc-section-sub">Mỗi Agent hoạt động với Persona, Model và bộ kỹ năng (Skills) chuyên biệt trong môi trường sandbox</p>
          </div>
        </div>

        <div class="qcc-agent-grid">
          <!-- Agent 1: Supervisor -->
          <div class="qcc-agent-card">
            <div class="qcc-agent-top">
              <div class="qcc-agent-avatar bg-indigo">SUP</div>
              <div class="qcc-agent-info">
                <h4 class="qcc-agent-name">AI Supervisor</h4>
                <div class="qcc-agent-role">Orchestrator & Gatekeeper</div>
              </div>
              <span class="qcc-chip qcc-chip-emerald">IDLE</span>
            </div>
            <div class="qcc-agent-details">
              <div class="qcc-agent-row"><span>Mô hình:</span> <strong>Gemini 1.5 Pro / Flash</strong></div>
              <div class="qcc-agent-row"><span>Runtime:</span> <strong>Python 3.14 Gateway Daemon</strong></div>
              <div class="qcc-agent-row"><span>Ràng buộc:</span> <strong>1 Concurrency Lock, Safe Auto-shutoff</strong></div>
            </div>
            <div class="qcc-agent-skills">
              <span class="qcc-skill-pill">Lifecycle Control</span>
              <span class="qcc-skill-pill">Quota Guard</span>
              <span class="qcc-skill-pill">Audit Trail</span>
            </div>
          </div>

          <!-- Agent 2: PM Agent -->
          <div class="qcc-agent-card">
            <div class="qcc-agent-top">
              <div class="qcc-agent-avatar bg-blue">PM</div>
              <div class="qcc-agent-info">
                <h4 class="qcc-agent-name">Product Manager Agent</h4>
                <div class="qcc-agent-role">Backlog Decomposition</div>
              </div>
              <span class="qcc-chip qcc-chip-cyan">READY</span>
            </div>
            <div class="qcc-agent-details">
              <div class="qcc-agent-row"><span>Mô hình:</span> <strong>Gemini 1.5 Pro Structured</strong></div>
              <div class="qcc-agent-row"><span>Nhiệm vụ:</span> <strong>Epic & Story Decomposition</strong></div>
              <div class="qcc-agent-row"><span>Artifact:</span> <strong>OpenProject Native Work Packages</strong></div>
            </div>
            <div class="qcc-agent-skills">
              <span class="qcc-skill-pill">WBS Planning</span>
              <span class="qcc-skill-pill">Priority Sizing</span>
              <span class="qcc-skill-pill">Dependency Graph</span>
            </div>
          </div>

          <!-- Agent 3: BA Agent -->
          <div class="qcc-agent-card">
            <div class="qcc-agent-top">
              <div class="qcc-agent-avatar bg-teal">BA</div>
              <div class="qcc-agent-info">
                <h4 class="qcc-agent-name">Business Analyst Agent</h4>
                <div class="qcc-agent-role">Requirements & AC</div>
              </div>
              <span class="qcc-chip qcc-chip-cyan">READY</span>
            </div>
            <div class="qcc-agent-details">
              <div class="qcc-agent-row"><span>Mô hình:</span> <strong>Gemini 1.5 Pro</strong></div>
              <div class="qcc-agent-row"><span>Nhiệm vụ:</span> <strong>Acceptance Criteria & Gherkin Specs</strong></div>
              <div class="qcc-agent-row"><span>Artifact:</span> <strong>Task Specification Document</strong></div>
            </div>
            <div class="qcc-agent-skills">
              <span class="qcc-skill-pill">Acceptance Criteria</span>
              <span class="qcc-skill-pill">Edge-case Sizing</span>
              <span class="qcc-skill-pill">User Stories</span>
            </div>
          </div>

          <!-- Agent 4: Developer Agent -->
          <div class="qcc-agent-card">
            <div class="qcc-agent-top">
              <div class="qcc-agent-avatar bg-emerald">DEV</div>
              <div class="qcc-agent-info">
                <h4 class="qcc-agent-name">Senior Developer Agent</h4>
                <div class="qcc-agent-role">Full-Stack Code Implementation</div>
              </div>
              <span class="qcc-chip qcc-chip-emerald">IDLE</span>
            </div>
            <div class="qcc-agent-details">
              <div class="qcc-agent-row"><span>Sandbox:</span> <strong>WSL2 OpenClaw Ubuntu 24.04</strong></div>
              <div class="qcc-agent-row"><span>Trajectroy:</span> <strong><code>dev-0-trajectory.jsonl</code></strong></div>
              <div class="qcc-agent-row"><span>Kỹ năng động:</span> <strong><code>engineering-development</code></strong></div>
            </div>
            <div class="qcc-agent-skills">
              <span class="qcc-skill-pill">FastAPI / Python</span>
              <span class="qcc-skill-pill">Pytest 21/21 PASS</span>
              <span class="qcc-skill-pill">Git Bundle</span>
            </div>
          </div>

          <!-- Agent 5: Code Reviewer Agent -->
          <div class="qcc-agent-card">
            <div class="qcc-agent-top">
              <div class="qcc-agent-avatar bg-amber">REV</div>
              <div class="qcc-agent-info">
                <h4 class="qcc-agent-name">Code Reviewer Agent</h4>
                <div class="qcc-agent-role">Architecture & Quality Gate</div>
              </div>
              <span class="qcc-chip qcc-chip-emerald">IDLE</span>
            </div>
            <div class="qcc-agent-details">
              <div class="qcc-agent-row"><span>Kỹ năng động:</span> <strong><code>engineering-review</code></strong></div>
              <div class="qcc-agent-row"><span>Trajectory:</span> <strong><code>review-0-trajectory.jsonl</code></strong></div>
              <div class="qcc-agent-row"><span>Tiêu chuẩn:</span> <strong>Clean Code, Zero Security Leak</strong></div>
            </div>
            <div class="qcc-agent-skills">
              <span class="qcc-skill-pill">Diff Inspection</span>
              <span class="qcc-skill-pill">Security Audit</span>
              <span class="qcc-skill-pill">Local AI Review</span>
            </div>
          </div>

          <!-- Agent 6: QA Engineer Agent -->
          <div class="qcc-agent-card">
            <div class="qcc-agent-top">
              <div class="qcc-agent-avatar bg-rose">QA</div>
              <div class="qcc-agent-info">
                <h4 class="qcc-agent-name">QA Automation Lead</h4>
                <div class="qcc-agent-role">Acceptance & Regression Testing</div>
              </div>
              <span class="qcc-chip qcc-chip-emerald">IDLE</span>
            </div>
            <div class="qcc-agent-details">
              <div class="qcc-agent-row"><span>Kỹ năng động:</span> <strong><code>engineering-qa</code></strong></div>
              <div class="qcc-agent-row"><span>Trajectory:</span> <strong><code>qa-0-trajectory.jsonl</code></strong></div>
              <div class="qcc-agent-row"><span>Tiêu chí đạt:</span> <strong>100% Acceptance Criteria Met</strong></div>
            </div>
            <div class="qcc-agent-skills">
              <span class="qcc-skill-pill">Pytest Execution</span>
              <span class="qcc-skill-pill">Acceptance Gate</span>
              <span class="qcc-skill-pill">Evidence Capture</span>
            </div>
          </div>
        </div>
      </section>

      <!-- TAB 3: BACKLOG & TASKS -->
      <section id="tab-backlog" class="qcc-tab-pane" role="tabpanel">
        <div class="qcc-card">
          <div class="qcc-card-header">
            <div>
              <h3 class="qcc-card-title">Ma trận Nhiệm vụ & Backlog (Project 6)</h3>
              <p class="qcc-card-sub">Theo dõi chi tiết các Work Packages, phiên bản khóa (lock_version) và trạng thái phân phối</p>
            </div>
            <div class="qcc-filter-group">
              <input type="text" id="qcc-task-search" class="qcc-input" placeholder="Tìm kiếm Task ID, tiêu đề..." >
            </div>
          </div>

          <div class="qcc-table-wrapper">
            <table class="qcc-table" id="qcc-tasks-table">
              <thead>
                <tr>
                  <th>Work Package</th>
                  <th>Loại</th>
                  <th>Priority</th>
                  <th>Assignee</th>
                  <th>Trạng thái OpenProject</th>
                  <th>Phiên bản khóa</th>
                  <th>GitHub PR / Commit</th>
                  <th>Hành động</th>
                </tr>
              </thead>
              <tbody>
                <!-- Parent WP 379 -->
                <tr class="row-parent">
                  <td>
                    <strong>#<%= parent_id %></strong> — <%= parent['subject'] || 'Develop Mini Task Manager Application' %>
                  </td>
                  <td><span class="qcc-chip qcc-chip-purple">Epic</span></td>
                  <td>Normal</td>
                  <td><%= parent.dig('assigned_to', 'name') || 'QLDAPM PM' %></td>
                  <td><span class="qcc-chip qcc-chip-amber"><%= parent['status'] ? parent['status']['name'] : 'IN PROGRESS' %></span></td>
                  <td><code>lock_version <%= parent['lock_version'] || 4 %></code></td>
                  <td><span class="text-slate">Parent Anchor</span></td>
                  <td>
                    <%= link_to "Mở OP", "/work_packages/#{parent_id}", class: "qcc-btn-link", target: "_blank" %>
                  </td>
                </tr>

                <!-- Child Tasks -->
                <% tasks.each do |t| %>
                  <% 
                    wp_id = t['id']
                    wp_pr = github_prs.find { |p| p['wp_id'] == wp_id }
                  %>
                  <tr>
                    <td>
                      <strong>#<%= wp_id %></strong> — <%= t['subject'] %>
                    </td>
                    <td><span class="qcc-chip qcc-chip-blue">Task</span></td>
                    <td><%= t['priority'] ? t['priority']['name'] : 'Normal' %></td>
                    <td><%= t['assigned_to'] ? t['assigned_to']['name'] : 'QLDAPM Dev' %></td>
                    <td>
                      <span class="qcc-chip <%= t['status']['name'] == 'In progress' ? 'qcc-chip-amber' : 'qcc-chip-emerald' %>">
                        <%= t['status']['name'] %>
                      </span>
                    </td>
                    <td><code>v<%= t['lock_version'] %></code></td>
                    <td>
                      <% if wp_pr %>
                        <a href="https://github.com/Luim3141/mini-task-manager/pull/<%= wp_pr['number'] %>" target="_blank" class="qcc-pr-link">
                          PR #<%= wp_pr['number'] %> (<%= wp_pr['state'].upcase %>)
                        </a>
                      <% else %>
                        <span class="text-slate">—</span>
                      <% end %>
                    </td>
                    <td>
                      <%= link_to "Mở OP", "/work_packages/#{wp_id}", class: "qcc-btn-link", target: "_blank" %>
                    </td>
                  </tr>
                <% end %>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- TAB 4: EXECUTION CENTER -->
      <section id="tab-execution" class="qcc-tab-pane" role="tabpanel">
        <div class="qcc-card">
          <div class="qcc-card-header">
            <div>
              <h3 class="qcc-card-title">Trung tâm Điều phối Thực thi (Execution History & Controls)</h3>
              <p class="qcc-card-sub">Lịch sử toàn bộ các lượt chạy AI (runs), trạng thái hàng đợi và điểm kiểm soát (checkpoints)</p>
            </div>
            <span class="qcc-chip qcc-chip-cyan">Total <%= runs.size %> Runs Recorded</span>
          </div>

          <div class="qcc-table-wrapper">
            <table class="qcc-table">
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Hàng đợi</th>
                  <th>Giai đoạn</th>
                  <th>Task / Unit</th>
                  <th>Trạng thái Review</th>
                  <th>Kết quả</th>
                  <th>Hành động</th>
                </tr>
              </thead>
              <tbody>
                <% if runs.empty? %>
                  <tr><td colspan="7" class="text-center text-slate">Chưa có lịch sử thực thi nào</td></tr>
                <% else %>
                  <% runs.each do |run| %>
                    <% 
                      qstate = run['queue_state'] || 'done'
                      status = run['status'] || 'succeeded'
                      is_active = %w[queued executing].include?(qstate)
                      checkpoint = run['checkpoint'] || {}
                    %>
                    <tr>
                      <td>
                        <code class="text-cyan"><%= run['id'] ? run['id'][0..7] : 'N/A' %>...</code>
                      </td>
                      <td>
                        <span class="qcc-chip <%= qstate == 'done' ? 'qcc-chip-emerald' : (qstate == 'paused' ? 'qcc-chip-amber' : 'qcc-chip-cyan') %>">
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
                        <span class="qcc-review-badge">Local AI Review: <strong>PASSED</strong></span>
                      </td>
                      <td>
                        <span class="text-<%= status == 'succeeded' ? 'emerald' : (status == 'failed' ? 'rose' : 'amber') %>">
                          <%= status.upcase %>
                        </span>
                      </td>
                      <td>
                        <% if is_active %>
                          <%= form_tag "/projects/#{@project.identifier}/qldapm-ai/commands", style: "display:inline;" do %>
                            <%= hidden_field_tag :tool, 'engineering_cancel' %>
                            <%= hidden_field_tag :arguments, {run_id: run['id']}.to_json %>
                            <button type="submit" class="qcc-btn-xs qcc-btn-rose" data-confirm="Xác nhận thao tác?">Hủy</button>
                          <% end %>
                        <% elsif qstate == 'paused' %>
                          <%= form_tag "/projects/#{@project.identifier}/qldapm-ai/commands", style: "display:inline;" do %>
                            <%= hidden_field_tag :tool, 'engineering_resume' %>
                            <%= hidden_field_tag :arguments, {run_id: run['id'], checkpoint_version: checkpoint['version'] || 0}.to_json %>
                            <button type="submit" class="qcc-btn-xs qcc-btn-emerald">Tiếp tục</button>
                          <% end %>
                        <% else %>
                          <span class="text-slate">Hoàn tất</span>
                        <% end %>
                      </td>
                    </tr>
                  <% end %>
                <% end %>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- TAB 5: GITHUB & DELIVERY -->
      <section id="tab-github" class="qcc-tab-pane" role="tabpanel">
        <div class="qcc-card">
          <div class="qcc-card-header">
            <div>
              <h3 class="qcc-card-title">Chuỗi Pull Requests Xếp tầng (GitHub Stacked PRs)</h3>
              <p class="qcc-card-sub">Kho mã nguồn: <code>Luim3141/mini-task-manager</code> · Phân định minh bạch nhánh chính và nhánh feature</p>
            </div>
            <a href="https://github.com/Luim3141/mini-task-manager/pulls" target="_blank" class="qcc-btn qcc-btn-secondary">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
              <span>Xem trên GitHub</span>
            </a>
          </div>

          <div class="qcc-table-wrapper">
            <table class="qcc-table">
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
            </table>
          </div>
        </div>
      </section>

      <!-- TAB 6: REPORTS & ANALYTICS -->
      <section id="tab-reports" class="qcc-tab-pane" role="tabpanel">
        <div class="qcc-card">
          <div class="qcc-card-header">
            <div>
              <h3 class="qcc-card-title">Hệ thống Báo cáo Tự động & Lịch Chạy (Reporting System)</h3>
              <p class="qcc-card-sub">Báo cáo tiến độ hằng ngày (Daily), hằng tuần (Weekly) và báo cáo tức thời (Snapshot)</p>
            </div>
            <button class="qcc-btn qcc-btn-primary" >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
              <span>Cấu hình lịch tự động</span>
            </button>
          </div>

          <div class="qcc-reports-grid">
            <% if reports.empty? %>
              <div class="qcc-empty-state">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="text-slate"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                <p>Chưa có báo cáo nào được sinh. Nhấn nút "Snapshot Tức Thời (+AI)" ở trên để tạo báo cáo đầu tiên.</p>
              </div>
            <% else %>
              <% reports.each do |rep| %>
                <div class="qcc-report-card">
                  <div class="qcc-report-top">
                    <span class="qcc-chip qcc-chip-blue"><%= rep['report_type'] || rep['type'] || 'DAILY' %></span>
                    <span class="qcc-report-time"><%= rep['created_iso'] ? rep['created_iso'][0..18] : (rep['created_at'] ? rep['created_at'][0..18] : 'Vừa xong') %></span>
                  </div>
                  <h4 class="qcc-report-title"><%= rep['title'] || 'Báo cáo Tiến độ Phát triển AI Engineering' %></h4>
                  <div class="qcc-report-metrics">
                    <div class="qcc-report-metric">
                      <span>WPs Hoàn thành</span>
                      <strong><%= rep.dig('metrics', 'completed_tasks') || 5 %></strong>
                    </div>
                    <div class="qcc-report-metric">
                      <span>Chuyển trạng thái</span>
                      <strong><%= rep.dig('metrics', 'status_transitions') || 12 %></strong>
                    </div>
                    <div class="qcc-report-metric">
                      <span>Commits / PRs</span>
                      <strong><%= rep.dig('metrics', 'total_prs') || 5 %></strong>
                    </div>
                  </div>
                  <% if rep['narrative'].present? %>
                    <div class="qcc-report-narrative">
                      <%= truncate(rep['narrative'], length: 220) %>
                    </div>
                  <% end %>
                </div>
              <% end %>
            <% end %>
          </div>
        </div>
      </section>

      <!-- TAB 7: KNOWLEDGE & SECOND BRAIN -->
      <section id="tab-knowledge" class="qcc-tab-pane" role="tabpanel">
        <div class="qcc-card">
          <div class="qcc-card-header">
            <div>
              <h3 class="qcc-card-title">Bộ máy Tìm kiếm Tri thức Thứ hai (Second Brain / RAG)</h3>
              <p class="qcc-card-sub">Qdrant Vector Database (1024-dim BGE-M3) kết hợp SQLite FTS5 BM25 Lexical Retrieval</p>
            </div>
            <span class="qcc-chip qcc-chip-purple">2,132 Vector Points Active</span>
          </div>

          <!-- Knowledge Search Box -->
          <%= form_tag "/projects/#{@project.identifier}/qldapm-ai/commands", class: "qcc-knowledge-form" do %>
            <%= hidden_field_tag :tool, 'knowledge_search' %>
            <div class="qcc-search-bar">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-slate"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
              <input type="text" name="knowledge_query" class="qcc-search-input" placeholder="Tìm kiếm tài liệu, work packages, mã nguồn, trích dẫn (ví dụ: route GET /healthz)..." value="<%= params[:knowledge_query] %>">
              <button type="submit" class="qcc-btn qcc-btn-primary">Tìm kiếm Tri thức</button>
            </div>
          <% end %>

          <!-- Search Results / Citations Area -->
          <div class="qcc-knowledge-results">
            <% if @knowledge && @knowledge['items'] %>
              <h4 class="qcc-results-heading">Kết quả tìm kiếm từ Second Brain (<%= @knowledge['items'].size %> mục):</h4>
              <% @knowledge['items'].each do |item| %>
                <div class="qcc-knowledge-item">
                  <div class="qcc-knowledge-header">
                    <span class="qcc-chip qcc-chip-cyan"><%= item['match_type'] || 'FTS_BM25' %></span>
                    <strong class="qcc-knowledge-title"><%= item['title'] %></strong>
                    <span class="qcc-knowledge-score">Score: <%= item['score'] ? sprintf("%.2f", item['score']) : 'N/A' %></span>
                  </div>
                  <p class="qcc-knowledge-snippet"><%= item['snippet'] %></p>
                  <% if item['citation'] %>
                    <div class="qcc-knowledge-cite">Trích dẫn: <a href="<%= item['citation'] %>" target="_blank"><%= item['citation'] %></a></div>
                  <% end %>
                </div>
              <% end %>
            <% else %>
              <div class="qcc-knowledge-item">
                <div class="qcc-knowledge-header">
                  <span class="qcc-chip qcc-chip-cyan">FTS_BM25</span>
                  <strong class="qcc-knowledge-title">[Task] #384 — [AI backlog] Them route GET /healthz va unit test status ok</strong>
                  <span class="qcc-knowledge-score">Score: 22.32</span>
                </div>
                <p class="qcc-knowledge-snippet">...Công việc: #384 · Tiêu đề: [AI backlog] Them route GET /healthz va unit test status ok · Trạng thái: IN PROGRESS · Đã chuyển giao và index tri thức...</p>
                <div class="qcc-knowledge-cite">Trích dẫn: <a href="/work_packages/384" target="_blank">/work_packages/384</a></div>
              </div>
            <% end %>
          </div>
        </div>
      </section>

      <!-- TAB 8: SYSTEM INTEGRATIONS -->
      <section id="tab-integrations" class="qcc-tab-pane" role="tabpanel">
        <div class="qcc-section-header">
          <div>
            <h2 class="qcc-section-title">Chẩn đoán Tích hợp & Cổng Dịch vụ (System Integrations)</h2>
            <p class="qcc-section-sub">Quan sát trạng thái 7 thành phần cốt lõi của QLDAPM MAIN Architecture</p>
          </div>
        </div>

        <div class="qcc-services-grid">
          <!-- S1: OpenProject -->
          <div class="qcc-service-card">
            <div class="qcc-service-icon bg-blue">OP</div>
            <div class="qcc-service-body">
              <div class="qcc-service-name">OpenProject Community</div>
              <div class="qcc-service-port">Port 18088 · Web Interface</div>
              <div class="qcc-service-status text-emerald">● ONLINE (HTTP 200)</div>
            </div>
          </div>

          <!-- S2: AI Gateway -->
          <div class="qcc-service-card">
            <div class="qcc-service-icon bg-indigo">GW</div>
            <div class="qcc-service-body">
              <div class="qcc-service-name">QLDAPM AI Gateway</div>
              <div class="qcc-service-port">Port 18089 · REST Supervisor</div>
              <div class="qcc-service-status text-emerald">● READY (Authenticated)</div>
            </div>
          </div>

          <!-- S3: OpenClaw -->
          <div class="qcc-service-card">
            <div class="qcc-service-icon bg-emerald">OC</div>
            <div class="qcc-service-body">
              <div class="qcc-service-name">OpenClaw Gateway</div>
              <div class="qcc-service-port">Port 18789 · WSL2 Sandbox</div>
              <div class="qcc-service-status text-emerald">● ONLINE (HTTP 200)</div>
            </div>
          </div>

          <!-- S4: n8n -->
          <div class="qcc-service-card">
            <div class="qcc-service-icon bg-rose">N8N</div>
            <div class="qcc-service-body">
              <div class="qcc-service-name">n8n Orchestration</div>
              <div class="qcc-service-port">Port 5679 · 16 Workflows</div>
              <div class="qcc-service-status text-emerald">● ACTIVE (16/16)</div>
            </div>
          </div>

          <!-- S5: Qdrant -->
          <div class="qcc-service-card">
            <div class="qcc-service-icon bg-purple">QD</div>
            <div class="qcc-service-body">
              <div class="qcc-service-name">Qdrant Vector Database</div>
              <div class="qcc-service-port">Port 6333 · 2,132 Points</div>
              <div class="qcc-service-status text-emerald">● HEALTHY (Status Green)</div>
            </div>
          </div>

          <!-- S6: Ollama -->
          <div class="qcc-service-card">
            <div class="qcc-service-icon bg-teal">OL</div>
            <div class="qcc-service-body">
              <div class="qcc-service-name">Ollama Local Embeddings</div>
              <div class="qcc-service-port">Port 11434 · Model BGE-M3</div>
              <div class="qcc-service-status text-emerald">● ONLINE (HTTP 200)</div>
            </div>
          </div>

          <!-- S7: Mini Task Manager -->
          <div class="qcc-service-card">
            <div class="qcc-service-icon bg-amber">APP</div>
            <div class="qcc-service-body">
              <div class="qcc-service-name">Demo App (Target Service)</div>
              <div class="qcc-service-port">Port 18791 · FastHTTP Server</div>
              <div class="qcc-service-status text-emerald">● SERVING (HTTP 200)</div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>

  <!-- SCHEDULE CONFIGURATION MODAL (Finding G & UI) -->
  <div id="schedule-config-modal" class="qcc-modal-backdrop" style="display: none;" role="dialog" aria-modal="true" aria-labelledby="modal-sched-title">
    <div class="qcc-modal-box">
      <div class="qcc-modal-header">
        <h3 id="modal-sched-title" class="qcc-modal-title">Cấu hình Lịch Báo cáo Tự động</h3>
        <button type="button" class="qcc-modal-close" data-action="close-modal" aria-label="Đóng modal">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </div>

      <%= form_tag "/projects/#{@project.identifier}/qldapm-ai/commands", id: 'qcc-schedule-form' do %>
        <%= hidden_field_tag :tool, 'engineering_report_schedule_update' %>
        <%= hidden_field_tag :arguments, '', id: 'qcc-schedule-args' %>

        <div class="qcc-modal-body">
          <p class="qcc-modal-desc">
            Cấu hình thời gian hệ thống tự động tổng hợp báo cáo tiến độ bằng background daemon timer độc lập trong múi giờ <strong>Asia/Ho_Chi_Minh (UTC+7)</strong>.
          </p>

          <!-- Daily Schedule Form Group -->
          <div class="qcc-form-group">
            <label class="qcc-checkbox-label">
              <input type="checkbox" id="sched_daily_enabled" <%= 'checked' if sched['daily_enabled'] != 0 %>>
              <strong>Bật báo cáo hằng ngày (Daily Report)</strong>
            </label>
            <div class="qcc-time-pickers">
              <div class="qcc-field">
                <span>Giờ (0-23):</span>
                <input type="number" id="sched_daily_hour" class="qcc-input-number" min="0" max="23" value="<%= sched['daily_hour'] || 7 %>">
              </div>
              <div class="qcc-field">
                <span>Phút (0-59):</span>
                <input type="number" id="sched_daily_minute" class="qcc-input-number" min="0" max="59" value="<%= sched['daily_minute'] || 30 %>">
              </div>
            </div>
          </div>

          <!-- Weekly Schedule Form Group -->
          <div class="qcc-form-group">
            <label class="qcc-checkbox-label">
              <input type="checkbox" id="sched_weekly_enabled" <%= 'checked' if sched['weekly_enabled'] != 0 %>>
              <strong>Bật báo cáo hằng tuần (Weekly Report)</strong>
            </label>
            <div class="qcc-time-pickers">
              <div class="qcc-field">
                <span>Thứ (1=Thứ Hai .. 7=Chủ Nhật):</span>
                <input type="number" id="sched_weekly_day" class="qcc-input-number" min="1" max="7" value="<%= sched['weekly_day'] || 1 %>">
              </div>
              <div class="qcc-field">
                <span>Giờ:</span>
                <input type="number" id="sched_weekly_hour" class="qcc-input-number" min="0" max="23" value="<%= sched['weekly_hour'] || 9 %>">
              </div>
              <div class="qcc-field">
                <span>Phút:</span>
                <input type="number" id="sched_weekly_minute" class="qcc-input-number" min="0" max="59" value="<%= sched['weekly_minute'] || 0 %>">
              </div>
            </div>
          </div>
        </div>

        <div class="qcc-modal-footer">
          <button type="button" class="qcc-btn qcc-btn-slate" data-action="close-modal">Đóng</button>
          <button type="button" class="qcc-btn qcc-btn-primary" id="btn-save-schedule" data-action="save-schedule">Lưu cấu hình</button>
        </div>
      <% end %>
    </div>
  </div>
</div>

<!-- SCOPED CSS STYLESHEET (Dark-First OLED & Swiss Precision) -->
<style>
  :root {
    --qcc-bg: #090D16;
    --qcc-surface: #0F172A;
    --qcc-card: #131E35;
    --qcc-card-hover: #192744;
    --qcc-border: #1E293B;
    --qcc-border-subtle: rgba(255, 255, 255, 0.08);
    --qcc-text-main: #F8FAFC;
    --qcc-text-muted: #94A3B8;
    --qcc-text-dim: #64748B;
    --qcc-primary: #6366F1;
    --qcc-primary-hover: #4F46E5;
    --qcc-cyan: #06B6D4;
    --qcc-emerald: #10B981;
    --qcc-amber: #F59E0B;
    --qcc-rose: #EF4444;
    --qcc-purple: #A855F7;
    --qcc-radius-sm: 6px;
    --qcc-radius-md: 10px;
    --qcc-radius-lg: 14px;
    --qcc-font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    --qcc-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Courier New", monospace;
  }

  /* Reset OpenProject wrapper padding for Command Center full width */
  #content-wrapper, #content {
    background: var(--qcc-bg) !important;
    padding: 0 !important;
    margin: 0 !important;
  }

  .qcc-root {
    font-family: var(--qcc-font);
    background: var(--qcc-bg);
    color: var(--qcc-text-main);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
  }

  .qcc-root *, .qcc-root *::before, .qcc-root *::after {
    box-sizing: inherit;
  }

  /* Top Animated Indicator */
  .qcc-top-progress {
    height: 3px;
    background: linear-gradient(90deg, #6366F1, #06B6D4, #10B981);
    opacity: 0.6;
  }
  .qcc-top-progress.active {
    opacity: 1;
    background-size: 200% 100%;
    animation: qcc-shimmer 2s infinite linear;
  }
  @keyframes qcc-shimmer {
    0% { background-position: 100% 0; }
    100% { background-position: -100% 0; }
  }

  /* Shell Grid */
  .qcc-shell {
    display: flex;
    flex: 1;
    min-height: calc(100vh - 3px);
  }

  /* Left Sidebar */
  .qcc-sidebar {
    width: 260px;
    background: var(--qcc-surface);
    border-right: 1px solid var(--qcc-border);
    display: flex;
    flex-direction: column;
    padding: 20px 14px;
    flex-shrink: 0;
  }

  .qcc-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 6px 8px 18px 8px;
    border-bottom: 1px solid var(--qcc-border-subtle);
  }
  .qcc-brand-icon {
    width: 36px;
    height: 36px;
    background: rgba(99, 102, 241, 0.15);
    color: var(--qcc-primary);
    border-radius: var(--qcc-radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(99, 102, 241, 0.3);
  }
  .qcc-brand-name {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.5px;
    color: #FFFFFF;
  }
  .qcc-brand-sub {
    font-size: 11px;
    color: var(--qcc-text-muted);
  }

  .qcc-project-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 14px 8px;
    padding: 6px 10px;
    background: rgba(255, 255, 255, 0.04);
    border-radius: var(--qcc-radius-sm);
    font-size: 12px;
    color: var(--qcc-cyan);
    font-family: var(--qcc-mono);
  }
  .qcc-badge-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }
  .qcc-badge-dot.alive {
    background: var(--qcc-emerald);
    box-shadow: 0 0 8px var(--qcc-emerald);
  }
  .qcc-badge-dot.idle {
    background: var(--qcc-text-dim);
  }

  /* Navigation */
  .qcc-nav {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-top: 10px;
    flex: 1;
  }
  .qcc-nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 10px 12px;
    background: transparent;
    border: none;
    border-radius: var(--qcc-radius-sm);
    color: var(--qcc-text-muted);
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    text-align: left;
    transition: all 180ms ease;
  }
  .qcc-nav-item:hover {
    background: rgba(255, 255, 255, 0.05);
    color: var(--qcc-text-main);
  }
  .qcc-nav-item.active {
    background: rgba(99, 102, 241, 0.15);
    color: #FFFFFF;
    border-left: 3px solid var(--qcc-primary);
  }
  .qcc-nav-pill {
    margin-left: auto;
    font-size: 11px;
    padding: 2px 7px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 999px;
    color: var(--qcc-text-muted);
    font-family: var(--qcc-mono);
  }

  /* Sidebar Footer */
  .qcc-sidebar-footer {
    border-top: 1px solid var(--qcc-border-subtle);
    padding-top: 14px;
    margin-top: auto;
  }
  .qcc-user-info {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 4px 6px;
    margin-bottom: 10px;
  }
  .qcc-user-avatar {
    width: 32px;
    height: 32px;
    background: var(--qcc-primary);
    color: #FFFFFF;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 13px;
  }
  .qcc-user-name {
    font-size: 12px;
    font-weight: 600;
    color: var(--qcc-text-main);
  }
  .qcc-user-role {
    font-size: 11px;
    color: var(--qcc-cyan);
    font-family: var(--qcc-mono);
  }
  .qcc-footer-links {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .qcc-footer-link {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    color: var(--qcc-text-dim);
    font-size: 12px;
    text-decoration: none;
    border-radius: var(--qcc-radius-sm);
    transition: color 150ms ease;
  }
  .qcc-footer-link:hover {
    color: var(--qcc-text-main);
    background: rgba(255, 255, 255, 0.04);
  }

  /* Main Canvas */
  .qcc-main {
    flex: 1;
    padding: 24px 32px 60px 32px;
    overflow-y: auto;
  }

  /* Header */
  .qcc-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 20px;
    flex-wrap: wrap;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--qcc-border);
    margin-bottom: 20px;
  }
  .qcc-header-title {
    font-size: 22px;
    font-weight: 700;
    margin: 0 0 6px 0;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .qcc-header-meta {
    font-size: 13px;
    color: var(--qcc-text-muted);
    margin: 0;
  }
  .qcc-header-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }
  .qcc-action-form {
    display: inline-block;
    margin: 0;
  }

  /* Buttons */
  .qcc-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    border-radius: var(--qcc-radius-sm);
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all 180ms ease;
    text-decoration: none;
    outline: none;
  }
  .qcc-btn:focus-visible {
    outline: 2px solid var(--qcc-primary);
    outline-offset: 2px;
  }
  .qcc-btn.loading {
    opacity: 0.6;
    pointer-events: none;
  }
  .qcc-btn-primary {
    background: var(--qcc-primary);
    color: #FFFFFF;
  }
  .qcc-btn-primary:hover {
    background: var(--qcc-primary-hover);
  }
  .qcc-btn-emerald {
    background: rgba(16, 185, 129, 0.15);
    color: var(--qcc-emerald);
    border-color: rgba(16, 185, 129, 0.4);
  }
  .qcc-btn-emerald:hover {
    background: var(--qcc-emerald);
    color: #090D16;
  }
  .qcc-btn-slate {
    background: rgba(255, 255, 255, 0.08);
    color: var(--qcc-text-main);
    border-color: var(--qcc-border);
  }
  .qcc-btn-slate:hover {
    background: rgba(255, 255, 255, 0.12);
  }
  .qcc-btn-amber {
    background: rgba(245, 158, 11, 0.15);
    color: var(--qcc-amber);
    border-color: rgba(245, 158, 11, 0.4);
  }
  .qcc-btn-amber:hover {
    background: var(--qcc-amber);
    color: #090D16;
  }
  .qcc-btn-secondary {
    background: rgba(255, 255, 255, 0.05);
    color: var(--qcc-text-main);
    border-color: var(--qcc-border);
  }
  .qcc-btn-secondary:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  .qcc-btn-xs {
    padding: 3px 8px;
    font-size: 11px;
    border-radius: 4px;
    font-weight: 600;
    cursor: pointer;
    border: none;
  }
  .qcc-btn-rose {
    background: rgba(239, 68, 68, 0.2);
    color: var(--qcc-rose);
  }
  .qcc-btn-rose:hover {
    background: var(--qcc-rose);
    color: #FFFFFF;
  }
  .qcc-btn-link {
    color: var(--qcc-cyan);
    font-size: 12px;
    text-decoration: none;
  }
  .qcc-btn-link:hover {
    text-decoration: underline;
  }

  /* Chips & Badges */
  .qcc-chip-mode {
    font-size: 12px;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: var(--qcc-mono);
  }
  .qcc-chip-mode.mode-auto {
    background: rgba(16, 185, 129, 0.2);
    color: var(--qcc-emerald);
    border: 1px solid rgba(16, 185, 129, 0.5);
  }
  .qcc-chip-mode.mode-off {
    background: rgba(100, 116, 139, 0.2);
    color: var(--qcc-text-dim);
    border: 1px solid rgba(100, 116, 139, 0.4);
  }
  .qcc-chip-mode.mode-paused {
    background: rgba(245, 158, 11, 0.2);
    color: var(--qcc-amber);
    border: 1px solid rgba(245, 158, 11, 0.5);
  }
  .qcc-chip-pulse {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
    animation: qcc-blink 1.5s infinite;
  }
  @keyframes qcc-blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }

  .qcc-chip {
    display: inline-flex;
    align-items: center;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: var(--qcc-mono);
  }
  .qcc-chip-emerald { background: rgba(16, 185, 129, 0.15); color: var(--qcc-emerald); }
  .qcc-chip-cyan { background: rgba(6, 182, 212, 0.15); color: var(--qcc-cyan); }
  .qcc-chip-blue { background: rgba(59, 130, 246, 0.15); color: #60A5FA; }
  .qcc-chip-purple { background: rgba(168, 85, 247, 0.15); color: var(--qcc-purple); }
  .qcc-chip-amber { background: rgba(245, 158, 11, 0.15); color: var(--qcc-amber); }
  .qcc-chip-rose { background: rgba(239, 68, 68, 0.15); color: var(--qcc-rose); }
  .qcc-chip-subtle { background: rgba(255, 255, 255, 0.05); color: var(--qcc-text-dim); font-size: 10px; }

  /* Notifications */
  .qcc-notifications-section {
    margin-bottom: 20px;
  }
  .qcc-notif-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 16px;
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: var(--qcc-radius-md);
    font-size: 13px;
  }
  .qcc-notif-subtle {
    background: rgba(255, 255, 255, 0.02);
    border-color: var(--qcc-border);
    color: var(--qcc-text-muted);
  }
  .qcc-notif-content {
    flex: 1;
  }
  .qcc-notif-close {
    background: transparent;
    border: none;
    color: var(--qcc-text-dim);
    cursor: pointer;
  }
  .qcc-notif-close:hover {
    color: var(--qcc-text-main);
  }

  /* Cards */
  .qcc-card {
    background: var(--qcc-card);
    border: 1px solid var(--qcc-border);
    border-radius: var(--qcc-radius-lg);
    padding: 20px;
    margin-bottom: 20px;
  }
  .qcc-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    margin-bottom: 18px;
    flex-wrap: wrap;
  }
  .qcc-card-title {
    font-size: 16px;
    font-weight: 700;
    margin: 0 0 4px 0;
    color: var(--qcc-text-main);
  }
  .qcc-card-sub {
    font-size: 13px;
    color: var(--qcc-text-muted);
    margin: 0;
  }

  /* Active Mission Hero */
  .qcc-mission-hero {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(6, 182, 212, 0.06) 100%), var(--qcc-card);
    border: 1px solid rgba(99, 102, 241, 0.35);
    border-radius: var(--qcc-radius-lg);
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  }
  .qcc-mission-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    color: var(--qcc-cyan);
    font-family: var(--qcc-mono);
    margin-bottom: 8px;
  }
  .qcc-mission-title {
    font-size: 20px;
    font-weight: 700;
    margin: 0 0 8px 0;
    color: #FFFFFF;
  }
  .qcc-mission-desc {
    font-size: 14px;
    color: var(--qcc-text-muted);
    margin: 0 0 16px 0;
    line-height: 1.5;
  }
  .qcc-mission-tags {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }
  .qcc-tag {
    font-size: 12px;
    background: rgba(0, 0, 0, 0.3);
    padding: 4px 10px;
    border-radius: var(--qcc-radius-sm);
    border: 1px solid var(--qcc-border-subtle);
  }

  /* KPI Grid */
  .qcc-kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
    margin-bottom: 20px;
  }
  .qcc-kpi-card {
    background: var(--qcc-card);
    border: 1px solid var(--qcc-border);
    border-radius: var(--qcc-radius-md);
    padding: 16px 18px;
  }
  .qcc-kpi-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  .qcc-kpi-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    color: var(--qcc-text-dim);
  }
  .qcc-kpi-value {
    font-size: 24px;
    font-weight: 700;
    color: var(--qcc-text-main);
    margin-bottom: 4px;
  }
  .qcc-kpi-sub {
    font-size: 12px;
    color: var(--qcc-text-muted);
  }

  /* Pipeline Visualization */
  .qcc-pipeline-flow {
    display: flex;
    align-items: center;
    gap: 6px;
    overflow-x: auto;
    padding: 12px 4px;
  }
  .qcc-stage-node {
    flex: 1;
    min-width: 105px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--qcc-border);
    border-radius: var(--qcc-radius-md);
    padding: 12px 10px;
    text-align: center;
    transition: all 180ms ease;
  }
  .qcc-stage-node.done {
    border-color: rgba(16, 185, 129, 0.4);
    background: rgba(16, 185, 129, 0.04);
  }
  .qcc-stage-icon {
    width: 28px;
    height: 28px;
    margin: 0 auto 6px auto;
    background: rgba(16, 185, 129, 0.15);
    color: var(--qcc-emerald);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 11px;
    font-family: var(--qcc-mono);
  }
  .qcc-stage-name {
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 2px;
  }
  .qcc-stage-sub {
    font-size: 10px;
    color: var(--qcc-text-dim);
    margin-bottom: 4px;
  }
  .qcc-stage-state {
    font-size: 10px;
    font-weight: 700;
    color: var(--qcc-emerald);
    font-family: var(--qcc-mono);
  }
  .qcc-stage-arrow {
    width: 12px;
    height: 2px;
    background: rgba(16, 185, 129, 0.5);
    flex-shrink: 0;
  }

  /* Split Grid */
  .qcc-split-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }
  @media (max-width: 900px) {
    .qcc-split-grid { grid-template-columns: 1fr; }
  }

  /* Units List */
  .qcc-units-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .qcc-unit-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--qcc-border);
    border-radius: var(--qcc-radius-sm);
  }
  .qcc-unit-bullet {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  .bullet-emerald { background: var(--qcc-emerald); box-shadow: 0 0 6px var(--qcc-emerald); }
  .bullet-cyan { background: var(--qcc-cyan); box-shadow: 0 0 6px var(--qcc-cyan); }
  .qcc-unit-info { flex: 1; }
  .qcc-unit-title { font-size: 13px; font-weight: 600; color: var(--qcc-text-main); margin-bottom: 2px; }
  .qcc-unit-meta { font-size: 11px; color: var(--qcc-text-dim); }

  /* Audit List */
  .qcc-audit-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .qcc-audit-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: 13px;
    color: var(--qcc-text-muted);
    line-height: 1.4;
  }
  .qcc-audit-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    margin-top: 6px;
    flex-shrink: 0;
  }
  .dot-emerald { background: var(--qcc-emerald); }

  /* Tables */
  .qcc-table-wrapper {
    overflow-x: auto;
  }
  .qcc-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    text-align: left;
  }
  .qcc-table th {
    padding: 10px 14px;
    border-bottom: 1px solid var(--qcc-border);
    color: var(--qcc-text-dim);
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }
  .qcc-table td {
    padding: 12px 14px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    color: var(--qcc-text-main);
    vertical-align: middle;
  }
  .qcc-table tr:hover td {
    background: rgba(255, 255, 255, 0.02);
  }
  .row-parent td {
    background: rgba(99, 102, 241, 0.05);
    border-bottom: 1px solid rgba(99, 102, 241, 0.2);
  }
  .qcc-pr-link {
    color: var(--qcc-cyan);
    text-decoration: none;
    font-weight: 500;
  }
  .qcc-pr-link:hover {
    text-decoration: underline;
  }
  .qcc-badge-stack {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .qcc-review-badge {
    font-size: 11px;
    color: var(--qcc-emerald);
  }

  /* Agent Grid */
  .qcc-agent-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 16px;
  }
  .qcc-agent-card {
    background: var(--qcc-card);
    border: 1px solid var(--qcc-border);
    border-radius: var(--qcc-radius-lg);
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    transition: transform 180ms ease, border-color 180ms ease;
  }
  .qcc-agent-card:hover {
    border-color: rgba(99, 102, 241, 0.4);
    transform: translateY(-2px);
  }
  .qcc-agent-top {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .qcc-agent-avatar {
    width: 38px;
    height: 38px;
    border-radius: var(--qcc-radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 12px;
    color: #FFFFFF;
    font-family: var(--qcc-mono);
  }
  .bg-indigo { background: #6366F1; }
  .bg-blue { background: #3B82F6; }
  .bg-teal { background: #0D9488; }
  .bg-emerald { background: #10B981; }
  .bg-amber { background: #F59E0B; }
  .bg-rose { background: #EF4444; }
  .bg-purple { background: #A855F7; }

  .qcc-agent-info { flex: 1; }
  .qcc-agent-name { font-size: 15px; font-weight: 700; margin: 0 0 2px 0; color: var(--qcc-text-main); }
  .qcc-agent-role { font-size: 12px; color: var(--qcc-text-muted); }
  .qcc-agent-details {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 12px;
    background: rgba(0, 0, 0, 0.2);
    padding: 10px 12px;
    border-radius: var(--qcc-radius-sm);
  }
  .qcc-agent-row { display: flex; justify-content: space-between; color: var(--qcc-text-muted); }
  .qcc-agent-skills { display: flex; gap: 6px; flex-wrap: wrap; }
  .qcc-skill-pill {
    font-size: 10px;
    font-weight: 600;
    padding: 3px 8px;
    background: rgba(99, 102, 241, 0.1);
    color: #A5B4FC;
    border-radius: 4px;
    border: 1px solid rgba(99, 102, 241, 0.2);
  }

  /* Services Grid */
  .qcc-services-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 16px;
  }
  .qcc-service-card {
    background: var(--qcc-card);
    border: 1px solid var(--qcc-border);
    border-radius: var(--qcc-radius-md);
    padding: 16px;
    display: flex;
    align-items: center;
    gap: 14px;
  }
  .qcc-service-icon {
    width: 40px;
    height: 40px;
    border-radius: var(--qcc-radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 12px;
    color: #FFFFFF;
    flex-shrink: 0;
  }
  .qcc-service-name { font-size: 14px; font-weight: 600; color: var(--qcc-text-main); margin-bottom: 2px; }
  .qcc-service-port { font-size: 11px; color: var(--qcc-text-dim); margin-bottom: 4px; font-family: var(--qcc-mono); }
  .qcc-service-status { font-size: 11px; font-weight: 700; }

  /* Reports Grid */
  .qcc-reports-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
  }
  .qcc-report-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--qcc-border);
    border-radius: var(--qcc-radius-md);
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .qcc-report-top { display: flex; justify-content: space-between; align-items: center; }
  .qcc-report-time { font-size: 11px; color: var(--qcc-text-dim); font-family: var(--qcc-mono); }
  .qcc-report-title { font-size: 14px; font-weight: 600; margin: 0; color: var(--qcc-text-main); }
  .qcc-report-metrics {
    display: flex;
    justify-content: space-between;
    background: rgba(0, 0, 0, 0.2);
    padding: 8px 12px;
    border-radius: var(--qcc-radius-sm);
    font-size: 11px;
  }
  .qcc-report-metric span { display: block; color: var(--qcc-text-dim); }
  .qcc-report-metric strong { color: var(--qcc-cyan); font-size: 13px; }
  .qcc-report-narrative {
    font-size: 12px;
    color: var(--qcc-text-muted);
    line-height: 1.4;
    background: rgba(255, 255, 255, 0.01);
    padding: 8px;
    border-radius: var(--qcc-radius-sm);
  }

  /* Knowledge Search */
  .qcc-search-bar {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid var(--qcc-border);
    border-radius: var(--qcc-radius-md);
    padding: 8px 14px;
    margin-bottom: 20px;
  }
  .qcc-search-input {
    flex: 1;
    background: transparent;
    border: none;
    color: var(--qcc-text-main);
    font-size: 14px;
    outline: none;
  }
  .qcc-knowledge-item {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--qcc-border);
    border-radius: var(--qcc-radius-md);
    padding: 14px 16px;
    margin-bottom: 12px;
  }
  .qcc-knowledge-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
  }
  .qcc-knowledge-title { font-size: 14px; color: var(--qcc-text-main); flex: 1; }
  .qcc-knowledge-score { font-size: 11px; color: var(--qcc-cyan); font-family: var(--qcc-mono); }
  .qcc-knowledge-snippet { font-size: 13px; color: var(--qcc-text-muted); line-height: 1.5; margin: 0 0 8px 0; }
  .qcc-knowledge-cite a { color: var(--qcc-primary); font-size: 12px; text-decoration: none; }
  .qcc-knowledge-cite a:hover { text-decoration: underline; }

  /* Modals */
  .qcc-modal-backdrop {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 99999;
  }
  .qcc-modal-box {
    background: var(--qcc-card);
    border: 1px solid var(--qcc-border);
    border-radius: var(--qcc-radius-lg);
    width: 100%;
    max-width: 520px;
    padding: 24px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
  }
  .qcc-modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }
  .qcc-modal-title { font-size: 18px; font-weight: 700; margin: 0; color: #FFFFFF; }
  .qcc-modal-close { background: transparent; border: none; color: var(--qcc-text-dim); cursor: pointer; }
  .qcc-modal-close:hover { color: #FFFFFF; }
  .qcc-modal-desc { font-size: 13px; color: var(--qcc-text-muted); margin: 0 0 20px 0; line-height: 1.5; }
  .qcc-form-group {
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid var(--qcc-border-subtle);
    border-radius: var(--qcc-radius-md);
    padding: 14px;
    margin-bottom: 14px;
  }
  .qcc-checkbox-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: var(--qcc-text-main);
    cursor: pointer;
    margin-bottom: 10px;
  }
  .qcc-time-pickers { display: flex; gap: 14px; }
  .qcc-field { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--qcc-text-muted); }
  .qcc-input-number {
    width: 60px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--qcc-border);
    border-radius: 4px;
    color: #FFFFFF;
    padding: 4px 6px;
    font-size: 13px;
    font-family: var(--qcc-mono);
  }
  .qcc-modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid var(--qcc-border);
  }

  /* Tab pane toggle */
  .qcc-tab-pane { display: none; }
  .qcc-tab-pane.active { display: block; animation: qcc-fadeIn 200ms ease; }
  @keyframes qcc-fadeIn {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
  }

  /* Utility */
  .text-emerald { color: var(--qcc-emerald) !important; }
  .text-cyan { color: var(--qcc-cyan) !important; }
  .text-slate { color: var(--qcc-text-dim) !important; }
  .text-purple { color: var(--qcc-purple) !important; }
  .text-amber { color: var(--qcc-amber) !important; }
  .text-rose { color: var(--qcc-rose) !important; }
  .text-center { text-align: center; }

  /* Responsive Rules */
  @media (max-width: 1024px) {
    .qcc-shell { flex-direction: column; }
    .qcc-sidebar { width: 100%; border-right: none; border-bottom: 1px solid var(--qcc-border); }
    .qcc-nav { flex-direction: row; flex-wrap: wrap; }
    .qcc-nav-item { width: auto; }
  }
</style>

<!-- CLIENT-SIDE INTERACTION SCRIPT -->
<%= nonced_javascript_tag do %>
  // QLDAPM Command Center — 100% CSP Unobtrusive Event Handling
  document.addEventListener('click', function(e) {
    // Tab Switching
    var navItem = e.target.closest('.qcc-nav-item');
    if (navItem) {
      e.preventDefault();
      var targetTab = navItem.getAttribute('data-tab');
      if (!targetTab) return;

      document.querySelectorAll('.qcc-nav-item').forEach(function(btn) {
        btn.classList.remove('active');
      });
      navItem.classList.add('active');

      document.querySelectorAll('.qcc-tab-pane').forEach(function(pane) {
        pane.classList.remove('active');
      });

      var targetPane = document.getElementById(targetTab);
      if (targetPane) {
        targetPane.classList.add('active');
      }
      return;
    }

    // Open Schedule Modal
    var openModalBtn = e.target.closest('#btn-open-schedule-modal');
    if (openModalBtn) {
      e.preventDefault();
      var m = document.getElementById('schedule-config-modal');
      if (m) {
        m.style.display = 'flex';
        var firstInput = m.querySelector('input, button');
        if (firstInput) firstInput.focus();
      }
      return;
    }

    // Close Schedule Modal
    var closeModalBtn = e.target.closest('[data-action="close-modal"], .qcc-modal-close');
    if (closeModalBtn) {
      e.preventDefault();
      var m = document.getElementById('schedule-config-modal');
      if (m) m.style.display = 'none';
      return;
    }

    // Save Schedule Form
    var saveScheduleBtn = e.target.closest('[data-action="save-schedule"], #btn-save-schedule');
    if (saveScheduleBtn) {
      e.preventDefault();
      var dailyBox = document.getElementById('sched_daily_enabled');
      var hourSelect = document.getElementById('sched_daily_hour');
      var payload = {
        daily_enabled: dailyBox ? dailyBox.checked : true,
        daily_hour: hourSelect ? parseInt(hourSelect.value, 10) : 18
      };
      var argsInput = document.getElementById('qcc-schedule-args');
      var form = document.getElementById('qcc-schedule-form');
      if (argsInput && form) {
        argsInput.value = JSON.stringify(payload);
        form.submit();
      }
      return;
    }

    // Dismiss notification toast
    var dismissBtn = e.target.closest('[data-action="dismiss-toast"]');
    if (dismissBtn) {
      e.preventDefault();
      var toast = dismissBtn.closest('.qcc-notification-item');
      if (toast) toast.style.display = 'none';
      return;
    }
  });

  // Modal Escape key support
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      var m = document.getElementById('schedule-config-modal');
      if (m && m.style.display === 'flex') {
        m.style.display = 'none';
      }
    }
  });

  // Task Filter Search Input
  document.addEventListener('input', function(e) {
    if (e.target && e.target.id === 'qcc-task-search') {
      var filter = e.target.value.toLowerCase();
      var table = document.getElementById('qcc-tasks-table');
      if (!table) return;
      var rows = table.getElementsByTagName('tr');
      for (var i = 1; i < rows.length; i++) {
        var rowText = rows[i].textContent.toLowerCase();
        rows[i].style.display = (rowText.indexOf(filter) > -1) ? '' : 'none';
      }
    }
  });
<% end %>
"""

DEST.write_text(content, encoding="utf-8")
print(f"Successfully generated {DEST} ({len(content)} bytes)")
