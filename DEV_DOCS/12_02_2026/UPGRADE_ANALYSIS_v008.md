# Biomni Upgrade Analysis: v0.0.7 → v0.0.8+

## Current Status

**Your Version**: v0.0.7 (local-development-v1)
**Latest Origin**: v0.0.8+ (100 commits ahead)
**Your API**: biomni_api_server_qwen3_next_80b_auto_clean_azimuth.py

---

## Major Changes in v0.0.8+

### 1. Core API Changes
- **biomni/agent/a1.py**: +468 lines added
- **biomni/llm.py**: +37 lines (OpenAI Responses API support)
- **biomni/config.py**: Minor updates

### 2. New Features (v0.0.7 → v0.0.8)
- ✅ GPT-5 models support (gpt-5, gpt-5-mini)
- ✅ OpenAI Responses API support for gpt-5
- ✅ Transcripformer embeddings integration
- ✅ State embeddings support
- ✅ UI improvements
- ✅ Protocol.io integration
- ✅ Addgene/Thermo protocols database
- ✅ sgRNA design know-how

### 3. Post v0.0.8 Changes (on main)
- ✅ Gradio version compatibility fixes
- ✅ ROI detection tools (analyze_pixel_distribution, find_roi_from_image)
- ✅ Database API updates (Reactome, QuickGO, ClinicalTrials, ChEMBL, etc.)
- ✅ Bug fixes and pre-commit hook updates

---

## Compatibility Analysis

### Your API Wrapper Uses:
```python
from biomni.agent import A1

AGENT_CONFIG = {
    'path': './data',
    'llm': 'Qwen/Qwen3-Next-80B-A3B-Instruct-FP8',
    'base_url': 'https://vllm.paas-jade.astrazeneca.net/v1',
    'api_key': 'natura15tup1d1ty',
    'commercial_mode': True,
    'output_folder': output_folder  # Your sandbox fix
}

agent = A1(**AGENT_CONFIG)
agent.chat(prompt)
```

### Potential Compatibility Issues:

#### 🟢 LOW RISK
- A1.__init__() signature: Likely backward compatible (uses **kwargs pattern)
- agent.chat() method: Core functionality preserved
- Your sandbox fix (output_folder): Independent addition, should merge cleanly

#### 🟡 MEDIUM RISK
- biomni/llm.py changes: New OpenAI Responses API support
  - May affect LLM initialization if using GPT models
  - You're using Qwen, so likely unaffected
- Database query updates: May improve accuracy but could change behavior
  - If your API relies on specific database outputs, test carefully

#### 🔴 POTENTIAL CONFLICTS
- biomni/agent/a1.py: +468 lines
  - Your sandbox fix modified this file
  - Need to check if upstream changes conflict with your output_folder implementation
  - Likely areas: __init__(), code execution paths

---

## Merge Strategy

### Option 1: Safe Test Branch (RECOMMENDED)
```bash
# Create test branch from your current state
git checkout -b test-upgrade-v0.0.8

# Merge latest origin/main
git merge origin/main

# Resolve conflicts (focus on biomni/agent/a1.py)
# Test API on different port (e.g., 8010)
```

### Option 2: Rebase (Cleaner history)
```bash
git checkout -b test-upgrade-v0.0.8
git rebase origin/main
# May have more conflicts but cleaner history
```

### Option 3: Cherry-pick (Selective)
```bash
# Only pick specific features you want
git checkout -b test-upgrade-v0.0.8
git cherry-pick <commit-hash>
```

---

## Testing Plan

### 1. Merge Testing
- [ ] Create test-upgrade-v0.0.8 branch
- [ ] Merge origin/main
- [ ] Resolve conflicts in biomni/agent/a1.py
- [ ] Verify sandbox fix (output_folder) still works

### 2. API Testing
- [ ] Update port in test API (8009 → 8010)
- [ ] Start test API server
- [ ] Test basic chat functionality
- [ ] Test file output sandboxing
- [ ] Test with commercial_mode=True
- [ ] Test concurrent requests

### 3. Regression Testing
- [ ] Verify IBD data loading
- [ ] Test database queries
- [ ] Check PDF output generation
- [ ] Verify auto-cleanup works

### 4. Performance Testing
- [ ] Compare response times
- [ ] Check memory usage
- [ ] Test long conversations

---

## Conflict Resolution Guide

### Expected Conflicts in biomni/agent/a1.py

**Your changes**:
- Lines 56-67: Added output_folder parameter
- Lines 190-196: Store and create output folder
- Lines 1394-1402: Pass working_dir to run_python_repl

**Upstream changes**:
- +468 lines throughout the file
- Possible: New parameters, methods, execution flow changes

**Resolution strategy**:
1. Accept upstream changes first (theirs)
2. Re-apply your sandbox fix on top
3. Test that both work together

---

## Rollback Plan

If upgrade fails:
```bash
# Quick rollback
git checkout local-development-v1

# Current stable server keeps running on port 8009
# No downtime
```

---

## Recommendations

1. ✅ **Use Option 1 (Test Branch)** - Safest approach
2. ✅ **Test on port 8010** - Keep production running
3. ✅ **Focus on a1.py conflicts** - Most critical
4. ✅ **Document changes** - Add to DEV_DOCS/
5. ⚠️ **Don't merge to main immediately** - Test thoroughly first
6. ⚠️ **Keep current server running** - Zero downtime

---

## Next Steps

1. Create test-upgrade-v0.0.8 branch
2. Merge origin/main
3. Resolve conflicts
4. Test API on port 8010
5. If successful, merge to local-development-v1
6. Restart production server with new code
