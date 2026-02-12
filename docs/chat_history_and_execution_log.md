# Chat History and Execution Log Features

## Overview

Biomni's API and Langflow component support configuration options for controlling conversation behavior and output detail:

1. **use_chat_history**: Maintains conversation context across multiple turns (Langflow component)
2. **include_execution_log**: Includes internal execution steps in responses (Langflow component)  
3. **save_pdf**: Controls whether to save conversation history as PDF (API server)

---

## 1. use_chat_history (Langflow Component)

### What it does:
- **When enabled (True)**: Maintains conversation context across multiple turns
- **When disabled (False)**: Each query is treated as an independent conversation

### Use Cases:

**Enabled - Multi-turn conversations:**
```
User: "What is BRCA1?"
Agent: "BRCA1 is a tumor suppressor gene involved in DNA repair..."

User: "What are common mutations in this gene?"
Agent: "Common BRCA1 mutations include..." ✅ Understands "this gene" = BRCA1
```

**Disabled - Independent queries:**
```
User: "What is BRCA1?"
Agent: "BRCA1 is a tumor suppressor gene..."

User: "What are common mutations in this gene?"
Agent: "Which gene are you referring to?" ❌ No context
```

### When to use:
- ✅ **Enable**: Research dialogues, exploratory conversations, follow-up questions
- ❌ **Disable**: Independent queries, batch processing, simple Q&A

### Implementation in Langflow:
```python
# From biomni_langflow_component.py
if use_chat_history and hasattr(self, '_chat_history'):
    # Multi-turn: send full history
    self._chat_history.append({"role": "user", "content": query})
    payload = {"messages": self._chat_history}
else:
    # Single-turn: send only current query
    payload = {"prompt": query}
    if use_chat_history:
        self._chat_history = [{"role": "user", "content": query}]
```

---

## 2. include_execution_log (Langflow Component)

### What it does:
- **When enabled (True)**: Appends the full execution log to the response
- **When disabled (False)**: Returns only the final answer

### The Execution Log Contains:
- User queries received
- Agent reasoning steps
- Tool invocations (e.g., `query_uniprot`, `query_literature`)
- Tool results and outputs
- Self-critique iterations
- Errors or retry attempts

### Example:

**Without execution log (include_log=False):**
```
BRCA1 is a tumor suppressor gene involved in DNA repair and genome stability.
```

**With execution log (include_log=True):**
```
BRCA1 is a tumor suppressor gene involved in DNA repair and genome stability.

--- Execution Log ---
==================================
 User Message 
==================================
What is BRCA1?

==================================
 AI Message 
==================================
I'll search the database for BRCA1 information...

==================================
 Tool Execution 
==================================
Tool: query_uniprot
Arguments: {'gene': 'BRCA1'}
Result: Retrieved protein P38398

==================================
 AI Message 
==================================
Based on the database query, BRCA1 functions as a tumor suppressor...
```

### When to use:
- ✅ **Enable**: Debugging, understanding reasoning, transparency, research audit trails
- ❌ **Disable**: Clean end-user output, production APIs, simple responses

### Implementation in Langflow:
```python
# From biomni_langflow_component.py
if include_log and result.get("log"):
    assistant_reply += f"\n\n--- Execution Log ---\n{result['log']}"
```

---

## 3. save_pdf (API Server)

### What it does:
- **When enabled (True, default)**: Saves conversation history as PDF with visualizations
- **When disabled (False)**: No PDF is generated, no output directory is created

### PDF Contents:
- Complete conversation history
- All agent reasoning steps
- Code execution blocks
- Generated plots and visualizations (if `include_images=True`)
- Formatted markdown with execution logs

### Output Structure:
```
./local_outputs/
  └── 20260209_122345_123/           # Timestamped folder
      └── conversation_20260209_122345_123.pdf
```

### API Request Examples:

**With PDF (default):**
```bash
curl -X POST "http://localhost:8009/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is BRCA1?",
    "save_pdf": true
  }'
```

**Without PDF:**
```bash
curl -X POST "http://localhost:8009/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is BRCA1?",
    "save_pdf": false
  }'
```

### When to use:
- ✅ **Enable**: Research documentation, sharing results, audit trails, presentations
- ❌ **Disable**: Quick queries, testing, batch processing, memory constraints

### Implementation in API Server:
```python
# From biomni_api_server_qwen3_next_80b_auto_clean_azimuth.py
if save_pdf:
    try:
        full_pdf_path = os.path.join(output_folder, pdf_filename)
        agent.save_conversation_history(full_pdf_path, save_pdf=True)
        pdf_path = f"{full_pdf_path}.pdf"
    except Exception as pdf_error:
        print(f"Warning: Failed to save PDF: {pdf_error}")
else:
    print(f"PDF saving skipped (save_pdf=False)")
```

**Important**: When `save_pdf=False`, the timestamped output directory is still created but remains empty. The directory creation happens before the PDF flag check. This is by design to maintain consistent folder structure for potential future outputs.

---

## Technical Details

### Return Structure from agent.go()

