#!/bin/bash
# Session State Backup Script
# Backs up ephemeral session state to permanent storage

PROJECT_ROOT="/data/jinc/git_chen/Biomni"
SESSION_ID="cd409bd2-684c-4f8c-88ef-c9a6961faebe"
SESSION_DIR="$HOME/.copilot/session-state/$SESSION_ID"
BACKUP_DIR="$PROJECT_ROOT/DEV_DOCS/session_backups"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "════════════════════════════════════════════════════════════════"
echo "GITHUB COPILOT SESSION BACKUP"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PATH="$BACKUP_DIR/session_backup_$TIMESTAMP"

# Check if session exists
if [ ! -d "$SESSION_DIR" ]; then
    echo -e "${RED}❌ Session directory not found:${NC} $SESSION_DIR"
    echo ""
    echo "This means:"
    echo "  • Session has already ended"
    echo "  • Or session ID changed"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Session found${NC}"
echo "   Location: $SESSION_DIR"
echo ""

# Create backup
echo "📦 Creating backup..."
mkdir -p "$BACKUP_PATH"

# Copy session files
if [ -f "$SESSION_DIR/events.jsonl" ]; then
    cp "$SESSION_DIR/events.jsonl" "$BACKUP_PATH/"
    SIZE=$(du -h "$SESSION_DIR/events.jsonl" | cut -f1)
    echo -e "${GREEN}   ✓ events.jsonl${NC} ($SIZE)"
fi

if [ -d "$SESSION_DIR/checkpoints" ]; then
    cp -r "$SESSION_DIR/checkpoints" "$BACKUP_PATH/"
    COUNT=$(ls "$SESSION_DIR/checkpoints"/*.md 2>/dev/null | wc -l)
    echo -e "${GREEN}   ✓ checkpoints/${NC} ($COUNT files)"
fi

if [ -d "$SESSION_DIR/files" ]; then
    cp -r "$SESSION_DIR/files" "$BACKUP_PATH/"
    echo -e "${GREEN}   ✓ files/${NC}"
fi

# Create metadata
cat > "$BACKUP_PATH/metadata.txt" << METADATA
Session Backup Metadata
=======================
Session ID: $SESSION_ID
Backup Time: $(date)
Backup By: $(whoami)@$(hostname)
Project: Medea Hybrid Implementation

Files Backed Up:
$(ls -lh "$BACKUP_PATH" | tail -n +2)

Purpose:
This backup preserves the ephemeral session state from GitHub Copilot CLI.
Can be used to review conversation history or extract context for future sessions.

Restore Instructions:
- events.jsonl contains full conversation transcript
- checkpoints/ contains compacted summaries
- Read these files to get context, but cannot directly restore session
METADATA

echo -e "${GREEN}   ✓ metadata.txt${NC}"
echo ""

# Show summary
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ BACKUP COMPLETE${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Backup location:"
echo "   $BACKUP_PATH"
echo ""
echo "Backup size:"
du -sh "$BACKUP_PATH" | awk '{print "   " $1}'
echo ""
echo "Files:"
ls -1 "$BACKUP_PATH" | sed 's/^/   • /'
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "💡 TIP: Run this script periodically during long sessions to"
echo "   preserve conversation history in case session breaks."
echo ""
echo "To auto-backup every hour, add to crontab:"
echo "   */60 * * * * $PROJECT_ROOT/scripts/backup_session.sh"
echo ""
