# Biomni API Error Analysis v2

**Date:** 2026-04-02  
**Logs analysed:** 21 log files across 2 server groups  
**Server script:** `biomni_api_server_qwen3next_80b_awq4b_drylab.py`  
**Model:** `Qwen3-Next-80B-A3B-Instruct-AWQ-4bit` (SCP nodes)  
**Total queries executed:** 6,119  
**Total HTTP 200 responses:** 8,191  
**Total log lines:** 603,483  

| Group | Ports | Node | Queries |
|---|---|---|---|
| SCP001 | 6000–6010 (11 instances) | semlscpg001 | 2,871 |
| SCP007 | 6070–6079 (10 instances) | semlscpg007 | 3,248 |

---

## Prior Fix Effectiveness — Comparison with v1 Analysis

The following table compares error counts from v1 (pre-fix, port 8010, `auto_clean_azimuth` server, 1,713 queries) against v2 (post-fix, 21 SCP servers, 6,119 queries).

| Issue | v1 Count (1,713 queries) | v1 Rate | v2 Count (6,119 queries) | v2 Rate | Δ | Verdict |
|---|---|---|---|---|---|---|
| **`biomni.utils` has no attribute `search_protocols` / `list_local_protocols` / `read_local_protocol`** | 210 | 12.3% | **0** | 0% | **−12.3%** | ✅ **RESOLVED** — system prompt import hint eliminated this entirely |
| **`No module named 'biomni.protocols'` / `'search_protocols'` / `'list_local_protocols'`** | 78 | 4.6% | **0** | 0% | **−4.6%** | ✅ **RESOLVED** |
| **`No module named 'advanced_web_search_claude'`** | 28 | 1.6% | **0** | 0% | **−1.6%** | ✅ **RESOLVED** — literature import hint fixed this |
| **`No module named 'biomni_data'`** | 34 | 2.0% | **0** | 0% | **−2.0%** | ✅ **RESOLVED** |
| **Wrong data lake path (`data/biomni/data_lake`)** | 162 | 9.5% | **0** | 0% | **−9.5%** | ✅ **RESOLVED** — "EXACT absolute path" note + `os.path.abspath` |
| **`vLLM engine is sleeping` / `Model not found`** | 38 | 2.2% | **0** | 0% | **−2.2%** | ✅ **RESOLVED** — keepalive thread prevents sleep (2,079 successful pings logged) |
| **`openai.InternalServerError` (502/503)** | 7 | 0.4% | **0** | 0% | **−0.4%** | ✅ **RESOLVED** (likely helped by keepalive) |
| **Unterminated string literals** | ~450 | 26.3% | **0** | 0% | **−26.3%** | ✅ **RESOLVED** — likely model improvement (AWQ-4bit variant handles code generation better for this pattern) |
| **Unclosed parentheses `'(' was never closed`** | ~234 | 13.7% | **0** | 0% | **−13.7%** | ✅ **RESOLVED** — same as above |
| **`invalid syntax`** | ~8 | 0.5% | 127 | 2.1% | +1.6% | ⚠️ **INCREASED** — different query mix / more complex codegen tasks |
| **Serper 400 Bad Request** | 6 | 0.4% | 27 | 0.4% | 0% | ➡️ **UNCHANGED** — same rate, pre-existing issue |
| **Circuit Breaker triggers** | 100 | 5.8% | 108 | 1.8% | −4.0% | ✅ **IMPROVED** rate (working as designed) |
| **GraphRecursionError** | 12 | 0.7% | 6 | 0.1% | −0.6% | ✅ **IMPROVED** rate |

### Summary

- **7 of 8 targeted issues fully resolved** (0 occurrences post-fix)
- Total hallucinated-import errors dropped from **~350 (20.4% of queries)** to **0 (0%)**
- Data lake path errors dropped from **162 (9.5%)** to **0 (0%)**
- vLLM sleep errors dropped from **38 (2.2%)** to **0 (0%)**

---

## New / Remaining Error Categories

### 1. Bare Function Calls Without Import — 61 NameErrors

The LLM calls biomni functions directly without importing them first. Unlike v1 (where it imported from the wrong module), now the LLM simply forgets to write the import statement at all.

| Function | NameErrors | Correct Imports | Success Rate | Correct Module |
|---|---|---|---|---|
| `advanced_web_search_claude` | 26 | 89 | 77% | `biomni.tool.literature` |
| `search_google` | 20 | 14 | 41% | `biomni.tool.literature` |
| `query_pubmed` | 15 | 20 | 57% | `biomni.tool.literature` |
| `query_scholar` | 2 | 5 | 71% | `biomni.tool.literature` |
| `list_local_protocols` | 2 | 3 | 60% | `biomni.tool.protocols` |
| `search_protocols` | 1 | 1 | 50% | `biomni.tool.protocols` |
| `query_ensembl` | 1 | 0 | 0% | `biomni.tool.database` |

**Root cause:** The system prompt's `PROTOCOL GENERATION` section has correct import hints for protocol functions and `advanced_web_search_claude`, but `search_google`, `query_pubmed`, `query_scholar`, and `query_ensembl` have no import hints in the prompt text. The function dictionary lists them with module paths, but the LLM doesn't always read and apply those paths.

**Proposed fix:** Extend the import instruction in the system prompt's `PROTOCOL GENERATION` section (or add a new `LITERATURE SEARCH` section) with:
```
from biomni.tool.literature import search_google, query_pubmed, query_scholar, query_arxiv, advanced_web_search_claude
from biomni.tool.database import query_ensembl
```

---

