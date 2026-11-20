# CODEX → GEMINI ANTIGRAVITY — EXECUTION MONITOR UI HANDOFF

Workspace authoritative: `D:\AI project\QLDAPM chat`.

**Mục tiêu:** nâng UI/UX của Execution Monitor đang chạy thật, ưu tiên Light Theme OpenProject. Giữ toàn bộ chức năng, dữ liệu, bảo mật và backend hiện có. Tài liệu này không cấp quyền deploy.

Phiên bàn giao chỉ đọc source/runtime/Git và tạo file này; không sửa code, build/deploy/restart container, gọi Gemini, sửa dữ liệu hoặc ghi đè báo cáo lịch sử. Các số test dưới đây là bằng chứng đã thực thi trước đây, không phải toàn bộ được chạy lại trong phiên bàn giao.

## 1. Trạng thái hiện tại

### 1.1 Kiểm chứng trực tiếp

Source/runtime được đối chiếu SHA-256 từng file lúc **2026-10-19 22:00:33 +07:00**, không chỉ sao chép báo cáo cũ.

| Hạng mục | Kết quả |
|---|---|
| Git branch | `codex/local-multi-agent-upgrade` |
| HEAD | `de7fe8f10ed23bb392b6661b0c7ccf9967524b4e` |
| Tracked changes, index/working tree | Không có; `git status --porcelain=v1 -uno` rỗng |
| Untracked trước file handoff | **2.413 file**, phải giữ nguyên |
| UI source | Cả4file `execution.html.erb`, `executions.html.erb`, `_execution_client.html.erb`, `_execution_style.html.erb` đều untracked |
| Staging | `COMPLETE_ON_STAGING`;18container chạy, các container có healthcheck đều healthy lúc kiểm tra |
| Gateway parity |51/51file source = qualified manifest = runtime |
| Core parity |47/47file overlay source = qualified manifest = runtime |
| Recovery | Hai app có restartpolicy `unless-stopped`; image-lock/runtime manifest đã lưu |

**HEAD không chứa đầy đủ sản phẩm hiện tại.** Đừng checkout HEAD rồi kết luận Monitor bị thiếu; nguồn bàn giao là working tree cùng hash manifest. Không reset/clean/stash/xóa untracked.

| Thành phần | Container | Image ID đang chạy |
|---|---|---|
| Gateway | `qldapm-ai-stage-staging-gateway-1` | `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b` |
| Core | `qldapm-ai-stage-staging-web-1` | `sha256:7d76c1eb8ad8e352c7daabd467d032cddba654536bc2ca5a89d9a36e9b138d20` |

Container IDs khi kiểm tra: Gateway `61689602da51f704618cc5786b8a221bce6b86a0f8d033226cf553d399312ade`; Core `5fbe3d84e5bb589c916e64ca4bc2e53b6a55c9d931493f27a7fed3f5761da8b4`. Inspect lại trước mutation vì IDs/starttimes có thể đổi sau vận hành.

### 1.2 Kiến trúc

- OpenProject Community17.9.1, Rails/Core, Native Angular/Primer frontend đã có trong image. **Monitor là Rails ERB + plain JavaScript + SVG**, không phải Angular component mới.
- Python Gateway dùng SQLite Store, typed AgentTask/AgentRun/ExecutionPlan/AgentResult; Supervisor/registry dispatch PM/BA/DEV/QA/Reviewer hiện hữu.
- Gemini SDK/provider/quota guard hiện hữu, giữ model `gemini-3.5-flash-lite`, Free Tier và saved key/policy. Reviewer deterministic local kiểm tra references/scope, không chứng minh toàn bộ ngữ nghĩa.
- PostgreSQL giữ dữ liệu Native; SQLite giữ runs/proposals/audit/usage/events. Second Brain và n8n giữ chức năng riêng, không cần đổi khi chỉnh UI.
- Native session → Rails project/permission → HMAC `Qldapm::AiBridge` → Gateway → fresh Native actor/project/item ACL/version → canonical data + typed projection → Monitor.
- Bridge có đích cố định `http://gateway:8090/internal/ui`. Browser không được tự cấp actor/project hoặc mở public Gateway endpoint mới.

### 1.3 Khởi chạy, truy cập và kiểm tra

URL kiểm tra từ landing local trong phiên này: **https://holmes-brunette-lender-stylus.trycloudflare.com**. Hostname `buried-glad-rpg-recall...` trong báo cáo deploy đã là lịch sử. Quick Tunnel có thể đổi hostname sau Docker startup.

- Landing ổn định trên host: `http://localhost:18090/` để lấy URL hiện tại.
- Assistant: `/projects/qldapm-local/qldapm-ai`.
- History: `/projects/qldapm-local/qldapm-ai/executions`.
- Detail: `/projects/qldapm-local/qldapm-ai/executions/<run_id>`.
- History/Detail JSON: thêm `.json`, cùng Native session và quyền hợp lệ.
- Run tham chiếu đã có: `7d528511-c957-40b1-bd1e-c6fe7dd28650`, owner actor7/PM; không hardcode ID này vào product hoặc cho actor khác xem.

