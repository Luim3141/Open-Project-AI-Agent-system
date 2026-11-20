require 'json'
require 'tempfile'
require 'minitest/autorun'
require 'active_support/core_ext/numeric/bytes'
require ARGV.fetch(0)
class AiBridgeAdmissionTest < Minitest::Test
  def test_callbacks_keep_native_capacity_without_waiting_in_puma
    key=Tempfile.new('bridge-fixture');key.write('fixture-only-signing-key');key.flush;ENV['QLDAPM_UI_KEY_FILE']=key.path
    lock=Mutex.new;active=0;maximum=0
    response=Object.new
    response.define_singleton_method(:code){'200'}
    response.define_singleton_method(:[]){|_|nil}
    response.define_singleton_method(:read_body){|&block|block.call('{"result":{}}')}
    http=Object.new
    http.define_singleton_method(:request) do |_req,&block|
      lock.synchronize{active+=1;maximum=[maximum,active].max}
      sleep 0.15
      block.call(response)
    ensure
      lock.synchronize{active-=1}
    end
    original=Net::HTTP.method(:start)
    Net::HTTP.define_singleton_method(:start){|*args,**kwargs,&block|block.call(http)}
    project=Struct.new(:id).new(6);actor=Struct.new(:id).new(18)
    outcomes=4.times.map{Thread.new do
      Qldapm::AiBridge.call(project,actor,'command',{action:'observer_task_progress',arguments:{task_id:397}});200
    rescue Qldapm::AiBridge::RequestError=>error
      error.status
    end}.map(&:value)
    assert_operator maximum,:<=,2
    assert_equal [200,200,429,429],outcomes.sort
    assert Qldapm::AiBridge.call(project,actor,'command',{action:'observer_active'})
    response.define_singleton_method(:code){'503'}
    response.define_singleton_method(:read_body){|&block|block.call('{"error":"MAINTENANCE"}')}
    ['1','1200','Thu, 12 Nov 2026 04:00:12 GMT'].each do |hint|
      response.define_singleton_method(:[]){|name|name=='Retry-After' ? hint : nil}
      error=assert_raises(Qldapm::AiBridge::RequestError){Qldapm::AiBridge.call(project,actor,'command',{action:'observer_active'})}
      assert_equal hint,error.retry_after
    end
  ensure
    Net::HTTP.define_singleton_method(:start,original) if original
    ENV.delete('QLDAPM_UI_KEY_FILE');key&.close!
  end
end
