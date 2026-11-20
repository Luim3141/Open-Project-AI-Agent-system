module QldapmRelationWrite
  extend ActiveSupport::Concern

  included do
    around_save :qldapm_serialized_relation, prepend: true
    around_destroy :qldapm_serialized_relation, prepend: true
  end

  def qldapm_serialized_relation
    ids = [from_id,to_id,from_id_in_database,to_id_in_database].compact.uniq
    projects = WorkPackage.where(id:ids).joins(:project).where(projects:{identifier:'qldapm-local'}).distinct.pluck(:project_id).sort
    return yield if projects.empty?
    self.class.transaction do
      projects.each { |id| self.class.connection.execute("SELECT pg_advisory_xact_lock(817609, #{Integer(id)})") }
      yield
    end
  end
end
