module QldapmBoardWrite
  extend ActiveSupport::Concern

  included do
    before_save :qldapm_board_permission, prepend: true
    before_destroy :qldapm_board_permission, prepend: true
  end

  def qldapm_board_permission
    board = is_a?(Boards::Grid) ? self : grid
    return unless board.is_a?(Boards::Grid)
    projects = [board.project, Project.find_by(id: board.project_id_in_database)].compact.uniq
    return if projects.none? { |project| Qldapm::Rbac.managed?(project) }
    unless projects.all? { |project| Qldapm::Rbac.pm?(project, User.current, fresh: true) }
      errors.add(:base, "QLDAPM_PM_REQUIRED")
      throw :abort
    end
  end
end
