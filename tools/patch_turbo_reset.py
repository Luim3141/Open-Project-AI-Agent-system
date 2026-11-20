from pathlib import Path

erb_path = Path("openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb")
content = erb_path.read_text(encoding="utf-8")

old_code = """  // Restore button state on page restore / BFCache navigation
  window.addEventListener('pageshow', function() {
    resetSubmittingButtons();
  });"""

new_code = """  // Restore button state on Turbo events and page restore
  ['turbo:submit-end', 'turbo:render', 'turbo:load', 'pageshow'].forEach(function(evt) {
    document.addEventListener(evt, function() {
      resetSubmittingButtons();
    });
    window.addEventListener(evt, function() {
      resetSubmittingButtons();
    });
  });"""

if old_code in content:
    content = content.replace(old_code, new_code)
    erb_path.write_text(content, encoding="utf-8")
    print("Successfully patched turbo event listeners in ERB!")
else:
    print("Warning: old_code not found")
