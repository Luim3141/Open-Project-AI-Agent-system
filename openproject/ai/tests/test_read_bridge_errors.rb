require 'json'
require 'ostruct'
require 'active_support/all'
require ARGV.fetch(0)
source=JSON.parse(STDIN.read).fetch('controller')
klass=Class.new do
  attr_accessor :failure,:body,:query,:bridge_calls
  def response;self;end
  def headers;@headers||={};end
  def cache_control;@cache_control||={};end
  def params;{run_id:'11111111-1111-4111-8111-111111111111'}.merge(query||{});end
  def request;OpenStruct.new(format:OpenStruct.new('json?'=>true),headers:{});end
  def bridge(*);@bridge_calls=(@bridge_calls||0)+1;raise failure;end
  def render(json:,status:);@body=[json,status];end
  def respond_to
    formatter=Object.new
    formatter.define_singleton_method(:html){|&block|nil}
    formatter.define_singleton_method(:json){|&block|block.call}
    yield formatter
  end
end
klass.class_eval("def bridge_error_status(error)\n"+source.split("  def bridge_error_status(error)\n",2).last.split("\n  end",2).first+"\nend")
%w[executions execution].each do |name|
  following=name=='executions' ? 'execution' : 'report'
  klass.class_eval("def #{name}\n"+source.split("  def #{name}\n",2).last.split("  def #{following}\n",2).first)
  [401,403,404,409,422,429,502,503,504].each do |status|
    c=klass.new;c.failure=Qldapm::AiBridge::RequestError.new('fixture',status,code:'FIXTURE',request_id:'fixture-request',retry_after:status==429 ? 1 : nil)
    c.public_send(name)
    raise "#{name}: #{c.body.inspect}" unless c.body[1]==status
    raise 'RETRY_AFTER_LOST' if status==429 && c.headers['Retry-After']!='1'
    raise 'REQUEST_ID_LOST' unless c.headers['X-Qldapm-Request-Id']=='fixture-request'
  end
end
['bad',-1].each do |offset|
  c=klass.new;c.query={offset:offset};c.failure=Qldapm::AiBridge::RequestError.new('must not call',503)
  c.executions
  raise 'INVALID_OFFSET_NOT_422' unless [422,:unprocessable_entity].include?(c.body[1])
  raise 'INVALID_OFFSET_REACHED_GATEWAY' unless c.bridge_calls.to_i==0
end
puts 'PASS both execution read endpoints preserve 9 error statuses, retry hints and request IDs'
