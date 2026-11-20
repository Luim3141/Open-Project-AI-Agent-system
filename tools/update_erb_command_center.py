import sys

file_path = 'openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update RUN ONCE form in top header
old_run_once = '''          <!-- RUN ONCE -->
          <%= form_tag "/projects/#{@project.identifier}/qldapm-ai/commands", class: "qcc-action-form" do %>
            <%= hidden_field_tag :tool, 'engineering_run_once' %>
            <%= hidden_field_tag :arguments, {native_id: 379, lock_version: parent['lock_version'] || 4, unit: 'health-check-v1'}.to_json %>
            <button type="submit" class="qcc-btn qcc-btn-primary" title="Chạy một lượt đơn lẻ có kiểm soát">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
              <span>RUN ONCE</span>
            </button>
          <% end %>'''

new_run_once = '''          <!-- RUN ONCE (Dynamically targeting eligible/latest unit) -->
          <%
            backlog_items = (Array(@engineering['backlog']) rescue [])
            active_or_next_unit = backlog_items.find { |b| b['state'] != 'succeeded' } || backlog_items.last || {'unit' => 'health-check-v1', 'native_id' => 384}
            target_unit_name = active_or_next_unit['unit'] || 'health-check-v1'
            target_native_id = (active_or_next_unit['native_id'] || 384).to_i
            target_task = (Array(@engineering['tasks']) rescue []).find { |t| t['id'] == target_native_id }
            target_lock = target_task ? target_task['lock_version'] : (parent['lock_version'] || 4)
          %>
          <%= form_tag "/projects/#{@project.identifier}/qldapm-ai/commands", class: "qcc-action-form" do %>
            <%= hidden_field_tag :tool, 'engineering_run_once' %>
            <%= hidden_field_tag :arguments, {native_id: target_native_id, lock_version: target_lock, unit: target_unit_name}.to_json %>
            <button type="submit" class="qcc-btn qcc-btn-primary" title="Chạy một lượt đơn lẻ có kiểm soát (Unit: <%= target_unit_name %>)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
              <span>RUN ONCE</span>
            </button>
          <% end %>'''

if old_run_once not in content:
    print('ERROR: old_run_once not found!')
    sys.exit(1)

content = content.replace(old_run_once, new_run_once, 1)

# 2. Update JavaScript submit handler & add resetSubmittingButtons
old_submit_js = '''  // Handle Form Submission: Disabling buttons & Visual Progress
  document.addEventListener('submit', function(e) {
    var form = e.target.closest('form');
    if (!form) return;

    if (form.id === 'qcc-schedule-form') {
      var dailyBox = document.getElementById('sched_daily_enabled');
      var hourSelect = document.getElementById('sched_daily_hour');
      var payload = {
        daily_enabled: dailyBox ? dailyBox.checked : true,
        daily_hour: hourSelect ? parseInt(hourSelect.value, 10) : 18
      };
      var argsInput = document.getElementById('qcc-schedule-args');
      if (argsInput) {
        argsInput.value = JSON.stringify(payload);
      }
    }

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
  });'''

new_submit_js = '''  function resetSubmittingButtons() {
    document.querySelectorAll('button.submitting').forEach(function(b) {
      b.disabled = false;
      b.classList.remove('submitting');
      var orig = b.getAttribute('data-original-html');
      if (orig) b.innerHTML = orig;
    });
    var progressBar = document.querySelector('.qcc-top-progress');
    if (progressBar) progressBar.classList.remove('active');
  }

  // Handle Form Submission: Disabling buttons & Visual Progress with Safety Reset
  document.addEventListener('submit', function(e) {
    var form = e.target.closest('form');
    if (!form) return;

    if (form.id === 'qcc-schedule-form') {
      var dailyBox = document.getElementById('sched_daily_enabled');
      var hourSelect = document.getElementById('sched_daily_hour');
      var payload = {
        daily_enabled: dailyBox ? dailyBox.checked : true,
        daily_hour: hourSelect ? parseInt(hourSelect.value, 10) : 18
      };
      var argsInput = document.getElementById('qcc-schedule-args');
      if (argsInput) {
        argsInput.value = JSON.stringify(payload);
      }
    }

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

    // Safety Timeout: Auto-restore button after 15 seconds to prevent permanent infinite loading on error
    setTimeout(function() {
      resetSubmittingButtons();
    }, 15000);
  });

  // Restore button state on page restore / BFCache navigation
  window.addEventListener('pageshow', function() {
    resetSubmittingButtons();
  });'''

if old_submit_js not in content:
    print('ERROR: old_submit_js not found!')
    sys.exit(1)

content = content.replace(old_submit_js, new_submit_js, 1)

# 3. Update Workforce titles and capability notes
old_role_meta = """            role_meta = {
              'supervisor' => { avatar: 'SUP', color: 'bg-indigo', title: 'AI Supervisor', sub: 'Orchestrator & Gatekeeper' },
              'pm'         => { avatar: 'PM',  color: 'bg-blue',   title: 'Product Manager Agent', sub: 'Backlog Decomposition & WBS' },
              'ba'         => { avatar: 'BA',  color: 'bg-teal',   title: 'Business Analyst Agent', sub: 'Requirements & Acceptance Criteria' },
              'dev'        => { avatar: 'DEV', color: 'bg-emerald',title: 'Senior Developer Agent', sub: 'Full-Stack Implementation (WSL2)' },
              'reviewer'   => { avatar: 'REV', color: 'bg-amber',  title: 'Code Reviewer Agent', sub: 'Architecture & Quality Gate (0 LLM)' },
              'qa'         => { avatar: 'QA',  color: 'bg-rose',   title: 'QA Automation Lead', sub: 'Acceptance & Regression Testing' }
            }"""

new_role_meta = """            role_meta = {
              'supervisor' => { avatar: 'SUP', color: 'bg-indigo', title: 'AI Supervisor', sub: 'Orchestrator & Gatekeeper (gemini-3.5-flash-lite)' },
              'pm'         => { avatar: 'PM',  color: 'bg-blue',   title: 'Product Manager Agent', sub: 'Backlog Decomposition & WBS (gemini-3.5-flash-lite)' },
              'ba'         => { avatar: 'BA',  color: 'bg-teal',   title: 'Business Analyst Agent', sub: 'Requirements & AC (gemini-3.5-flash-lite)' },
              'dev'        => { avatar: 'DEV', color: 'bg-emerald',title: 'Senior Developer Agent', sub: 'Implementation via OpenClaw Worktree & Scripts' },
              'reviewer'   => { avatar: 'REV', color: 'bg-amber',  title: 'Code Reviewer Agent', sub: 'Local-Policy Exact-Diff Checker (0 LLM Calls)' },
              'qa'         => { avatar: 'QA',  color: 'bg-rose',   title: 'QA Automation Lead', sub: 'Automated Pytest Runner (No LLM Reasoning)' }
            }"""

if old_role_meta in content:
    content = content.replace(old_role_meta, new_role_meta, 1)
else:
    print('NOTE: old_role_meta exact match not found, checking role_meta lines')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('SUCCESS: updated ERB command center view.')
