# PDF Generation Fix - Signal Thread Issue

**Date**: February 18, 2026  
**Error**: `signal only works in main thread of the main interpreter`

## Root Cause
`signal.SIGALRM` only works in main thread. Gradio runs in background threads.

## Solution
Check thread before using signal:
```python
use_timeout = threading.current_thread() is threading.main_thread()
if use_timeout:
    signal.signal(signal.SIGALRM, timeout_handler)
```

## Result
✅ PDF generation works (9052 bytes)  
✅ HTTP link: `http://alan.astrazeneca.net:8100/{session_id}/conversation_{session_id}.pdf`

## Commit
`cc34776` - fix: enable PDF generation in Gradio background threads