```python
log, response = agent.go("What is BRCA1?")

# log: List of execution steps (each step is a formatted string)
log = [
    "================================== User Message ==================================\nWhat is BRCA1?",
    "================================== AI Message ==================================\nSearching database...",
    "================================== Tool Execution ==================================\nTool: query_uniprot(...)"
]

# response: Final answer string
response = "BRCA1 is a tumor suppressor gene..."
```

### API Response Structure

```json
{
  "response": "BRCA1 is a tumor suppressor gene...",
  "log": "User Message: What is BRCA1?\nAI: Searching...\nTool: query_uniprot...",
  "data": null,
  "pdf_path": "./local_outputs/20260209_122345_123/conversation_20260209_122345_123.pdf"
}
```

### Langflow Component Configuration

```python
# Configuration options in biomni_langflow_component.py
{
    "use_chat_history": {
        "display_name": "Use Chat History",
        "type": "bool",
        "value": False,
        "info": "Whether to maintain conversation history"
    },
    "include_log": {
        "display_name": "Include Execution Log",
        "type": "bool",
        "value": False,
        "info": "Whether to include Biomni's execution log in the response"
    },
    "timeout": {
        "display_name": "Timeout (seconds)",
        "type": "int", 
        "value": 180,
        "info": "Request timeout (Biomni can take time for complex queries)"
    },
    "max_output_length": {
        "display_name": "Max Output Length",
        "type": "int",
        "value": 0,  # 0 means no limit
        "info": "Maximum characters to return (0 = no limit)"
    }
}
```

---

## Best Practices

### For Research Conversations
```yaml
use_chat_history: true
include_log: false        # Unless debugging
save_pdf: true           # Document findings
timeout: 180
```

### For Production APIs
```yaml
use_chat_history: false
include_log: false
save_pdf: false          # Reduce I/O and storage
max_output_length: 5000
timeout: 180
```

### For Debugging
```yaml
use_chat_history: true
include_log: true         # See full reasoning
save_pdf: true           # Keep detailed records
timeout: 300
```

### For Batch Processing
```yaml
use_chat_history: false   # Independent queries
include_log: false
save_pdf: false          # Reduce overhead
timeout: 180
```

---

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/test_chat_history_and_log.py -v

# Run specific test
pytest tests/test_chat_history_and_log.py::TestChatHistoryAndExecutionLog::test_execution_log_structure -v
```

The test suite covers:
- Log structure and content
- Chat history context maintenance  
- Single vs multi-turn conversations
- Execution log formatting
- API response structures
- PDF generation control
- Langflow integration patterns

---

## Examples

### Example 1: Single Query with PDF

```python
from biomni.agent import A1

agent = A1(path='./data')
log, response = agent.go("What is BRCA1?")

# Save conversation as PDF
agent.save_conversation_history("brca1_analysis.pdf", save_pdf=True)
# Result: brca1_analysis.pdf created with full conversation
```

### Example 2: Single Query without PDF

```python
from biomni.agent import A1

agent = A1(path='./data')
log, response = agent.go("What is BRCA1?")

# Don't save PDF
agent.save_conversation_history("output.pdf", save_pdf=False)
# Result: No file created, returns immediately
```

### Example 3: Multi-turn Conversation in Langflow

```yaml
# Langflow Configuration
Component: BiomniComponent
Settings:
  use_chat_history: true
  include_log: false

# Turn 1
Input: "What is BRCA1?"
Output: "BRCA1 is a tumor suppressor gene..."

# Turn 2 (with context)
Input: "What mutations are associated with it?"
Output: "Common BRCA1 mutations include frameshift mutations..." # Knows "it" = BRCA1
```

### Example 4: API with Execution Log

```bash
# Request with execution log
curl -X POST "http://localhost:8009/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is BRCA1?"}' | jq '.log'

# Output shows full execution trace:
# "User Message: What is BRCA1?\n
#  AI Message: I'll search the database...\n
#  Tool Execution: query_uniprot(gene='BRCA1')\n
#  Tool Result: Retrieved protein P38398\n
#  AI Message: Based on the query..."
```

---

## Troubleshooting

### Chat History Not Working
- Check that `use_chat_history: true` is set in Langflow component
- Verify `self._chat_history` is being maintained between calls
- Ensure messages are in correct format: `{"role": "user/assistant", "content": "..."}`

### Execution Log Missing
- Verify `include_log: true` in Langflow component
- Check that API returns `log` field in response
- Ensure `agent.log` is populated after `agent.go()` call

### PDF Not Generated
- Check `save_pdf: true` in API request
- Verify PDF generation dependencies installed (WeasyPrint, markdown2pdf, or Pandoc)
- Check `./local_outputs/` directory permissions
- Look for timeout errors (default 60s for PDF generation)

### Empty Output Directory Created
- This is expected behavior even with `save_pdf=False`
- Directory is created before PDF flag check for consistency
- Will be cleaned up by auto-cleanup scripts if configured

---

## Related Documentation

- Main README: `README.md`
- Configuration Guide: `docs/configuration.md`
- API Server Documentation: `server.md`
- Langflow Component: `biomni_langflow_component.py`
- Contributing Guide: `CONTRIBUTION.md`

