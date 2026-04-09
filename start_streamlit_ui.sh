#!/usr/bin/env bash
# Launch Biomni Streamlit UI on port 7863
# Usage: bash start_streamlit_ui.sh [port] [api_url]
# Defaults: port=7863, api_url=http://localhost:8020

PORT=${1:-7863}
export BIOMNI_UI_API_URL=${2:-http://localhost:8020}

cd /alan-data/jinc/git_chen/Biomni

systemctl --user stop biomni-ui-streamlit.scope 2>/dev/null
sleep 0.5

systemd-run --user --scope --unit=biomni-ui-streamlit \
  bash -c "exec /alan-data/jinc/miniconda3/envs/biomni_e1/bin/streamlit run biomni_streamlit_ui.py \
    --server.port $PORT \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.maxUploadSize 200 \
    > /alan-data/jinc/git_chen/Biomni/logs/biomni_streamlit_ui.log 2>&1" &

echo "Biomni Streamlit UI starting on port $PORT (API: $BIOMNI_UI_API_URL)"
echo "Access at: http://alan:$PORT"
echo "Log: logs/biomni_streamlit_ui.log"
