#!/bin/bash
cd /data/jinc/git_chen/Biomni

# Activate conda environment
source /alan-data/jinc/miniconda3/etc/profile.d/conda.sh
conda activate biomni_e1

# Configure proxy settings for vLLM backend access
# IMPORTANT: Add specific hostnames to NO_PROXY since httpx may not parse CIDR notation correctly
export http_proxy=
export https_proxy="http://emeapzen.astrazeneca.net:9480"
export HTTP_PROXY=
export HTTPS_PROXY="http://emeapzen.astrazeneca.net:9480"
export NO_PROXY="10.0.0.0/8,172.29.0.0/8,astrazeneca.net,*.astrazeneca.net,vllm.paas-jade.astrazeneca.net,localhost,127.0.0.1"
export no_proxy="10.0.0.0/8,172.29.0.0/8,astrazeneca.net,*.astrazeneca.net,vllm.paas-jade.astrazeneca.net,localhost,127.0.0.1"
echo "✅ Configured proxy settings (vLLM hostname explicitly bypassed)"

# Load environment variables from .env
if [ -f .env ]; then
    set -a
    source .env
    set +a
    echo "✅ Loaded API keys from .env"
else
    echo "⚠️ .env file not found"
fi

# Kill any existing server on port 8012
EXISTING_PID=$(lsof -i :8012 | grep -v COMMAND | awk '{print $2}' | head -1)
if [ ! -z "$EXISTING_PID" ]; then
    kill $EXISTING_PID 2>/dev/null
    sleep 2
    echo "✅ Killed existing server (PID: $EXISTING_PID)"
fi

# Launch server
echo "🚀 Starting API server on port 8012..."
nohup uvicorn biomni_api_server_qwen3_next_80b_auto_clean_azimuth:app --host 0.0.0.0 --port 8012 > logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth_8012.log 2>&1 &

SERVER_PID=$!
echo "✅ Server started with PID: $SERVER_PID"
echo "📋 Log file: logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth_8012.log"

sleep 5
if lsof -i :8012 > /dev/null 2>&1; then
    echo "✅ Server is listening on port 8012"
    NEW_PID=$(lsof -i :8012 | grep uvicorn | awk '{print $2}' | head -1)
    echo "📊 Verifying proxy settings in process..."
    cat /proc/$NEW_PID/environ | tr '\0' '\n' | grep -E "NO_PROXY|HTTPS_PROXY|SERPER_API_KEY" | sed 's/=.*/=***/' || true
else
    echo "❌ Server failed to start, check logs"
    tail -20 logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth_8012.log
fi
