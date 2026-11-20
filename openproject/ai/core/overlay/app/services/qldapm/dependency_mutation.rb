require 'json'
require 'digest'
require 'openssl'

module Qldapm
  class DependencyMutation
    INPUT = %w[predecessor_id successor_id lag].freeze
    APPROVED = (INPUT + %w[scope_hash proposal_id proposal_hash request_id]).freeze
    SHA = /\A[a-f0-9]{64}\z/
    UUID = /\A[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\z/
    SCHEDULE_FIELDS = %w[start_date due_date duration schedule_manually lock_version updated_at updated_on].freeze

    def self.canonical(value)
      case value
      when Hash then value.keys.sort.to_h { |key| [key, canonical(value[key])] }
      when Array then value.map { |entry| canonical(entry) }
      else value
      end
    end

    def self.fingerprint(value)
      Digest::SHA256.hexdigest(JSON.generate(canonical(value)))
    end

    def self.validate!(payload, approved: true)
      raise ArgumentError, 'DEPENDENCY_FIELDS_DENIED' unless payload.is_a?(Hash) && payload.keys.sort == (approved ? APPROVED : INPUT).sort
      raise ArgumentError, 'DEPENDENCY_IDS_INVALID' unless %w[predecessor_id successor_id].all? { |key| payload[key].is_a?(Integer) && payload[key].positive? } && payload['predecessor_id'] != payload['successor_id']
      raise ArgumentError, 'DEPENDENCY_LAG_INVALID' unless payload['lag'].is_a?(Integer) && (-2000..2000).cover?(payload['lag'])
      return unless approved
      raise ArgumentError, 'DEPENDENCY_APPROVAL_INVALID' unless %w[scope_hash proposal_hash].all? { |key| payload[key].is_a?(String) && payload[key].match?(SHA) } && payload['proposal_id'].is_a?(String) && payload['proposal_id'].match?(UUID)
      raise ArgumentError, 'DEPENDENCY_REQUEST_INVALID' unless payload['request_id'].is_a?(String) && payload['request_id'].match?(/\AQLDAPM-request-[a-f0-9]{64}\z/)
    end

    def self.verify_signature!(user, payload, headers)
      validate!(payload)
      raise ArgumentError, 'DEPENDENCY_APPROVED_ACTOR_BINDING_REQUIRED' unless payload['request_id'] == 'QLDAPM-request-'+Digest::SHA256.hexdigest("#{user.id}:proposal-#{payload['proposal_id']}")
      at = headers['X-Qldapm-At'].to_s
      signature = headers['X-Qldapm-Mutation'].to_s
      path = ENV.fetch('QLDAPM_UI_KEY_FILE', '/qldapm-ui/ui.key')
      raise ArgumentError, 'DEPENDENCY_SIGNATURE_EXPIRED_OR_MISSING' unless at.match?(/\A[0-9]{10}\z/) && (Time.now.to_i-at.to_i).abs <= 30 && File.file?(path) && signature.match?(SHA)
      expected = OpenSSL::HMAC.hexdigest('SHA256', File.binread(path), "#{user.id}:#{at}:#{fingerprint(payload)}")
      raise ArgumentError, 'DEPENDENCY_SIGNATURE_DENIED' unless OpenSSL.fixed_length_secure_compare(signature, expected)
    end

    def self.endpoints(user, payload)
      items = %w[predecessor_id successor_id].map { |key| WorkPackage.visible(user).find(payload[key]) }
      project = items.first.project
      raise ArgumentError, 'DEPENDENCY_NATIVE_MAIN_MANAGER_REQUIRED' unless project.id == 5 && project.identifier == 'qldapm-local' && items.all? { |item| item.project_id == project.id } && Rbac.pm?(project, user, fresh: true)
      raise ArgumentError, 'DEPENDENCY_NATIVE_PERMISSION_REQUIRED' unless items.all? { |item| user.allowed_in_work_package?(:manage_work_package_relations,item) && user.allowed_in_work_package?(:edit_work_packages,item) }
      items
    end

    def self.state(item)
      {'attributes'=>item.attributes, 'parent_id'=>item.parent_id}
    end

    def self.scope(user, predecessor, successor)
      all = WorkPackage.where(project_id: successor.project_id).includes(:parent).order(:id).limit(2001).to_a
      raise ArgumentError, 'DEPENDENCY_PROJECT_TOO_LARGE' if all.size > 2000
      by_id = all.index_by(&:id)
      ids = [predecessor.id, successor.id]
      loop do
        expanded = ids + ids.filter_map { |id| by_id.fetch(id).parent_id } + all.filter_map { |item| item.id if ids.include?(item.parent_id) }
        expanded += Relation.follows.where(to_id: ids).pluck(:from_id)
        expanded = expanded.uniq.sort
        raise ArgumentError, 'DEPENDENCY_CROSS_PROJECT_SCHEDULE_DENIED' unless (expanded-by_id.keys).empty?
        break if expanded == ids.sort
        ids = expanded
      end
      visible = WorkPackage.visible(user).where(id: ids).pluck(:id)
      raise ArgumentError, 'DEPENDENCY_SCOPE_NOT_AUTHORIZED' unless visible.sort == ids.sort && ids.all? { |id| user.allowed_in_work_package?(:edit_work_packages,by_id.fetch(id)) }
      relations = Relation.where(from_id: ids).or(Relation.where(to_id: ids)).order(:id).map(&:attributes)
      document = {'project_id'=>successor.project_id,'work_packages'=>ids.to_h { |id| [id.to_s,state(by_id.fetch(id))] }, 'relations'=>relations}
      {'hash'=>fingerprint(document), 'items'=>ids.map { |id| item=by_id.fetch(id); {'id'=>id,'lockVersion'=>item.lock_version,'startDate'=>item.start_date&.iso8601,'dueDate'=>item.due_date&.iso8601,'scheduleManually'=>item.schedule_manually,'parent_id'=>item.parent_id} }, 'document'=>document}
    end

    def self.plan(user, payload)
      validate!(payload, approved: false)
      WorkPackage.transaction do
        predecessor, successor = endpoints(user,payload)
        successor.qldapm_lock_projects
        predecessor, successor = endpoints(user,payload)
        relation = Relation.new(from: successor,to: predecessor,relation_type: 'follows',lag: payload['lag'])
        contract = Relations::CreateContract.new(relation,user)
        raise ArgumentError, contract.errors.full_messages.join('; ') unless contract.valid?
        snapshot = scope(user,predecessor,successor)
        {'project_id'=>5,'predecessor_id'=>predecessor.id,'successor_id'=>successor.id,'type'=>'follows','lag'=>payload['lag'],
         'scope_hash'=>snapshot['hash'],'possible_affected'=>snapshot['items'],
         'notice'=>'Possible affected scope, not predicted dates. Native scheduling is authoritative; manual leaves can retain their dates.'}
      end
    end

    def self.call(user, payload, headers)
      verify_signature!(user,payload,headers)
      WorkPackage.transaction do
        predecessor, successor = endpoints(user,payload)
        successor.qldapm_lock_projects
        predecessor, successor = endpoints(user,payload)
        receipt = MutationReceipt.find_by(project_id:5,user_id:user.id,request_id:payload['request_id'])
        if receipt
          raise ArgumentError, 'DEPENDENCY_IDEMPOTENCY_KEY_REUSED' unless receipt.request_hash == fingerprint(payload) && receipt.work_package_id == successor.id
          return receipt.result
        end
        snapshot = scope(user,predecessor,successor)
        raise ArgumentError, 'DEPENDENCY_STALE_APPROVED_SCOPE' unless snapshot['hash'] == payload['scope_hash']
        before = WorkPackage.where(project_id:5).includes(:parent).index_by(&:id).transform_values { |item| state(item) }
        result = Relations::CreateService.new(user:).call(from:successor,to:predecessor,relation_type:'follows',lag:payload['lag'],send_notifications:false)
        raise ArgumentError, result.errors.full_messages.join('; ') unless result.success?
        after = WorkPackage.where(project_id:5).includes(:parent).index_by(&:id)
        raise ArgumentError, 'DEPENDENCY_UNEXPECTED_NATIVE_RESOURCE' unless before.keys.sort == after.keys.sort
        changed = before.keys.select { |id| before[id] != state(after.fetch(id)) }
        approved_ids = snapshot['items'].map { |item| item['id'] }
        raise ArgumentError, 'DEPENDENCY_OUTSIDE_APPROVED_SCOPE' unless (changed-approved_ids).empty?
        changed.each do |id|
          old = before.fetch(id); current = state(after.fetch(id))
          keys = (old['attributes'].keys | current['attributes'].keys).select { |key| old['attributes'][key] != current['attributes'][key] }
          raise ArgumentError, 'DEPENDENCY_UNEXPECTED_NATIVE_FIELDS' unless (keys-SCHEDULE_FIELDS).empty? && old['parent_id'] == current['parent_id']
        end
        relation = result.result
        raise ArgumentError, 'DEPENDENCY_NATIVE_RELATION_MISMATCH' unless relation.persisted? && relation.from_id == successor.id && relation.to_id == predecessor.id && relation.relation_type == 'follows' && relation.lag == payload['lag']
        successor.reload
        body = {'id'=>successor.id,'lockVersion'=>successor.lock_version,'request_id'=>payload['request_id'],'provenance'=>'ai_gateway',
                'proposal_id'=>payload['proposal_id'],'proposal_hash'=>payload['proposal_hash'],'scope_hash'=>payload['scope_hash'],
                'relation'=>{'id'=>relation.id,'type'=>'follows','predecessor_id'=>predecessor.id,'successor_id'=>successor.id,'lag'=>relation.lag},
                'changed_ids'=>changed.sort,'readback'=> (changed+[predecessor.id,successor.id]).uniq.sort.map { |id| item=after.fetch(id); {'id'=>id,'lockVersion'=>item.lock_version,'startDate'=>item.start_date&.iso8601,'dueDate'=>item.due_date&.iso8601,'scheduleManually'=>item.schedule_manually} }}
        MutationReceipt.create!(project_id:5,user_id:user.id,work_package:successor,journal_id:successor.journals.order(:version).last&.id,
                                request_id:payload['request_id'],request_hash:fingerprint(payload),provenance:'ai_gateway',result:body)
        body
      end
    end
  end
end
