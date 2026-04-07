# Biomni Performance & Stability Fixes — Round 4

**Date:** 2026-04-07  
**Branch:** `private/local-development-v1`  
**Commits:** `7867e18` · `9d16118` · `1d4a6fa`  
**Context:** Follows machine stability investigation in [`biomni_machine_stability_analysis.md`](biomni_machine_stability_analysis.md)

---

## Overview

Four targeted fixes applied after identifying the root causes of machine instability and slow data loading during large-scale benchmark experiments. Together these reduce disk pressure by ~25 GB, eliminate a silent TCP socket leak, and make repeated data access 10–100× faster.

| # | Fix | Root cause | Impact |
|---|-----|-----------|--------|
| 1 | VSCode fileWatcher exclusions | 139K dirs burning 99% CPU | CPU pressure eliminated |
| 2 | CLOSE-WAIT keepalive leak | Bare `requests.get()` leaks sockets | 74 zombie TCP connections fixed |
| 3 | `local_outputs` disabled by default | 10,903 new dirs/day accumulating | 26 GB cleaned; 0 new dirs at scale |
| 4 | Data lake CSV → Parquet | Large CSVs re-read from disk per query | 62% smaller, 10–100× faster reads |

---

## Fix 1: VSCode fileWatcher CPU Overload

### Problem

`local_outputs/` contained **139,091 timestamped subdirectories** (one per Biomni query, never deleted, accumulating since Sep 2025). VSCode's fileWatcher process (PID 1249281) was scanning this tree continuously at **99% CPU**, causing sustained I/O pressure even during idle periods.

**Evidence:**
```
local_outputs/: 139,091 dirs, 26 GB, growing ~10,903 dirs/day
VSCode fileWatcher PID 1249281: 99% CPU constant
```

### Fix

Created `.vscode/settings.json` to exclude high-churn directories from VSCode's file watching and search indexing:

```json
{
  "files.watcherExclude": {
    "**/local_outputs/**": true,
    "**/logs/**": true,
    "**/__pycache__/**": true,
    "**/biomni_env/**": true,
    "**/.biomni/**": true
  },
  "search.exclude": {
    "**/local_outputs/**": true,
    "**/logs/**": true
  }
}
```

**File:** `/alan-data/jinc/git_chen/Biomni/.vscode/settings.json` (local only, gitignored)

### Outcome
- fileWatcher CPU drops to near 0% immediately on next VSCode reload
- No code changes required — purely a workspace settings change

---

## Fix 2: CLOSE-WAIT TCP Socket Leak in vLLM Keepalive

### Problem

All 5 API server scripts (`biomni_api_server_*.py`) run a background keepalive thread that pings the remote vLLM `/models` endpoint every 300 seconds. The ping used a **bare `requests.get()` call** with no connection management:

```python
# BEFORE — leaks one TCP socket per ping
resp = _requests.get(f"{base_url}/models", timeout=10)
```

After vLLM sends its response, it closes the TCP connection from its side (sends FIN). The local Python process receives the FIN but **never explicitly closes its side of the socket**, leaving it stuck in `CLOSE-WAIT` state indefinitely.

**Evidence at time of investigation:**
```
vLLM connections: 74 × CLOSE-WAIT + 1 × ESTABLISHED (across 75 ports)
```
Each CLOSE-WAIT socket holds a small amount of kernel memory. At 75 ports × 300 s interval, these accumulate until the process exits or the OS cleans them up (which can take hours).

> **Note:** This does NOT affect your experiment scripts. The keepalive thread is a server-side health check pinging vLLM. It is completely separate from (a) your client's HTTP connection to the Biomni API and (b) the Biomni agent's inference calls to vLLM via the OpenAI client.

### Fix

Use a **short-lived `requests.Session` context manager** with `Connection: close` header. The `with` block guarantees the session (and its underlying connection pool) is closed after each ping:

```python
# AFTER — TCP connection fully closed after each ping
def _ping():
    while True:
        try:
            with _requests.Session() as s:
                s.headers.update({"Connection": "close"})
                resp = s.get(f"{base_url}/models", timeout=10)
            print(f"[Keepalive] vLLM ping -> HTTP {resp.status_code}")
        except Exception as e:
            print(f"[Keepalive] vLLM ping failed: {e}")
        time.sleep(interval_seconds)
```

