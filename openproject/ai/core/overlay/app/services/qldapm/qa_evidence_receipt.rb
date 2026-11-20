require 'json'
require 'digest'
require 'openssl'
require 'active_support/security_utils'

module Qldapm
  class QaEvidenceReceipt
    RUN_DOMAIN = "qldapm.native-qa-run.v1\0".freeze
    REVIEW_DOMAIN = "qldapm.native-qa-review.v1\0".freeze
    UUID = /\A[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\z/
    SHA = /\A[a-f0-9]{64}\z/

    def self.canonical(value) = JSON.generate(Mutations.canonical(value))
    def self.sha(value) = Digest::SHA256.hexdigest(value)

    def self.signed(bundle, key, domain)
      raise ArgumentError, 'QA_PROOF_SIGNATURE_REQUIRED' unless bundle.is_a?(Hash) && bundle.keys.sort == %w[document signature] &&
        bundle['document'].is_a?(String) && bundle['signature'].is_a?(String) && bundle['signature'].match?(SHA)
      expected = OpenSSL::HMAC.hexdigest('SHA256', key, domain + bundle['document'])
      raise ArgumentError, 'QA_PROOF_SIGNATURE_INVALID' unless ActiveSupport::SecurityUtils.secure_compare(bundle['signature'], expected)
      value=JSON.parse(bundle['document'])
      raise ArgumentError, 'QA_PROOF_DOCUMENT_REQUIRED' unless value.is_a?(Hash)
      value
    end

    def self.native_snapshot(item)
      {'id'=>item.id, 'version'=>item.lock_version, 'description'=>item.description.to_s,
       'project'=>"/api/v3/projects/#{item.project_id}", 'fields'=>{'subject'=>item.subject,
         'startDate'=>item.start_date&.iso8601, 'dueDate'=>item.due_date&.iso8601, 'type_id'=>item.type_id,
         'status_id'=>item.status_id, 'assignee_id'=>item.assigned_to_id, 'priority_id'=>item.priority_id,
         'priority_name'=>item.priority.name, 'parent_id'=>item.parent_id}}
    end

    def self.preflight(packet, item, user, destination, **options)
      receipt=verify(packet,item,user,destination,**options)
      failures=GatePolicy.new.errors(item.qldapm_snapshot.merge('data'=>receipt['data']),
        item.qldapm_actor(user),item.status.name,destination)
      {'valid'=>failures.empty?,'errors'=>failures,'lockVersion'=>item.lock_version,
       'qa_evidence_id'=>receipt['evidence_id'],'hash'=>receipt['hash'],
       'scope'=>'SIGNED_QA_AND_EXISTING_GATE_POLICY; NATIVE_UPDATE_FORM_STILL_REQUIRED'}
    end

    def self.verify(packet, item, user, destination, key_file: ENV.fetch('QLDAPM_UI_KEY_FILE', '/qldapm-ui/ui.key'))
      raise ArgumentError, 'QA_NATIVE_MANAGER_REQUIRED' unless item.qldapm_managed? && item.project_id == 5 &&
        Qldapm::Rbac.pm?(item.project,user,fresh:true) && user.allowed_in_work_package?(:edit_work_packages,item)
      raise ArgumentError, 'QA_PROOF_PACKET_SCHEMA' unless packet.is_a?(Hash) && packet['version'].is_a?(Integer) && packet['version'] == 1 &&
        packet.keys.sort == %w[evidence_document reviews run version] && canonical(packet).bytesize <= 1_048_576 && File.file?(key_file)
      key=File.binread(key_file);run=signed(packet['run'],key,RUN_DOMAIN);evidence=JSON.parse(packet.fetch('evidence_document'))
      raise ArgumentError, 'QA_PROOF_DOCUMENT_REQUIRED' unless evidence.is_a?(Hash) && run['binding'].is_a?(Hash)
      application=run['verification_kind'] == 'AUTOMATED_APPLICATION_WBS'
      raise ArgumentError, 'QA_PROOF_SOURCE_SCOPE' unless run['project_id'] == 5 && run['actor'].is_a?(Integer) &&
        run['id'].is_a?(String) && run['id'].match?(UUID) &&
        (application || run['verification_kind'] == 'AUTOMATED_NATIVE_READBACK' && run.dig('producer','id') == 'qldapm-native-readback-v1') &&
        run.dig('producer','code_sha256').is_a?(String) && run.dig('producer','code_sha256').match?(SHA)
      binding=run.fetch('binding');snapshot=native_snapshot(item)
      raise ArgumentError, 'QA_PROOF_SOURCE_CHANGED' unless binding['native_id'].is_a?(Integer) && binding['native_id'] == item.id &&
        binding['version'].is_a?(Integer) && binding['version'] == item.lock_version &&
        binding['snapshot_sha256'] == sha(canonical(snapshot)) && binding['criteria_sha256'] == sha(item.description.to_s) &&
        binding['assignee'] == (item.assigned_to_id && "/api/v3/users/#{item.assigned_to_id}")
      if binding.key?('assignee_identity')
        assigned=User.active.find_by(id:item.assigned_to_id);role=assigned && Qldapm::Rbac.role(item.project,assigned,fresh:true)
        raise ArgumentError, 'QA_PROOF_ASSIGNEE_ROLE_CHANGED' unless binding['assignee_identity'] ==
          {'actor'=>item.assigned_to_id,'role'=>role == 'BA-PM' ? 'BA' : role}
      end
      started,finished=run.values_at('started_at','finished_at');tests=run.fetch('tests');criteria=run.fetch('criteria')
      raise ArgumentError, 'QA_PROOF_TEST_RESULT_INVALID' unless run['verdict'] == 'PASSED' &&
        [started,finished].all? { |at| at.is_a?(Numeric) && at.finite? } && started <= finished && finished <= Time.now.to_f+30 &&
        criteria.is_a?(Hash) && (1..100).cover?(criteria.length) && tests.is_a?(Array) && (1..500).cover?(tests.length) &&
        tests.all? { |test| test.is_a?(Hash) && test['outcome'] == 'PASSED' && criteria.key?(test['criterion_id']) &&
          %w[reference expected actual].all? { |field| test[field].is_a?(String) && test[field].bytesize.between?(1,4000) } } &&
        tests.map { |test| test['reference'] }.uniq.length == tests.length &&
        tests.map { |test| test['criterion_id'] }.uniq.sort == criteria.keys.sort &&
        item.description.to_s.scan(/^[ \t]*(AC[0-9]+):/).flatten.sort == criteria.keys.sort
      artifact=run.fetch('artifact');expected_artifact={'suite'=>run['producer']['id'],'project_id'=>5,'binding'=>binding,
        'producer'=>run['producer'],'started_at'=>started,'finished_at'=>finished,'tests'=>tests,'verdict'=>'PASSED'}
      raise ArgumentError, 'QA_PROOF_ARTIFACT_CHANGED' unless artifact.is_a?(String) && sha(artifact) == run['artifact_sha256']
      if application
        ApplicationQaReceipt.verify(run,item,key)
      else
        raise ArgumentError, 'QA_PROOF_ARTIFACT_CHANGED' unless JSON.parse(artifact) == expected_artifact
      end
      manifest={'schema'=>application ? 'QLDAPM_AUTOMATED_APPLICATION_QA_V1' : 'QLDAPM_AUTOMATED_NATIVE_QA_V1','work_package_id'=>item.id,'source_version'=>item.lock_version,
        'criteria'=>criteria,'tests'=>tests,'artifact_sha256'=>run['artifact_sha256'],'started_at'=>started,'finished_at'=>finished}
      raise ArgumentError, 'QA_PROOF_EVIDENCE_CHANGED' unless evidence['id'].is_a?(String) && evidence['id'].match?(UUID) &&
        evidence['actor'] == run['actor'] && evidence['project_id'] == 5 && evidence['verification_kind'] == run['verification_kind'] &&
        evidence['producer'] == run['producer'] && evidence['run_id'] == run['id'] &&
        evidence['binding'] == binding.merge('artifact_sha256'=>run['artifact_sha256']) && evidence['manifest'] == manifest
      fingerprint=sha(packet['evidence_document']);bundles=packet.fetch('reviews')
      raise ArgumentError, 'QA_TWO_INDEPENDENT_REVIEWS_REQUIRED' unless bundles.is_a?(Array) && bundles.length == 2
      reviews=bundles.map { |bundle| signed(bundle,key,REVIEW_DOMAIN) }
      raise ArgumentError, 'QA_REVIEW_CHAIN_INVALID' unless reviews.map { |review| review['stage'] } == %w[qa manager] &&
        reviews.map { |review| review['actor'] }.uniq.length == 2
      reviews.each do |review|
        actor=review['actor'];reviewer=actor.is_a?(Integer) && User.active.find_by(id:actor)
        role=reviewer && reviewer.active? && Qldapm::Rbac.role(item.project,reviewer,fresh:true)
        raise ArgumentError, 'QA_REVIEWER_REVOKED_OR_NONINDEPENDENT' unless role && role == review['role'] &&
          (review['stage'] == 'qa' ? role == 'QA' : %w[PM AI_SYSTEM_OWNER].include?(role)) &&
          actor != run['actor'] && actor != item.assigned_to_id && review['evidence_id'] == evidence['id'] &&
          review['hash'] == fingerprint && review['decision'] == 'accept' && review['at'].is_a?(Numeric) &&
          review['at'].finite? && review['at'].between?(0,Time.now.to_f+30)
      end
      kind = case [item.type.name,item.status.name,destination]
             when ['Task','IN TESTING','REVIEW'],['Subtask','IN TESTING','REVIEW'] then 'test'
             when ['Task','REVIEW','READY FOR RELEASE'] then 'retest'
             when ['Subtask','REVIEW','DONE'] then 'completion'
             else raise ArgumentError, 'QA_NATIVE_TRANSITION_PAIR_UNSUPPORTED'
             end
      data=item.qldapm_gate.deep_dup;manager=reviews.last
      snapshot=item.qldapm_snapshot.merge('data'=>data)
      raise ArgumentError, 'QA_NATIVE_REVIEWER_POLICY_DENIED' unless GatePolicy.new.can_approve?(snapshot,
        {'id'=>manager['actor'],'role'=>manager['role']},kind)
      # The proposed gate is read-only until the caller saves it in the Native mutation transaction.
      record={'revision'=>data.fetch('revision',0),'reference'=>"qldapm-qa:#{evidence['id']}:#{fingerprint}",
        'actor_id'=>reviews.first['actor'],'recorded_by'=>user.id,'result'=>'passed','verification'=>application ? 'automated_application_wbs' : 'automated_native_readback',
        'source_version'=>item.lock_version,'artifact_sha256'=>run['artifact_sha256']}
      data['evidence'] ||= {};data['evidence'][kind] ||= [];data['evidence'][kind] << record
      data['approvals'] ||= {}
      (kind == 'test' ? %w[test retest ba pm completion] : kind == 'retest' ? %w[retest ba pm] : %w[completion]).each { |name| data['approvals'].delete(name) }
      data['approvals'][kind]=record.merge('actor_id'=>manager['actor'],'role'=>manager['role'])
      data['qa_bridge']={'evidence_id'=>evidence['id'],'hash'=>fingerprint,'run_id'=>run['id'],'source_version'=>item.lock_version,
        'artifact_sha256'=>run['artifact_sha256'],'producer'=>run['producer'],'reviews'=>reviews,'recorded_by'=>user.id}
      {'data'=>data,'kind'=>kind,'evidence_id'=>evidence['id'],'hash'=>fingerprint,'source_version'=>item.lock_version}
    rescue KeyError,TypeError,JSON::ParserError
      raise ArgumentError, 'QA_PROOF_MALFORMED'
    end
  end
end
