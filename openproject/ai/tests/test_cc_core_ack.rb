require 'json'
require 'active_support/all'
source=JSON.parse(STDIN.read).fetch('controller')
method=source.split('  def render_engineering(status: :ok)',2).last.split('  def parse_write_scope',2).first
klass=Class.new do
  const_set(:ArgumentError,Class.new(StandardError))
  attr_accessor :body
  def initialize
    @role='AI_SYSTEM_OWNER';@result={'accepted'=>true,'request_id'=>'request-fixture','current_state'=>'PAUSED'}
  end
  def response = self
  def headers = {}
  def cache_control = {}
  def request = self
  def format = self
  def json? = true
  def post? = true
  def params = {format:'json'}
  def bridge(*) = raise('SLOW_STATUS_REFRESH_BLOCKED_COMMAND_ACK')
  def render(json:,status:) = (self.body=[json,status])
  def render_to_string(partial:,formats:,locals:)
    formatter=locals.fetch(:format_vn_time)
    raise 'EMPTY_TIMESTAMP_NOT_HANDLED' unless [nil,'','not-a-time'].all?{|v|formatter.call(v)=='Chưa có dữ liệu'}
    'Native version 2'
  end
end
klass.class_eval('def render_engineering(status: :ok)'+method)
c=klass.new;c.send(:render_engineering)
raise 'COMMAND_RECEIPT_LOST' unless c.body[0][:result]['request_id']=='request-fixture'
raise 'HTTP_SUCCESS_LOST' unless c.body[1]==:ok
raise 'ACK_CONTAINS_STALE_ENGINEERING' if c.body[0][:engineering]
puts 'PASS actual Core renderer: immediate command receipt independent of slow full-status refresh'
c.instance_variable_set(:@knowledge,{'items'=>[]});c.send(:render_engineering)
raise 'KNOWLEDGE_PARTIAL_MISSING' unless c.body[0][:knowledge_html]=='Native version 2'
puts 'PASS partial render handles absent/invalid index timestamps with controller constant shadowing'
