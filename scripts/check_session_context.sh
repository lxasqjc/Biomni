#!/bin/bash
# Check Session Context - Quick Summary
# Shows summary of available session backups for selective loading

PROJECT_ROOT="/data/jinc/git_chen/Biomni"
BACKUP_DIR="$PROJECT_ROOT/DEV_DOCS/session_backups"

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "════════════════════════════════════════════════════════════════"
echo "SESSION CONTEXT CHECKER"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if backups exist
if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A "$BACKUP_DIR" 2>/dev/null | grep session_backup)" ]; then
    echo "✅ No previous session backups found"
    echo "   Starting fresh - no context to load"
    echo ""
    exit 0
fi

# Find most recent backup
LATEST_BACKUP=$(ls -td "$BACKUP_DIR"/session_backup_* 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "✅ No session backups found"
    exit 0
fi

echo -e "${GREEN}📊 Previous session found!${NC}"
echo ""

# Show backup info
BACKUP_NAME=$(basename "$LATEST_BACKUP")
BACKUP_SIZE=$(du -sh "$LATEST_BACKUP" | cut -f1)
BACKUP_DATE=$(echo "$BACKUP_NAME" | sed 's/session_backup_//' | sed 's/_/ /' | sed 's/\([0-9]\{8\}\) \([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\1 \2:\3:\4/')

echo "📦 Backup Details:"
echo "   Date: $BACKUP_DATE"
echo "   Size: $BACKUP_SIZE"
echo "   Location: $LATEST_BACKUP"
echo ""

# Check if context already extracted
CONTEXT_DIR="$LATEST_BACKUP/extracted_context"
if [ ! -d "$CONTEXT_DIR" ]; then
    echo -e "${YELLOW}⚠️  Context not yet extracted${NC}"
    echo ""
    echo "Run this to extract:"
    echo "   bash scripts/extract_session_context.sh"
    echo ""
    exit 0
fi

# Show checkpoint info
if [ -d "$CONTEXT_DIR/checkpoints" ]; then
    CHECKPOINT_COUNT=$(ls "$CONTEXT_DIR/checkpoints"/*.md 2>/dev/null | wc -l)
    echo "📑 Available Checkpoints: $CHECKPOINT_COUNT"
    echo ""
    
    # List checkpoints with sizes
    ls -lh "$CONTEXT_DIR/checkpoints"/*.md 2>/dev/null | while read -r line; do
        SIZE=$(echo "$line" | awk '{print $5}')
        FILE=$(echo "$line" | awk '{print $NF}')
        BASENAME=$(basename "$FILE")
        LINES=$(wc -l < "$FILE" 2>/dev/null || echo "0")
        echo "   • $BASENAME"
        echo "     Size: $SIZE, Lines: $LINES"
    done
    echo ""
    
    # Show latest checkpoint info
    LATEST_CHECKPOINT=$(ls "$CONTEXT_DIR/checkpoints"/*.md 2>/dev/null | tail -1)
    if [ -n "$LATEST_CHECKPOINT" ]; then
        CHECKPOINT_NAME=$(basename "$LATEST_CHECKPOINT")
        CHECKPOINT_LINES=$(wc -l < "$LATEST_CHECKPOINT")
        CHECKPOINT_SIZE=$(du -h "$LATEST_CHECKPOINT" | cut -f1)
        
        echo -e "${BLUE}💡 Recommended: Load ONLY latest checkpoint${NC}"
        echo "   File: $CHECKPOINT_NAME"
        echo "   Size: $CHECKPOINT_SIZE ($CHECKPOINT_LINES lines)"
        echo ""
        echo "   Command:"
        echo "   cat $LATEST_CHECKPOINT"
        echo ""
    fi
fi

echo "════════════════════════════════════════════════════════════════"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Selective Loading${NC}"
echo ""
echo "✅ DO: Paste ONLY latest checkpoint (~200-500 tokens)"
echo "   → Provides context without bloating new session"
echo "   → Compatible with Copilot's memory management"
echo ""
echo "❌ DON'T: Paste all checkpoints or full transcript"
echo "   → Would interfere with Copilot's automatic compression"
echo "   → Wastes context window on old information"
echo ""
echo "💬 Tell Copilot:"
echo '   "Continuing from previous session: [paste latest checkpoint]"'
echo ""
