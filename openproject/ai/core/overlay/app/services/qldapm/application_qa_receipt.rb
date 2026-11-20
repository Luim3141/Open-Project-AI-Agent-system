require 'json'
require 'digest'

module Qldapm
  module ApplicationQaReceipt
    DOMAIN = "qldapm.wbs-application-proof.v1\0".freeze
    PRODUCER = {'id'=>'qldapm-wbs-application-v1',
      'code_sha256'=>'fec0d913e57172c422f749a3d9e068a5cd33aa6ff35b4cfee43f0fa0aed05f77'}.freeze
    CRITERIA_SHA = 'bf84577edd40c07b8215c0e15a182a7d659db2dae3563981fe6cc12cf21057a7'.freeze
    FIELDS = %w[actor build criteria finished_at id producer producer_sha256 project_id qualification source sources started_at tests verdict version].freeze
    GATEWAY_PATHS = %w[native_wbs.py native_wbs_hierarchy.py native_wbs_relations.py wbs_analysis.py].freeze

    def self.verify(run, item, key)
      receipt=QaEvidenceReceipt
      raise ArgumentError,'APPLICATION_QA_PINNED_PRODUCER_REQUIRED' unless run['actor'] == 18 && run['producer'] == PRODUCER &&
        item.id == 371 && item.type_id == 1 && item.subject.start_with?('[Bug] [CODEX TEST]') &&
        receipt.sha(receipt.canonical(run['criteria'])) == CRITERIA_SHA &&
        item.description.to_s.scan(/^[ \t]*(AC[1-9][0-9]{0,3}):[ \t]+([^\r\n]+)$/).to_h == run['criteria']
      producer=User.active.find_by(id:18)
      raise ArgumentError,'APPLICATION_QA_PRODUCER_REVOKED' unless producer && producer.active? &&
        Rbac.role(item.project,producer,fresh:true) == 'AI_SYSTEM_OWNER'
      proof=receipt.signed({'document'=>run['artifact'],'signature'=>run['application_signature']},key,DOMAIN)
      raise ArgumentError,'APPLICATION_QA_ARTIFACT_CHANGED' unless proof.keys.sort == FIELDS.sort &&
        proof['version'].is_a?(Integer) && proof['version'] == 1 && proof['id'].is_a?(String) && proof['id'].match?(receipt::UUID) &&
        proof['actor'] == 18 && proof['project_id'] == 5 && proof['producer'] == PRODUCER['id'] &&
        proof['producer_sha256'] == PRODUCER['code_sha256'] && proof['source'] == receipt.native_snapshot(item) &&
        proof['qualification'] == 'ISOLATED_APPLICATION_AND_NATIVE; synthetic embeddings and isolated decisions; not human QA approval' &&
        %w[criteria tests started_at finished_at verdict].all? { |field| proof[field] == run[field] }
      sources=proof['sources'];build=proof['build']
      raise ArgumentError,'APPLICATION_QA_CODE_CHANGED' unless sources.is_a?(Hash) && sources.keys.sort == %w[core gateway] &&
        sources['core'] == ApplicationQaSources.read(Rails.root) && sources['gateway'].is_a?(Hash) &&
        sources['gateway'].keys.sort == GATEWAY_PATHS.sort && sources['gateway'].values.all? { |v| v.is_a?(String) && v.match?(receipt::SHA) }
      raise ArgumentError,'APPLICATION_QA_BUILD_REQUIRED' unless build.is_a?(Hash) && build.keys.sort == %w[core gateway] &&
        build.values.all? { |v| v.is_a?(String) && v.match?(/\Asha256:[a-f0-9]{64}\z/) }
      tests=run['tests']
      raise ArgumentError,'APPLICATION_QA_FIXED_TESTS_REQUIRED' unless tests.length == 4 &&
        tests.map { |test| test['criterion_id'] }.sort == %w[AC1 AC2 AC3 AC4] && tests.all? { |test|
          test.keys.sort == %w[actual criterion_id expected outcome proof_sha256 reference] &&
          test['reference'] == "wbs-application:#{test['criterion_id']}" &&
          test['proof_sha256'].is_a?(String) && test['proof_sha256'].match?(receipt::SHA) }
      true
    rescue Errno::ENOENT
      raise ArgumentError,'APPLICATION_QA_CODE_CHANGED'
    end
  end
end
