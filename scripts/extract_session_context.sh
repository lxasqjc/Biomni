#!/bin/bash
# Extract Readable Context from Session Backup
# Converts session backup into human-readable format for context loading

PROJECT_ROOT="/data/jinc/git_chen/Biomni"
BACKUP_DIR="$PROJECT_ROOT/DEV_DOCS/session_backups"

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "════════════════════════════════════════════════════════════════"
echo "SESSION CONTEXT EXTRACTOR"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Find most recent backup
LATEST_BACKUP=$(ls -td "$BACKUP_DIR"/session_backup_* 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ No backups found in $BACKUP_DIR"
    echo ""
    echo "Run backup_session.sh first to create a backup."
    exit 1
fi

echo -e "${GREEN}✅ Found backup${NC}"
echo "   Location: $LATEST_BACKUP"
echo ""

# Create context directory
CONTEXT_DIR="$LATEST_BACKUP/extracted_context"
mkdir -p "$CONTEXT_DIR"

echo "📝 Extracting context..."
echo ""

# Extract checkpoints (already readable)
if [ -d "$LATEST_BACKUP/checkpoints" ]; then
    cp -r "$LATEST_BACKUP/checkpoints" "$CONTEXT_DIR/"
    COUNT=$(ls "$CONTEXT_DIR/checkpoints"/*.md 2>/dev/null | wc -l)
    echo -e "${GREEN}   ✓ checkpoints/${NC} ($COUNT markdown files)"
fi

# Parse events.jsonl for key information
if [ -f "$LATEST_BACKUP/events.jsonl" ]; then
    # Extract user messages
    grep '"role":"user"' "$LATEST_BACKUP/events.jsonl" | \
        python3 -c "
import sys, json
print('User Messages:')
print('=' * 60)
for i, line in enumerate(sys.stdin, 1):
    try:
        event = json.loads(line)
        if 'content' in event:
            content = event['content'][:200]
            print(f'\n{i}. {content}...')
    except: pass
" > "$CONTEXT_DIR/user_messages.txt"
    
    MSG_COUNT=$(grep -c '"role":"user"' "$LATEST_BACKUP/events.jsonl")
    echo -e "${GREEN}   ✓ user_messages.txt${NC} ($MSG_COUNT messages)"
    
    # Extract tool calls
    grep '"name":' "$LATEST_BACKUP/events.jsonl" | head -50 > "$CONTEXT_DIR/tool_calls.txt"
    TOOL_COUNT=$(wc -l < "$CONTEXT_DIR/tool_calls.txt")
    echo -e "${GREEN}   ✓ tool_calls.txt${NC} ($TOOL_COUNT calls)"
    
    # Extract file operations
    grep -E '"path"|"view"|"edit"|"create"' "$LATEST_BACKUP/events.jsonl" | \
        grep -v '"name":"view"' | head -50 > "$CONTEXT_DIR/file_operations.txt"
    FILE_COUNT=$(wc -l < "$CONTEXT_DIR/file_operations.txt")
    echo -e "${GREEN}   ✓ file_operations.txt${NC} ($FILE_COUNT operations)"
fi

# Create summary
cat > "$CONTEXT_DIR/SESSION_SUMMARY.md" << 'SUMMARY'
# Session Context Summary

This directory contains extracted context from a GitHub Copilot session backup.

## Files

### Checkpoints (checkpoints/)
- Compacted conversation summaries created by Copilot
- Read these first - they contain the most important context
- Organized chronologically

### User Messages (user_messages.txt)
- All messages sent by the user
- Useful to understand what was requested

### Tool Calls (tool_calls.txt)
- Sample of tool invocations (bash, edit, create, etc.)
- Shows what actions were taken

### File Operations (file_operations.txt)
- Files that were created or modified
- Extract file paths to see what changed

## How to Use This for Session Continuity

1. **Read checkpoints first** - Start with the latest checkpoint
2. **Review user messages** - See what was requested
3. **Check file operations** - Know what files were created/modified
4. **Provide to new session** - Share relevant context when restarting

## Limitations

- Cannot directly "restore" a session - Copilot CLI doesn't support this
- This is READ-ONLY context extraction
- Use this as reference material when starting a new session
- Copilot will need to be briefed on the context manually

## Example Usage

```bash
# When starting a new session after a break:
cat checkpoints/001-*.md
cat SESSION_SUMMARY.md

# Then tell Copilot:
# "Continuing from previous session. Here's the context: [paste checkpoint]"
```

SUMMARY

echo -e "${GREEN}   ✓ SESSION_SUMMARY.md${NC}"
echo ""

# Show results
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ CONTEXT EXTRACTION COMPLETE${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Context directory:"
echo "   $CONTEXT_DIR"
echo ""
echo "Files created:"
ls -1 "$CONTEXT_DIR" | sed 's/^/   • /'
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo -e "${BLUE}📖 Next Steps:${NC}"
echo ""
echo "1. Read the extracted context:"
echo "   cat $CONTEXT_DIR/SESSION_SUMMARY.md"
echo ""
echo "2. View checkpoints (most important):"
echo "   ls $CONTEXT_DIR/checkpoints/"
echo ""
echo "3. When session breaks, provide this context to new session:"
echo "   cat $CONTEXT_DIR/checkpoints/*.md"
echo ""