Người dùng mở Docker Desktop, đợi Engine/healthchecks; các service tự phục hồi và dùng lại key/config đã lưu. Không chạy provision để khởi động, không bật Windows autostart/thay WSL storage trong công việc UI này.

```powershell
Set-Location 'D:\AI project\QLDAPM chat'
docker info --format '{{.ServerVersion}}'
docker ps --format '{{.Names}} | {{.Image}} | {{.Status}}'
docker inspect qldapm-ai-stage-staging-web-1 qldapm-ai-stage-staging-gateway-1 --format '{{.Name}} | {{.Image}} | {{.State.Health.Status}} | {{.HostConfig.RestartPolicy.Name}}'
git branch --show-current
git rev-parse HEAD
git status --short
```

Không in raw Env/inspect/log có thể chứa credentials. Nếu vừa startup, đợi và chẩn đoán có lọc, không restart hệ thống tùy tiện.

## 2. Những gì đã triển khai và kiểm chứng

Trong tài liệu, `E = D:\AI project\QLDAPM chat\docs\ai-multi-agent-upgrade\execution-monitor\run_20261019_1635`. Bằng chứng dưới đây nằm trong E.

| Chức năng | Hiện thực | Bằng chứng/phạm vi |
|---|---|---|
| History | SQL actor/project pagination; UI10rows/page; search/state/asc-desc/previous-next/empty/error | `browser-e2e.json`: filter/sort/pagination trên clone; `deployment/serving-browser.json`: ownhistory5roles và searchempty qua publicHTTPS |
| Supervisor/Agent Graph | Từ ExecutionPlan thật; Supervisor/specialists/Reviewer/Final; single/parallel DAG support | Savedrun6nodes; clone/public assertions; unit single/parallel/invalidDAG |
| Assignment edges | Supervisor→steps, dashed; không mô tả specialist trực tiếp gọi agent khác |4assignmentedges của run tham chiếu |
| Dependency edges | Từ dependencies thực, solid, leaves→Final |6dependencyedges của run tham chiếu; không hardcode cùng một chuỗi |
| Graph interaction | Click/keyboard/zoom/fit/pan/compact/ancestorhighlight/table fallback | `browser-e2e.json`, `browser-extra.json` |
| Agent Detail | Objective/assignment/dependencies/sources/state/timing/provider/usage/error/validation/output/limitations | StoredBAoutput publicUI; canonical4outputs gồmReviewer và timing mới trên clone |
| Timeline/Replay | Events đã lưu, agentfilter, readonly replay1event/giây | Clone filter/replay/slider; public replay/sessionexpiry; không gọi model/enqueue |
| Final Report | Stored aggregate + sources, warnings/data missing | ERB+JS render/sources, projection và detail flow; không có chứng nhận semantic correctness toàn báo cáo |
| Gemini usage | LIVE_GEMINI từ LIVE_SUCCESS receipts; MOCK_TEST riêng, local riêng | Storedrun4calls/9.324tokens; publicassertions, unitusage/missing/retry |
| RBAC/isolation | Ownactor/project; fresh NativeACL/version; STALE ẩn dữ liệu | Backend crossactor/project/revoked/version;4nonPMroles bị API403/UIhidden khi mở PMrun |
| Session/XSS/network | Reauthorize replay/node; clearPrivate khi hết phiên/mất mạng; textContent/SVGtext | Clone XSS/networkfault/pollstop; publicsessionexpiry |
| Responsive | Desktopgrid, stack≤1100px,375px metrics2cột/graph330px; table mở≤760px | Clone375/dark và public375; theme hiện theo OSmedia riêng cần cải thiện |

Baseline evidence:

- `windows-regression.json`:196PASS; `linux-regression.json`:127PASS trên immutableGateway; monitor-specific18tests.
- `browser-e2e.json`:22PASS + `browser-extra.json`:3PASS trên clone cùng image.20cases trong fullfinalimage run,2BAcases tiếp tục sau sửa fixturelookup `BA-PM`; không gọi là một lần chạy duy nhất.
- `deployment/serving-browser.json`, `deployment/serving-test-results.csv`:30publicUI/API checksPASS trên5tài khoản thật, TOTP/logout, không modelcall mới.
- `deployment/post-deploy-parity.json`, `final-preservation.json`, `final-artifact-validation.json`: parity/scope/data/config proof.
- `deployment/screenshots/public-historical-graph.png`, `public-mobile-overview.png`; clone screenshots trong `E/screenshots/`.
- `deployment/browser-js-classification.json`:0MonitorJSerrors,11NativeHAL autherrors trên anonymous/login/logout; không che totalerrors thành0.

**Không fake telemetry lịch sử.** Run tham chiếu có BA/DEV/QA output trích từ aggregate theo nhãn host chính xác; không có Revieweroutput riêng hoặc agenttimestamps. Giữ missing-data warnings, không chia đều duration hoặc gọi Gemini để bù. Run mới có canonical outputs/events; lifecycle mới đã qualify bằng SDKMockTransport trên clone, không có generation Google mới trên serving image này.

