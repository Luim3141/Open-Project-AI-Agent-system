class QldapmWorkPackageTreeHook < OpenProject::Hook::ViewListener
  render_on :view_layouts_base_html_head, partial: "qldapm_work_packages/navigation"
end
