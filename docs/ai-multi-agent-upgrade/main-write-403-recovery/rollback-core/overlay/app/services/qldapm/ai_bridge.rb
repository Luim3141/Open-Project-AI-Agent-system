require "net/http"
require "openssl"
require "securerandom"

module Qldapm
  class AiBridge
    ERRORS = {
      "GEMINI_DISABLED_PENDING_LOCAL_CREDENTIAL_COST_AND_DATA_VERIFICATION" => "Gemini OFF: cấu hình, key hoặc quyền sử dụng chưa hợp lệ. Chưa gọi Google; cần kiểm tra local.",
      "GEMINI_FREE_DATA_SCOPE_DENIED" => "Câu hỏi ngoài phạm vi Gemini được cho phép hoặc chứa thông tin cá nhân/key. Hãy bỏ thông tin đó trước khi gửi.",
      "GEMINI_METADATA_SHAPE_DENIED" => "Dữ liệu không thuộc metadata được phép gửi Google. AI đã dừng; dùng Tool/Insights local để kiểm tra.",
      "GEMINI_CIRCUIT_OPEN" => "Gemini đã dừng sau lỗi/quota; cần đối soát local, không tự retry hay dùng model trả phí.",
      "GEMINI_LOCAL_RPM_EXHAUSTED" => "Gemini đã hết giới hạn RPM an toàn; chưa gọi Google, không dùng model trả phí.",
      "GEMINI_LOCAL_TPM_EXHAUSTED" => "Gemini đã hết giới hạn TPM an toàn; chưa gọi Google, không dùng model trả phí.",
      "GEMINI_LOCAL_RPD_EXHAUSTED" => "Gemini đã hết giới hạn RPD an toàn; chưa gọi Google, không dùng model trả phí.",
      "GEMINI_QUOTA_429" => "Google từ chối do quota; Gemini chờ cooldown trước yêu cầu mới. Receipt đã nhận được vẫn được giữ.",
      "OPENPROJECT_401" => "Phiên xác thực OpenProject không còn hợp lệ; cần đăng nhập lại.",
      "OPENPROJECT_403" => "OpenProject từ chối vì tài khoản của bạn không có quyền thực hiện thao tác này.",
      "OPENPROJECT_404" => "Không tìm thấy công việc trong dự án bạn được phép truy cập.",
      "OPENPROJECT_409" => "Công việc đã thay đổi. Đọc lại phiên bản mới trước khi sửa hoặc duyệt.",
      "OPENPROJECT_422" => "OpenProject không chấp nhận thay đổi theo workflow, quyền hoặc dữ liệu hiện tại. Chưa có xác nhận thành công.",
      "OPENPROJECT_502" => "Chưa xác định được kết quả từ OpenProject. Kiểm tra receipt và công việc trước khi gửi lại.",
      "OPENPROJECT_503" => "OpenProject đang gián đoạn. Kiểm tra receipt và công việc trước khi gửi lại thao tác ghi.",
      "STALE_WORK_PACKAGE" => "Preview đã cũ vì công việc vừa thay đổi. Tạo preview mới trước khi duyệt.",
      "STALE_EXPIRED_OR_CONSUMED_PROPOSAL" => "Đề xuất đã hết hạn, đã xử lý hoặc phiên bản/hash không còn khớp. Không thực hiện lại.",
      "PROPOSAL_NOT_FOUND" => "Không tìm thấy đề xuất của tài khoản này. Chưa thực hiện thao tác.",
      "RUN_WRITE_SCOPE_POSITIVE_IDS" => "Phạm vi chỉ nhận ID công việc là số nguyên dương.",
      "AI_BUSY" => "Một yêu cầu Gemini đang chạy. Chờ kết quả hiện tại trước khi gửi yêu cầu mới."
    }.freeze

    def self.call(project, actor, operation, command)
      key_file = ENV.fetch("QLDAPM_UI_KEY_FILE", "/qldapm-ui/ui.key")
      raise ArgumentError, "AI bridge chưa được cấu hình" unless File.file?(key_file)
      data = {actor: actor.id, project: project.id, audience: "qldapm-ai-ui", at: Time.now.to_i,
              nonce: SecureRandom.hex(16), operation:, command:}
      body = JSON.generate(data)
      # Fixed private destination, never a URL from a ticket, model or browser.
      uri = URI("http://gateway:8090/internal/ui")
      request = Net::HTTP::Post.new(uri)
      request["Content-Type"] = "application/json"
      request["X-Qldapm-Signature"] = OpenSSL::HMAC.hexdigest("SHA256", File.binread(key_file), body)
      request.body = body
      response_body = +""
      Net::HTTP.start(uri.host, uri.port, nil, open_timeout: 3, read_timeout: 100, write_timeout: 5) do |http|
        http.request(request) do |response|
          response.read_body do |chunk|
            raise ArgumentError, "AI response quá lớn" if response_body.bytesize + chunk.bytesize > 2.megabytes
            response_body << chunk
          end
          unless response.code == "200"
            document = JSON.parse(response_body)
            code = document.is_a?(Hash) ? document["error"].to_s[/\A(?:OPENPROJECT_[0-9]+|[A-Z][A-Z0-9_]+)/] : nil
            # Only known codes become UI messages; never echo upstream text or credentials.
            raise ArgumentError, ERRORS.fetch(code) { "AI gateway từ chối hoặc chưa sẵn sàng (#{response.code}); không tự gửi lại thao tác ghi" }
          end
        end
      end
      document = JSON.parse(response_body)
      raise ArgumentError, "AI gateway trả dữ liệu không hợp lệ" unless document.is_a?(Hash)
      document
    rescue JSON::ParserError, IOError, SystemCallError, Timeout::Error
      raise ArgumentError, "AI gateway chưa sẵn sàng; không tự gửi lại thao tác ghi"
    end
  end
end
