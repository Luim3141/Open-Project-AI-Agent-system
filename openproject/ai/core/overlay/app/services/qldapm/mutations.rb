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
      qa_requested=payload.key?('qa_proof') || payload.key?('qa_authorization')
      phase_requested=payload.key?('phase_proof') || payload.key?('phase_authorization')
      raise ArgumentError,'ONE_NATIVE_PROOF_DOMAIN_REQUIRED' if qa_requested && phase_requested
      raise ArgumentError, "PM_REQUIRED" unless item.qldapm_managed? && Qldapm::Rbac.pm?(item.project, user, fresh:qa_requested || phase_requested)
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
      if qa_requested
        raise ArgumentError, 'QA_GATEWAY_SIGNATURE_REQUIRED' unless provenance == 'ai_gateway'
        raise ArgumentError, 'QA_PROOF_AND_AUTHORIZATION_REQUIRED' unless payload['qa_proof'].is_a?(Hash) && payload['qa_authorization'].is_a?(Hash)
        raise ArgumentError, 'QA_TRANSITION_ONLY' unless payload['action'] == 'transition'
        authorization=payload['qa_authorization']
        raise ArgumentError, 'QA_APPROVED_REQUEST_BINDING_REQUIRED' unless authorization.keys.sort == %w[proposal_hash proposal_id qa_evidence_hash qa_evidence_id] &&
          authorization['proposal_id'].is_a?(String) && authorization['proposal_id'].match?(QaEvidenceReceipt::UUID) &&
          authorization['proposal_hash'].is_a?(String) && authorization['proposal_hash'].match?(QaEvidenceReceipt::SHA) &&
          authorization['qa_evidence_id'].is_a?(String) && authorization['qa_evidence_id'].match?(QaEvidenceReceipt::UUID) &&
          authorization['qa_evidence_hash'].is_a?(String) && authorization['qa_evidence_hash'].match?(QaEvidenceReceipt::SHA) &&
          payload['request_id'] == 'QLDAPM-request-'+Digest::SHA256.hexdigest("#{user.id}:proposal-#{authorization['proposal_id']}")
      end
      if phase_requested
        raise ArgumentError,'PHASE_GATEWAY_SIGNATURE_REQUIRED' unless provenance=='ai_gateway'
        phase_authorization=NativePhaseReceipt.authorization!(payload,user)
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
        qa_receipt=nil
        phase_receipt=nil
        if phase_requested
          phase_receipt=NativePhaseReceipt.preview(payload['phase_proof'],item,user,payload.fetch('status_id'),payload.fetch('lock_version'))
          raise ArgumentError,'PHASE_EXACT_APPROVED_BINDING_REQUIRED' unless phase_receipt['id']==phase_authorization['phase_id'] && phase_receipt['hash']==phase_authorization['phase_hash']
          item.qldapm_gate=phase_receipt['data']
          (item.qldapm_gate['events'] ||= []) << {'operation'=>'native_source_phase_transition','actor_id'=>user.id,
            'revision'=>item.qldapm_gate.fetch('revision',0),'source_version'=>phase_receipt['source_version'],
            'request_id'=>payload['request_id'],'request_hash'=>command_hash,'proposal_id'=>phase_authorization['proposal_id'],
            'proposal_hash'=>phase_authorization['proposal_hash'],'phase_id'=>phase_receipt['id'],'phase_hash'=>phase_receipt['hash']}
          User.execute_as(user) { raise ArgumentError,item.errors.full_messages.join('; ') unless item.save }
        end
        if qa_requested
          destination=::Status.find(Integer(payload.fetch('status_id'))).name
          preflight=QaEvidenceReceipt.preflight(payload['qa_proof'],item,user,destination)
          raise ArgumentError, preflight['errors'].join('; ') unless preflight['valid']
          qa_receipt=QaEvidenceReceipt.verify(payload['qa_proof'],item,user,destination)
          raise ArgumentError, 'QA_EXACT_APPROVED_EVIDENCE_BINDING_REQUIRED' unless qa_receipt['evidence_id']==authorization['qa_evidence_id'] &&
            qa_receipt['hash']==authorization['qa_evidence_hash']
          item.qldapm_gate=qa_receipt['data']
          item.qldapm_gate['events'] ||= []
          item.qldapm_gate['events'] << {'operation'=>'automated_qa_transition','actor_id'=>user.id,
            'revision'=>item.qldapm_gate.fetch('revision',0),'source_version'=>qa_receipt['source_version'],
            'request_id'=>payload['request_id'],'request_hash'=>command_hash,'proposal_id'=>authorization['proposal_id'],
            'proposal_hash'=>authorization['proposal_hash'],'qa_evidence_id'=>qa_receipt['evidence_id'],'qa_hash'=>qa_receipt['hash']}
          # Both saves share the transaction/project lock; a rejected transition rolls back both journals.
          User.execute_as(user) { raise ArgumentError, item.errors.full_messages.join('; ') unless item.save }
        end
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
        if qa_receipt
          body['qa_native']={'evidence_id'=>qa_receipt['evidence_id'],'hash'=>qa_receipt['hash'],
            'source_version'=>qa_receipt['source_version'],'artifact_sha256'=>item.qldapm_gate.dig('qa_bridge','artifact_sha256')}
        end
        if phase_receipt
          body['phase_native']={'id'=>phase_receipt['id'],'hash'=>phase_receipt['hash'],'source_version'=>phase_receipt['source_version'],
            'kind'=>phase_receipt['kind'],'gate_revision'=>item.qldapm_gate.fetch('revision',0),'status_id'=>item.status_id,
            'proposal_id'=>phase_authorization['proposal_id'],'proposal_hash'=>phase_authorization['proposal_hash']}
        end
        MutationReceipt.create!(project_id: item.project_id, user_id: user.id, work_package: item,
          journal_id: item.journals.order(:version).last&.id, request_id: payload["request_id"], request_hash: command_hash, provenance:, result: body)
        body
      end
    end
  end
end
