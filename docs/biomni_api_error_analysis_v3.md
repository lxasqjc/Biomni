# Biomni API Error Analysis v3

**Date:** 2026-04-02  
**Logs analysed:** 51 log files across 5 SCP server groups  
**Server script:** `biomni_api_server_qwen3next_80b_awq4b_drylab.py`  
**Model:** `Qwen3-Next-80B-A3B-Instruct-AWQ-4bit` (SCP nodes)  
**Total queries executed:** 5,698  
**Total HTTP 200 responses:** 5,695  
**Total log lines:** 618,996  
**Total `<observation>Error` blocks:** 830  
**Overall error rate:** 14.6% (830 errors / 5,698 queries)  

| Group | Ports | Node | Queries | Errors | Rate |
|---|---|---|---|---|---|
| SCP001 | 6000–6010 (11 instances) | semlscpg001 | 1,253 | 158 | 12.6% |
| SCP002 | 6020–6029 (10 instances) | semlscpg002 | 1,141 | 185 | 16.2% |
| SCP003 | 6030–6039 (10 instances) | semlscpg003 | 940 | 186 | 19.8% |
| SCP007 | 6070–6079 (10 instances) | semlscpg007 | 1,086 | 150 | 13.8% |
| SCP012 | 6120–6129 (10 instances) | semlscpg012 | 1,278 | 151 | 11.8% |

---

## Prior Fix Effectiveness — Comparison with v1 and v2

### v1 → v3 (Originally Targeted Issues)

All 8 issues targeted in the v1 fix round remain **fully resolved** across 5,698 queries:

| Issue | v1 Count (1,713 q) | v1 Rate | v3 Count (5,698 q) | v3 Rate | Verdict |
|---|---|---|---|---|---|
| `biomni.utils` hallucinated imports | 350 | 20.4% | **0** | 0% | ✅ **RESOLVED** |
| `No module named 'biomni.protocols'` | 78 | 4.6% | **0** | 0% | ✅ **RESOLVED** |
| `No module named 'advanced_web_search_claude'` | 28 | 1.6% | **0** | 0% | ✅ **RESOLVED** |
| `No module named 'biomni_data'` | 34 | 2.0% | **0** | 0% | ✅ **RESOLVED** |
| Wrong data lake path (`data/biomni/data_lake`) | 162 | 9.5% | **0** | 0% | ✅ **RESOLVED** |
| vLLM engine sleeping / Model not found | 38 | 2.2% | **0** | 0% | ✅ **RESOLVED** |
| `openai.InternalServerError` (502/503) | 7 | 0.4% | **0** | 0% | ✅ **RESOLVED** |
| Unterminated string / unclosed parentheses | ~684 | 39.9% | **0** | 0% | ✅ **RESOLVED** |

### v2 → v3 (Issues Identified in v2 Analysis)

| Issue | v2 Count (6,119 q) | v2 Rate | v3 Count (5,698 q) | v3 Rate | Δ Rate | Verdict |
|---|---|---|---|---|---|---|
| **NameError (all)** | 61 | 1.00% | 51 | 0.90% | −0.10% | ➡️ Slightly improved |
| ↳ `advanced_web_search_claude` | 26 | 0.42% | 16 | 0.28% | −0.14% | ➡️ Slightly improved |
| ↳ `search_google` | 20 | 0.33% | 10 | 0.18% | −0.15% | ➡️ Slightly improved |
| ↳ `query_pubmed` | 15 | 0.25% | 5 | 0.09% | −0.16% | ➡️ Slightly improved |
| **Column guessing / not-in-index** | 136 | 2.22% | 274 | 4.81% | +2.59% | ⚠️ **WORSENED** |
| **`np.skew` hallucination** | 17 | 0.28% | 5 | 0.09% | −0.19% | ✅ Improved |
| **Serper 400 Bad Request** | 27 | 0.44% | 44 | 0.77% | +0.33% | ⚠️ **WORSENED** |
| **Circuit breaker triggers** | 108 | 1.76% | 92 | 1.61% | −0.15% | ➡️ Unchanged |
| **GraphRecursionError** | 6 | 0.10% | 6 | 0.11% | +0.01% | ➡️ Unchanged |
| **Invalid syntax (single-line code)** | 127 | 2.08% | 77 | 1.35% | −0.72% | ✅ Improved |
| **Pickle data truncated** | 7 | 0.11% | 13 | 0.23% | +0.11% | ➡️ Slightly worsened |

