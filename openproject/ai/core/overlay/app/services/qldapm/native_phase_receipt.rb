require_relative 'mutations'
require_relative 'qa_evidence_receipt'

module Qldapm
  class NativePhaseReceipt
    DOMAIN="qldapm.native-phase-source.v1\0".freeze
    REVIEW_DOMAIN="qldapm.native-phase-review.v1\0".freeze
    FIELDS=%w[version id actor project_id kind source gate_revision created_at].freeze
    REVIEW_FIELDS=%w[artifact_id hash actor role decision kind approvals at].freeze

    def self.canonical(value) = JSON.generate(Mutations.canonical(value))

    def self.preview(packet,item,user,status_id,version,**options)
      raise ArgumentError,'PHASE_STALE_WORK_PACKAGE' unless version.is_a?(Integer) && version==item.lock_version
      raise ArgumentError,'PHASE_STATUS_ID_REQUIRED' unless status_id.is_a?(Integer) && status_id.positive?
      destination=::Status.find(status_id)
      unless WorkPackages::UpdateContract.new(item,user).assignable_statuses.where(id:destination.id).exists?
        raise ArgumentError,'PHASE_NATIVE_TRANSITION_DENIED'
      end
      preflight(packet,item,user,destination.name,**options).merge('status_id'=>destination.id,'lockVersion'=>item.lock_version)
    end

    def self.authorization!(payload,user)
      authorization=payload['phase_authorization']
      raise ArgumentError,'PHASE_APPROVED_REQUEST_REQUIRED' unless payload['phase_proof'].is_a?(Hash) && authorization.is_a?(Hash) &&
        authorization.keys.sort==%w[phase_hash phase_id proposal_hash proposal_id] &&
        %w[phase_id proposal_id].all? { |key| authorization[key].is_a?(String) && authorization[key].match?(QaEvidenceReceipt::UUID) } &&
        %w[phase_hash proposal_hash].all? { |key| authorization[key].is_a?(String) && authorization[key].match?(QaEvidenceReceipt::SHA) } &&
        payload['action']=='transition' && payload['request_id']=='QLDAPM-request-'+Digest::SHA256.hexdigest("#{user.id}:proposal-#{authorization['proposal_id']}")
      authorization
    end

    def self.preflight(packet,item,user,destination,key_file: ENV.fetch('QLDAPM_UI_KEY_FILE','/qldapm-ui/ui.key'))
      raise ArgumentError,'PHASE_NATIVE_MANAGER_REQUIRED' unless item.qldapm_managed? && item.project_id==5 &&
        Rbac.pm?(item.project,user,fresh:true) && user.allowed_in_work_package?(:edit_work_packages,item)
      raise ArgumentError,'PHASE_PACKET_SCHEMA' unless packet.is_a?(Hash) && packet.keys.sort==%w[artifact review version] &&
        packet['version'].is_a?(Integer) && packet['version']==1 && canonical(packet).bytesize<=131072 && File.file?(key_file)
      key=File.binread(key_file)
      document=QaEvidenceReceipt.signed(packet['artifact'],key,DOMAIN)
      review=QaEvidenceReceipt.signed(packet['review'],key,REVIEW_DOMAIN)
      raise ArgumentError,'PHASE_ARTIFACT_SCHEMA' unless document.keys.sort==FIELDS.sort && document['version']==1 &&
        document['version'].is_a?(Integer) && document['id'].is_a?(String) && document['id'].match?(QaEvidenceReceipt::UUID) &&
        document['actor'].is_a?(Integer) && document['project_id']==5 && %w[scope analysis].include?(document['kind'])
      raise ArgumentError,'PHASE_SOURCE_CHANGED' unless document['source']==QaEvidenceReceipt.native_snapshot(item) &&
        document['source']['id'].is_a?(Integer) && document['source']['version'].is_a?(Integer) &&
        document['gate_revision'].is_a?(Integer) && document['gate_revision']==item.qldapm_gate.fetch('revision',0)
      producer=User.active.find_by(id:document['actor'])
      raise ArgumentError,'PHASE_PRODUCER_REVOKED' unless producer && producer.allowed_in_work_package?(:view_work_packages,item) &&
        %w[BA-PM PM AI_SYSTEM_OWNER].include?(Rbac.role(item.project,producer,fresh:true))
      fingerprint=Digest::SHA256.hexdigest(canonical(document))
      approvals=document['kind']=='scope' ? %w[scope] : %w[scope analysis]
      raise ArgumentError,'PHASE_EXACT_ACCEPTED_REVIEW_REQUIRED' unless review.keys.sort==REVIEW_FIELDS.sort &&
        review['artifact_id']==document['id'] && review['hash']==fingerprint && review['decision']=='accept' && review['kind']==document['kind'] &&
        review['approvals']==approvals
      raise ArgumentError,'PHASE_TIMESTAMP_INVALID' unless [document['created_at'],review['at']].all? { |at| at.is_a?(Numeric) && at.finite? && at.between?(0,Time.now.to_f+30) } && review['at']>=document['created_at']
      reviewer=review['actor'].is_a?(Integer) && User.active.find_by(id:review['actor'])
      data=item.qldapm_gate.deep_dup
      raise ArgumentError,'PHASE_REVIEWER_NONINDEPENDENT_OR_REVOKED' unless reviewer &&
        reviewer.allowed_in_work_package?(:view_work_packages,item) &&
        Rbac.pm?(item.project,reviewer,fresh:true) && Rbac.role(item.project,reviewer,fresh:true)==review['role'] &&
        ![document['actor'],item.assigned_to_id,*data.fetch('contributors',[])].include?(review['actor'])
      description=item.description.to_s.gsub(/\r\n?/,"\n")
      criteria=description.scan(/^[ \t]*(AC[1-9][0-9]{0,3}):[ \t]+([^\r\n]+)$/)
      labels=description.scan(/^[ \t]*(AC[0-9]+):/).flatten
      raise ArgumentError,'PHASE_UNIQUE_AC_REQUIRED' unless criteria.length.between?(1,100) && criteria.all? { |_,text| !text.strip.empty? } && criteria.map(&:first).uniq.length==criteria.length && criteria.map(&:first)==labels
      ac=criteria.map { |id,text| "#{id}: #{text}" }.join("\n")
      if data['acceptance_criteria']!=ac
        data['revision']=data.fetch('revision',0)+1;data['approvals']={};data['acceptance_criteria']=ac
      end
      data['approvals']={}
      data['contributors']=(data.fetch('contributors',[])+[document['actor']]).uniq
      data['reviewer_id'] ||= review['actor']
      kind=document['kind'];keys=kind=='scope' ? %w[story scope] : %w[story scope analysis]
      record={'revision'=>data.fetch('revision',0),'reference'=>"qldapm-native-phase:#{document['id']}:#{fingerprint}",
        'actor_id'=>document['actor'],'role'=>Rbac.role(item.project,producer,fresh:true),'source_version'=>item.lock_version}
      data['evidence'] ||= {}
      keys.each do |name|
        raise ArgumentError,"PHASE_NATIVE_#{name.upcase}_REQUIRED" unless description.match?(/^[ \t]*#{Regexp.escape(name.capitalize)}:[ \t]+\S[^\r\n]*$/)
        (data['evidence'][name] ||= []) << record
      end
      snapshot=item.qldapm_snapshot.merge('data'=>data)
      policy=GatePolicy.new
      approvals.each do |approval|
        raise ArgumentError,'PHASE_APPROVER_POLICY_DENIED' unless policy.can_approve?(snapshot,{'id'=>review['actor'],'role'=>review['role']},approval)
        data['approvals'][approval]=record.merge('actor_id'=>review['actor'],'role'=>review['role'])
      end
      errors=policy.errors(snapshot,item.qldapm_actor(user),item.status.name,destination)
      raise ArgumentError,errors.join('; ') unless errors.empty?
      {'valid'=>true,'errors'=>[],'id'=>document['id'],'hash'=>fingerprint,'source_version'=>item.lock_version,'kind'=>kind,'data'=>data}
    rescue KeyError,TypeError,JSON::ParserError
      raise ArgumentError,'PHASE_PROOF_MALFORMED'
    end
  end
end
