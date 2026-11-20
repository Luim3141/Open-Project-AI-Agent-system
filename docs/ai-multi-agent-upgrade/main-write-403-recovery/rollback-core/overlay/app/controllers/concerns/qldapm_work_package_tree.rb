module QldapmWorkPackageTree
  def index
    return super unless request.format.html? && @project&.identifier == "qldapm-local" &&
      params[:native_table] != "1" && params[:query_id].blank? && params[:query_props].blank? && params[:name].blank?

    @tree_items = WorkPackage.visible(User.current).where(project: @project)
      .includes(:type, :status).order(:id).to_a
    visible_ids = @tree_items.map(&:id).to_set
    @tree_children = @tree_items.group_by(&:parent_id)
    # Keep permitted standalone items visible when their parent is absent or not readable.
    roots = @tree_items.reject { |item| visible_ids.include?(item.parent_id) }
      .sort_by { |item| [item.type.name == "Epic" ? 0 : 1, item.id] }
    @tree_root_count = roots.size
    @tree_per_page = [5, 10, 20].include?(params[:per_page].to_i) ? params[:per_page].to_i : 20
    @tree_page_count = [(@tree_root_count.to_f / @tree_per_page).ceil, 1].max
    @tree_page = params[:page].to_i.clamp(1, @tree_page_count)
    @tree_roots = roots.slice((@tree_page - 1) * @tree_per_page, @tree_per_page) || []
    render "qldapm_work_packages/index", layout: "base"
  end
end
