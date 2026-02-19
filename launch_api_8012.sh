#!/bin/bash
cd /data/jinc/git_chen/Biomni
source /alan-data/jinc/miniconda3/etc/profile.d/conda.sh
conda activate biomni_e1

# Load .env if exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "Loaded .env with API keys"
fi

# Launch API server
nohup uvicorn biomni_api_server_qwen3_next_80b_auto_clean_azimuth:app --host 0.0.0.0 --port 8012 > logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth_8012.log 2>&1 &

echo "API server started on port 8012"
echo "Log: logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth_8012.log"