### Summary

- **All 8 v1 fixes remain fully effective** (0 occurrences across 5,698 queries)
- v2 fixes show **marginal improvement** on NameErrors (−0.10%) and np.skew (−0.19%)
- **Column guessing is the #1 new problem** (4.81%), up from 2.22% in v2 — likely due to different query mix (more proteomics questions)
- **Serper 400 errors increased** due to error result caching — failed queries get permanently cached

---

## New / Remaining Error Categories (v3)

### 1. Column Key Guessing — 274 errors (4.81%)

**The single largest error category.** The LLM guesses DataFrame column names instead of inspecting them first.

Two sub-patterns:
- **KeyError on column name** (152): `'gene_symbol'`, `'Gene'`, `'gene'`, `'gene_id'`, `'gene_name'`, `'gene_set'`, `'DepMap_ID'`
- **"not in index" errors** (122): `"['Normal tissue', 'Tumor tissue'] not in index"`

**Primary offender:** `proteinatlas.tsv` (40+ errors) — the LLM guesses columns like `'Normal tissue'`, `'Tumor tissue'`, `'Protein abundance'` which don't exist. The file has 107 columns with names like `'RNA tissue specificity'`, `'Cancer prognostics - Bladder...'`, etc.

**Root cause:** Despite the existing prompt instruction "Always inspect DataFrame columns with df.columns.tolist() and df.head() before accessing specific columns", the LLM still guesses.

**Fix (v3):** Strengthen the CODING BEST PRACTICES section with explicit pattern and add a data lake column preview hint for frequently-misused files.

---

### 2. Invalid Syntax (Single-Line Code) — 77 errors (1.35%)

The LLM generates multi-statement Python code on a single line without newlines, causing `SyntaxError: invalid syntax`.

**Examples:**
```
import pandas as pd import os # Check file path...
with open(...) as f: content = f.read() print(content)
```

**Root cause:** The LLM sometimes outputs `<execute>` blocks with all code on a single line. When passed to `exec()`, this is invalid Python.

**Fix (v3):** Add prompt hint about multi-line code in execute blocks.

---

### 3. NameError (Missing Imports) — 51 errors (0.90%)

The LLM calls biomni functions without importing them first. Slightly improved from v2 (61 → 51) but still present.

| Function | v2 Count | v3 Count | Change |
|---|---|---|---|
| `advanced_web_search_claude` | 26 | 16 | −38% |
| `search_google` | 20 | 10 | −50% |
| `query_pubmed` | 15 | 5 | −67% |
| `extract_url_content` | 0 | 4 | NEW |
| `query_scholar` | 2 | 3 | +50% |
| `math` | 0 | 2 | NEW |
| `query_ensembl` | 1 | 1 | — |
| `query_uniprot` | 0 | 1 | NEW |
| `search_protocols` | 1 | 1 | — |
| Other (data variables) | — | 8 | NEW |

**New finding:** `extract_url_content` (4 errors) and `query_uniprot` (1 error) are not in the FUNCTION IMPORT REFERENCE.

**Fix (v3):** Add missing functions to the import reference, especially `extract_url_content`.

---

### 4. Serper 400 Bad Request — 44 errors (0.77%)

Web search failures from the Serper API. **Worsened from v2** despite the query sanitization fix (truncate to 256 chars).

**Root cause:** Error results are permanently cached in the disk cache (`_search_cache[key] = err`). Once a query returns a 400 error, all subsequent calls with the same query return the cached error immediately — the "[Cache HIT]" prefix confirms this. The `query.strip()[:256]` sanitization was added but the stale error cache entries from before the fix still cause failures.

