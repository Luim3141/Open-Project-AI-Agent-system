# Operator bootstrap only: fixed web command, private connector metadata, no business tools.
require "json"
require "net/http"
require "time"

module QuickTunnelWeb
  HOST = /\A[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.trycloudflare\.com\z/

  def self.hostname(document)
    value = JSON.parse(document).fetch("hostname")
    raise ArgumentError, "QUICK_HOST_DENIED" unless value.is_a?(String) && HOST.match?(value)
    value
  end

  def self.current_host
    http = Net::HTTP.new("quick-tunnel", 2000, nil)
    http.open_timeout = 2
    http.read_timeout = 3
    response = http.get("/quicktunnel")
    raise ArgumentError, "QUICK_METADATA_DENIED" unless response.code == "200" && response.body.bytesize < 8192
    hostname(response.body)
  rescue StandardError
    nil
  end

  def self.stop(pid)
    Process.kill("TERM", -pid)
    deadline = Process.clock_gettime(Process::CLOCK_MONOTONIC) + 45
    until Process.waitpid(pid, Process::WNOHANG)
      if Process.clock_gettime(Process::CLOCK_MONOTONIC) >= deadline
        Process.kill("KILL", -pid)
        Process.waitpid(pid)
        break
      end
      sleep 0.2
    end
  rescue Errno::ESRCH, Errno::ECHILD
    nil
  end

  def self.ready?
    [["127.0.0.1", 8080, "/health_checks/default"], ["quick-tunnel", 2000, "/ready"]].all? do |host, port, path|
      http = Net::HTTP.new(host, port, nil)
      http.open_timeout = 2
      http.read_timeout = 3
      http.get(path).code == "200"
    end
  rescue StandardError
    false
  end

  def self.publish(host, ready)
    record = {url: "https://#{host}", updated_at: Time.now.utc.iso8601, native_web: ready ? "ready" : "starting"}
    page = "<!doctype html><html lang='vi'><meta charset='utf-8'><meta http-equiv='refresh' content='10'><title>QLDAPM</title>" \
      "<h1>QLDAPM</h1><p>OpenProject: #{ready ? 'sẵn sàng' : 'đang khởi động, vui lòng đợi'}.</p>" \
      "<p><a href='https://#{host}'>Mở OpenProject và đăng nhập</a></p>" \
      "<p>Link đổi sau mỗi lần tạo tunnel. Gemini/n8n có trạng thái riêng.</p></html>"
    {"current-url.json" => JSON.generate(record), "index.html" => page}.each do |name, body|
      temporary = "/qldapm-access/#{name}.#{Process.pid}.tmp"
      File.write(temporary, body)
      File.rename(temporary, "/qldapm-access/#{name}")
    end
  end

  def self.run
    quitting = false
    %w[TERM INT].each { |signal| Signal.trap(signal) { quitting = true } }
    active_host = nil
    child = nil
    published = nil
    begin
      until quitting
        observed = current_host
        if observed && observed != active_host
          stop(child) if child
          active_host = observed
          environment = {"OPENPROJECT_HOST__NAME" => observed, "OPENPROJECT_HTTPS" => "true", "MIGRATE" => "false",
            "OPENPROJECT_COLLABORATIVE__EDITING__HOCUSPOCUS__URL" => "",
            "OPENPROJECT_ADDITIONAL__HOST__NAMES" => JSON.generate([observed, "localhost:18091", "127.0.0.1:18091", "staging-web", "localhost:8088"])}
          child = Process.spawn(environment, "./docker/prod/web", pgroup: true)
          published = nil
          puts "Quick Tunnel hostname configured; native web starting, no provider call"
          $stdout.flush
        end
        state = active_host && [active_host, ready?]
        if state && state != published
          publish(*state)
          published = state
        end
        if child && Process.waitpid(child, Process::WNOHANG)
          child = nil
          raise "NATIVE_WEB_EXITED"
        end
        15.times { break if quitting; sleep 1 }
      end
    ensure
      stop(child) if child
    end
  end
end

QuickTunnelWeb.run if $PROGRAM_NAME == __FILE__
