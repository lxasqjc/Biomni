# Biomni Session Persistence Guide

## Quick Setup

Project-specific configuration for GitHub Copilot CLI session persistence.

### Configuration

- **Project Root**: `/data/jinc/git_chen/Biomni`
- **Session ID**: `cd409bd2-684c-4f8c-88ef-c9a6961faebe`
- **Backup Directory**: `DEV_DOCS/session_backups/`

### Daily Workflow

#### Starting a Session

```bash
# Check for previous session backups
bash scripts/check_session_context.sh

# If backups exist, load ONLY latest checkpoint
cat DEV_DOCS/session_backups/session_backup_*/extracted_context/checkpoints/00*.md
```

#### During Active Session

**Backup every ~5 conversation rounds:**
```bash
bash scripts/backup_session.sh
```

**When to backup:**
- Before running long commands (builds, tests)
- After completing significant tasks
- Before leaving computer
- Every 30-60 minutes of active work

#### Ending a Session

```bash
# Final backup
bash scripts/backup_session.sh

# Extract context for next session
bash scripts/extract_session_context.sh
```

---

## Available Scripts

### `scripts/backup_session.sh`
Creates timestamped backup of current session state to `DEV_DOCS/session_backups/`.

### `scripts/extract_session_context.sh`
Extracts readable context from latest backup for loading into new sessions.

### `scripts/check_session_context.sh`
Shows summary of available backups and recommends what to load.

---

## Important Notes

- ⚠️ **Only load latest checkpoint** - Avoid context window bloat
- ⚠️ **Backup frequently** - Session state is ephemeral
- ⚠️ **Never commit session_backups/** - It's in .gitignore

---

## Compliance Status

✅ Scripts installed and configured
✅ DEV_DOCS structure created
✅ Session backups directory created
✅ .gitignore updated

---

**For complete details, see**: `/data/jinc/AGENTS_UNIVERSAL/SESSION_PERSISTENCE_RULES.md`
