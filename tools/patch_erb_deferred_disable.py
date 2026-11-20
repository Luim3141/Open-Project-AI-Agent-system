import sys

file_path = 'openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''    var btn = form.querySelector('button[type="submit"]');
    if (btn) {
      btn.disabled = true;
      btn.classList.add('submitting');
      var originalHtml = btn.innerHTML;
      btn.setAttribute('data-original-html', originalHtml);
      btn.innerHTML = '<span class="qcc-spinner"></span> <span>Đang xử lý...</span>';
    }'''

replacement = '''    var btn = form.querySelector('button[type="submit"]');
    if (btn) {
      var originalHtml = btn.innerHTML;
      btn.setAttribute('data-original-html', originalHtml);
      // Defer disabling button so browser dispatches the form submit event
      setTimeout(function() {
        if (btn) {
          btn.disabled = true;
          btn.classList.add('submitting');
          btn.innerHTML = '<span class="qcc-spinner"></span> <span>Đang xử lý...</span>';
        }
      }, 10);
    }'''

if target not in content:
    print('ERROR: target not found in ERB!')
    sys.exit(1)

content = content.replace(target, replacement, 1)
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('SUCCESS: updated ERB submit handler with deferred disable.')