## 3. Source map và phạm vi chỉnh sửa an toàn

Các đường dẫn repo bên dưới tương đối với workspace authoritative ở đầu file; overlay tương ứng `/app/<phần sau core/overlay/>` trong Core.

| File | Mục đích / vùng sửa an toàn |
|---|---|
| `openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb` | `executions` history và `execution` detail HTML/JSON. Không đổi auth/project/permission/no-store/safeerrors cho cosmeticUI |
| `openproject/ai/core/overlay/config/routes.rb` | Hai GET Monitor hiện dòng32–33; giữ endpoint và Native routes khác |
| `openproject/ai/core/overlay/app/views/qldapm_ai/executions.html.erb` | History forms/table/filters/sort/pagination/empty/error; có thể chỉnh layout, presentation, labels, giữ escaping và bindings |
| `openproject/ai/core/overlay/app/views/qldapm_ai/execution.html.erb` | Shell overview/SVG toolbar/AgentDetail/Timeline/Replay/FinalSources; nơi nhóm accordion/tabs/layout |
| `openproject/ai/core/overlay/app/views/qldapm_ai/_execution_style.html.erb` | **CSS Monitor inline, scoped `.execution-monitor`**; không có Monitor.scss riêng. Chỉnh colors/type/spacing/grids/breakpoints |
| `openproject/ai/core/overlay/app/views/qldapm_ai/_execution_client.html.erb` | **PlainJS trong javascript_tag nonce:true**; graph/detail/timeline/final/poll/replay; không có Monitor.ts |
| `openproject/ai/core/overlay/app/views/qldapm_ai/_result.html.erb` | Link từ Assistant result đến run Monitor; giữ binding/state/result |
| `openproject/ai/core/overlay/app/views/qldapm_ai/_control_center.html.erb` | Registry vs runtime vs lastreceipt, history/Monitor navigation; chỉnh layout, không gộp3khái niệm thành LIVEbadge |
| `openproject/ai/core/overlay/app/views/qldapm_ai/show.html.erb` | HostAssistant và inline `.qldapm-ai-*` CSS; tránh ảnh hưởng tool/preview/confirm forms |
| `openproject/ai/core/overlay/app/services/qldapm/ai_bridge.rb` | HMAC/fixedtarget/responsecap2MB/safeerrors; không sửa cho UIpolish |
| `openproject/ai/core/overlay/config/initializers/qldapm_gates.rb` | Readonly Monitor mapping view_work_packages; không nới permissions |
| `openproject/ai/gateway/execution_monitor.py` | TypedMonitorNode/ExecutionMonitor, layers/observed/project_execution; graph/metrics truth từ backend |
| `openproject/ai/gateway/execution_events.py` | Append/dedup typed code/ID/time events, không output/prompt/secrets |
| `openproject/ai/gateway/store.py` | execution_records hiện304, execution_history315; indexedscopedSQL, **filter/sort server-side** |
| `openproject/ai/gateway/service.py` | Readcommands667–677, get_ai_run freshACL; CC last_provider_state; không sửa quyền/provider vì UI |
| `openproject/ai/gateway/catalog.py` | Readcommand export/descriptions; thêmServiceaction thiếucatalog từng làm startupfail |
| `openproject/ai/gateway/live_agents.py`, `supervisor.py`, `gemini.py` | Algorithm/registry/provider/instrumentation hiện hữu; chỉ tham khảo trong UI scope |
| `openproject/ai/tests/test_execution_monitor.py` |18tests graph/states/usage/scope/events/missingdata/no-provider-on-read |
| `openproject/ai/automation/ExecutionMonitorCore.Dockerfile` | ChildCore COPYoverlay, giữ dependencyruntime; không cần Angularbuild |
| `openproject/ai/automation/RemainingGateway.Dockerfile` | Gatewaychild nếu thật sự đổi backend; thường không cần |
| `openproject/ai/provision_local_stage.py` | Guardeddeploy, chỉ dùng sau approval mới; không chạy default |

### 3.1 Seam JavaScript

Trong `_execution_client.html.erb`: `detail()` khoảng35; `graph()`46; `timeline()`69; `snapshot()`75; `render()`76; `clearPrivate()`89; `poll()`90; `reauthorize()`102; fit/zoom105–106; replayhandlers110–111. Line numbers có thể đổi khi sửa.

- Graph: DOM/SVG tạo từ `node.level`, layout bands2cột, compact heights78/130; sửa spacing/width/wrapping/edge routing, không đổi assignment/dependency semantics.
- Detail: có thể nhóm summary/expanded metadata, không bỏ output/sources/validation/provider/timing.
- FinalReport nằm trong `render()` và ERBcontainers, không có TScomponent riêng.
- Giữ `execution-monitor`, `em-graph`, `em-agent-*`, `em-node-table`, `em-timeline`, `em-replay-*`, `em-final-*`, data-endpoint/data-node/data-kind hoặc cập nhật JS/E2E đồng bộ.
- Giữ textContent/SVGtext, CSPnonce, reauthorization/sessionclearing/pollbackoff/terminalstop. Node pointerdown phải không chiếm backgroundpan; keyboard vẫn chọn được.

