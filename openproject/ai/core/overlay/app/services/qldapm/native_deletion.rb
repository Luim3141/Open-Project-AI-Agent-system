require_relative 'dependency_mutation'

module Qldapm
  class NativeDeletion < DependencyMutation
    DOMAIN="qldapm.native-delete.v1\0".freeze

    def self.validate!(payload, approved: true)
      fields=%w[id lock_version]+(approved ? %w[snapshot_sha256 proposal_id proposal_hash request_id] : [])
      raise ArgumentError, 'NATIVE_DELETE_FIELDS_DENIED' unless payload.is_a?(Hash) && payload.keys.sort==fields.sort
      raise ArgumentError, 'NATIVE_DELETE_ID_VERSION_INVALID' unless payload['id'].is_a?(Integer) && payload['id'].positive? && payload['lock_version'].is_a?(Integer) && payload['lock_version']>=0
      return unless approved
      raise ArgumentError, 'NATIVE_DELETE_PROPOSAL_INVALID' unless %w[snapshot_sha256 proposal_hash].all? { |key| payload[key].is_a?(String) && payload[key].match?(SHA) } && payload['proposal_id'].is_a?(String) && payload['proposal_id'].match?(UUID)
      raise ArgumentError, 'NATIVE_DELETE_REQUEST_INVALID' unless payload['request_id'].is_a?(String) && payload['request_id'].match?(/\AQLDAPM-request-[a-f0-9]{64}\z/)
    end

    def self.authorize!(user)
      project=Project.visible(user).find(5)
      raise ArgumentError, 'NATIVE_DELETE_MAIN_MANAGER_REQUIRED' unless project.identifier=='qldapm-local' && user.active? && Rbac.pm?(project,user,fresh:true) && user.allowed_in_project?(:delete_work_packages,project)
      raise ArgumentError, 'NATIVE_DELETE_SCHEMA_NOT_INSTALLED' unless NativeDeletionEvent.table_exists?
      project
    end

    def self.eligible!(user,item,payload)
      raise ArgumentError, 'NATIVE_DELETE_PROJECT_DENIED' unless item.project_id==5 && user.allowed_in_project?(:delete_work_packages,item.project)
      raise ArgumentError, 'NATIVE_DELETE_STALE_SOURCE' unless item.lock_version==payload['lock_version']
      # Bound the first contract to a new, independent Task; no cascade or history reference removal.
      raise ArgumentError, 'NATIVE_DELETE_NEW_ORPHAN_TASK_REQUIRED' unless item.type.name=='Task' && item.status.name=='NEW' && item.parent_id.nil? && !item.children.exists? && !Relation.where(from_id:item.id).or(Relation.where(to_id:item.id)).exists? && !MutationReceipt.where(work_package_id:item.id).exists? && item.qldapm_gate['qa_bridge'].nil?
      raise ArgumentError, 'NATIVE_DELETE_EXISTING_ACTIVITY_OR_ATTACHMENT_HOLD' if item.journals.count>1 || item.attachments.exists? || item.time_entries.exists?
      contract=WorkPackages::DeleteContract.new(item,user)
      raise ArgumentError, contract.errors.full_messages.join('; ') unless contract.valid?
    end

    def self.source_hash(item)
      fingerprint({'native'=>QaEvidenceReceipt.native_snapshot(item),'attributes'=>item.attributes,
        'journals'=>item.journals.order(:id).map(&:attributes),'custom_values'=>item.custom_values.order(:id).map(&:attributes)})
    end

    def self.plan(user,payload)
      validate!(payload,approved:false);authorize!(user)
      item=WorkPackage.visible(user).find(payload['id']);eligible!(user,item,payload)
      {'id'=>item.id,'project_id'=>5,'lock_version'=>item.lock_version,'subject'=>item.subject,
       'snapshot_sha256'=>source_hash(item),
       'permanent_delete'=>true,'cascade'=>false,
       'notice'=>'Permanently delete exactly this NEW independent Task and its Native-owned content; preserve a signed tombstone. No other Work Package is deleted.'}
    end

    def self.receipt(user,request_id)
      authorize!(user)
      raise ArgumentError, 'NATIVE_DELETE_REQUEST_INVALID' unless request_id.is_a?(String) && request_id.match?(/\AQLDAPM-request-[a-f0-9]{64}\z/)
      NativeDeletionEvent.find_by!(project_id:5,user_id:user.id,request_id:request_id).result
    end

    def self.call(user,payload,headers)
      verify_signature!(user,payload,headers);authorize!(user)
      WorkPackage.transaction do
        WorkPackage.connection.execute('SELECT pg_advisory_xact_lock(817609,5)')
        authorize!(user)
        event=NativeDeletionEvent.find_by(project_id:5,user_id:user.id,request_id:payload['request_id'])
        if event
          raise ArgumentError, 'NATIVE_DELETE_IDEMPOTENCY_KEY_REUSED' unless event.request_hash==fingerprint(payload)
          return event.result
        end
        item=WorkPackage.visible(user).lock.find(payload['id']);eligible!(user,item,payload)
        raise ArgumentError, 'NATIVE_DELETE_STALE_SOURCE_HASH' unless source_hash(item)==payload['snapshot_sha256']
        before=WorkPackage.where.not(id:item.id).order(:id).map(&:attributes)
        previous=Thread.current[:qldapm_approved_delete]
        begin
          # Only this verified, exact approved bridge may satisfy the existing destroy guard.
          Thread.current[:qldapm_approved_delete]=item.id
          result=Journal::NotificationConfiguration.with(false) { WorkPackages::DeleteService.new(user:,model:item).call(delete_descendants:false) }
        ensure
          Thread.current[:qldapm_approved_delete]=previous
        end
        raise ArgumentError, result.errors.full_messages.join('; ') unless result.success?
        raise ArgumentError, 'NATIVE_DELETE_NOT_PERSISTED' if WorkPackage.exists?(item.id)
        raise ArgumentError, 'NATIVE_DELETE_UNEXPECTED_WORK_PACKAGE_CHANGE' unless before==WorkPackage.order(:id).map(&:attributes)
        document={'schema'=>'QLDAPM_NATIVE_DELETE_V1','producer'=>'qldapm-native-delete-v1','event_id'=>SecureRandom.uuid,
          'project_id'=>5,'native_id'=>payload['id'],'source_version'=>payload['lock_version'],'snapshot_sha256'=>payload['snapshot_sha256'],
          'actor_id'=>user.id,'proposal_id'=>payload['proposal_id'],'proposal_hash'=>payload['proposal_hash'],
          'request_id'=>payload['request_id'],'request_hash'=>fingerprint(payload),'deleted_at'=>Time.now.utc.iso8601(6)}
        encoded=JSON.generate(Mutations.canonical(document));key=File.binread(ENV.fetch('QLDAPM_UI_KEY_FILE','/qldapm-ui/ui.key'))
        body={'document'=>encoded,'signature'=>OpenSSL::HMAC.hexdigest('SHA256',key,DOMAIN+encoded)}
        NativeDeletionEvent.create!(project_id:5,user_id:user.id,native_id:payload['id'],source_version:payload['lock_version'],
          event_id:document['event_id'],request_id:payload['request_id'],request_hash:fingerprint(payload),result:body)
        body
      end
    end
  end
end
