# Biomni Development Documentation Index

This directory contains session-specific documentation following the AGENTS universal documentation rules.

## Documentation Sessions

### [12_02_2026] - Repository Cleanup and AGENTS Compliance

Session focused on:
- Repository cleanup and commit organization
- Implementing AGENTS universal rules compliance
- Fixing agent sandbox file leakage issue
- Setting up session persistence infrastructure

**Key Documents:**
- [CLEANUP_SUMMARY.md](12_02_2026/CLEANUP_SUMMARY.md) - Comprehensive cleanup report
- [SANDBOX_FIX_TECHNICAL_SUMMARY.md](12_02_2026/SANDBOX_FIX_TECHNICAL_SUMMARY.md) - Technical sandbox implementation
- [QUICK_START_AFTER_CLEANUP.md](12_02_2026/QUICK_START_AFTER_CLEANUP.md) - Post-cleanup guide

**Changes Made:**
- Fixed agent file leakage to repository root
- Added production API servers with sandbox support
- Organized documentation structure
- Implemented session backup infrastructure

---

## Previous Work (Feb 11, 2026)

**Sandbox Fix Implementation:**
- Modified `biomni/agent/a1.py` to accept `output_folder` parameter
- Modified `biomni/tool/support_tools.py` to use working directory during execution
- Created new API servers: `biomni_api_server_qwen3_30b_auto_clean.py` and `biomni_api_server_qwen3_next_80b_auto_clean_azimuth.py`
- Archived 80+ leaked output files to `archive/session_outputs/`

---

## Documentation Structure

Per AGENTS universal rules:
- Each session gets a dated folder: `DEV_DOCS/DD_MM_YYYY/`
- Session-specific docs go in their respective folders
- This INDEX.md tracks all sessions
- Session backups stored in `session_backups/` (gitignored)

---

**Last Updated**: February 12, 2026
