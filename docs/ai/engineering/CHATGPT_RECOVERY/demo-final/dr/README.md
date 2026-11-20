# Demo recovery kit

Kit dùng snapshot mới từ MAIN, không thay master key n8n và không restore vào MAIN. `creation-*.json` chứng minh capture; chỉ `restore-*.json` có kết quả `LOCAL_RESTORE_VERIFIED` mới chứng minh restore đã chạy. Baseline và final có nhãn/timestamp riêng; source workspace uncommitted và runtime image digests được giữ độc lập, không lấy Git HEAD làm bằng chứng serving source.

Tạo bản mới khi engineering mode OFF và không có active run:

```powershell
python openproject/ai/automation/demo_recovery.py backup --label final
```

Lệnh in đường dẫn kit mới bên dưới `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/demo-recovery-<UTC>-final`. Không ghi đè kit cũ. Kit có:

- `ciphertext/qldapm-demo-recovery.aesgcm`: AES-256-GCM, authenticated magic/schema, random key32/nonce12/tag16; streaming tránh nạp toàn bộ archive vào RAM.
- `ciphertext/decrypt_demo_recovery.py` và `FORMAT.json`: bootstrap độc lập, hash và image IDs; Python + `cryptography` cần sẵn trên máy phục hồi.
- `recovery-custody/recovery.key`: recovery key, **không copy cùng ciphertext sang một nơi công khai**. Hai folder trên cùng laptop chỉ tách file; chưa phải Owner custody/off-host copy.
- `snapshot/`: raw snapshot private phục vụ rollback, không chia sẻ. DACL tạo bằng helper hiện có cho current Windows user/SYSTEM. Snapshot chứa credentials/config/key đang hoạt động.

Payload bao gồm PostgreSQL; Gateway/Knowledge SQLite online backup; n8n SQLite/config/environment key/assets; Qdrant collection config, toàn bộ points/payload/vectors qua scroll read-only; Compose/runtime config và container inspect; worker/Gateway/Core source và Git bundles; OpenClaw WSL Node/runtime/config/sessions/engineering worktrees/checkpoints; demo source/Git/SQLite; Docker image export theo exact digests, không chỉ tên tags.

Final capture còn giữ `docs/ai/engineering/` gồm Windows delivery journals, run evidence và source manifests không được commit; Git bundle riêng không chứa các file untracked này. Private Gateway provider-admission token và health/DR metadata hiện hữu cũng được giữ. Baseline 17:12 UTC ngày 02/11 chưa có Windows journals trong source archive; không dùng baseline để khẳng định đã bao phủ phần đó.

Final kit còn có `ollama-models.tar` và `ollama-runtime.json`: model manifests/blobs BGE-M3 đang chạy, phiên bản Ollama, runtime model digest và `api/show` source blob. Restore đối chiếu từng layer bằng content-addressed SHA256 và binding source blob; API runtime digest được giữ riêng, không giả định bằng hash nguyên văn manifest file. Không cần tải lại model để lấy lại dữ liệu; executable/installer Ollama trên một máy khác vẫn chưa được diễn tập.

Không copy virtualenv/cache có thể dựng lại: Windows `.venv`, `node_modules`, `__pycache__`, pytest/cache; WSL virtualenv/cache và OpenClaw cache/downloads/tmp. Node/OpenClaw installed runtime vẫn được giữ. Virtualenv tái tạo từ requirements pinned là bước hướng dẫn, không giả thành full physical-machine PASS. Các snapshot nhất quán từng store, không phải một transaction nguyên khối qua mọi dịch vụ.

Diễn tập trên clone riêng, không publish ports hay dùng MAIN networks/volumes:

```powershell
python openproject/ai/automation/demo_recovery.py restore --kit '<private kit path>'
```

Restore giải mã vào folder mới, xác minh GCM trước khi parse/extract, chặn traversal/link trong outer archive và so SHA256 mọi file. Sau đó n8n decrypt credentials/server với copied workflows disabled; PostgreSQL/Core dùng restored dump và exact image; Gateway/Knowledge chạy copied SQLite; Qdrant được tạo lại trên internal network và đối chiếu mọi ID/payload/vector; OpenClaw restored Node CLI chạy `--version` network-none/config parse; demo SQLite và source/Git bundles được kiểm tra. Không chạy model, không replay workflow/coding hoặc restore MAIN. Resource peak của từng drill có cap, chạy tuần tự; phối hợp không chạy Native clone cùng qualification/deployment khác.

Qdrant drill còn chạy query bằng một vector đã khôi phục, kiểm tra project filter và project không tồn tại trả rỗng; đây là kiểm chứng khả năng phục hồi dữ liệu/query, không chứng minh semantic retrieval đạt benchmark. Native drill đọc Project5/6 qua authenticated HTTP API bằng token chỉ tạo trên clone. OpenClaw drill thực thi Node đã khôi phục trong tmpfs có quyền exec của container cô lập; không khởi động gateway thứ hai.

`restore-baseline-components.json` ghi bằng chứng baseline từng component: n8n 16 workflow/4 credentials decrypt và server; Gateway HTTP200 + hai SQLite integrity; Qdrant points/payload/vector và filters; source/Git/demo SQLite; restored OpenClaw CLI. Chưa có Native/Core drill cho baseline nên hồ sơ này **không** mang `LOCAL_RESTORE_VERIFIED`. Chỉ dùng `restore-final.json` sau khi diễn tập đầy đủ kit cuối.

Nếu phải cài lại laptop, copy `ciphertext/` và lấy recovery key từ custody riêng. Bootstrap chỉ unpack file vào **folder mới**, không tự restore service:

```powershell
python decrypt_demo_recovery.py --ciphertext qldapm-demo-recovery.aesgcm --key-file '<separate recovery.key>' --output '<new private restore folder>'
```

Sau unpack: xem `manifest.json`, xác minh image digests, `docker load --input images.tar` trên Docker mới; khôi phục source từ `source.tar.gz`, bundles và Compose/config vào private paths. `demo_recovery.py restore` là clone qualification, không phải lệnh cutover máy mới. Khôi phục WSL distro/service vào máy mới cần giữ `/home/openclaw` paths và dựng virtualenv từ pinned requirements; không ghi đè một MAIN còn hoạt động. Không đưa `.env`, n8n key, OpenClaw config hoặc raw snapshot lên GitHub.

Để khôi phục embeddings sau khi cài lại laptop: cài đúng phiên bản Ollama ghi trong `ollama-runtime.json`, giải nén `ollama-models.tar` vào một thư mục private mới rồi cấu hình `OLLAMA_MODELS` trỏ tới phần `ollama-models`; kiểm tra `api/tags`/`api/show` và một embedding BGE-M3 trước khi bật Knowledge sync. Kit giữ model binaries, không tự chạy trình cài đặt Windows hay thay Ollama MAIN.

Trạng thái off-host luôn là `OFF_HOST_COPY_PENDING_OWNER` đến khi Owner copy và kiểm checksum ở đích. Physical-machine DR là `NOT_TESTED`; Owner đã defer yêu cầu này cho demo. Mất key thì không giải mã được; lộ cả key và ciphertext thì toàn bộ snapshot có thể đọc được.
