require "digest"
require "json"

module QldapmGateWrite
  extend ActiveSupport::Concern
  TRACKED = %w[subject description assigned_to_id parent_id project_id type_id].freeze

  included do
    before_save :qldapm_validate_write, prepend: true
    around_save :qldapm_serialized_save, prepend: true
    before_destroy :qldapm_guard_destroy, prepend: true
  end

  def qldapm_managed?
    project&.identifier == "qldapm-local" || (persisted? && Project.find_by(id: project_id_in_database)&.identifier == "qldapm-local")
  end

  def qldapm_actor(user = User.current)
    {"id" => user&.id, "role" => Qldapm::Rbac.role(project, user)}
  end

  def qldapm_snapshot
    bug_scope = type.name == "Subtask" && qldapm_gate["kind"] == "qa" && parent ? parent : self
    descendants = WorkPackage.where(id: bug_scope.descendants.select(:id)).includes(:status).to_a
    {"id" => id, "type" => type.name, "native_subtask" => type.name == "Subtask", "status" => status.name, "assignee" => assigned_to_id,
     "data" => qldapm_gate, "children" => children.includes(:status).map { |c|
       {"id" => c.id, "type" => c.type.name, "status" => c.status.name, "stream" => c.qldapm_gate["stream"], "kind" => c.qldapm_gate["kind"]}
     }, "blocking_bugs" => descendants.select { |c| c.qldapm_gate["kind"] == "fix_bug" }.map { |c|
       {"id" => c.id, "status" => c.status.name}
     }}
  end

  def qldapm_lock_projects
    ids = [project_id, project_id_in_database].compact.uniq.sort
    ids.each { |identifier| self.class.connection.execute("SELECT pg_advisory_xact_lock(817609, #{Integer(identifier)})") }
  end

  def qldapm_serialized_save
    return yield unless qldapm_managed?
    self.class.transaction do
      qldapm_lock_projects
      yield
    end
  end

  def qldapm_validate_write
    return unless qldapm_managed?
    unless Qldapm::Rbac.pm?(project, User.current, fresh: true)
      if new_record? || (changed_with_custom_fields - %w[lock_version updated_at updated_on]).any?
        errors.add(:base, "QLDAPM_PM_REQUIRED")
        throw :abort
      end
      return
    end
      fresh = persisted? ? WorkPackage.find(id) : nil
      source_field = WorkPackageCustomField.find_by!(name: "Source ID")
      source_id = custom_value_for(source_field)&.value.to_s
      if source_id.empty? || (fresh && fresh.qldapm_gate["source_id"] && fresh.qldapm_gate["source_id"] != source_id)
        errors.add(:base, "QLDAPM_SOURCE_ID_REQUIRED_AND_IMMUTABLE")
        throw :abort
      end
      if WorkPackage.where(project_id:).where.not(id:).joins(:custom_values)
          .where(custom_values: {custom_field_id: source_field.id, value: source_id}).exists?
        errors.add(:base, "QLDAPM_DUPLICATE_SOURCE_ID")
        throw :abort
      end
      if fresh && fresh.project_id != project_id
        errors.add(:base, "QLDAPM_PROJECT_MOVE_REQUIRES_LOCAL_APPROVAL")
        throw :abort
      end
      if fresh && fresh.lock_version != lock_version
        errors.add(:base, "QLDAPM_STALE_WORK_PACKAGE")
        throw :abort
      end
      parents = [parent_id, parent_id_in_database].compact.uniq
      substantive = new_record? || (changes.keys & (TRACKED + %w[status_id qldapm_gate])).any?
      if substantive && WorkPackage.where(id: parents).joins(:status).where(statuses: {name: %w[REVIEW DONE]}).exists?
        errors.add(:base, "QLDAPM_PARENT_CLOSED_REOPEN_PARENT_FIRST")
        throw :abort
      end
      data = (qldapm_gate || {}).deep_dup
      before = fresh&.qldapm_gate || {}
      if fresh&.status&.name == "DONE" && status_id == fresh.status_id && substantive &&
          !(changes.keys == ["qldapm_gate"] && data.except("transition_reason", "events") == before.except("transition_reason", "events") &&
            data.fetch("events", []).last&.fetch("operation", nil) == "reason")
        errors.add(:base, "QLDAPM_REOPEN_BEFORE_EDIT")
        throw :abort
      end
      if (changes.keys & TRACKED).any? && !new_record?
        data["revision"] = before.fetch("revision", 0) + 1
        data["approvals"] = {}
      end
      if !new_record? && (changes.keys & %w[subject description]).any?
        actor = qldapm_actor
        data["contributors"] = (data.fetch("contributors", []) + [actor["id"]]).uniq if actor["role"]
      end
      data["revision"] ||= 0
      data["source_id"] ||= source_id
      data["checklist"] ||= []
      data["evidence"] ||= {}
      data["approvals"] ||= {}
      if type.name == "Subtask" && !data["stream"]
        assignee_role = qldapm_actor(assigned_to)["role"] if assigned_to.is_a?(User)
        data["stream"] = %w[BE FE].include?(assignee_role) ? "development" : "business"
        data["kind"] = assignee_role == "QA" ? "qa" : "work"
      end
      self.qldapm_gate = data
      if new_record? && status.name != "NEW"
        errors.add(:base, "QLDAPM_CREATE_IN_NEW_ONLY")
        throw :abort
      end
      if fresh && status_id != fresh.status_id
        policy = Qldapm::GatePolicy.new
        # Permissions and independence must still hold when the transition is executed.
        data["approvals"].delete_if do |key, record|
          reviewer = User.active.find_by(id: record["actor_id"])
          !reviewer || !policy.can_approve?(qldapm_snapshot, qldapm_actor(reviewer), key)
        end
        failures = policy.errors(qldapm_snapshot, qldapm_actor, fresh.status.name, status.name)
        if status.name == "CODE REVIEW"
          reviewer = User.active.find_by(id: data["reviewer_id"])
          failures << "ACTIVE_CODE_REVIEWER_REQUIRED" unless reviewer && policy.can_approve?(qldapm_snapshot, qldapm_actor(reviewer), "code")
        end
        failures.each { |message| errors.add(:base, "QLDAPM_#{message}") }
        throw :abort if failures.any?
        data.delete("transition_reason")
        self.qldapm_gate = data
      end
  end

  def qldapm_guard_destroy
    return unless qldapm_managed?
    unless Qldapm::Rbac.pm?(project, User.current, fresh: true)
      errors.add(:base, "QLDAPM_PM_REQUIRED")
      throw :abort
    end
    qldapm_lock_projects
    unless Thread.current[:qldapm_approved_delete] == id
      errors.add(:base, "QLDAPM_DELETE_REQUIRES_LOCAL_APPROVAL")
      throw :abort
    end
    parents = [parent_id, WorkPackage.where(id:).pick(:parent_id)].compact.uniq
    if WorkPackage.where(id: parents).joins(:status).where(statuses: {name: %w[REVIEW DONE]}).exists?
      errors.add(:base, "QLDAPM_PARENT_CLOSED_REOPEN_PARENT_FIRST")
      throw :abort
    end
  end
end
