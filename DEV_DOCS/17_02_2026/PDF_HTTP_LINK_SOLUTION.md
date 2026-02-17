# PDF Report HTTP Link Solution

**Date**: February 17, 2026  
**Issue**: Gradio File download not working  
**Solution**: Use HTTP server links instead

## Problem
- Gradio download button caused panel flash but no download
- No errors - silent failure

## Solution
Use existing HTTP server on port 8100:
- Save PDFs to session folders: `local_outputs/{session_id}/`
- Generate clickable link: `http://alan.astrazeneca.net:8100/{session_id}/conversation_{session_id}.pdf`
- Display link in chat as markdown

## Changes
1. Removed Gradio File component and download button
2. PDF saved to agent's session folder
3. Function returns HTTP URL instead of file path
4. Link displayed in chat message

## Configuration
```python
HTTP_SERVER_BASE_URL = "http://alan.astrazeneca.net:8100"
```

## Advantages
- Reliable (no Gradio quirks)
- Simple (no state management)
- Browsable (can access all sessions)
- Persistent (survives UI restart)

## Commit
```
e98d842 - feat: use HTTP server links instead of Gradio download for PDFs
```