### 2. `numpy.skew` AttributeError — 17 occurrences

The LLM writes `np.skew(data)` which doesn't exist in NumPy. The correct function is `scipy.stats.skew()` or `pd.Series.skew()`.

| Pattern | Count |
|---|---|
| `np.skew(...)` | 37 bare calls |
| `module 'numpy' has no attribute 'skew'` | 17 errors |
| LLM self-corrects to `scipy.stats.skew` | 15 (88% self-correction rate) |

**Assessment:** The LLM self-corrects in ~88% of cases after seeing the error. This is a common LLM knowledge error (confusing `np.mean`/`np.std` pattern with `np.skew` which doesn't exist). Low priority.

**Proposed fix (optional):** Add a note to the system prompt's software library section:
```
Note: numpy does not have a skew() function. Use scipy.stats.skew() or pd.Series.skew() instead.
```

---

### 3. DataFrame Column Mismatch — 136 occurrences

The LLM guesses column names that don't exist in the dataset, producing `KeyError: "['column'] not in index"`.

| Top Hallucinated Columns | Count |
|---|---|
| `['Normal tissue', 'Tumor tissue']` | 8 |
| `['Normal tissue', 'Tumor tissue', 'Log2 fold change']` | 8 |
| `['Normal tissue', 'Tumor tissue', 'Tumor/normal log2 fold change']` | 6 |
| Various protein/expression column guesses | ~114 |

**Assessment:** These errors occur when the LLM reads a dataset description (from the data lake listing) but guesses column names rather than first inspecting them with `df.columns` or `df.head()`. The LLM usually self-corrects on retry by examining actual columns.

**Proposed fix:** Add a note to the data lake section of the system prompt:
```
BEST PRACTICE: Always inspect DataFrame columns with df.columns.tolist() and df.head() before accessing specific columns. Do not guess column names.
```

---

### 4. Shape / Broadcast Errors — 25 occurrences

`operands could not be broadcast together with shapes (1684,) (1183,)` — the LLM tries to perform element-wise operations on arrays of different lengths (e.g., mismatched gene lists across datasets).

**Assessment:** Data-specific errors. The LLM should be aligning or filtering data before operations. Low-medium priority, self-corrects on retry in most cases.

---

### 5. Empty Sequence / No Data Errors — 53 occurrences

| Error | Count |
|---|---|
| `attempt to get argmin of an empty sequence` | 15 |
| `No columns to parse from file` | 16 |
| `min()/max() arg is an empty sequence` / `pop from empty list` | 10 |
| `pickle data was truncated` | 7 |
| `string indices must be integers` | 9 |

**Assessment:** These arise when the LLM reads empty files, empty API responses, or truncated pickle files (especially `genebass_pLoF_filtered.pkl`, `gwas_catalog.pkl`). The pickle truncation errors suggest corrupted files on the SCP nodes.

**Proposed fix:** Check integrity of `.pkl` files in `data/biomni_data/data_lake/`:
```bash
python -c "import pickle; pickle.load(open('data/biomni_data/data_lake/genebass_pLoF_filtered.pkl','rb'))" 
```

---

### 6. Serper API 400 Errors — 27 occurrences

Same rate as v1 (0.4% of queries). The LLM sends malformed queries to the Serper Google search API.

**Proposed fix:** Add input sanitization in `biomni/tool/literature.py`'s search functions — truncate query to 256 chars, strip special characters.

---

### 7. Hallucinated Functions — 2 occurrences

| Error | Count |
|---|---|
| `cannot import name 'query_gtex' from 'biomni.tool.database'` | 1 |
| `Protocols.io access token is not configured` | 1 |

**Assessment:** `query_gtex` does not exist — LLM hallucinated it. The protocols.io token missing is a config issue on SCP nodes.

---

### 8. Timeout / Connection Errors — 8 occurrences

Generic `timeout` errors, likely when the vLLM backend is briefly overloaded. Acceptable rate (0.1% of queries).

---

## Actionable Fix Summary

| # | Issue | Impact | Fix Location | Priority |
|---|---|---|---|---|
| 1 | Bare function calls (search_google, query_pubmed, etc.) — 61 NameErrors | Medium | `biomni/agent/a1.py` system prompt — add import hints for all literature functions | 🔴 High |
| 2 | DataFrame column guessing — 136 errors | Medium | `biomni/agent/a1.py` system prompt — add "always inspect columns first" note | 🟡 Medium |
| 3 | `np.skew` hallucination — 17 errors (88% self-correct) | Low | `biomni/agent/a1.py` system prompt — optional note | 🟢 Low |
| 4 | Serper 400 errors — 27 | Low | `biomni/tool/literature.py` — input sanitization | 🟡 Medium |
| 5 | Truncated pickle files — 7 | Low | Check file integrity on SCP nodes | 🟡 Medium |
| 6 | `query_gtex` hallucination — 1 | Minimal | N/A — rare | 🟢 Low |

---

## Notes

- The keepalive thread is working effectively: 2,079 successful pings logged, zero vLLM sleep errors.
- The `import_instruction` line ("IMPORTANT: When using any function, you MUST first import it from its module") only appears when `use_tool_retriever=True` (i.e., `is_retrieval=True`). The drylab servers default to `use_tool_retriever=False`, meaning the LLM sees the function dictionary but not the explicit import reminder. This explains why bare-call NameErrors still occur.
- Circuit breaker is working as designed — 108 triggers at 1.8% rate (improved from 5.8% in v1).
- The AWQ-4bit model appears to generate fewer syntax errors (unterminated strings, unclosed parens) compared to the FP8 model, though the query mix is different.
