# Gradio UI - Proxy and Path Fixes

**Date**: February 12, 2026  
**Issue**: API connection errors and data file path resolution failures  
**Status**: ✅ FIXED

---

## 🐛 Problems Identified

### Problem 1: API Connection Error
**Error**: `openai.APIConnectionError: Connection error.`

**Root Cause**:
- Gradio server running without correct proxy configuration
- `NO_PROXY` was missing AstraZeneca internal networks
- Internal endpoints like `vllm.paas-jade.astrazeneca.net` were being incorrectly routed through proxy

**Symptom**:
```
File "/alan-data/jinc/miniconda3/envs/biomni_e1/lib/python3.11/site-packages/openai/_base_client.py", line 1011, in request
    raise APIConnectionError(request=request) from err
openai.APIConnectionError: Connection error.
```

### Problem 2: Data File Not Found
**Error**: `[Errno 2] No such file or directory: './data/biomni_data/ibd_clean_xavier/redshift_data/raw_tables/ibd_21183_procedures_emr.csv'`

**Root Cause**:
- Agent config used relative path `'./data'`
- When agent executes Python code inside sandbox directory (`./local_outputs/gradio_demo`), relative paths don't resolve correctly
- Even though symlink worked from shell, the execution context was wrong

---

## ✅ Solutions Applied

### Fix 1: Add Proxy Configuration to Launcher Script

**Modified**: `start_biomni_gradio_demo.sh`

**Added** (before line 43):
```bash
# Export proxy settings for drylab workstation
export http_proxy=
export https_proxy="http://emeapzen.astrazeneca.net:9480"
export HTTP_PROXY=
export HTTPS_PROXY="http://emeapzen.astrazeneca.net:9480"
export NO_PROXY="10.0.0.0/8,172.29.0.0/8,astrazeneca.net"
export no_proxy="10.0.0.0/8,172.29.0.0/8,astrazeneca.net"
```

**Why this works**:
- `NO_PROXY` now includes AZ internal networks and domains
- Internal API endpoints bypass the proxy
- External endpoints (if any) still route through proxy

### Fix 2: Use Absolute Paths in Agent Config

**Modified**: `biomni_gradio_demo.py`

**Changed** (lines 13-20):
```python
# Before:
AGENT_CONFIG = {
    'path': './data',
    'output_folder': './local_outputs/gradio_demo',
    ...
}

# After:
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_CONFIG = {
    'path': os.path.join(SCRIPT_DIR, 'data'),  # Use absolute path
    'output_folder': os.path.join(SCRIPT_DIR, 'local_outputs/gradio_demo'),
    ...
}
```

**Why this works**:
- Absolute paths resolve correctly regardless of execution context
- Sandbox directory doesn't affect data file lookup
- Symlinks work properly with absolute paths

---

## 🧪 Testing Performed

### Test 1: Verify Proxy Configuration
```bash
# With correct proxy
export https_proxy="http://emeapzen.astrazeneca.net:9480"
export NO_PROXY="10.0.0.0/8,172.29.0.0/8,astrazeneca.net"

curl -k -X POST https://vllm.paas-jade.astrazeneca.net/v1/chat/completions \
  -H "Authorization: Bearer natura15tup1d1ty" \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen3-Next-80B-A3B-Instruct-FP8", "messages": [{"role":"user","content":"Say hello"}]}'
```
**Result**: ✅ HTTP 200, successful response

### Test 2: Verify Server Starts with Proxy
```bash
./start_biomni_gradio_demo.sh
lsof -i :7861
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:7861
```
**Result**: ✅ Server listening, HTTP 200

### Test 3: Verify Data File Access
**Query**: "Generate Kaplan-Meier survival analysis for IBD patients"

**Before fix**: 
```
Error: [Errno 2] No such file or directory: './data/biomni_data/ibd_clean_xavier/...'
```

**After fix**:
✅ Successfully finds and reads IBD dataset files

---

## 📁 Files Modified

1. **`start_biomni_gradio_demo.sh`**
   - Added proxy environment variables (lines 42-48)
   - Ensures spawned Python process inherits correct proxy settings

2. **`biomni_gradio_demo.py`**
   - Added `SCRIPT_DIR` calculation (line 13)
   - Changed `path` to absolute (line 15)
   - Changed `output_folder` to absolute (line 20)

3. **`AGENTS/DRYLAB_PROXY_CONFIG.md`** (new file)
   - Universal documentation for proxy configuration
   - Applies to all projects on drylab workstation
   - Includes troubleshooting and testing instructions

---

## 🎯 Current Status

**Gradio UI**: ✅ Running on port 7861  
**Proxy**: ✅ Correctly configured  
**Data Access**: ✅ IBD files accessible  
**API Connection**: ✅ LLM endpoint reachable  
**Status**: STABLE and TESTED

**Access URLs**:
- Local: `http://localhost:7861`
- External: `http://10.85.202.54:7861`

---

## 🔍 Technical Details

### Why Relative Paths Failed

When agent executes Python code:
1. Agent creates sandbox in `./local_outputs/gradio_demo/`
2. Changes working directory to sandbox for code execution
3. Relative path `./data` now points to `./local_outputs/gradio_demo/data` (doesn't exist)
4. File access fails

With absolute paths:
1. Agent still creates sandbox and changes working directory
2. But data path is `/data/jinc/git_chen/Biomni/data` (always correct)
3. File access succeeds

### Why NO_PROXY Matters

Without correct `NO_PROXY`:
```
Request → Python HTTP client → Proxy (emeapzen:9480) → vllm.paas-jade.astrazeneca.net
                                  ↑ Proxy rejects internal AZ domain
                                  ↓ Returns 502 Bad Gateway
```

With correct `NO_PROXY`:
```
Request → Python HTTP client → Check NO_PROXY → Direct to vllm.paas-jade.astrazeneca.net
                                  ↑ Matches "astrazeneca.net"
                                  ↓ Bypass proxy, direct connection ✅
```

---

## 📚 Related Issues & Documentation

### This Session
- `GRADIO_UI_SETUP.md` - Initial setup documentation
- `GRADIO_UI_ERROR_FIX.md` - Tool retrieval 502 error fix (different issue)
- `SANDBOX_FIX_TECHNICAL_SUMMARY.md` - Sandbox implementation details

### Universal Rules
- `AGENTS/DRYLAB_PROXY_CONFIG.md` - Proxy configuration standard
- `AGENTS/SESSION_PERSISTENCE_RULES.md` - Session backup workflow

### Related Code
- `biomni/agent/a1.py` - Agent initialization and sandbox support
- `biomni/tool/support_tools.py` - Tool execution with working directory

---

## 🚀 Next Steps

### Immediate
- [x] Test IBD queries in browser UI
- [x] Verify Kaplan-Meier analysis works
- [ ] Test other data-intensive queries

### Future Improvements
1. **Add health check endpoint** - Monitor API connectivity
2. **Graceful degradation** - Fallback if API unreachable
3. **Configuration validation** - Check paths exist at startup
4. **Environment detection** - Auto-detect drylab vs other environments

---

**Fixed By**: GitHub Copilot CLI  
**Fixes Verified**: February 12, 2026, 16:28 UTC  
**Server PID**: 3105260  
**Solutions**: Proxy configuration + absolute paths
