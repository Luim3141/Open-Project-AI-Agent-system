require 'digest'
require 'json'

module Qldapm
  # Reads the existing final transition; never creates approval or changes workflow policy.
  class ObserverAcceptance
    def self.last_transition(journals, status_id)
      transition = nil
      journals.each_cons(2) do |previous, current|
        next unless previous.data && current.data
        if previous.data.status_id != current.data.status_id
          transition = current.data.status_id == status_id ? [previous, current] : nil
        end
      end
      transition
    end

    def self.call(user, identifier)
      item = WorkPackage.visible(user).find(identifier)
      project = item.project
      raise ArgumentError, 'OBSERVER_PROJECT_DENIED' unless [5, 6].include?(project.id) &&
        {5 => 'qldapm-local', 6 => 'ai-dev-demo'}[project.id] == project.identifier
      raise ArgumentError, 'OBSERVER_NATIVE_READ_DENIED' unless user.allowed_in_work_package?(:view_work_packages, item) && Rbac.role(project, user, fresh: true)
      journals = item.journals.includes(:data).reorder(version: :desc).limit(200).to_a.reverse
      pair = last_transition(journals, item.status_id)
      change = nil
      if pair
        previous, journal = pair
        actor = User.active.find_by(id: journal.user_id)
        role = actor && Rbac.role(project, actor, fresh: true)
        change = {'journal_id' => journal.id, 'journal_version' => journal.version,
                  'actor_id' => journal.user_id, 'current_actor_role' => role,
                  'at' => journal.created_at.to_f, 'from_status_id' => previous.data.status_id,
                  'to_status_id' => journal.data.status_id,
                  'provenance' => 'NATIVE_JOURNAL_AUTHOR_CURRENT_ROLE_RECHECKED'}
      end
      closed = item.status.is_closed? && item.status.name == 'DONE'
      errors = []
      if item.qldapm_managed? && closed && pair
        actor = User.active.find_by(id: pair.last.user_id)
        errors = actor ? GatePolicy.new.errors(item.qldapm_snapshot, item.qldapm_actor(actor), Status.find(pair.first.data.status_id).name, 'DONE') : ['APPROVER_REVOKED']
      end
      latest_matches = journals.last&.data&.status_id == item.status_id
      verified = closed && latest_matches && change && %w[PM AI_SYSTEM_OWNER].include?(change['current_actor_role']) &&
        !%w[import system_update].include?(pair.last.cause_type) && errors.empty?
      {'task_id' => item.id, 'project_id' => project.id, 'lock_version' => item.lock_version,
       'status_id' => item.status_id, 'status_name' => item.status.name, 'is_closed' => item.status.is_closed?,
       'verified' => !!verified, 'status_change' => change, 'gate_errors' => errors,
       'gate_policy' => item.qldapm_managed? ? 'EXISTING_NATIVE_GATE_POLICY' : 'ENGINEERING_RUNTIME_GATES_REQUIRED',
       'source_hash' => Digest::SHA256.hexdigest(JSON.generate([item.id, item.lock_version, item.status_id, change])),
       'history_truncated' => journals.length >= 200, 'observed_at' => Time.now.to_f}
    end
  end
end
