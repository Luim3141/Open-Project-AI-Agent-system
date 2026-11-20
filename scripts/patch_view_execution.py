path = 'openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = "      fetch('/projects/<%= @project.identifier %>/qldapm-ai/execution?run_id="
end_marker = "  // Modal Escape key support"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

print(f"start_idx: {start_idx}, end_idx: {end_idx}")

replacement = """      var execUrl = '/projects/<%= @project.identifier %>/qldapm-ai/executions/' + encodeURIComponent(runId) + '?format=json';
      fetch(execUrl, {
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
        document.getElementById('qcc-dag-container').innerHTML = '<div style="color:#F43F5E; padding:16px; background:rgba(244,63,94,0.1); border-radius:6px; border:1px solid rgba(244,63,94,0.3);"><strong style="display:block; margin-bottom:6px;">Lỗi nạp dữ liệu Telemetry:</strong>' + err.message + '<br><span style="font-size:11px; color:#94A3B8;">Vui lòng kiểm tra kết nối AI Gateway hoặc xem trực tiếp trong nhật ký SQLite.</span></div>';
      });
      return;
    }
  });

  function renderExecutionData(data) {
    if (!data) return;
    var stateStr = (data.state || 'COMPLETED').toUpperCase();
    var badgeClass = stateStr === 'COMPLETED' ? 'qcc-chip-emerald' : (stateStr === 'RUNNING' ? 'qcc-chip-cyan' : ((stateStr === 'FAILED' || stateStr === 'BLOCKED') ? 'qcc-chip-rose' : 'qcc-chip-amber'));
    var badgeElem = document.getElementById('qcc-run-modal-status-badge');
    badgeElem.textContent = stateStr;
    badgeElem.className = 'qcc-chip ' + badgeClass;

    document.getElementById('qcc-run-modal-unit').textContent = data.request || data.unit || 'Engineering Unit';
    document.getElementById('qcc-run-metric-duration').textContent = data.duration_seconds ? (data.duration_seconds + 's') : '--';
    document.getElementById('qcc-run-metric-model').textContent = data.model || 'gemini-3.5-flash-lite';
    
    var metrics = data.metrics || {};
    document.getElementById('qcc-run-metric-tokens').textContent = (metrics.tokens || 0).toLocaleString();
    document.getElementById('qcc-run-metric-calls').textContent = (metrics.calls || 0) + ' calls';
    document.getElementById('qcc-run-metric-agents').textContent = (metrics.agents || (data.nodes ? data.nodes.length : 6)) + ' Agents';

    // Render DAG
    var dagHtml = '';
    if (stateStr === 'FAILED' || stateStr === 'BLOCKED') {
      dagHtml += '<div style="margin-bottom:12px; padding:10px 14px; background:rgba(244,63,94,0.12); border-left:3px solid #F43F5E; border-radius:4px; font-size:12px; color:#FCA5A5;"><strong>Cảnh báo phiên thực thi:</strong> ' + (data.final_output || 'Phiên thực thi gặp lỗi hoặc bị chặn tại bước kiểm tra.') + '</div>';
    }

    var nodes = data.nodes || [];
    nodes.forEach(function(node, idx) {
      var nState = (node.state || 'PENDING').toUpperCase();
      var stateClass = nState === 'COMPLETED' ? 'text-emerald' : (nState === 'RUNNING' ? 'text-cyan' : ((nState === 'FAILED' || nState === 'BLOCKED') ? 'text-rose' : 'text-slate'));
      var stateBg = nState === 'COMPLETED' ? 'rgba(52, 211, 153, 0.08)' : (nState === 'RUNNING' ? 'rgba(6, 182, 212, 0.08)' : ((nState === 'FAILED' || nState === 'BLOCKED') ? 'rgba(244, 63, 94, 0.12)' : 'rgba(30, 41, 59, 0.4)'));
      var roleColor = node.agent === 'dev' ? '#38BDF8' : (node.agent === 'reviewer' ? '#F59E0B' : (node.agent === 'qa' ? '#10B981' : (node.agent === 'ba' ? '#EC4899' : (node.agent === 'pm' ? '#8B5CF6' : '#A78BFA'))));

      dagHtml += '<div class="qcc-dag-node-box" style="background:' + stateBg + '; border-left: 3px solid ' + roleColor + ';">';
      dagHtml += '  <div class="qcc-dag-node-header">';
      dagHtml += '    <strong style="color:' + roleColor + ';">' + (node.name || node.agent) + '</strong>';
      dagHtml += '    <span class="' + stateClass + '" style="font-size:11px; font-weight:600;">' + nState + '</span>';
      dagHtml += '  </div>';
      dagHtml += '  <div style="font-size:12px; color:#CBD5E1;">' + (node.objective || '') + '</div>';
      if (node.output) {
        dagHtml += '  <div style="font-size:11px; color:#94A3B8; background:#030712; padding:6px 10px; border-radius:4px; margin-top:4px; max-height:100px; overflow-y:auto; white-space:pre-wrap; word-break:break-all;">' + node.output + '</div>';
      }
      dagHtml += '</div>';

      if (idx < nodes.length - 1) {
        dagHtml += '<div class="qcc-dag-arrow">↓</div>';
      }
    });
    document.getElementById('qcc-dag-container').innerHTML = dagHtml || '<p class="text-slate">Không có thông tin DAG cho lượt chạy này.</p>';

    // Render Events
    var events = data.events || [];
    var eventsHtml = '';
    events.forEach(function(ev, idx) {
      var evStatus = (ev.status || 'OK').toUpperCase();
      var evClass = evStatus === 'COMPLETED' || evStatus === 'OK' ? 'qcc-chip-emerald' : (evStatus === 'QUEUED' || evStatus === 'RUNNING' ? 'qcc-chip-cyan' : ((evStatus === 'FAILED' || evStatus === 'BLOCKED') ? 'qcc-chip-rose' : 'qcc-chip-slate'));
      eventsHtml += '<tr>';
      eventsHtml += '<td>' + (ev.sequence || idx + 1) + '</td>';
      eventsHtml += '<td style="color:#94A3B8;">' + (ev.timestamp ? (new Date(ev.timestamp * 1000).toLocaleTimeString()) : '--') + '</td>';
      eventsHtml += '<td><strong style="color:#38BDF8;">' + (ev.agent_id || 'supervisor') + '</strong></td>';
      eventsHtml += '<td><code>' + (ev.event_type || '') + '</code></td>';
      eventsHtml += '<td><span class="qcc-chip ' + evClass + '">' + evStatus + '</span></td>';
      eventsHtml += '</tr>';
    });
    document.getElementById('qcc-events-tbody').innerHTML = eventsHtml || '<tr><td colspan="5" class="text-center text-slate">Không có sự kiện ghi nhận</td></tr>';

    // Render Real Diff Content
    var diffText = '';
    var devNode = (data.nodes || []).find(function(n) { return n.agent === 'dev'; });
    if (devNode && devNode.output) {
      diffText = '=== [Dev Agent Output & Files] ===\\n' + devNode.output;
    } else if (data.final_output) {
      diffText = '=== [Final Output] ===\\n' + data.final_output;
    } else {
      diffText = 'Không có mã nguồn diff trực tiếp được ghi nhận trong lượt chạy này.';
    }
    document.getElementById('qcc-diff-content').textContent = diffText;

    // Render Real QA Content
    var qaText = '';
    var qaNode = (data.nodes || []).find(function(n) { return n.agent === 'qa'; });
    var reviewerNode = (data.nodes || []).find(function(n) { return n.agent === 'reviewer'; });
    if (qaNode && qaNode.output) {
      qaText += '=== [QA Agent Evidence] ===\\n' + qaNode.output + '\\n\\n';
    }
    if (reviewerNode && reviewerNode.output) {
      qaText += '=== [Reviewer Exact-Diff Verdict] ===\\n' + reviewerNode.output + '\\n\\n';
    }
    if (!qaText) {
      if (data.request && data.request.indexOf('planning') !== -1) {
        qaText = 'Tác vụ này là giai đoạn Lập kế hoạch PM/BA (Planning), không có bước thực thi Pytest mã nguồn.\\nĐặc tả kỹ thuật và tiêu chí nghiệm thu được tạo tại Tab Backlog.';
      } else if (stateStr === 'FAILED' || stateStr === 'BLOCKED') {
        qaText = 'Phiên thực thi bị gián đoạn trước khi bước QA được tiến hành.\\nNguyên nhân: ' + (data.final_output || 'Lỗi kiểm tra tính khả dụng hoặc phụ thuộc.');
      } else {
        qaText = 'Không có log kiểm thử QA riêng biệt cho lượt chạy này.';
      }
    }
    document.getElementById('qcc-qa-content').textContent = qaText;

    // Render Raw JSON
    document.getElementById('qcc-raw-content').textContent = JSON.stringify(data, null, 2);
  }

"""

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + replacement + content[end_idx:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESSFULLY_REPLACED")
else:
    print("FAILED_TO_FIND_MARKERS")
