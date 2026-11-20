require "net/http"
require "openssl"
require "securerandom"
require "time"

module Qldapm
  class AiBridge
    class RequestError < ArgumentError
      attr_reader :status, :code, :request_id, :retry_after
      def initialize(message, status, code: nil, request_id: nil, retry_after: nil)
        @status = status
        @code, @request_id = code, request_id
        @retry_after = retry_after
        super(message)
      end
    end
    ERRORS = {
      "QA_NATIVE_GATE_REJECTED" => "Bằng chứng đã được kiểm tra nhưng công việc còn thiếu điều kiện Native workflow. Kiểm tra story/scope, checklist, build và reviewer; chưa ghi Native.",
      "QA_NATIVE_PREFLIGHT_SOURCE_CHANGED" => "Phiên bản hoặc hash QA đã đổi trong lúc kiểm tra. Đọc lại nguồn và tạo proposal mới.",
      "QA_NATIVE_READBACK_OUTCOME_UNKNOWN" => "Chưa xác định readback của Native QA transition. Chỉ đối soát exact Native receipt; không gửi lại thao tác ghi.",
      "QA_NATIVE_RECEIPT_SOURCE_CHANGED_HOLD" => "Có receipt nhưng nguồn Native đã đổi tiếp. Giữ kết quả để đối soát, không replay hoặc gọi PASS cho phiên bản hiện tại.",
      "QA_AUTOMATED_CRITERION_UNSUPPORTED" => "Runner chỉ kiểm tra các assertion readback Native được hỗ trợ. Tiêu chí này chưa có test phù hợp; chưa tạo QA PASS hoặc ghi Native.",
      "QA_UNIQUE_NATIVE_CRITERIA_REQUIRED" => "Cần đủ acceptance criteria Native có mã AC duy nhất; không bỏ qua tiêu chí trống hoặc trùng.",
      "QA_INDEPENDENT_REVIEWER_REQUIRED" => "Người duyệt phải độc lập với người khởi tạo bằng chứng và assignee.",
      "QA_REVIEW_REQUIRED_BEFORE_MANAGER" => "Cần QA review độc lập trước khi PM/Owner quyết định bằng chứng tự động.",
      "QA_CHANGED_STALE_OR_ALREADY_DECIDED" => "Bằng chứng, phiên bản hoặc trạng thái review đã thay đổi. Đọc lại trước khi quyết định; không replay.",
      "QA_RUN_SOURCE_CHANGED" => "Nguồn Native đã thay đổi sau kiểm thử. Chạy lại trên phiên bản mới; chưa ghi Native.",
      "QA_TRUSTED_RUN_INTEGRITY_FAILED" => "Chữ ký hoặc hash artifact không hợp lệ. Đã chặn review và thực thi; cần đối soát.",
      "QA_REVIEW_PROVENANCE_INVALID" => "Không xác minh được provenance của quyết định review. Đã chặn thực thi.",
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
      "SUPERVISOR_READ_ONLY_EXPLICIT_IDS_REQUIRED" => "Supervisor local chỉ phân tích/dự thảo. Hãy chọn Gemini để yêu cầu thao tác nghiệp vụ; quyền ghi vẫn được kiểm tra theo tài khoản và scope.",
      "PM_ONLY_BUSINESS_WRITE_REQUIRED" => "Chỉ PM được tạo, sửa hoặc chuyển trạng thái công việc. Checkbox không cấp thêm quyền.",
      "AI_CREATE_PARENT_OUTSIDE_USER_SCOPE" => "Công việc cha nằm ngoài phạm vi được phép trong lượt này. Chọn đúng ID cha rồi gửi yêu cầu mới.",
      "NATIVE_READ_DENIED" => "Không có quyền đọc công việc trong phạm vi đã chọn.",
      "AI_BUSY" => "Một yêu cầu Gemini đang chạy. Chờ kết quả hiện tại trước khi gửi yêu cầu mới.",
      "NO_ELIGIBLE_WORK" => "Không có công việc hợp lệ để chạy. Các unit hoàn tất sẽ không được chạy lại; xem Backlog và trạng thái PAUSED.",
      "ENGINEERING_REPORT_SCHEDULE_CONFLICT" => "Lịch đã được thay đổi trong phiên khác. Đóng rồi mở lại cấu hình để đọc phiên bản mới trước khi lưu.",
      "ENGINEERING_REPORT_SCHEDULE_INVALID" => "Cấu hình lịch không hợp lệ. Kiểm tra giờ, phút, ngày và múi giờ trước khi lưu.",
      "ENGINEERING_STATE_REVISION_CONFLICT" => "Trạng thái điều khiển đã thay đổi. Đọc trạng thái mới trước khi gửi lại lệnh."
    }.freeze

    # Gateway callbacks use this same Puma pool; reserve threads for Native reads.
    BRIDGE_CAPACITY = [ENV.fetch('RAILS_MAX_THREADS', '4').to_i / 2, 1].max
    ADMISSION = Mutex.new
    @in_flight = 0

    def self.call(project, actor, operation, command, request_id: nil)
      admitted = ADMISSION.synchronize do
        if @in_flight < BRIDGE_CAPACITY
          @in_flight += 1
          true
        end
      end
      unless admitted
        raise RequestError.new('AI bridge đang bận; yêu cầu này chưa gửi tới Gateway. Vui lòng thử lại.', 429,
                               code: 'AI_BRIDGE_BUSY', request_id: request_id, retry_after: 1)
      end
      call_with_slot(project, actor, operation, command, request_id: request_id)
    ensure
      ADMISSION.synchronize { @in_flight -= 1 } if admitted
    end

    def self.call_with_slot(project, actor, operation, command, request_id: nil)
      observer = (command[:action] || command['action']).to_s.start_with?('observer_')
      started = Process.clock_gettime(Process::CLOCK_MONOTONIC)
      key_file = ENV.fetch("QLDAPM_UI_KEY_FILE", "/qldapm-ui/ui.key")
      raise ArgumentError, "AI bridge chưa được cấu hình" unless File.file?(key_file)
      data = {actor: actor.id, project: project.id, audience: "qldapm-ai-ui", at: Time.now.to_i,
              nonce: SecureRandom.hex(16), operation:, command:}
      body = JSON.generate(data)
      # Fixed private destination, never a URL from a ticket, model or browser.
      uri = URI("http://gateway:8090/internal/ui")
      request = Net::HTTP::Post.new(uri)
      request["Content-Type"] = "application/json"
      request['X-Qldapm-Request-Id'] = request_id if observer && request_id.to_s.match?(/\A[0-9a-f-]{36}\z/)
      request["X-Qldapm-Signature"] = OpenSSL::HMAC.hexdigest("SHA256", File.binread(key_file), body)
      request.body = body
      response_body = +""
      transport = {}
      Net::HTTP.start(uri.host, uri.port, nil, open_timeout: 3, read_timeout: observer ? 10 : 100, write_timeout: 5) do |http|
        http.request(request) do |response|
          transport = {request_id: response['X-Qldapm-Request-Id'], server_timing: response['Server-Timing']}
          response.read_body do |chunk|
            raise ArgumentError, "AI response quá lớn" if response_body.bytesize + chunk.bytesize > 2.megabytes
            response_body << chunk
          end
          unless response.code == "200"
            document = JSON.parse(response_body)
            code = document.is_a?(Hash) ? document["error"].to_s[/\A(?:OPENPROJECT_[0-9]+|[A-Z][A-Z0-9_]+)/] : nil
            # Only known codes become UI messages; never echo upstream text or credentials.
            message = ERRORS.fetch(code) { "AI gateway trả HTTP #{response.code}; chưa xác nhận thao tác. Kiểm tra quyền, dữ liệu và receipt trước khi gửi lại." }
            retry_after = response['Retry-After'].to_s
            unless retry_after.match?(/\A\d+\z/)
              begin
                Time.httpdate(retry_after)
              rescue ArgumentError
                retry_after = nil
              end
            end
            raise RequestError.new(message, response.code.to_i, code: code, request_id: transport[:request_id], retry_after: retry_after)
          end
        end
      end
      document = JSON.parse(response_body)
      raise ArgumentError, "AI gateway trả dữ liệu không hợp lệ" unless document.is_a?(Hash)
      document['_transport'] = transport.merge(duration_ms: (Process.clock_gettime(Process::CLOCK_MONOTONIC) - started) * 1000) if observer
      document
    rescue JSON::ParserError, IOError, SystemCallError, Timeout::Error, SocketError => error
      if observer
        timeout = error.is_a?(Timeout::Error)
        raise RequestError.new(timeout ? 'Observer upstream timeout' : 'Observer bridge unavailable', timeout ? 504 : 503,
                               code: timeout ? 'OBSERVER_BRIDGE_TIMEOUT' : 'OBSERVER_BRIDGE_UNAVAILABLE', request_id: request_id)
      end
      raise ArgumentError, "AI gateway chưa sẵn sàng; không tự gửi lại thao tác ghi"
    end
    private_class_method :call_with_slot
  end
end
