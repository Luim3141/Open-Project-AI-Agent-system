# Remaining issues / chưa nghiệm thu đầy đủ

1. **FUNCTIONAL PARTIAL**, không FULL PASS: mutation/control flows trên MAIN chưa được phép thực hiện mới. Không cần người dùng duyệt lại những quyết định đã chốt; nếu muốn nghiệm thu livewrites cần một scope cụ thể mới, không tự đổi gates.
2. RAG lexical retrieval/citations hoạt động, nhưng semantic answerability gate vẫn FAILED/FROZEN/UNVERIFIED_RETRIEVAL theo evidence hiện hành. Không giảm threshold, reindex toàn bộ hay generate answer để che gate.
3. Một UI RAG lượt trước không hiện results; subsequent trace200~11s/full14checksPASS. Chưa có metadata đủ để kết luận abort20s hay root cause khác. Screenshot Studio sau burst cũng có Explorer429 dù graph đã hiển thị; probe riêng sau đó tải19Task/HTTP200. Chưa chứng minh mọi tình huống burst đều phục hồi. Report503 ban đầu tương tự chưa biết upstreamcode; masking contract đã sửa nhưng không gọi đó là proof initial429.
4. TG-R08/R09/R10 natural-language globalblocked/pending/allartifact wording chưa đủ fresh Gemini/Telegram loops; direct adapters semantic proof có, globalactiveOwner35→36 có. Budget18/20, reserve2; không tăng quota/reset hoặc đổi model.
5. 17n8nactive contracts/history không thay thế fresh trigger+verifiedbusinesssideeffect của từng branch. Offline/retry/duplicate cases dùng isolatedtests; không tạo outage/sendspam để đóng gate.
6. GitHubPR15 có0remoteCIchecks/0humanreviews; local AIReviewerPASS+JUnit64 khác remoteCI.398 vẫn cần Owner acceptance; không tựapprove/merge/deploy.
7. Historical18codingreceipts requested3.5lite nhưng khôngpersist resolvedversion; không backfill dữ liệu giả. New bot receipts có actualresolved3.5lite. Metadata access xác minh đúng3.5lite, không inference thêm.
8. MCP action catalog/source/isolatedtransport verified, chưa dùng newMAINMCPsession qua đủroles. Các legacy modules absent được exclude rõ; commandsNOTTESTED trong matrix giữ nguyên.
9. Performance/multi-tab/tail/mobilefullcampaign DEFERRED ngoài task này; historical p95gate chưa đóng. Không dùng nó để phủ nhận những functional reads đã PASS.

Không còn lỗi P0 đã được tái hiện chưa sửa. Các F1–F5 đã deploy và targeted regression pass; coverage gaps/intermittentRAG vẫn được giữ công khai, không đảm bảo toàn hệ thống không còn lỗi.
