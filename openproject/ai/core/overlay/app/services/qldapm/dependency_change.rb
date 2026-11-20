require_relative 'dependency_mutation'

module Qldapm
  class DependencyChange < DependencyMutation
    def self.validate!(payload, approved: true)
      operation=payload.is_a?(Hash) && payload['operation']
      raise ArgumentError, 'DEPENDENCY_CHANGE_OPERATION_INVALID' unless %w[update delete].include?(operation)
      fields=%w[operation relation_id]+(operation=='update' ? %w[lag] : [])
      fields+=%w[predecessor_id successor_id scope_hash proposal_id proposal_hash request_id] if approved
      raise ArgumentError, 'DEPENDENCY_CHANGE_FIELDS_DENIED' unless payload.keys.sort==fields.sort
      ids=%w[relation_id]+(approved ? %w[predecessor_id successor_id] : [])
      raise ArgumentError, 'DEPENDENCY_CHANGE_IDS_INVALID' unless ids.all? { |key| payload[key].is_a?(Integer) && payload[key].positive? }
      if operation=='update'
        raise ArgumentError, 'DEPENDENCY_LAG_INVALID' unless payload['lag'].is_a?(Integer) && (-2000..2000).cover?(payload['lag'])
      end
      return unless approved
      raise ArgumentError, 'DEPENDENCY_CHANGE_ENDPOINTS_INVALID' if payload['predecessor_id']==payload['successor_id']
      raise ArgumentError, 'DEPENDENCY_APPROVAL_INVALID' unless %w[scope_hash proposal_hash].all? { |key| payload[key].is_a?(String) && payload[key].match?(SHA) } && payload['proposal_id'].is_a?(String) && payload['proposal_id'].match?(UUID)
      raise ArgumentError, 'DEPENDENCY_REQUEST_INVALID' unless payload['request_id'].is_a?(String) && payload['request_id'].match?(/\AQLDAPM-request-[a-f0-9]{64}\z/)
    end

    def self.relation(user,payload)
      item=Relation.visible(user).find(payload['relation_id'])
      raise ArgumentError, 'DEPENDENCY_FOLLOWS_RELATION_REQUIRED' unless item.relation_type=='follows'
      item
    end

    def self.change_endpoints(user,payload,item)
      predecessor,successor=endpoints(user,{'predecessor_id'=>item.to_id,'successor_id'=>item.from_id})
      if payload.key?('predecessor_id') && (payload['predecessor_id']!=predecessor.id || payload['successor_id']!=successor.id)
        raise ArgumentError, 'DEPENDENCY_CHANGE_ENDPOINTS_CHANGED'
      end
      [predecessor,successor]
    end

    def self.validate_contract!(user,payload,item)
      if payload['operation']=='update'
        item.lag=payload['lag'];contract=Relations::UpdateContract.new(item,user)
      else
        contract=Relations::DeleteContract.new(item,user)
      end
      raise ArgumentError, contract.errors.full_messages.join('; ') unless contract.valid?
    end

    def self.plan(user,payload)
      validate!(payload,approved:false)
      WorkPackage.transaction do
        item=relation(user,payload);predecessor,successor=change_endpoints(user,payload,item)
        successor.qldapm_lock_projects
        item=relation(user,payload);predecessor,successor=change_endpoints(user,payload,item)
        old_lag=item.lag
        validate_contract!(user,payload,item)
        snapshot=scope(user,predecessor,successor)
        {'project_id'=>5,'operation'=>payload['operation'],'relation_id'=>item.id,'predecessor_id'=>predecessor.id,
         'successor_id'=>successor.id,'lag'=>payload.fetch('lag',item.lag),'before'=>{'lag'=>old_lag},'scope_hash'=>snapshot['hash'],
         'possible_affected'=>snapshot['items'],
         'notice'=>'Only this follows relation changes. Native may reschedule the exact bounded source scope; no Work Package deletion.'}
      end
    end

    def self.call(user,payload,headers)
      verify_signature!(user,payload,headers)
      WorkPackage.transaction do
        # Endpoints survive relation deletion, so a committed exact receipt remains readable on retry.
        predecessor,successor=endpoints(user,payload)
        successor.qldapm_lock_projects
        predecessor,successor=endpoints(user,payload)
        receipt=MutationReceipt.find_by(project_id:5,user_id:user.id,request_id:payload['request_id'])
        if receipt
          raise ArgumentError, 'DEPENDENCY_IDEMPOTENCY_KEY_REUSED' unless receipt.request_hash==fingerprint(payload) && receipt.work_package_id==successor.id
          return receipt.result
        end
        item=relation(user,payload);change_endpoints(user,payload,item)
        snapshot=scope(user,predecessor,successor)
        raise ArgumentError, 'DEPENDENCY_STALE_APPROVED_SCOPE' unless snapshot['hash']==payload['scope_hash']
        validate_contract!(user,payload,item)
        before=WorkPackage.where(project_id:5).includes(:parent).index_by(&:id).transform_values { |entry| state(entry) }
        prior_relations=Relation.order(:id).index_by(&:id).transform_values(&:attributes)
        lag=payload.fetch('lag',item.lag)
        # This Native UpdateService treats all call params as Relation attributes.
        result=Journal::NotificationConfiguration.with(false) do
          if payload['operation']=='update'
            Relations::UpdateService.new(user:,model:item).call(lag:lag)
          else
            Relations::DeleteService.new(user:,model:item).call
          end
        end
        raise ArgumentError, result.errors.full_messages.join('; ') unless result.success?
        current_relations=Relation.order(:id).index_by(&:id).transform_values(&:attributes)
        raise ArgumentError, 'DEPENDENCY_UNRELATED_RELATION_CHANGED' unless prior_relations.except(item.id)==current_relations.except(item.id)
        if payload['operation']=='delete'
          raise ArgumentError, 'DEPENDENCY_RELATION_DELETE_NOT_PERSISTED' if current_relations.key?(item.id)
        else
          current=Relation.find(item.id)
          raise ArgumentError, 'DEPENDENCY_NATIVE_RELATION_MISMATCH' unless current.from_id==successor.id && current.to_id==predecessor.id && current.relation_type=='follows' && current.lag==lag && current.description==prior_relations.fetch(item.id)['description']
        end
        after=WorkPackage.where(project_id:5).includes(:parent).index_by(&:id)
        raise ArgumentError, 'DEPENDENCY_UNEXPECTED_NATIVE_RESOURCE' unless before.keys.sort==after.keys.sort
        changed=before.keys.select { |identifier| before[identifier]!=state(after.fetch(identifier)) }
        raise ArgumentError, 'DEPENDENCY_OUTSIDE_APPROVED_SCOPE' unless (changed-snapshot['items'].map { |entry| entry['id'] }).empty?
        changed.each do |identifier|
          old=before.fetch(identifier);current=state(after.fetch(identifier))
          fields=(old['attributes'].keys | current['attributes'].keys).select { |key| old['attributes'][key]!=current['attributes'][key] }
          raise ArgumentError, 'DEPENDENCY_UNEXPECTED_NATIVE_FIELDS' unless (fields-SCHEDULE_FIELDS).empty? && old['parent_id']==current['parent_id']
        end
        successor.reload
        body={'id'=>successor.id,'lockVersion'=>successor.lock_version,'request_id'=>payload['request_id'],'provenance'=>'ai_gateway',
              'proposal_id'=>payload['proposal_id'],'proposal_hash'=>payload['proposal_hash'],'scope_hash'=>payload['scope_hash'],
              'operation'=>payload['operation'],'relation'=>{'id'=>item.id,'type'=>'follows','predecessor_id'=>predecessor.id,'successor_id'=>successor.id,'lag'=>lag},
              'changed_ids'=>changed.sort,'readback'=>(changed+[predecessor.id,successor.id]).uniq.sort.map { |identifier| entry=after.fetch(identifier);{'id'=>identifier,'lockVersion'=>entry.lock_version,'startDate'=>entry.start_date&.iso8601,'dueDate'=>entry.due_date&.iso8601,'scheduleManually'=>entry.schedule_manually} }}
        MutationReceipt.create!(project_id:5,user_id:user.id,work_package:successor,journal_id:successor.journals.order(:version).last&.id,
                                request_id:payload['request_id'],request_hash:fingerprint(payload),provenance:'ai_gateway',result:body)
        body
      end
    end
  end
end
