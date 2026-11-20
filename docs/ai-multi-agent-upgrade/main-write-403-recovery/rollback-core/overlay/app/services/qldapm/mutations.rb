require "openssl"
require "digest"

module Qldapm
  class Mutations
    def self.canonical(value)
      case value
      when Hash then value.keys.sort.to_h { |key| [key, canonical(value[key])] }
      when Array then value.map { |entry| canonical(entry) }
      else value
      end
    end

    def self.call(item, user, payload, headers)
      raise ArgumentError, "PM_REQUIRED" unless item.qldapm_managed? && Qldapm::Rbac.pm?(item.project, user)
      raise ArgumentError, "EDIT_DENIED" unless user.allowed_in_work_package?(:edit_work_packages, item)
      raise ArgumentError, "MUTATION_ACTION_DENIED" unless %w[update_work_package transition].include?(payload["action"])
      raise ArgumentError, "REQUEST_ID_DENIED" unless payload["request_id"].to_s.match?(/\AQLDAPM-request-[a-f0-9]{64}\z/)
      command_hash = Digest::SHA256.hexdigest(JSON.generate(canonical(payload.merge("id" => item.id))))
      at = headers["X-Qldapm-At"].to_i
      signature = headers["X-Qldapm-Mutation"].to_s
      key_path = ENV.fetch("QLDAPM_UI_KEY_FILE", "/qldapm-ui/ui.key")
      provenance = "unknown"
      if !signature.empty?
        raise ArgumentError, "AI_SIGNATURE_EXPIRED" if (Time.now.to_i - at).abs > 30 || !File.file?(key_path)
        expected = OpenSSL::HMAC.hexdigest("SHA256", File.binread(key_path), "#{user.id}:#{at}:#{command_hash}")
        raise ArgumentError, "AI_SIGNATURE_DENIED" unless ActiveSupport::SecurityUtils.secure_compare(signature, expected)
        provenance = "ai_gateway"
      end
      WorkPackage.transaction do
        item.qldapm_lock_projects
        item.reload
        receipt = MutationReceipt.find_by(project_id: item.project_id, user_id: user.id, request_id: payload["request_id"])
        if receipt
          raise ArgumentError, "IDEMPOTENCY_KEY_REUSED" unless receipt.request_hash == command_hash && receipt.work_package_id == item.id
          return receipt.result
        end
        raise ArgumentError, "STALE_WORK_PACKAGE" unless item.lock_version == Integer(payload.fetch("lock_version"))
        attributes = {lock_version: item.lock_version}
        if payload["action"] == "transition"
          attributes[:status_id] = Integer(payload.fetch("status_id"))
        else
          changes = payload.fetch("changes")
          raise ArgumentError, "CHANGES_DENIED" unless (changes.keys - %w[subject description assignee_id start_date due_date priority_id]).empty?
          attributes.merge!(changes.slice("subject", "description", "start_date", "due_date", "priority_id").symbolize_keys)
          attributes[:assigned_to_id] = Integer(changes["assignee_id"]) if changes.key?("assignee_id")
        end
        result = WorkPackages::UpdateService.new(user:, model: item).call(attributes)
        raise ArgumentError, result.errors.full_messages.join("; ") unless result.success?
        item.reload
        body = {"id" => item.id, "lockVersion" => item.lock_version, "request_id" => payload["request_id"], "provenance" => provenance}
        MutationReceipt.create!(project_id: item.project_id, user_id: user.id, work_package: item,
          journal_id: item.journals.order(:version).last&.id, request_id: payload["request_id"], request_hash: command_hash, provenance:, result: body)
        body
      end
    end
  end
end
