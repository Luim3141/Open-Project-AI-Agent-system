# P00 — Free-only / license audit, 15/10/2026

## Actual provider observation (read-only browser, no API call)

- Existing signed-in QLDAPM Google account (PRO badge separately visible), exact project `gen-lang-client-0020540057` / Default Gemini Project: Projects page **Free tier**.
- Rate Limit page URL `https://aistudio.google.com/u/1/rate-limit?timeRange=last-28-days&project=gen-lang-client-0020540057`:
  - Gemini 3.5 Flash Lite: 15 RPM / 250000 TPM / 500 RPD.
  - Displayed usage 6 RPM /39.4K TPM /214 RPD is **peak over 28 days**, not remaining quota today.
  - TPD not exposed in this observation; do not invent it or claim unlimited TPD.
- Billing page `https://aistudio.google.com/u/1/billing`: **No billing account**. Same account, only the exact project listed. No Set up billing/prepayment clicked. This is UI evidence, not a billing API response or cryptographic entitlement proof.
- [Official pricing](https://ai.google.dev/gemini-api/docs/pricing) currently lists model `gemini-3.5-flash-lite` with Free Tier input/output. [Rate-limit documentation](https://ai.google.dev/gemini-api/docs/rate-limits) requires current project limits; daily reset Pacific, limits shared by project, not API-key multiplication.
- [Gemini terms](https://ai.google.dev/gemini-api/terms) reviewed as a deployment privacy dependency. Unpaid content has different data handling; current business-content consent is not a classification/redaction proof. No private tickets/code/PII sent in P00.
- Key PRESENT and retained, not re-enrolled; current validity not probed. Provider remains OFF until Free-only/privacy gates implemented. Historical continuous billing authorization remains in private proof as history, not usable authority under new scope. Do not enable it with the old CLI.
- Newly initiated Gemini/provider requests: **0**; billing/credit/project/key/account privileges changed: **0**. Staging ledger history469 retained. Zero new purchase/subscription; not a full Google billing ledger reconciliation.

## License decisions / missing fact

- [Docker Desktop official license](https://docs.docker.com/subscription-billing/desktop-license/) checked: free for personal/education/noncommercial open source, or qualifying small business with **both** <250 employees and <USD10m annual revenue. Five app users alone do not prove organization eligibility. Host Windows Enterprise edition does not establish it either. Owner clarification sent; **eligibility PENDING**, no purchase requested. Existing containers/backup diagnostics only; no new n8n installation yet. If ineligible, evaluate free Docker Engine-compatible runtime separately, not a paid plan or silent migration.
- n8n docs URL in original plan currently returns Page Not Found. Checked primary [n8n LICENSE.md](https://github.com/n8n-io/n8n/blob/master/LICENSE.md?plain=1) and [official license documentation source](https://github.com/n8n-io/n8n-docs/blob/main/docs/n8n-community-license/README.md). Sustainable Use License allows own internal business/personal/noncommercial use; Enterprise files/features excluded. Scope is internal reports for five QLDAPM users with one owner editor; do not resell hosted n8n/editor access or use paid project/SSO features. Exact release license will be checked again at P04 pinning; n8n not installed during P00.
- Research of vendor licensing source on GitHub is an engineering dependency check; no GitHub Research/crawler or product research agent implemented.

P00 acceptance cannot be advertised as complete free-license qualification until organization eligibility is resolved. Free alternative is deterministic/local operation pending that fact. No billing activation or trial permitted.

## Owner clarification — 15/10/2026

Owner answered the in-chat licensing question: **Cá nhân / học tập**. This resolves Docker Desktop personal/education eligibility for the requested local five-person system; no company-size/revenue assumption or paid plan. P00-09 can close against this answer plus ADR/observed Free-tier evidence. This does not waive any runtime, privacy, LAN or release gate.