### 3.2 Tokens/theme đã kiểm tra từ serving image

Workspace không có đầy đủ NativefrontendSCSS source; `/app/frontend/src` và `/app/app/assets/stylesheets` không có trong servingimage. Không bịa TS/SCSS path hoặc npm pipeline cho Monitor.

Path **trong Core container, chỉ tham khảo**:

- `/app/app/views/custom_styles/_primer_color_mapping.erb`: Primer↔OpenProject mapping, selectors `[data-color-mode]`, `data-light-theme`, `data-dark-theme`.
- `/app/app/views/custom_styles/_inline_css.erb`: designcolors; `/app/lib/open_project/custom_styles/color_themes.rb`: themes.
- `/app/app/components/custom_styles/theme_selector_component.rb` và `.html.erb`: Native theme selector.
- `/app/public/assets/frontend/styles-OVMOSZVV.css`: compiledstyles hiện tại; hashedname thay đổi theo image, không edit bundle trong container.

Tokens thấy thật trong mapping: `--bgColor-default`, `--bgColor-muted`, `--fgColor-default`, `--fgColor-link`, `--borderColor-default`, `--accent-color`, `--button-primary-*`, `--body-background`, `--body-font-color`. Kiểm tra computedstyles/token/font cụ thể trên clone trước khi dùng; không đoán tên token. Monitor đang `font:inherit` nhưng tự đặt heading/metric/output sizes; nên kế thừa Native typography, không tải font ngoài.

**Nguồn nền navy:** `_execution_style.html.erb` có `@media(prefers-color-scheme:dark)` override `--em-bg:#172334`, `--em-soft:#111b29`, `--em-text:#edf3fb` mà không đọc Native theme choice. OSdark có thể làm Monitor navy trong OpenProjectLight. Sửa theme scope/tokenoverride, không đổi userpreference/DB hay theme toàn app.

## 4. Hướng nâng cấp UI/UX

1. **Light Theme trước:** bỏ navy khi NativeLight được chọn, kể cả OSdark. Dựa trên actual Native theme attributes/tokens; không đoán class `dark` từ framework khác, không đổi theme toàn app.
2. **Đồng bộ Native:** font inheritance, heading scale, accent links, button/form/table styles hiện hữu. Primarybutton không nhất thiết luôn xanh dương; dùng token thực.
3. **Giữ SVG hoạt động:** cải thiện spacing/centering/edgecrossings/wrapping/legend/selected/running/failed cues. Không thay plan hay gắn LIVE cho Reviewerlocal.
4. **AgentDetail ngắn hơn:** summary mục tiêu/state/output; metadata kỹ thuật/provider/timing/validation/limitations trong nhóm mở được. Không xóa field hoặc cắt output mà không có cách đọc đủ.
5. **Timeline:** rows compact/grouping, rõ agent/event/time; giữ ordering/filter/replay và origin/missingdata warnings.
6. **FinalReport:** chia sections/typography/sources/collapse dễ đọc. Dữ liệu vẫn textContent/escaped. Nếu thêm Markdown phải sanitize và regressionXSS; không render rawHTML.
7. **History:** request/status/mode/agent/time/usage dễ scan, forms/pagination/empty/error đồng bộ; dùng serverpagination, không tải mọi run xuống client.
8. **Responsive:** tránh chữ Developer vỡ thành nhiều mảnh ở375px; overflow nằm trong component, không ngang toàn window. Giữ table/list và44px controls/focus.
9. **Presentation/FocusMode tùy chọn:** làm sau các mục chính; có thoát/Esc/focus rõ, không bỏ cảnh báo/sources, không tạo execution mới hoặc thêm framework lớn.

## 5. Ràng buộc và phạm vi

- Chỉ làm UI/UX source/clone; không Main/Production/CSDLDPT, không reset/clean Git, xóa file/dữ liệu, viết lại113tasks.
- Không thay Gemini/Supervisor algorithm nếu không có lỗi thật; không đổi model/key/project/Billing/FreeOnly/quota/paidfallback. Không yêu cầu nhập lại savedkey.
- Giữ Native RBAC, PM-only-write, actor/project/HMAC binding, TOTP/nativegates; không tạo/disable/rotate devices để chữa test.
- Không restart QuickTunnel, n8n/n8n-editor, PostgreSQL hoặc DockerDesktop vì UI.
- Không gọi Gemini để kiểm tra layout; dùng storedrun/fixturemock trên clone. Không submitmock/runs hoặc sửa dữ liệu Staging hiện hữu để chụp ảnh đẹp.
- Giữ no-store, safe403/503, STALEhidden, provider-on-read=0, poll1run/3s/backoff/terminalstop/hidden-tabpause và clearPrivate khi auth/networkfail.
- Không đưa credentials/codes/cookies/tokens/businesssensitivepayload vào code/prompts/logs/screenshots/handoff.
- **Approval61e1719f đã dùng cho deployment hoàn thành. UIcandidate mới cần preview/exactimages/impact/rollback và phê duyệt mới. File này không cấp quyền deploy.**