**Files changed:** All 5 API servers:
- `biomni_api_server_qwen3next_80b_awq4b_drylab.py`
- `biomni_api_server_qwen3_next_80b_auto_clean_azimuth.py`
- `biomni_api_server_qwen3_5_25B_drylab.py`
- `biomni_api_server_qwen3_5_35B_azimuth.py`
- `biomni_api_server_qwen3_coder_next_awq_4b_azimuth.py`

**Commit:** `7867e18`

---

## Fix 3: Disable `local_outputs` by Default

### Problem

Every Biomni API query created a timestamped subdirectory under `local_outputs/` (e.g. `local_outputs/20260407_091234_567/`) regardless of whether the output was needed. At benchmark scale (~50 concurrent background experiments), this created **~10,903 new directories per day** — 26 GB of disk accumulation that was never cleaned up.

This had two negative effects:
1. **Disk pressure**: 139,091 dirs before cleanup; growing without bound
2. **fileWatcher amplification**: Every new directory triggered another VSCode inotify event (see Fix 1)

### Fix

Added `ENABLE_LOCAL_OUTPUTS` environment variable to all 5 API servers. Default is `0` (disabled):

```python
# At startup
ENABLE_LOCAL_OUTPUTS = os.getenv("BIOMNI_LOCAL_OUTPUTS", "0").lower() in ("1", "true", "yes")
if ENABLE_LOCAL_OUTPUTS:
    os.makedirs('./local_outputs', exist_ok=True)
    print("PDF outputs will be saved to: ./local_outputs/")
else:
    print("Local outputs disabled (set BIOMNI_LOCAL_OUTPUTS=1 to enable)")

# Per request
output_folder = f"./local_outputs/{timestamp}" if ENABLE_LOCAL_OUTPUTS else None
```

If a client explicitly requests `save_pdf=True`, a directory is created on-demand just for that PDF — `output_folder=None` does not break PDF saving:

```python
if save_pdf:
    pdf_dir = output_folder or f"./local_outputs/{timestamp}"
    os.makedirs(pdf_dir, exist_ok=True)
    ...
```

**To re-enable** (e.g., for interactive UI sessions where you want to keep outputs):
```bash
export BIOMNI_LOCAL_OUTPUTS=1
uvicorn biomni_api_server_qwen3_next_80b_auto_clean_azimuth:app ...
```

**Commit:** `9d16118`

### One-time Cleanup

Also performed a manual cleanup of all timestamped output dirs older than 7 days:
```bash
find local_outputs/ -mindepth 1 -maxdepth 1 -type d -mtime +7 -name "202[56]*" -print0 \
  | xargs -0 -P8 rm -rf
```

**Result:** 139,118 → 70,604 directories (68,548 deleted), **26 GB → 1.2 GB recovered**.

Named directories (e.g. `test_gradio`, `deepresearch-discard`, `Qwen3-Next-80B-A3B-Instruct`) were preserved intentionally.

---

## Fix 4: Data Lake CSV/TSV → Parquet Migration

### Problem

Biomni runs benchmark experiments where many independent queries load the same large data lake files. Each query runs in a fresh Python environment (no state sharing), so files are re-read from disk on every query. The largest files are CSV/TSV format:

| File | Original size |
|------|--------------|
| `kg.csv` | 937 MB |
| `BindingDB_All_202409.tsv` | 818 MB |
| `DepMap_OmicsExpressionProteinCodingGenesTPMLogp1.csv` | 498 MB |
| `DepMap_CRISPRGeneEffect.csv` | 411 MB |
| `DepMap_CRISPRGeneDependency.csv` | 404 MB |
| `sgRNA_KO_SP_human.txt` | 362 MB |
| `sgRNA_KO_SP_mouse.txt` | 356 MB |
| `evebio_observed_points_table.csv` | 168 MB |
| *(+ 18 more CSV/TSV files)* | ... |

Although the OS page cache keeps recently-read files in RAM, with 91% RAM used there is almost no cache headroom — files frequently get evicted and must be re-read from NVMe on each query.

CSV/TSV parsing is also CPU-intensive (byte-by-byte text scanning, type inference per cell). Parquet is a columnar binary format that stores type metadata explicitly and uses compressed column chunks — reads are dramatically faster.

### Conversion Results

| Metric | Value |
|--------|-------|
| Files converted (CSV/TSV/TXT) | 26 |
| PKL files converted (DataFrames only) | 2 (`genebass_synonymous_filtered`, `genebass_missense_LC_filtered`) |
| Total original size | 7,592 MB |
| Total parquet size | 2,856 MB |
| **Size saved** | **4,736 MB (62% reduction)** |
| Originals archived | 30 files → `data_lake/csv_originals/` |

