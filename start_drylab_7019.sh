#!/usr/bin/env bash
# Launch Biomni API server for Qwen3.5-25B (gguf) on ludwig drylab — port 7019
set -euo pipefail

cd /alan-data/jinc/git_chen/Biomni

# Proxy: ludwig must bypass the proxy
unset http_proxy HTTP_PROXY
export https_proxy="http://emeapzen.astrazeneca.net:9480"
export HTTPS_PROXY="http://emeapzen.astrazeneca.net:9480"
export NO_PROXY="ludwig,vllm.paas-jade.astrazeneca.net,*.astrazeneca.net,10.0.0.0/8,172.29.0.0/8,localhost,127.0.0.1"
export no_proxy="ludwig,vllm.paas-jade.astrazeneca.net,*.astrazeneca.net,10.0.0.0/8,172.29.0.0/8,localhost,127.0.0.1"

PORT=7019
LOG="logs/biomni_api_server_qwen3_5_25B_drylab_${PORT}.log"
mkdir -p logs

echo "Starting Biomni drylab server on port ${PORT} → ludwig:1234 (qwen3_5)..."
nohup /alan-data/jinc/miniconda3/envs/biomni_e1/bin/uvicorn \
    biomni_api_server_qwen3_5_25B_drylab:app \
    --host 0.0.0.0 --port "${PORT}" \
    > "${LOG}" 2>&1 &

echo "PID: $!  Log: ${LOG}"