## 6. Build và testing cho phiên UI tiếp theo

Các lệnh build/test sau là hướng dẫn, **không chạy trong phiên bàn giao**. Dùng run/output mới, không ghi đè E.

### 6.1 Build Core UI candidate

Ưu tiên chỉ đổi sourceCore, giữ Gateway456c38f6. Không build từ Core3b cũ vì sẽ mất Monitor. Private `build_candidates.py` cũ assert Gateway40cb; không chạy nguyên trạng sau deployment.

PowerShell dưới đây chỉ tạo image, không thay servingcontainer. Nếu baseline drift thì dừng/reconcile:

```powershell
Set-Location 'D:\AI project\QLDAPM chat'
$py = '.\openproject\ai\.venv\Scripts\python.exe'
$coreParent = (docker inspect qldapm-ai-stage-staging-web-1 --format '{{.Image}}').Trim()
if ($coreParent -ne 'sha256:7d76c1eb8ad8e352c7daabd467d032cddba654536bc2ca5a89d9a36e9b138d20') { throw 'Reconcile parent before build' }
$uiBuildId = Get-Date -Format 'yyyyMMdd-HHmmss'
$baseTag = 'qldapm-ui-base:' + $uiBuildId
$candidateTag = 'qldapm-ui-candidate:' + $uiBuildId
$sourceSha = & $py -c 'from pathlib import Path; import json,hashlib; r=Path("openproject/ai"); h={p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/"core/overlay").rglob("*") if p.is_file() and "__pycache__" not in p.parts}; print(hashlib.sha256(json.dumps(h,sort_keys=True).encode()).hexdigest())'
if ($LASTEXITCODE -ne 0) { throw 'Source manifest failed' }
docker tag $coreParent $baseTag
if ($LASTEXITCODE -ne 0) { throw 'Base tag failed' }
docker build --pull=false --build-arg "CORE_IMAGE=$baseTag" --build-arg "SOURCE_SHA256=$sourceSha" -f openproject/ai/automation/ExecutionMonitorCore.Dockerfile -t $candidateTag openproject/ai
if ($LASTEXITCODE -ne 0) { throw 'Build failed; do not deploy' }
$coreCandidate = (docker image inspect $candidateTag --format '{{.Id}}').Trim()
```

Lưu exactcandidateID/parent/per-filehashes/commands/results vào runUI mới. SOURCE_SHA256 label không thay per-file parity. Dockerfile COPYoverlay, giữ dependencies; đổi ERB không cần npm/Angular rebuild. Kiểm tra Native db/migrate/fixtures hashes không đổi.

Nếu backend thật sự cần đổi: review callers/security, thêm regression; dùng `RemainingGateway.Dockerfile` với GATEWAY_IMAGE tag trỏ serving456c38f6, không dùng default006b. CosmeticUI thường không cần Gatewaybuild.

### 6.2 Windows tests

```powershell
Set-Location 'D:\AI project\QLDAPM chat\openproject\ai'
& '.\.venv\Scripts\python.exe' -m unittest tests.test_execution_monitor
```

Chạy lại đúng196-suite từ workspace root:

```powershell
$py = '.\openproject\ai\.venv\Scripts\python.exe'
& $py -c 'from pathlib import Path; import sys,json,unittest; sys.path.insert(0,str(Path("openproject/ai").resolve())); v=json.loads(Path("docs/ai-multi-agent-upgrade/execution-monitor/run_20261019_1635/windows-regression.json").read_text()); s=unittest.defaultTestLoader.loadTestsFromNames(["tests."+m for m in v["modules"]]); r=unittest.TextTestRunner().run(s); raise SystemExit(not r.wasSuccessful())'
```

Không rootdiscovery hoặc chạy legacyrotation/secretfallbackscripts. Modules đúng nằm trong snapshotJSON; một số hosttests in “GeminiOFF” trong mock, không phải quyền sửa cấu hình serving.

### 6.3 Linux image regression

Từ workspace root, dùng currentGateway nếu UI-only, hoặc qualifiedcandidateGateway khi backend đổi:

```powershell
$testDir = (Resolve-Path '.\openproject\ai\tests').Path
$linuxModules = @('test_live_agents','test_planner','test_supervisor','test_pm_agent','test_ba_agent','test_dev_agent','test_qa_agent','test_reviewer_agent','test_agent_registry','test_remaining_integration','test_agent_queue','test_agent_store','test_provider_wait','test_quota_reset','test_quota_classes','test_execution_monitor') | ForEach-Object { 'tests.' + $_ }
docker run --rm --pull never --network none --read-only --cap-drop ALL --security-opt no-new-privileges:true --memory 768m --pids-limit 128 --tmpfs '/tmp:size=128m,mode=1777' --env 'QLDAPM_AI_RUNTIME=' --env 'PYTHONPATH=/qa:/app' --mount "type=bind,source=$testDir,target=/qa/tests,readonly" --entrypoint python sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b -m unittest @linuxModules
```

