# Biomni v0.0.8 Upgrade - Test Status

**Date**: February 12, 2026  
**Branch**: test-upgrade-v0.0.8  
**Status**: ✅ Merge successful, ready for testing

---

## Merge Summary

### ✅ Successfully Merged
- **100+ commits** from origin/main
- **127 files changed**: +20,436 insertions, -677 deletions
- Version: v0.0.7 → v0.0.8+

### ✅ Sandbox Fix Preserved
Your custom sandbox implementation is **fully preserved**:
- `biomni/agent/a1.py`: output_folder parameter present (9 occurrences)
- `biomni/tool/support_tools.py`: working_dir support present
- Auto-merged without conflicts! 🎉

---

## Major New Features

### 1. New Tools & Databases
- ✅ **100+ Protocol files** (Addgene, ThermoFisher)
- ✅ **Lab automation** tools (biomni/tool/lab_automation.py)
- ✅ **Protocol integration** (biomni/tool/protocols.py)
- ✅ **New databases**: ChEMBL, ClinicalTrials, DailyMed, PubChem, UniChem, QuickGO, ENCODE

### 2. Know-How System
- ✅ `biomni/know_how/` - New knowledge base system
- ✅ sgRNA design guide
- ✅ Single-cell annotation guide
- ✅ CRISPick resources, Addgene gRNA sequences

### 3. Evaluation Framework
- ✅ `biomni/eval/` - New evaluation system
- ✅ Biomni Eval1 implementation

### 4. Model Support
- ✅ GPT-5 and GPT-5-mini support
- ✅ OpenAI Responses API support
- ✅ Transcripformer embeddings
- ✅ State embeddings

### 5. Database Updates
- ✅ Reactome API update fixes
- ✅ QuickGO query improvements
- ✅ ChEMBL, UniChem, ClinicalTrials accuracy updates

---

## Test Configuration

### Test API Server
**File**: `biomni_api_server_test_v008.py`  
**Port**: 8010 (production on 8009)  
**Config**: Same as production (Qwen3-Next-80B, commercial_mode=True)

### Start Test Server
```bash
cd /data/jinc/git_chen/Biomni
git checkout test-upgrade-v0.0.8
conda activate biomni_e1
python biomni_api_server_test_v008.py
```

Server will start on: `http://alan:8010`

---

## Testing Checklist

### 1. Basic Functionality ⏳
- [ ] Server starts without errors
- [ ] Agent initialization works
- [ ] `/health` endpoint responds
- [ ] `/chat` endpoint accepts requests

### 2. Sandbox Fix Verification ⏳
- [ ] Files created in `local_outputs/<session>/` not root
- [ ] Test plot generation
- [ ] Test CSV export
- [ ] Verify no files leak to repository root

### 3. New Features Testing ⏳
- [ ] Protocol search works (Addgene/ThermoFisher)
- [ ] New database queries work (ChEMBL, ClinicalTrials)
- [ ] Lab automation tools accessible
- [ ] Know-how system works

### 4. Regression Testing ⏳
- [ ] Existing queries still work
- [ ] IBD data loading works
- [ ] PDF generation works
- [ ] Commercial mode filtering works
- [ ] Concurrent requests work

### 5. Performance Testing ⏳
- [ ] Response time comparison
- [ ] Memory usage check
- [ ] Long conversation handling

---

## Test Commands

### Simple Test
```bash
curl -X POST "http://alan:8010/health"
```

### Chat Test
```bash
curl -X POST "http://alan:8010/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a simple test plot and save as test.png",
    "save_pdf": false
  }'
```

### Sandbox Test
```bash
# After chat request, check output location
ls -lh local_outputs/*/
ls *.png  # Should find nothing in root
```

### Protocol Test
```bash
curl -X POST "http://alan:8010/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What protocols are available for AAV production?",
    "save_pdf": false
  }'
```

---

## Rollback Plan

If tests fail:

```bash
# Stop test server (Ctrl+C or find PID)
ps aux | grep biomni_api_server_test_v008 | grep -v grep

# Switch back to stable branch
git checkout local-development-v1

# Production server on port 8009 continues running
# No downtime!
```

---

## Next Steps After Successful Testing

1. **If all tests pass**:
   ```bash
   # Merge to local-development-v1
   git checkout local-development-v1
   git merge test-upgrade-v0.0.8
   
   # Push to private remote
   git push private local-development-v1
   
   # Restart production server with new code
   # (Find PID, stop, restart on 8009)
   ```

2. **If tests fail**:
   - Document failures in this file
   - Debug on test branch
   - Re-test until stable
   - Keep production running on old code

---

## Files Modified in This Session

**Created**:
- `biomni_api_server_test_v008.py` - Test API server (port 8010)
- `DEV_DOCS/12_02_2026/UPGRADE_ANALYSIS_v008.md` - Detailed analysis
- `DEV_DOCS/12_02_2026/UPGRADE_TEST_STATUS.md` - This file

**Branch**:
- `test-upgrade-v0.0.8` - Created from local-development-v1
- Merged origin/main (100+ commits)
- Ready for testing

---

## Contact

If you encounter issues during testing, check:
1. Logs: Monitor console output for errors
2. `local_outputs/`: Verify file sandboxing
3. Memory: Check if new tools consume more resources
4. DEV_DOCS/12_02_2026/UPGRADE_ANALYSIS_v008.md for details

---

**Last Updated**: February 12, 2026  
**Status**: Ready for testing 🧪
