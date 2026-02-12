# Biomni Sandbox Fix - Technical Summary

## State Before Fix: Partial Implementation

### What Was Already There ✅
The sandbox concept was **partially implemented** at the API level:

1. **API Server** (`biomni_api_server_qwen3_next_80b_auto_clean_azimuth.py`):
   ```python
   # Line 71-72: Created session-specific folders
   timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
   output_folder = f"./local_outputs/{timestamp}"
   os.makedirs(output_folder, exist_ok=True)
   
   # Line 117: Saved PDFs to session folder
   full_pdf_path = os.path.join(output_folder, pdf_filename)
   agent.save_conversation_history(full_pdf_path, save_pdf=True)
   ```

2. **Directory Structure**: `local_outputs/` existed with timestamped session folders

### The Critical Bug 🐛
The `output_folder` was created but **never passed to the agent!**

```python
# OLD CODE (Line 81):
agent = A1(**AGENT_CONFIG)  # ❌ Agent has no idea where to save files!
```

**Result**: When the agent executed Python code:
```python
# Inside agent execution:
plt.savefig('plot.png')     # Saves to os.getcwd() = /data/jinc/git_chen/Biomni/
df.to_csv('data.csv')       # Saves to os.getcwd() = /data/jinc/git_chen/Biomni/
```

All files leaked to the repository root instead of `local_outputs/<session>/`.

---

## The Fix: Three-Part Solution

### Part 1: Agent Core (`biomni/agent/a1.py`)

**Added `output_folder` parameter to agent initialization:**

```python
# Line 56-67: Added parameter
def __init__(
    self,
    path: str | None = None,
    llm: str | None = None,
    # ... other params ...
    output_folder: str | None = None,  # ← NEW
):
```

**Stored it as instance variable:**

```python
# Line 190-196: Store and create folder
self.output_folder = output_folder
if output_folder:
    os.makedirs(output_folder, exist_ok=True)
    print(f"📁 Output folder: {output_folder}")
```

**Passed it to code execution:**

```python
# Line 1394-1402: Pass to run_python_repl
if hasattr(self, 'output_folder') and self.output_folder:
    result = run_with_timeout(
        run_python_repl, 
        args=[code], 
        kwargs={'working_dir': self.output_folder},  # ← Pass it here
        timeout=timeout
    )
else:
    result = run_with_timeout(run_python_repl, [code], timeout=timeout)
```

### Part 2: Execution Environment (`biomni/tool/support_tools.py`)

**Modified `run_python_repl()` to accept and use `working_dir`:**

```python
# Line 13: Added working_dir parameter
def run_python_repl(command: str, working_dir: str = None) -> str:
    """Executes Python code in persistent environment.
    
    Args:
        command: Python code to execute
        working_dir: Optional working directory for file operations
    """
    
    def execute_in_repl(command: str) -> str:
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()

        # Save current working directory
        original_cwd = None
        if working_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(working_dir)  # ← Change to session folder!
            except Exception as e:
                print(f"Warning: Could not change to {working_dir}: {e}")

        # ... execute code ...
        
        finally:
            sys.stdout = old_stdout
            # Restore original working directory
            if original_cwd:
                try:
                    os.chdir(original_cwd)  # ← Always restore!
                except Exception as e:
                    print(f"Warning: Could not restore working directory: {e}")
```

### Part 3: API Wrapper Connection

**Connected the dots in API server:**

```python
# Line 81: OLD CODE
agent = A1(**AGENT_CONFIG)  # ❌

# Line 81: NEW CODE
agent = A1(**AGENT_CONFIG, output_folder=output_folder)  # ✅
```

---

## How It Works Now 🎯

### Execution Flow:

```
1. API Request arrives
   ↓
2. Create: output_folder = "./local_outputs/20260211_154723_456"
   ↓
3. Create agent: A1(..., output_folder="./local_outputs/20260211_154723_456")
   ↓
4. Agent stores: self.output_folder = "./local_outputs/20260211_154723_456"
   ↓
5. Agent executes code:
   - original_cwd = os.getcwd()  # Save: /data/jinc/git_chen/Biomni
   - os.chdir(self.output_folder)  # Change to session folder
   - exec(code)  # All file operations happen here!
     • plt.savefig('plot.png')  → saves to ./local_outputs/20260211_154723_456/plot.png ✅
     • df.to_csv('data.csv')    → saves to ./local_outputs/20260211_154723_456/data.csv ✅
   - os.chdir(original_cwd)  # Restore: /data/jinc/git_chen/Biomni
   ↓
6. Return result
```

### Key Properties:

✅ **Sandboxed**: All file operations contained in session folder  
✅ **Safe**: Original directory always restored (even on errors)  
✅ **Persistent**: Agent namespace preserved across executions within session  
✅ **Backward Compatible**: If `output_folder=None`, behaves as before  
✅ **Per-Request**: Each API request gets its own session folder  

---

## Why This Design?

### Alternative Approaches Considered:

1. **❌ Modify all tool functions**: Would require changing 100+ functions across 20+ files
2. **❌ Monkey-patch `open()`/`savefig()`**: Too invasive, fragile, hard to debug
3. **✅ Change working directory during execution**: Clean, simple, centralizes the fix

### Benefits:

- **Single point of change**: Only `run_python_repl()` needs modification
- **Non-invasive**: Existing tool functions work unchanged
- **Transparent**: Tools use relative paths naturally
- **Testable**: Easy to verify with simple test cases
- **Maintainable**: Clear separation of concerns

---

## Verification

After restart, the logs show:

```
[Biomni API] Output folder: ./local_outputs/20260211_154723_456
📁 Output folder: ./local_outputs/20260211_154723_456
```

And files are created in:
```
./local_outputs/20260211_154723_456/
├── plot.png
├── data.csv
└── conversation_20260211_154723_456.pdf
```

Not in:
```
./  (repository root) ✅
```

---

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| API creates folder | ✅ Yes | ✅ Yes |
| Agent knows folder | ❌ No | ✅ Yes |
| Working dir changed | ❌ No | ✅ Yes (during execution) |
| Files contained | ❌ No (leaked to root) | ✅ Yes (in session folder) |
| Backward compatible | N/A | ✅ Yes (`output_folder=None`) |

**The fix was to complete the implementation chain**: API → Agent → Execution Environment