Đây là127-suite tại baseline, networknone. Windowsfullsuite không bê nguyên vào image vì hostoperatorfiles/prototypes bị `.dockerignore` loại; chọn sai suite từng gây importerrors. Không ship lại obsoleteprototype để test xanh.

## 7. Clone và Browser E2E

### 7.1 Owned resources giữ lại, đã inspect hiện stopped

| Container | Label `qldapm.qualification` | Vai trò |
|---|---|---|
| `qldapm-em-core-20261019-1635` | `execution-monitor-20261019-1635` | Coreclone, loopback18097 |
| `qldapm-em-gateway-20261019-1635` | `execution-monitor-20261019-1635` | Gatewayclone, loopback18098 |
| `qldapm-rd-db-20261018` | `remaining-20261018` | FixturePG tái sử dụng có kiểm tra ownership |

Networks: `qldapm-rd-20261018` internal, `qldapm-rd-loopback-20261018`. Dataset/state/bind/volume giữ nguyên; không reset/reseed. Metadata E/clone-resources.json và clone-cleanup.json. Clone dùng syntheticproviderkey/providerdisabled, không mang realGeminikey sang UItest.

Privateoperator root:

`C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\operator\execution-monitor-20261019_1635`

| Script trong root này | Vai trò / tránh chạy nhầm |
|---|---|
| `setup_clone.py` | Setupbanđầu, assert state chưa có; không rerun trên existingstate |
| `refresh_clone.py` | Recipe copyEnv/mounts privately, recreate ownedclones/aliases/processes; đọc manifest cũ, không chạy nguyên trạng để test candidate mới |
| `browser_e2e.py` | FullMonitor Playwright, realRails/Gateway/Native, storedlive +MockTransportworker |
| `browser_extras.py` | CCseparation, pan/fit, replay sliderauthorization |
| `fixture_worker.py` | RealSupervisor/SDKMockTransport, synthetickey, readfixture451, không Nativewrite |
| `qualify_linux.py` | Linuxrecipe, nhưng output trỏ runcũ; copy/adapt sang runmới |
| `deployment/serving_browser.py` |30readonlypublicchecks/5roles; chỉ dùng sau deploy được approve |
| `deployment/apply_monitor.py` | Deployment đã hoàn thành, receiptguard/oldbaseline; không rerun/reuseapproval |

`openproject/ai/tests/post_deployment_browser_uat.py` chứa `current_codes()` dùng Railsrunner READONLY để sinh mã test từ device hiện có, không exportseed/rotate. Không chạy cả driver đó cho UIpolish vì còn các ca chức năng khác. Cache auth/TOTPcodes/cookies cũ có thể hết hạn; làm mới testinput đúng phạm vi bằng helper, không đổi account/MFA.

### 7.2 Quy trình UI clone

1. Inspect labels/state/images/mounts/networks/ports, không in Env/privatevalues. Không để oldRDCore/Gateway và clone mới cùng dùng aliasgateway/staging-web đang active trên cùng network.
2. Tạo run/output mới; có thể dùng existingfixturePG sau ownershipcheck. Recreate **ownedcloneCore** bằng `$coreCandidate`; giữ cloneGateway nếu backend không đổi. Dùng recipe refresh_clone.py nhưng manifest/input mới, không ghi đè candidate-images.json của E.
3. Historicalrun phải giữ owner7/PM; BA6/BE8/FE9/QA10. Không transpose vào fixturePM13 vì databaseclone khác có thêm tài khoản đó.
4. Hai appclone có PID1sleep. `docker start` không tự chạy app; sau khi reconcile/start đúng ownedcontainers, dùng:

```powershell
docker exec -d qldapm-em-gateway-20261019-1635 python -m uvicorn gateway.app:app --host 0.0.0.0 --port 8090 --no-access-log
docker exec -d qldapm-em-core-20261019-1635 bundle exec rails server -b 0.0.0.0 -p 8080 --pid /tmp/execution-monitor.pid
```

Nếu tênclone mới thì thay đúng tên. Không chạy commands này vào servingcontainers hoặc tạo process duplicate; kiểm tra PID/port trước retry. Đợi `http://localhost:18097/login` thật ready, không coi sleepUp là appready.

5. Copy/adapt browser driver sang **private newrun**, thay endpoint/candidate/evidencepaths và freshauthinput. Chạy bằng venv đã có Playwright:

```powershell
# Placeholder: Gemini phải chuẩn bị driver/input cho runUI mới trước, không phải file có sẵn.
& '.\openproject\ai\.venv\Scripts\python.exe' '<private-new-ui-run>\browser_e2e.py'
```

