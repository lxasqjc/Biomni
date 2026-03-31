# Biomni API Error Analysis

**Log analysed:** `logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth_8010.log`  
**Server:** `biomni_api_server_qwen3_next_80b_auto_clean_azimuth.py`, port 8010  
**Model:** `Qwen3-Next-80B-A3B-Instruct-FP8` @ `vllm.paas-jade.astrazeneca.net/v1`  
**Total successful requests (HTTP 200):** 1,713  
**Log size:** 260,447 lines  

---

## Error Summary by Category

### 1. LLM Code Generation Syntax Errors — ~700 occurrences

These errors occur when the model generates syntactically broken Python code that the executor catches and reports as an `<observation>Error: ...</observation>`.

| Error | Count | Root Cause |
|---|---|---|
| `unterminated string literal (detected at line N)` | ~450 | LLM generates multi-line strings without proper closing |
| `'(' was never closed (at line N)` | ~234 | LLM generates unclosed parentheses |
| `closing ')'/']' does not match '('/'['` | ~13 | Mismatched brackets in generated code |
| `invalid syntax` / `invalid syntax. Perhaps you forgot a comma?` | ~8 | Other codegen syntax issues |

**Assessment:** These are LLM output quality issues, not Biomni bugs. The executor correctly catches and reports them. The circuit breaker prevents infinite retry loops.

---

### 2. Hallucinated Import Paths — ~350 occurrences

The LLM tries to import functions from incorrect module paths. The functions **do exist** in Biomni but in `biomni.tool.protocols`, not in `biomni.utils`.

| Error | Count | Correct Import |
|---|---|---|
| `module 'biomni.utils' has no attribute 'search_protocols'` | 70 | `from biomni.tool.protocols import search_protocols` |
| `module 'biomni.utils' has no attribute 'read_local_protocol'` | 70 | `from biomni.tool.protocols import read_local_protocol` |
| `module 'biomni.utils' has no attribute 'list_local_protocols'` | 70 | `from biomni.tool.protocols import list_local_protocols` |
| `No module named 'biomni_data'` | 34 | Data is accessed via path, not a Python module |
| `No module named 'search_protocols'` | 32 | Same — top-level import not valid |
| `No module named 'advanced_web_search_claude'` | 28 | `from biomni.tool.literature import advanced_web_search_claude` |
| `No module named 'biomni.protocols'` | 24 | `from biomni.tool.protocols import ...` |
| `No module named 'list_local_protocols'` | 22 | Same as above |
| `cannot import name 'list_local_protocols' from 'biomni.data'` | ~8 | Same |
| `No module named 'biomni.search'`, `biomni.tools`, `biomni.web`, `web_search` | ~30 | Various hallucinated module paths |

**Root cause:** The system prompt's `PROTOCOL GENERATION` section instructs the LLM to call `search_protocols()`, `list_local_protocols()`, and `read_local_protocol()` but does not specify the import path. The LLM guesses `biomni.utils` (the most frequently imported biomni module) rather than `biomni.tool.protocols`.

**Fix:** Add the correct import statement to the system prompt's `PROTOCOL GENERATION` section.

---

### 3. Data Lake Path Errors — ~162 occurrences

The LLM constructs incorrect absolute paths when accessing the data lake.

| Error Pattern | Count | Correct Path |
|---|---|---|
| `/data/jinc/git_chen/Biomni/data/biomni/data_lake/...` | 114 | `/data/jinc/git_chen/Biomni/data/biomni_data/data_lake/...` |
| `/data/jinc/git/chen/Biomni/data/biomni/data_lake/...` | 48 | Same (`git/chen` → `git_chen` — old hallucination, pre-dates path fix) |

**Root cause (pre-fix):** `self.path` was stored as a relative path `./data/biomni_data`, causing the system prompt to show a relative data lake path. The LLM then hallucinated the wrong absolute path.

**Root cause (post-fix, remaining 114):** Even with `os.path.abspath` applied (fix in `biomni/agent/a1.py` commit `c87cd32`), the LLM still writes `data/biomni/` instead of `data/biomni_data/` when constructing paths from scratch in generated code — a short-term memory / reconstruction error.

**Fix:** Add an explicit path note to the data lake section of the system prompt.

---

### 4. Backend / Infrastructure Errors — ~57 occurrences

| Error | Count | Cause |
|---|---|---|
| `openai.BadRequestError: Model not found or vLLM engine is sleeping` | 38 | vLLM auto-sleep / cold start on `vllm.paas-jade.astrazeneca.net` |
| `openai.InternalServerError` (nginx 502/503) | 7 | vLLM backend overloaded |
| `Error performing web search: 400 Bad Request` (Serper API) | 6 | Invalid query sent to Serper search API |

**Fix:** Add a background keepalive thread to all API servers that periodically pings the vLLM backend to prevent sleep.

---

### 5. Agent Loop Errors — ~112 occurrences

| Error | Count | Cause |
|---|---|---|
| `[Circuit Breaker] search failure #N` | 100 | Circuit breaker triggering (working as designed) |
| `GraphRecursionError: Recursion limit of 500 reached` | 12 | Agent loop failed to converge — likely stuck in search retry loop |

**Assessment:** The circuit breaker (firing 100 times) is **working correctly** — it prevents infinite search loops. The 12 `GraphRecursionError` cases are requests where the agent exhausted 500 LangGraph steps without a `<solution>` tag, indicating the task was too open-ended or the agent got stuck.

---

## Actionable Fixes

| # | Issue | Fix Location | Status |
|---|---|---|---|
| 1 | Protocol functions imported from wrong module | `biomni/agent/a1.py` system prompt | ✅ Fixed in commit |
| 2 | Data lake path reconstruction errors | `biomni/agent/a1.py` system prompt | ✅ Fixed in commit |
| 3 | vLLM engine sleeping → 400 errors | All API server scripts | ✅ Fixed in commit |
| 4 | LLM codegen syntax errors | LLM quality — not fixable from Biomni side | ⚠️ Mitigated by circuit breaker |
| 5 | GraphRecursionError (12 cases) | Handled by 500-step limit — acceptable | ⚠️ No action needed |

---

## Notes

- The `git/chen` path errors (48 occurrences) pre-date the `os.path.abspath` fix applied on 2026-03-19. These should not appear in newer logs.
- The circuit breaker (`_consecutive_search_failures`) is functioning as intended — it prevents the agent from hammering search APIs after repeated failures.
- Search result caching (`~/.biomni/search_cache`, disk-based) is active and shared across all parallel server instances, reducing 429 rate-limit errors.
