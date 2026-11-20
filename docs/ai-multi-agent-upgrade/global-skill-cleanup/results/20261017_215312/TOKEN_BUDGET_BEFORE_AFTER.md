# ANTIGRAVITY TOKEN BUDGET COMPARISON REPORT
**Generated at:** 2026-10-17T21:53:15.101537  
**Target:** Global Skills Cleanup (`~/.gemini/config/skills`)

## 1. Executive Summary

| Metric | Before Cleanup | After Cleanup | Net Reduction |
| :--- | :--- | :--- | :--- |
| **Global Skills Count** | **1,463** | **77** | **-1386 (94.7%)** |
| **Plugin Skills Count** | 91 | 91 | 0 (Untouched) |
| **Built-in Skills Count** | 8 | 8 | 0 (Untouched) |
| **Total Active Registered Skills** | **1,561** | **175** | **-1386** |
| **Estimated Global Customization Tokens** | **~88,382 tokens** | **~5,506 tokens** | **-~82,876 tokens (-93.8%)** |
| **Total Customization Tokens (Global + Plugins + Builtin)** | **~101,573 tokens** | **~18,697 tokens** | **-~82,876 tokens** |
| **Context Window Budget Limit** | 20,000 tokens | 20,000 tokens | — |
| **Context Overrun Status** | **+81,573 tokens (507.9% OVER)** | **WITHIN BUDGET** | **RECOVERED REASONING CAPACITY** |
| **Excluded Skills from Prompt** | **~1,180 skills excluded** | **0 skills excluded** | **100% of kept skills active in context** |

## 2. Key Impacts
1. **Zero Excluded Skills:** All 77 whitelisted global skills are now indexed directly in Antigravity's active context window.
2. **Context Window Relief:** Token consumption of Global Skills reduced from ~88,382 down to ~5,506 tokens, freeing ~83,000 tokens of LLM attention and working memory.
3. **No Hallucination Noise:** Removed 1,385 irrelevant skills (crypto, niche personas, redundant cloud SDKs, marketing bots).
