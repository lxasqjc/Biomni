#!/bin/bash
# Production deployment script for Biomni API server
# Fixes concurrency and memory issues

export http_proxy=
export https_proxy="http://emeapzen.astrazeneca.net:9480"
export HTTP_PROXY=
export HTTPS_PROXY="http://emeapzen.astrazeneca.net:9480"

set -e

echo "🚀 Starting Biomni API Server in Production Mode"

# Set environment variables for better performance
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Change to the correct directory
cd /alan-data/jinc/git_chen/Biomni

# Kill any existing instances
pkill -f "biomni_api_server_qwen3_30b_auto_clean" || echo "No existing instances to kill"

# Production deployment with Gunicorn for better concurrency
# echo "Starting with Gunicorn for production concurrency..."

# Option 1: High concurrency (recommended for multiple users)
# nohup gunicorn biomni_api_server_qwen3_30b_auto_clean:app \
#     --bind 0.0.0.0:8019 \
#     --workers 4 \
#     --worker-class uvicorn.workers.UvicornWorker \
#     --max-requests 100 \
#     --max-requests-jitter 50 \
#     --preload \
#     --timeout 600 \
#     --access-logfile logs/biomni_access.log \
#     --error-logfile logs/biomni_error.log \
#     --pid logs/biomni.pid \
#     > logs/biomni_production.log 2>&1 &

# Option 2: Alternative - Uvicorn with multiple workers (uncomment if preferred)
nohup uvicorn biomni_api_server_qwen3_30b_auto_clean:app \
    --host 0.0.0.0 \
    --port 8019 \
    --workers 4 \
    --access-log \
    --log-level info \
    > logs/biomni_uvicorn.log 2>&1 &

echo "✅ Biomni API server started in production mode"
echo "📊 Server running on: http://0.0.0.0:8019"
echo "📝 Logs: ./logs/biomni_production.log"
echo "🔍 Check status: curl http://localhost:8019/health"
echo "🛑 Stop server: pkill -f biomni_api_server_qwen3_30b_auto_clean"

# Show initial logs
sleep 3
echo "=== Initial server logs ==="
tail -20 logs/biomni_production.log

echo "=== Production server deployment complete ==="