**Special cases:**
- `gwas_catalog.pkl` (174 MB): Mixed-type `CHR_ID` column (`float` + `str`). Fixed by coercing all object columns to `str` before writing parquet.
- `genebass_pLoF_filtered.pkl` (545 MB): File is genuinely corrupt (truncated pickle). Kept as-is.
- `txgnn_prediction.pkl`, `txgnn_name_mapping.pkl`: Python dicts, not DataFrames — kept as PKL.

### Directory Reorganisation

```
data_lake/
├── *.parquet           ← all active data files (Biomni uses these)
├── DATA_LAKE_INDEX.md  ← index with rows, columns, key column names for all 70 files
├── csv_originals/      ← archived originals (not listed to Biomni agent)
│   ├── kg.csv
│   ├── BindingDB_All_202409.tsv
│   └── ... (30 files)
├── *.pkl               ← non-DataFrame PKL files (kept in place)
├── go-plus.json        ← non-tabular, kept as-is
└── hp.obo              ← non-tabular, kept as-is
```

The `csv_originals/` subdirectory is a depth-1 subdirectory — `glob.glob(data_lake_path + "/*")` does not recurse into it, so the Biomni agent never sees the archived originals.

### Biomni Agent Changes

**`biomni/env_desc.py` and `biomni/env_desc_cm.py`:** All data lake dict keys updated from `.csv`/`.tsv`/`.txt` → `.parquet`. Added `DATA_LAKE_INDEX.md` entry as the first item (sorted alphabetically), prompting Biomni to read it first:

```python
data_lake_dict = {
    "DATA_LAKE_INDEX.md": "Index of all data lake files: format, size, row/column counts, and key columns. Read this FIRST before accessing data lake files to plan your approach efficiently.",
    "affinity_capture-ms.parquet": "...",
    "BindingDB_All_202409.parquet": "...",
    ...
}
```

**`biomni/agent/a1.py` — CODING BEST PRACTICES section:**

```
- DATA LAKE FORMAT: Most data lake files are in Parquet (.parquet) format.
  ALWAYS use pd.read_parquet(path) for .parquet files — it is 10-100x faster
  than pd.read_csv for large files. NEVER use pd.read_csv() on a .parquet file.
- DATA LAKE INDEX: A file named DATA_LAKE_INDEX.md exists in the data lake
  directory. Read it first to understand available files, their formats, and
  key columns before deciding which file to use.
```

**Commit:** `1d4a6fa`

### DATA_LAKE_INDEX.md

A machine-readable index of all 70 parquet files is maintained at `data/biomni_data/data_lake/DATA_LAKE_INDEX.md` and mirrored to `docs/data_lake_index.md` (git-tracked). Each row includes file name, format, size, row count, column count, and the first ~8 column names.

Example entries:
| File | Size | Rows | Columns | Key Columns |
|------|------|------|---------|-------------|
| `kg.parquet` | 49.9 MB | 8,100,498 | 12 | relation, display_relation, x_index, x_id, x_type, x_name, x_source, y_index |
| `proteinatlas.parquet` | 5.2 MB | 20,162 | 107 | Gene, Gene synonym, Ensembl, Gene description, Uniprot, Chromosome, Position, Protein class |
| `DepMap_CRISPRGeneDependency.parquet` | 205.8 MB | 1,183 | 17,917 | Unnamed: 0, A1BG (1), A1CF (29974), … |

---

## Summary of Commits

| Commit | Description |
|--------|-------------|
| `7867e18` | fix: CLOSE-WAIT socket leak in keepalive + VSCode watcher exclusions |
| `9d16118` | fix: disable local_outputs by default via BIOMNI_LOCAL_OUTPUTS env var |
| `1d4a6fa` | feat: convert data lake CSV/TSV to parquet for 10-100x faster access |

---

## Related Documents

- [`biomni_machine_stability_analysis.md`](biomni_machine_stability_analysis.md) — root cause analysis of machine "deaths" (memory exhaustion, socket leaks, I/O pressure)
- [`biomni_api_error_analysis_v3.md`](biomni_api_error_analysis_v3.md) — v3 error analysis (cache poisoning fix, column guessing fix, import hints)
- [`biomni_local_dev_changelog.md`](biomni_local_dev_changelog.md) — full changelog since development cycle start
- [`data_lake_index.md`](data_lake_index.md) — full index of all 70 data lake parquet files
