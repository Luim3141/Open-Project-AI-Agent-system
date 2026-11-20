# Main329 schedule validation — 21/10/2026

Owner selected the Staging plan as baseline:5Oct–27Nov2026, Mon–Fri,4two-week Sprints. `MAIN_SCRUM_329_SCHEDULE_PROPOSAL.csv` maps exact Native Main IDs/subjects and preserves actor/status/scheduling-mode fields. Six Staging-only fixtures436/441/442/443/446/447 are excluded. No dates, statuses or Sprint assignments have been written.

**The unchanged Staging proposal is not safe to apply.** All343actual Main follows relations were checked using Native semantics (relation.from=successor, to=predecessor; even lag0 requires a later start than predecessor finish).191relations conflict, involving186successor Work Packages. Details: `schedule-constraint-analysis.json`. Native form/cascade dry-run remains PENDING; this report does not claim Native acceptance.

There are72actor-days with concurrent leaf assignments and a peak of9leaf items for one actor/day. These are concurrency signals, not estimates of nine full days of work. Effort estimates and actual availability are unknown. All53Task containers currently belong to Main BA20; legacy display name “QLDAPM PM” is not evidence that their business role is PM. Do not silently reassign them or treat rollup Tasks as extra leaf effort.

Planned dates in the past mean potential overdue work, not accepted completion. Keep statuses and native QA/PM gates until actual completion/acceptance evidence exists. The CSV explicitly preserves each current status and flags past planned finishes.

Next: calculate a dependency-compatible adjustment, qualify date propagation on a separate isolated fixture/clone, compare deadline/Sprint effects, and present the concrete change for Owner review. Do not bulk apply the invalid baseline merely because Owner said to follow Staging.


## Native qualification đã thực thi —21/10/2026

Bản serial-leaf đầu tiên dừng an toàn sau2clonepatches khi form104 kéo ngày về6Oct (104follows102, song song103). Đây là khác biệt proposal/NativeASAP; không sửa scheduler hoặc épmanual để che lỗi. Bản mới `MAIN_SCRUM_329_NATIVE_FORK_PROPOSAL.csv` giữ graphspecification→BE/FEparallel→QA→acceptance. MỗiTask5workingdays; durations1/2/2/1/1, không phải effort.53manualspecificationleaves và212automaticleaves giữ nguyên. Owner hiện cóspecificationleafPM19/acceptanceleafBA20; không tựswap để khớp tênrole.

`dry_run_native_schedule.py --resume-native-fork` đã thực thi realNativeforms/PATCH trênownedclone, reconcilepartialcheckpoint vàgiữbackuphash. 265leafread/patch vàparentrollupkhớp đủ329row,343followsPASS,480.14s. Assignees/status/modes/Sprint/Versiongiữnguyên;8Mainprotectedtablesunchanged. `schedule-native-fork-clone-dryrun.json` làbằngchứng; khôngrerunblind.

CSVsha256 `6d0991b35c9836ef7e99f32d4aed80f3dfce9573a278f4952c3abe21b791dc1d`. GiữCSV đãqualification bấtbiến,thôngtinNativeDryRunPENDINGtrongCSV phảnánhthờiđiểmlậpproposal; sidecarJSONghiPASSvàbindexacthash,khôngđổibytes đểgiảchứngthực. Deadline8Jan2027/7two-weekiterations; criticalchain14Tasks/70workingdaysvớigiảđịnh5ngàyTask. NativecalendarMon–Fri/0weekdayexceptions; ngàynghỉthực tế/capacity/effortchưaxácnhận.77actor-daysconcurrent,peak12leafitems/actor/day: KHÔNGcapacityPASS hoặc camkết tiếnđộ.

Nếu chọnphươngán này, projectedNativeSprintmembershipchanges234/318; thêmiterationsS6/S7,VersionsSprint5/6/7 vàgánRoadmapVersions318non-Epics. BulkSprint/Versionqualification CHƯA chạy vàchưaduyệt. NativeV3Sprints chỉcóGET trongsourcehiệnhành; viếtSprints phảiđiquaNativeRailsweb/contracts/services,khôngtựbịaPOSTAPI hoặcARupdate. Câu hỏiOwnervề08/01/2027 đangchờ, chỉ là chọnmốcđểhoànthiệnproposal cuối, chưa phảiphêduyệtbulk/Mainapply.

Không tựDone từngàyquáhạn. KhôngMainWPdate/status/membershipwrites; MainGanttdatebars/Roadmapcardschưađượctuyênbốhoànthành.
