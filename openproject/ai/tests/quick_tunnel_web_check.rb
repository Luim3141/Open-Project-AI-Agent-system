require_relative "../automation/quick_tunnel_web"
raise "valid host rejected" unless QuickTunnelWeb.hostname('{"hostname":"unit-test.trycloudflare.com"}') == "unit-test.trycloudflare.com"
%w[evil.example.com abc.trycloudflare.com.evil a.trycloudflare.com:443 https://a.trycloudflare.com ../bad -bad.trycloudflare.com].each do |host|
  begin
    QuickTunnelWeb.hostname(JSON.generate(hostname: host))
    raise "invalid host accepted"
  rescue ArgumentError
    nil
  end
end
pid = Process.spawn("ruby", "-e", "sleep 60", pgroup: true)
QuickTunnelWeb.stop(pid)
begin
  Process.waitpid(pid, Process::WNOHANG)
  raise "child not reaped"
rescue Errno::ECHILD
  nil
end
puts "Quick Tunnel hostname boundary and graceful child shutdown PASS"
