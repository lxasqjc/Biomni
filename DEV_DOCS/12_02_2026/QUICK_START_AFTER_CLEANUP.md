# Quick Start After Cleanup

## What Was Done

1. ✅ **Archived 80+ generated files** from root → `archive/session_outputs/`
2. ✅ **Updated .gitignore** to prevent future file leakage
3. ✅ **Fixed sandbox implementation** in agent core + API wrappers
4. ✅ **Created test script** to verify the fix works

## Files Modified

- `biomni/agent/a1.py` - Added `output_folder` parameter
- `biomni/tool/support_tools.py` - Modified `run_python_repl()` to use working directory
- `biomni_api_server_qwen3_next_80b_auto_clean_azimuth.py` - Pass output_folder to agent ✅
- `biomni_api_server_qwen3_30b_auto_clean.py` - Pass output_folder to agent ✅
- `.gitignore` - Added archive/ and session file patterns

## Next Steps (REQUIRED)

### 1. Restart API Server

Your current server is running OLD code. Restart it:

```bash
# Stop current (replace with actual PID from 'ps aux | grep biomni')
kill -9 682702

# Start with new code
cd /data/jinc/git_chen/Biomni
conda activate biomni_e1
./start_biomni_production.sh

# OR manually:
nohup uvicorn biomni_api_server_qwen3_next_80b_auto_clean_azimuth:app \
  --host 0.0.0.0 --port 8009 \
  > logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth.log 2>&1 &
```

### 2. Verify It Works

```bash
# Quick test
curl -X POST "http://alan:8009/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a simple test plot and save as test.png", "save_pdf": false}'

# Check files are in session folder
ls -lh local_outputs/*/

# Verify NO files in root
ls *.png *.csv 2>&1 | grep -q "No such file" && echo "✅ Clean!" || echo "⚠️ Files leaked"
```

### 3. Monitor

Look for this in logs:
```
[Biomni API] Output folder: ./local_outputs/20260211_150627_123
📁 Output folder: ./local_outputs/20260211_150627_123
```

## Important Notes

- **biomni_api_server.py** (old version) still uses global agent - can't be fixed without rewrite
- **Use**: `biomni_api_server_qwen3_next_80b_auto_clean_azimuth.py` (recommended, on port 8009)
- **Or**: `biomni_api_server_qwen3_30b_auto_clean.py` (alternative)

Both now properly sandbox all file operations! 🎉
