# Biomni Gradio UI Demo - Setup Complete ✅

**Date**: February 12, 2026  
**Port**: 7861  
**Status**: Running

---

## 🎨 Access Information

**Local Access**:
- URL: http://localhost:7861
- Direct: http://10.85.202.54:7861

**Process Information**:
- PID: Check with `cat /data/jinc/git_chen/Biomni/.biomni_gradio_demo.pid`
- Log: `/data/jinc/git_chen/Biomni/biomni_gradio_demo.log`
- Python Environment: `biomni_e1` conda environment

---

## 🚀 Features

The Gradio UI provides:

1. **Interactive Chat Interface**
   - Dual-pane view: Main agent + Executor details
   - File upload support (images, PDFs, etc.)
   - Real-time streaming responses
   - Copy and share buttons

2. **Biomni A1 Agent**
   - Same configuration as your API server
   - Model: Qwen/Qwen3-Next-80B-A3B-Instruct-FP8
   - Commercial mode enabled
   - Sandbox file operations (output: `./local_outputs/gradio_demo/`)

3. **v0.0.8 Capabilities**
   - 100+ protocols (Addgene, ThermoFisher)
   - sgRNA design knowledge base
   - 7 new databases (ChEMBL, ClinicalTrials, etc.)
   - Lab automation support
   - GPT-5 compatible

---

## 📋 Management Commands

### Start/Stop
```bash
# Start (if not running)
cd /data/jinc/git_chen/Biomni
GRADIO_PORT=7861 ./start_biomni_gradio_demo.sh

# Stop
PID=$(cat .biomni_gradio_demo.pid)
kill $PID

# Or force stop
pkill -f biomni_gradio_demo.py
```

### Monitor
```bash
# View logs
tail -f /data/jinc/git_chen/Biomni/biomni_gradio_demo.log

# Check status
lsof -i :7861

# Check process
ps aux | grep biomni_gradio_demo
```

### Alternative Ports
```bash
# Launch on different port
GRADIO_PORT=7862 ./start_biomni_gradio_demo.sh

# With public sharing
GRADIO_PORT=7861 GRADIO_SHARE=True ./start_biomni_gradio_demo.sh

# With access code protection
GRADIO_PORT=7861 GRADIO_REQUIRE_AUTH=True ./start_biomni_gradio_demo.sh
# Default access code: "Biomni2025"
```

---

## 🔧 Configuration

**Environment Variables** (set before running `start_biomni_gradio_demo.sh`):

| Variable | Default | Description |
|----------|---------|-------------|
| `GRADIO_PORT` | 7861 | Port to bind to |
| `GRADIO_SERVER_NAME` | 0.0.0.0 | Server name/IP (0.0.0.0 = all interfaces) |
| `GRADIO_SHARE` | False | Create public shareable link via Gradio |
| `GRADIO_REQUIRE_AUTH` | False | Require access code ("Biomni2025") |

**Agent Configuration** (in `biomni_gradio_demo.py`):
```python
AGENT_CONFIG = {
    'path': './data',
    'llm': 'Qwen/Qwen3-Next-80B-A3B-Instruct-FP8',
    'base_url': 'https://vllm.paas-jade.astrazeneca.net/v1',
    'api_key': 'natura15tup1d1ty',
    'commercial_mode': True,
    'output_folder': './local_outputs/gradio_demo'
}
```

---

## 🆚 Gradio UI vs API Server

**Gradio UI (Port 7861)**:
- ✅ Interactive web interface
- ✅ Visual chat experience
- ✅ File upload in browser
- ✅ Real-time streaming
- ✅ Great for testing and demos
- ⚠️ Single-user sessions (one conversation at a time)

**API Server (Port 8009)**:
- ✅ Programmatic access
- ✅ Multiple concurrent requests
- ✅ Integration with other tools
- ✅ PDF generation
- ✅ Production-grade
- ⚠️ No visual interface

**Best Practice**: Use both!
- Gradio UI for interactive exploration and demos
- API server for production workloads and integrations

---

## 🐛 Troubleshooting

### Port already in use
```bash
# Find what's using the port
lsof -i :7861

# Kill specific process
kill <PID>
```

### UI not starting
```bash
# Check logs
cat /data/jinc/git_chen/Biomni/biomni_gradio_demo.log

# Test conda environment
conda run -n biomni_e1 python -c "from biomni.agent import A1; print('OK')"

# Remove stale PID file
rm /data/jinc/git_chen/Biomni/.biomni_gradio_demo.pid
```

### Gradio not installed
```bash
# Install gradio (should already be installed)
pip install 'gradio>=5.0,<6.0'
```

### Dependencies missing
```bash
# The script uses conda environment biomni_e1
# If you see import errors, activate the environment:
conda activate biomni_e1

# Then check if biomni is installed
python -c "from biomni.agent import A1; print('Biomni OK')"
```

---

## 📁 Files Created

1. **`biomni_gradio_demo.py`**
   - Main UI launcher script
   - Configures agent and Gradio settings
   - Uses conda environment biomni_e1

2. **`start_biomni_gradio_demo.sh`**
   - Bash wrapper for nohup background launch
   - PID file management
   - Port conflict detection

3. **`.biomni_gradio_demo.pid`**
   - Stores process ID (created when running)

4. **`biomni_gradio_demo.log`**
   - Application logs (created when running)

---

## 🎯 Usage Examples

### Basic Query
```
User: "What databases are available in Biomni?"
Agent: Lists all available databases including new ChEMBL, ClinicalTrials, etc.
```

### Protocol Search
```
User: "Show me the AAV production protocol from Addgene"
Agent: Retrieves and displays the full protocol with steps
```

### File Upload
```
User: Upload an Excel file with gene expression data
Agent: Analyzes the data and provides insights
```

### Complex Analysis
```
User: "Design sgRNAs for TP53 gene and find relevant protocols"
Agent: 
1. Searches validated sgRNA database
2. Provides design recommendations
3. Links to relevant CRISPR protocols
```

---

## 🔐 Security Notes

1. **Access Control**: 
   - Set `GRADIO_REQUIRE_AUTH=True` for password protection
   - Default code: "Biomni2025" (change in `biomni_gradio_demo.py`)

2. **Network Exposure**:
   - Currently bound to 0.0.0.0 (accessible from network)
   - Use `GRADIO_SERVER_NAME=127.0.0.1` for localhost only
   - Firewall rules should protect external access

3. **API Keys**:
   - Qwen API key is in the script (natura15tup1d1ty)
   - Consider moving to environment variables for production

---

## 📊 Performance

**Initial Load**: ~15-20 seconds (agent initialization)  
**Response Time**: Similar to API server (~5-30s depending on query)  
**Memory**: ~2-3GB (similar to API server)  
**Concurrency**: Single user (creates fresh agent per conversation)

---

## ✅ Next Steps

1. **Test the UI**: Open http://localhost:7861 in your browser
2. **Try Examples**: Test with protocol queries, sgRNA design, database searches
3. **Monitor Logs**: `tail -f biomni_gradio_demo.log`
4. **Compare with API**: Test same query on both UI and API server
5. **Share with Team**: Forward the URL (http://10.85.202.54:7861) if on same network

---

**Documentation**: This file  
**Code**: `biomni_gradio_demo.py`, `start_biomni_gradio_demo.sh`  
**Feature Documentation**: `DEV_DOCS/12_02_2026/NEW_FEATURES_v008_DETAILED.md`
