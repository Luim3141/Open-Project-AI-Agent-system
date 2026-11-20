# Grouped source / exact quote diagnostic04/11/2026

Same six observed DEV questions and unchanged source spans, grouped by Native source; one answer+exact quote with128output tokens within the original pilot plan. No gold support was inserted. Local Qwen3 1.7B only; no MAIN or heldout changes.

The run stopped at the third question with INVALID_RESPONSE_ValueError. Two responses were validated: create/list-VI selected the unit name without SQLite/create/list proof; create/list-EN quoted the exact functional title but generated only the vague answer “AI unit”. Literal supporting-span count1/2 does not certify answer quality. Third response was rejected by validation; the exact underlying ValueError and rejected response were not retained, so hallucination versus ambiguous/mismatched quote is not established. Do not rerun simply to repair this report.

No full DEV/holdout or deployment follows from this failed gate. Source grouping/quote generation did not establish bilingual answerability. Before another genuinely different candidate, retain invalid replies privately and log only fixed safe validation codes, freeze it, and obtain independent evaluation after implementation. Preserve existing three Owner fixture-label approvals; do not treat them as quality sign-off.