Driver dùng `sync_playwright()` và `pw.chromium.launch(channel='msedge',headless=True)`. Không cần testframework mới. Không thay URL thành serving rồi submitmockworker/runs lên đó.

6. Preserve assertions: Assistant→History→Monitor, actualplan/edges/nodeoutput/sources, keyboard/zoom/pan/fit/compact, timeline/filter/replay/slider, historysearch/sort/pagination/empty/error, failed/running/stale, networkfault/sessionexpiry/crossactor403/XSS, no providercalls/ledgergrowth khi xem.
7. Theme matrix: NativeLight+OSlight và **NativeLight+OSdark** phải hết mismatchnavy. Kiểm tra actualthemeattributes/computedtokens; các theme khác nếu còn hỗ trợ.
8. Baseline đã thử desktop1600×1100/1440×1000, mobile375×900. UI mới nên thêm1280×800,1920×1080,375×812,768×1024tablet. Viewports bổ sung **chưa được coi đã PASS**.
9. Chụp và xem ảnh viewport/section trong Native scroller; ảnh full-element quá dài từng bị trắng ngoài viewport/compositor, không dùng làm visualacceptance. Không để credentials trong screenshot.
10. Dừng đúng ownedclones sau qualification, giữ data/volume/evidence; không cleanup networks/volumes hàng loạt.

## 8. Chuẩn bị candidate, backup, deploy và rollback

### 8.1 Trước khi xin approval mới

Hoàn tất source/candidate/hash manifest, relevantregression, cloneE2E và visualacceptance; kiểm tra không Native migration và Gatewayunchanged nếu UI-only. Preview phải ghi exactimages/services/downtime/backup/recovery, test results và source/runtime parity. Lưu run mới, cập nhật architecture trong cùng UI change, giữ checkpoint khi quota/ngắt. Không viết lại113tasks.

Bằng chứng của deployment Monitor hiện hành trong `E/deployment/`:

- Backup trước `a6128654-1af4-4086-8d41-68c094eb3216`: pre-deploy-backup.json, pre-deploy-pg-restore.json, pre-deploy-cold-restore.json —221PGtables/assets/config+3SQLite.
- Backup sau `61266765-03f3-459c-b7b1-a96f4a656591`: post-deploy-backup.json, post-deploy-cold-restore.json, sqlite-history-preservation.json —3SQLite logicalrestore/retention.
- `E/rollback-compatibility.json`: Gateway40cb mở additiveeventschema. Đây là proof cũ, **không phải baseline rollback UI mới**.

### 8.2 Sau phê duyệt mới — không chạy ở bước handoff

Snapshot private manifest/env/image-lock/config hashes và actualruntimeIDs/images; kiểm tra noactive/unknownjobs. Có lease `jira_sync_backup.operator_lease('staging')`. Không mở live SQLite/WAL từ Windows.

Online backup hiện hữu:

```powershell
docker exec qldapm-ai-stage-local-backup-1 python3 /trusted/local_backup.py once
# Dùng ID backup vừa nhận. Placeholder sau phải được thay bằng NEW backup ID.
& '.\openproject\ai\.venv\Scripts\python.exe' '.\openproject\ai\check_backup_sqlite.py' "$env:LOCALAPPDATA\QLDAPM\openproject-ai\operator\local-backups\<NEW-BACKUP-ID>"
```

`jira_sync_backup.rehearse_backup(directory,data_only=True)` là fullPG/assets/config restore drill. Không thay onlinebackup bằng `jira_sync_backup.create_backup('staging')` máy móc: hàm đó stopwriters. Đừng tạo downtime ngoài preview.

Hiện **không có `--core-only` hoặc `--rollback` CLIflag**. Existing `--application-only` yêu cầu cả Core/Gatewayimage, target2appservices và reloadexistinglocalbackup. Với UI-only, giữ Gatewaycurrent nhưng preview vẫn phải mô tả targets/possibleGatewayrecreate và backupreload. Không dùng defaultprovision vì còn chọn n8n/accessservices.

Chỉ sau ownerapprove exactcandidate/scope, lệnh dự kiến:

```powershell
# $coreCandidate = exact image đã qualify và được duyệt, không phải baseline/placeholder bất kỳ.
& '.\openproject\ai\.venv\Scripts\python.exe' '.\openproject\ai\provision_local_stage.py' --application-only --gateway-image 'sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b' --core-image $coreCandidate
```

Nếu bị ngắt/mất điện: đọc receipt APPLYING/unknown cùng actualimages/health trước retry, không chạy lại vô điều kiện. Sau apply phải có health, per-fileparity, privatehashes/manifest/image-lock/restartpolicy, Native/auth-only differences, ledger không tăng do xemUI và Playwright trên URL lấy mới từ18090. Chỉ COMPLETE_ON_STAGING sau runtime/UIproof.

### 8.3 Rollback

Baseline cho UIupgrade là **Core7d76c1eb + Gateway456c38f6** đang bàn giao, không phải pre-MonitorCore3b/Gateway40cb (sẽ bỏ chức năng Monitor). Giữ baselineimages/private snapshots trước apply.