**Fix (v3):** 
1. Do NOT cache error results — remove `_search_cache[key] = err` for 400/transient errors
2. Clear stale error entries from the existing cache

---

### 5. Shape/Data Operation Errors — 98 errors (1.72%)

Various errors from operating on data without validation:

| Sub-category | Count | Example |
|---|---|---|
| Shape broadcast mismatch | 30 | `operands could not be broadcast together with shapes (1684,) (1183,)` |
| Empty sequence/list | 33 | `min() arg is an empty sequence`, `pop from empty list` |
| No columns to parse | 20 | `No columns to parse from file` |
| String type errors | 16 | `string indices must be integers, not 'str'` |
| dtype mismatch | 13 | `cannot use method 'nlargest' with this dtype` |
| str accessor | 11 | `Can only use .str accessor with string values!` |
| Insufficient data | 11 | `` `x` and `y` must have length at least 2 `` |
| Reindex duplicates | 8 | `cannot reindex on an axis with duplicate labels` |

**Root cause:** LLM doesn't validate data shapes/types before operations.

**Fix (v3):** Add data validation guidance to CODING BEST PRACTICES.

---

### 6. Attribute Errors — 23 errors (0.40%)

| Pattern | Count |
|---|---|
| `numpy.skew` | 5 |
| `pandas.np` | 1 |
| `numpy.ndarray.skew` | 1 |
| Type mismatches (`.startswith` on int, `.strip` on float64) | 16 |

**Fix:** np.skew hint exists but needs reinforcement. Type-checking guidance in best practices.

---

### 7. Pickle Data Truncated — 13 errors (0.23%)

```
pickle data was truncated
```

**Root cause:** Corrupted `.pkl` files on SCP nodes. These are data lake files that weren't fully downloaded.

**Fix:** Not fixable from API side — requires re-downloading the pickle files on affected SCP nodes.

---

### 8. File Not Found — 4 errors (0.07%)

| Path | Count |
|---|---|
| `data_lake/gtex_tissue_gene_gene_tpm.parquet` | 1 |
| `biomni/know_how/resource/addgene_grna_sequences.csv` | 1 |
| `biomni/know_how/resource/CRISPick_download_links.txt` | 1 |
| Cache file (very long path) | 1 |

**Root cause:** Missing resource files on some SCP nodes.

---

## v3 Actionable Fixes

| # | Fix | Category | Expected Impact |
|---|---|---|---|
| 1 | **Stop caching error results in search functions** | Serper 400 | Eliminate ~44 cached error results being re-served |
| 2 | **Clear stale error entries from disk cache** | Serper 400 | Remove existing poison cache entries |
| 3 | **Strengthen column inspection prompt** — add explicit `df.columns.tolist()` pattern before ANY DataFrame column access | Column guessing | Reduce 274 errors |
| 4 | **Add `extract_url_content` and `query_uniprot` to FUNCTION IMPORT REFERENCE** | NameError | Reduce 5 errors, prevent new ones |
| 5 | **Add multi-line code hint to system prompt** — "Always write Python code with proper newlines between statements" | Invalid syntax | Reduce 77 errors |
| 6 | **Add data validation hints** — check for empty DataFrames, validate shapes before operations | Data operation errors | Reduce 98 errors |

---

## Appendix: Error Rate Trend Across Versions

| Metric | v1 (1,713 q) | v2 (6,119 q) | v3 (5,698 q) |
|---|---|---|---|
| Hallucinated imports | 20.4% | 0% | 0% |
| Data lake path errors | 9.5% | 0% | 0% |
| vLLM sleep errors | 2.2% | 0% | 0% |
| Syntax errors (string/paren) | 39.9% | 0% | 0% |
| NameError (missing import) | — | 1.00% | 0.90% |
| Column guessing | — | 2.22% | 4.81% |
| Invalid syntax (single-line) | — | 2.08% | 1.35% |
| Serper 400 | 0.4% | 0.44% | 0.77% |
| np.skew | — | 0.28% | 0.09% |
