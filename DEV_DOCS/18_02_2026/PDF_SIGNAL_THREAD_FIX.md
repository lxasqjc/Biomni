# PDF Generation Fix - Signal Thread Issue

**Date**: February 18, 2026
**Issue**: PDF generation failed silently in Gradio UI
**Error**: `signal only works in main thread of the main interpreter`

## Root Cause

`save_conversation_history()` uses `signal.SIGALRM` for 60s timeout, but signal only works in main thread. Gradio runs responses in background threads.

## Solution

Check thread before using signal:

```python
import threading
use_timeout = threading.current_thread() is threading.main_thread()

if use_timeout:
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(60)
```

## Result

✅ PDF generation now works in Gradio UI (9052 bytes)
✅ HTTP link displayed correctly

## Commit

```
cc34776 - fix: enable PDF generation in Gradio background threads
```
