#!/bin/bash
cd /data/jinc/git_chen/Biomni

# Activate conda environment
source /alan-data/jinc/miniconda3/etc/profile.d/conda.sh
conda activate biomni_e1

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
lsof -i :8012 | grep -v COMMAND | awk '{print $2}' | xargs -r kill 2>/dev/null
sleep 2

# Launch server
echo "🚀 Starting API server on port 8012..."
nohup uvicorn biomni_api_server_qwen3_next_80b_auto_clean_azimuth:app --host 0.0.0.0 --port 8012 > logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth_8012.log 2>&1 &

SERVER_PID=$!
echo "✅ Server started with PID: $SERVER_PID"
echo "📋 Log file: logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth_8012.log"

sleep 5
if lsof -i :8012 > /dev/null 2>&1; then
    echo "✅ Server is listening on port 8012"
else
    echo "❌ Server failed to start, check logs"
    tail -20 logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth_8012.log
fi
