#!/bin/bash
# Start Biomni Gradio UI with PDF support in background

# Proxy configuration for drylab workstation
export http_proxy=
export https_proxy="http://emeapzen.astrazeneca.net:9480"
export HTTP_PROXY=
export HTTPS_PROXY="http://emeapzen.astrazeneca.net:9480"
export NO_PROXY="10.0.0.0/8,172.29.0.0/8,astrazeneca.net"
export no_proxy="10.0.0.0/8,172.29.0.0/8,astrazeneca.net"

# Configuration
GRADIO_PORT=${GRADIO_PORT:-7861}
GRADIO_SERVER_NAME=${GRADIO_SERVER_NAME:-"0.0.0.0"}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/biomni_gradio_with_pdf.log"
PID_FILE="${SCRIPT_DIR}/.biomni_gradio_with_pdf.pid"

echo "=================================="
echo "Biomni Gradio UI with PDF Reports"
echo "=================================="
echo "Port: $GRADIO_PORT"
echo "Log: $LOG_FILE"
echo "=================================="

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  Server already running (PID: $OLD_PID)"
        echo "   Stop it first: kill $OLD_PID"
        exit 1
    else
        rm "$PID_FILE"
    fi
fi

# Check port
if lsof -i :$GRADIO_PORT > /dev/null 2>&1; then
    echo "❌ Port $GRADIO_PORT is in use!"
    exit 1
fi

# Export env vars
export GRADIO_PORT
export GRADIO_SERVER_NAME

# Start server
echo "🚀 Starting Gradio UI in background..."
nohup bash -c "source $(conda info --base)/etc/profile.d/conda.sh && conda activate biomni_e1 && python '${SCRIPT_DIR}/biomni_gradio_demo_with_pdf.py'" > "$LOG_FILE" 2>&1 &
PID=$!

echo "$PID" > "$PID_FILE"
sleep 3

if ps -p "$PID" > /dev/null 2>&1; then
    echo "✅ Server started (PID: $PID)"
    echo "   URL: http://localhost:$GRADIO_PORT"
    echo "   Log: tail -f $LOG_FILE"
else
    echo "❌ Failed to start"
    cat "$LOG_FILE"
    rm "$PID_FILE"
    exit 1
fi
