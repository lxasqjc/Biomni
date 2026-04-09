#!/usr/bin/env bash
# Launch Biomni Streamlit UI
# Usage: bash start_streamlit_ui.sh [port] [api_url]
# Defaults: port=7863, api_url=http://localhost:8020

PORT=${1:-7863}
export BIOMNI_UI_API_URL=${2:-http://localhost:8020}

cd /alan-data/jinc/git_chen/Biomni

# Kill any existing process on this port
OLDPID=$(lsof -t -i :$PORT 2>/dev/null)
if [ -n "$OLDPID" ]; then
    kill -9 $OLDPID 2>/dev/null
    sleep 1
fi

# Use setsid nohup so the process survives terminal/tmux disconnects
setsid nohup /alan-data/jinc/miniconda3/envs/biomni_e1/bin/streamlit run biomni_streamlit_ui.py \
    --server.port $PORT \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.maxUploadSize 200 \
    > /alan-data/jinc/git_chen/Biomni/logs/biomni_streamlit_ui.log 2>&1 &

echo "Biomni Streamlit UI starting on port $PORT (API: $BIOMNI_UI_API_URL)"
echo "Access at: http://alan:$PORT"
echo "Log: logs/biomni_streamlit_ui.log"
sleep 3 && ss -tlnp | grep "$PORT" | grep -q streamlit && echo "Running OK" || echo "Check log for errors"
