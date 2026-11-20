require 'json'
require 'tempfile'
class ApplicationController
  def self.before_action(*) = nil
  def self.authorize_with_permission(*) = nil
end
class Integer
  def megabytes = self * 1024 * 1024
end
require '/app/app/controllers/qldapm_ai_controller'
require '/app/app/services/qldapm/ai_bridge'
c = QldapmAIController.allocate
{' '=>[], '50'=>[50], '50, '=>[50], '#50, 51'=>[50,51], '50 50'=>[50]}.each do |input, expected|
  raise 'SCOPE_VALID_INPUT_FAILED' unless c.send(:parse_write_scope,input)==expected
end
['-50','2.5','WP 50','50/2026','abc50','0','50, -23'].each do |input|
  begin
    c.send(:parse_write_scope,input)
    raise 'SCOPE_INVALID_INPUT_ACCEPTED'
  rescue ArgumentError
  end
end
key = Tempfile.new('ui-key'); key.write('synthetic-test-key'); key.close
ENV['QLDAPM_UI_KEY_FILE'] = key.path
class Net::HTTP
  def self.start(*)
    yield Object.new.tap { |http|
      def http.request(*)
        response=Object.new
        def response.code = '403'
        def response.read_body = yield('{"error":"SUPERVISOR_READ_ONLY_EXPLICIT_IDS_REQUIRED"}')
        yield response
      end
    }
  end
end
begin
  Qldapm::AiBridge.call(Struct.new(:id).new(5),Struct.new(:id).new(19),'command',{})
  raise 'EXPECTED_TYPED_ERROR'
rescue Qldapm::AiBridge::RequestError => e
  raise 'WRONG_STATUS' unless e.status==403
  raise 'WRONG_MESSAGE' unless e.message.include?('Supervisor local chỉ phân tích')
  raise 'GENERIC_UNAVAILABLE' if e.message.include?('chưa sẵn sàng')
end
puts JSON.generate({scope_cases:12,typed_http_error:true,network_calls:0,passed:true})