Khi cần: lưu post-attempt state/receipts để giữ audit; khôi phục đúng private env/manifest/image-lock snapshot và chỉ recreate approved appservices về baselinepair. Giữ database/assets/SQLiteevents/SecondBrain/keys, không restore/drop DB chỉ để quay giao diện.

Forwardprovision có lineageguard có thể từ chối ancestorimage. Đừng cho rằng đưa parent vào cùng CLI là rollback hợp lệ. Chuẩn bị/review scopedCompose recovery với cùng file set/environment trong provision_local_stage.py: stage/deep-ai/gemini-free/local-runtime vàquick/backup theo manifest; pins baselinepair, `up -d --no-deps --no-build --pull never staging-web staging-gateway`. Không defaultCompose toàn hệ thống, không `down -v`, prune hay xóaevents. Nếu recovery vượt scopepreview thì xin phê duyệt phù hợp.

## 9. Những lỗi cần tránh

- **Sai baseline/script:** old builddriver assert40cb, serving đã456; deploymentreceipt/approval61e đã dùng. Tạo run mới, không sửa lịch sử để script cũ chạy lại.
- **Clone permissions:** coldSQLite0600 owner1000, imageUSER10001 khiến uvicorn không mở được DB trong clone; PID1sleep vẫnUp. Clone qualify dùngUID1000. Không nới quyền privatefiles/serving để chữa lỗi clone.
- **Docker cp/tmpfs:** Desktop từng không copyfile tmpfs qua dockercp; dùng dockerexec stdin/stdout giữ data trong privatefiles/memory, không dump vào chat.
- **Windows live WAL:** chỉ Linuxdockerexec hoặc coldimmutablebackups, không dùng WindowsPython/Store mở livecontainerDB.
- **Default networkpools đầy:** không prunenetworks; dùng ownedexistingnetwork hoặc checked-disjoint internalsubnet cho drill, cleanup chỉ tài nguyên vừa tạo/đúnglabel.
- **Fixture role/account:** accounts dùng label BA-PM, Native roleBA; lookup chỉBA từng StopIteration. Historicalactor7 không phải syntheticfixture13. Không sửaaccount/database để né lỗi test.
- **Expiredauth:** làm mới testcodes/session qua readonlyhelper; không rotateTOTP, disableMFA hoặc chạy rootlegacysecretfallback.
- **Playwright:** SVG dùng text_content(), không inner_text(); Locator.filter() không có exact (get_by_role có). Turbo navigation phải waitURL/content, không countassert ngay sau click.
- **Worker imports:** Python từ/tmp cần PYTHONPATH=/app; không nhầm fixtureimportfail thành providerfailure.
- **Telemetry:** missingpendingduration là null/“Chưa có dữ liệu”, không0s; không fake LIVE/RUNNING/timestamps/Revieweroutput.
- **Theme:** OSmedia riêng không phản ánh Nativeuser theme. Chữa CSS/themebinding, không thay Gemini/Supervisor.

## 10. INSTRUCTIONS_FOR_GEMINI

1. Đọc file này; tiếp theo AGENTS.md, architecture.md, openproject/ai/README.md, openproject/ai/CHECKPOINT.md, execution-monitor/LATEST.json và FINAL_EXECUTION_MONITOR_READINESS.md. Ưu tiên source/runtime mới hơn lịch sử; không audit lại113tasks từ đầu.
2. Đối chiếu branch/HEAD/untracked, servingimageIDs và per-filehashmanifest. Đọc4UI files, Controller/readAPI và Native thememapping. Nếu drift, ghi rõ trước khi sửa, không reset để che drift.
3. **Bắt đầu trực tiếp UI/UX:** LightTheme/navy, typography/layout, graphclarity, AgentDetail groups, Timeline/FinalReport, History/responsive. Giữ chức năng, schema, escaping và security/recovery/reauthorization. Không chỉ tạo proposal/mockup.
4. Dùng run/candidate/output mới; buildCore từ đúng servingbaseline, qualify clone với storedrun và offlineproviderfixtures. Phân biệt REAL_UI/REAL_API/MOCK, ghi test chưa chạy, screenshots thật, hashes, defects và checkpoint.
5. Khi candidate đủ reviewable mới trình preview/exactimageIDs/impact/backup/rollback và xin **phê duyệt mới**. Không deploy/restart bằng approvalcũ hoặc tài liệu này. Giữ Main/Tunnel/n8n/database/keys/model/billing/RBAC/TOTP/data.
6. Hết phiên/quota: lưu source/candidate nào đang dở, testedimages/paths, còn việc gì, approvalpending hay deployed. Không ghi DONE/COMPLETE_ON_STAGING khi chỉ clonePASS; không xóa/ghi đè lịch sử để dọn bàn giao.

**Đầu ra mong đợi:** UI thật phù hợp OpenProjectLight, graph/detail/timeline/history dễ trình diễn hơn, không mất chức năng/bảo mật; candidate đã kiểm thử có hồ sơ để owner duyệt deployment mới.
