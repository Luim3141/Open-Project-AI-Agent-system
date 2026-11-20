# Minimal Main Gemini smoke — approval required

Scope: existing Main provider, existing saved key, project `gen-lang-client-0020540057`, saved model `gemini-3.5-flash-lite`, Free Tier only. No key/model/billing change, no restart, no business data or source files sent.

Send only the existing adapter's fixed public prompt:

> Reply with exactly QLDAPM_OK. This is a synthetic connectivity test.

Use actual Main adapter `Gemini.smoke`, after its production proof/key/model/expiry/quota guard validates. Maximum two Google requests: one `countTokens`, then one `generateContent` with `maxOutputTokens=128` and minimal thinking. Both count against the conservative local request allowance. No retry, agent loop, tool invocation, WP write or paid fallback. Stop on invalid proof, changed settings, quota, provider/network error, unexpected response or output other than QLDAPM_OK.

Record redacted outcome and Main local usage. A successful smoke establishes fixed-text connectivity only; it does not prove a full Gemini multi-agent chain, billing status via Google Console, or all specialist outputs. Do not copy Stage readiness receipts or manufacture a Main generation receipt. Any follow-up live multi-agent call needs its own reviewed budget.

Owner's existing approval says “Duyệt cả hai, chưa gọi Google”. This preview requires a new explicit approval before either request. Until then provider live status remains NOT_RUN.
