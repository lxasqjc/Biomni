# Biomni Repository Cleanup Summary

**Date:** February 11, 2026
**Status:** ✅ Complete - Changes Ready for Testing

## Problem Identified

The Biomni agent was creating session output files (*.png, *.csv, etc.) directly in the repository root directory instead of in the designated `local_outputs/<session_name>/` folders, despite having sandbox support implemented at the API level.

## Root Cause

The sandbox implementation had a critical gap:
1. The API server (`biomni_api_server_qwen3_next_80b_auto_clean_azimuth.py`) created session-specific folders like `local_outputs/20251002_132633_384/`
2. However, the `A1` agent class didn't accept or use an `output_folder` parameter
3. When the agent executed Python code via `run_python_repl()`, it didn't change the working directory
4. Therefore, all `plt.savefig()`, `df.to_csv()`, and similar calls saved files to the current working directory (repository root)

## Actions Taken

### 1. Archived Existing Generated Files (80 files)
Moved all session-generated output files from root to `archive/session_outputs/`:
- *.png (plots and images)
- *.csv (data exports)
- *.txt, *.json (analysis results)
- *.html, *.pdf, *.zip (reports and data)
- *.fa, *.R (scripts)

Files preserved in original format at: `./archive/session_outputs/`

### 2. Updated `.gitignore`
Added explicit patterns to prevent future file leakage:
```gitignore
archive/          # Archive directory itself
*.png             # Session plots
*.pdf             # Generated PDFs
*.html            # HTML reports
*.zip             # Data archives
```

### 3. Fixed Sandbox Implementation

#### Modified Files:

**a) `biomni/agent/a1.py`** (Agent Core)
- Added `output_folder` parameter to `__init__()` method
- Stores `self.output_folder` for use during code execution
- Creates the output folder if it doesn't exist
- Passes `output_folder` to `run_python_repl()` via `working_dir` kwarg

**b) `biomni/tool/support_tools.py`** (Execution Environment)
- Modified `run_python_repl()` to accept `working_dir` parameter
- Saves current working directory before execution
- Changes to `working_dir` if provided
- Executes Python code (where all file operations happen)
- Restores original working directory after execution

**c) `biomni_api_server_qwen3_next_80b_auto_clean_azimuth.py`** (API Wrapper)
- Now passes `output_folder=output_folder` when creating `A1` agent instances
- This connects the session folder to the agent's execution environment

## How It Works Now

1. API receives request → creates `./local_outputs/20260211_150000_123/`
2. Agent initialized with `output_folder="./local_outputs/20260211_150000_123/"`
3. Agent stores this path in `self.output_folder`
4. When agent executes Python code:
   - Saves current directory (e.g., `/data/jinc/git_chen/Biomni`)
   - Changes to output folder (`./local_outputs/20260211_150000_123/`)
   - Executes code (all `plt.savefig()`, `to_csv()` calls save here)
   - Restores original directory
5. Result: All files contained in session folder ✅

## Testing

A test script has been created: `test_sandbox_fix.py`

**DO NOT RUN YET** - The API server needs to be restarted first for changes to take effect.

## Required Next Steps

### 1. Restart the API Server

The running API server (PID 682702) is using the old code. You need to:

```bash
# Stop current server
lsof -t -i :8009 | xargs kill -9

# Restart with new code
cd /data/jinc/git_chen/Biomni
conda activate biomni_e1
nohup uvicorn biomni_api_server_qwen3_next_80b_auto_clean_azimuth:app --host 0.0.0.0 --port 8009 > logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth.log 2>&1 &

# Verify it's running
ps aux | grep biomni_api_server | grep -v grep
tail -f logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth.log
```

### 2. Test the Fix

After restart, you can either:

**Option A: Run the test script**
```bash
python test_sandbox_fix.py
```

**Option B: Make a real API call**
```bash
curl -X POST "http://alan:8009/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a simple plot showing x vs x^2 for x from 0 to 10, save it as test_plot.png",
    "save_pdf": false
  }'
```

Then check:
```bash
# Should see files in a timestamped folder:
ls -lh local_outputs/*/

# Should see NO new files in root:
ls -1 *.png *.csv 2>/dev/null
```

### 3. Verify in Production

Monitor the next few actual queries to confirm files stay in `local_outputs/`.

## Additional Notes

- **Git Status:** Many files show as modified because you haven't committed in months. The actual changes for this cleanup are:
  - `.gitignore` (updated)
  - `.github/copilot-instructions.md` (new)
  - `biomni/agent/a1.py` (sandbox fix)
  - `biomni/tool/support_tools.py` (sandbox fix)
  - `biomni_api_server_qwen3_next_80b_auto_clean_azimuth.py` (sandbox fix)
  - `archive/` (new directory with moved files)
  - `test_sandbox_fix.py` (new test script)

- **Backward Compatibility:** The changes are backward compatible - if `output_folder` is not provided, the agent behaves as before (saves to current directory)

- **Performance:** No performance impact - directory changes are instant operations

## Recommendations

1. **Commit the cleanup:** Consider committing the archive and gitignore changes
2. **Monitor logs:** Watch for "Output folder:" messages in API logs to verify it's working
3. **Periodic cleanup:** Set up a cron job to clean old session folders from `local_outputs/`
4. **Documentation:** Update any user docs to mention that outputs are in `local_outputs/<session>/`

## Questions?

If files still leak after restart, check:
1. Is the agent being created with `output_folder` parameter?
2. Does the log show "📁 Output folder: ..." on agent creation?
3. Are there any tool functions that use `os.chdir()` or absolute paths?

Note: biomni_api_server.py uses a GLOBAL agent instance (old pattern).
This means it cannot properly use output_folder per-request.
Recommendation: Use biomni_api_server_qwen3_next_80b_auto_clean_azimuth.py 
or biomni_api_server_qwen3_30b_auto_clean.py instead, which create 
fresh agent instances per request and support proper sandboxing.

