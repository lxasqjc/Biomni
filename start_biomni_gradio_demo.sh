#!/bin/bash
# Start Biomni Gradio UI in background with nohup

# Configuration
GRADIO_PORT=${GRADIO_PORT:-7861}  # Default to 7861 to avoid conflict with default 7860
GRADIO_SERVER_NAME=${GRADIO_SERVER_NAME:-"0.0.0.0"}
GRADIO_SHARE=${GRADIO_SHARE:-"False"}
GRADIO_REQUIRE_AUTH=${GRADIO_REQUIRE_AUTH:-"False"}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/biomni_gradio_demo.log"
PID_FILE="${SCRIPT_DIR}/.biomni_gradio_demo.pid"

echo "=================================="
echo "Biomni Gradio UI Launcher"
echo "=================================="
echo "Port: $GRADIO_PORT"
echo "Server: $GRADIO_SERVER_NAME"
echo "Log: $LOG_FILE"
echo "=================================="

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  Gradio UI already running (PID: $OLD_PID)"
        echo "   Stop it first: kill $OLD_PID"
        exit 1
    else
        echo "🧹 Removing stale PID file..."
        rm "$PID_FILE"
    fi
fi

# Check if port is in use
if lsof -i :$GRADIO_PORT > /dev/null 2>&1; then
    echo "❌ Port $GRADIO_PORT is already in use!"
    echo "   Check with: lsof -i :$GRADIO_PORT"
    exit 1
fi

# Export proxy settings for drylab workstation
export http_proxy=
export https_proxy="http://emeapzen.astrazeneca.net:9480"
export HTTP_PROXY=
export HTTPS_PROXY="http://emeapzen.astrazeneca.net:9480"
export NO_PROXY="10.0.0.0/8,172.29.0.0/8,astrazeneca.net"
export no_proxy="10.0.0.0/8,172.29.0.0/8,astrazeneca.net"

# Export environment variables
export GRADIO_PORT
export GRADIO_SERVER_NAME
export GRADIO_SHARE
export GRADIO_REQUIRE_AUTH

# Activate conda environment and start in background with nohup
echo "🚀 Starting Gradio UI in background..."
# Use bash to source conda and run python directly for better logging
nohup bash -c "source $(conda info --base)/etc/profile.d/conda.sh && conda activate biomni_e1 && python '${SCRIPT_DIR}/biomni_gradio_demo.py'" > "$LOG_FILE" 2>&1 &
PID=$!

# Save PID
echo "$PID" > "$PID_FILE"

# Wait a moment and check if it started successfully
sleep 3

if ps -p "$PID" > /dev/null 2>&1; then
    echo "✅ Gradio UI started successfully!"
    echo "   PID: $PID"
    echo "   URL: http://localhost:$GRADIO_PORT"
    if [ "$GRADIO_SERVER_NAME" != "127.0.0.1" ]; then
        echo "   External: http://$(hostname -I | awk '{print $1}'):$GRADIO_PORT"
    fi
    echo "   Log: $LOG_FILE"
    echo ""
    echo "📋 Management commands:"
    echo "   View logs: tail -f $LOG_FILE"
    echo "   Stop UI: kill $PID"
    echo "   Or: pkill -f biomni_gradio_demo.py"
else
    echo "❌ Failed to start Gradio UI"
    echo "   Check logs: cat $LOG_FILE"
    rm "$PID_FILE"
    exit 1
fi

echo ""
echo "🎨 Gradio UI is ready!"
echo "   Open http://localhost:$GRADIO_PORT in your browser"
