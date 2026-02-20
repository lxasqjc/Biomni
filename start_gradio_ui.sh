#!/bin/bash
cd /data/jinc/git_chen/Biomni

# Configure proxy settings for vLLM backend access
export http_proxy=
export https_proxy="http://emeapzen.astrazeneca.net:9480"
export HTTP_PROXY=
export HTTPS_PROXY="http://emeapzen.astrazeneca.net:9480"
export NO_PROXY="10.0.0.0/8,172.29.0.0/8,astrazeneca.net,*.astrazeneca.net,vllm.paas-jade.astrazeneca.net,localhost,127.0.0.1"
export no_proxy="10.0.0.0/8,172.29.0.0/8,astrazeneca.net,*.astrazeneca.net,vllm.paas-jade.astrazeneca.net,localhost,127.0.0.1"
echo "✅ Configured proxy settings"

# Kill existing server
EXISTING_PID=$(lsof -i :7861 | grep LISTEN | awk '{print $2}' | head -1)
if [ ! -z "$EXISTING_PID" ]; then
    kill $EXISTING_PID 2>/dev/null
    sleep 2
    echo "✅ Killed existing server (PID: $EXISTING_PID)"
fi

# Start server with correct Python
echo "🚀 Starting Gradio UI on port 7861..."
nohup /alan-data/jinc/miniconda3/envs/biomni_e1/bin/python biomni_gradio_demo_with_pdf.py > biomni_gradio_with_pdf.log 2>&1 &
SERVER_PID=$!
echo "✅ Server started with PID: $SERVER_PID"
echo "📋 Log file: biomni_gradio_with_pdf.log"

sleep 8
if lsof -i :7861 > /dev/null 2>&1; then
    echo "✅ Server is listening on port 7861"
    echo "🌐 Access at: http://localhost:7861"
else
    echo "❌ Server failed to start, check logs"
    tail -20 biomni_gradio_with_pdf.log
fi
