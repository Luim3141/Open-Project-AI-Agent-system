require 'json'
require 'active_support/all'
module Qldapm
  module AiBridge
    class RequestError < ArgumentError
      attr_reader :status,:retry_after,:request_id
      def initialize(status); @status = status; @retry_after=status==429 ? 1 : nil; @request_id='fixture'; super('synthetic'); end
    end
  end
end
source = JSON.parse(STDIN.read).fetch('controller')
method = source.split("  def report\n", 2).last.split("  def show\n", 2).first
klass = Class.new do
  attr_accessor :failure, :body
  def response; self; end
  def headers; @headers||={}; end
  def cache_control; {}; end
  def helpers; self; end
  def qldapm_report_document(result)
    raise 'REPORT_BINDING_LOST' unless result[:id] == 'fixture-report'
    {'rendered_html' => '<p>Persisted text</p>', 'raw_markdown' => 'Persisted text'}
  end
  def params; {id: 'fixture-report'}; end
  def bridge(*); raise failure if failure; {'result' => {id: 'fixture-report', narrative: 'Persisted text'}}; end
  def render(json:, status: 200); self.body = [json, status]; end
end
klass.class_eval("def report\n" + method)
if source.include?("  def bridge_error_status(error)\n")
  klass.class_eval("def bridge_error_status(error)\n"+source.split("  def bridge_error_status(error)\n",2).last.split("\n  end",2).first+"\nend")
end
[[nil, 200], [Qldapm::AiBridge::RequestError.new(403), 403],
 *[404,409,422,429,502,503,504].map{|status|[Qldapm::AiBridge::RequestError.new(status),status]}].each do |failure, expected|
  controller = klass.new; controller.failure = failure; controller.report
  raise "report status #{controller.body[1]} != #{expected}" unless controller.body[1] == expected
  raise 'READER_NOT_RETURNED' if expected == 200 && !controller.body[0].dig('reader', 'rendered_html')
  raise 'RETRY_AFTER_LOST' if expected==429 && controller.headers['Retry-After']!='1'
end
puts 'PASS report controller success, forbidden and unavailable status contracts; no GUI'
