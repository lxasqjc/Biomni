#!/usr/bin/env python3
"""
FastAPI server for Biomni agent — Qwen3.5-25B (UD_Q6_K_XL.gguf) on ludwig drylab.
Model/endpoint can be configured via environment variables:
  BIOMNI_MODEL       - model name (default: qwen3_5)
  BIOMNI_BASE_URL    - base URL (default: http://ludwig:1234/v1)
  BIOMNI_API_KEY     - API key (default: not-needed)
  BIOMNI_COMMERCIAL_MODE - "true"/"false"
"""
from fastapi import FastAPI, Request
from pydantic import BaseModel
from biomni.agent import A1
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import asyncio
import gc
import threading
import time
import requests as _requests

# ---------------------------------------------------------------------------
# Startup configuration: env vars > defaults
# ---------------------------------------------------------------------------
_DEFAULT_MODEL    = "qwen3_5"
_DEFAULT_BASE_URL = "http://ludwig:1234/v1"
_DEFAULT_API_KEY  = "not-needed"

AGENT_CONFIG = {
    'path': './data',
    'llm': os.environ.get("BIOMNI_MODEL", _DEFAULT_MODEL),
    'base_url': os.environ.get("BIOMNI_BASE_URL", _DEFAULT_BASE_URL),
    'api_key': os.environ.get("BIOMNI_API_KEY", _DEFAULT_API_KEY),
    'commercial_mode': os.environ.get("BIOMNI_COMMERCIAL_MODE", "true").lower() != "false",
    # Tool retriever: pre-filters tools per query to prevent search loops.
    # Default False to preserve existing behaviour. Set env BIOMNI_USE_TOOL_RETRIEVER=true to enable.
    'use_tool_retriever': os.environ.get("BIOMNI_USE_TOOL_RETRIEVER", "false").lower() == "true",
}

# Optional global chat_template_kwargs applied to every request (e.g. enable_thinking).
# Per-request values (from ChatRequest) take precedence.
_GLOBAL_CHAT_TEMPLATE_KWARGS: Optional[Dict[str, Any]] = (
    {"enable_thinking": os.environ.get("BIOMNI_ENABLE_THINKING", "").lower() == "true"}
    if os.environ.get("BIOMNI_ENABLE_THINKING", "") != ""
    else None
)

# Optional global reasoning_effort: "low", "medium", "high" — passed via extra_body to vLLM (≥0.8.x).
_GLOBAL_REASONING_EFFORT: Optional[str] = os.environ.get("BIOMNI_REASONING_EFFORT") or None

print("Biomni API server configured for per-request agent instances...")

# Test agent initialization at startup (optional verification)
try:
    test_agent = A1(**AGENT_CONFIG)
    print("✅ Agent initialization test successful!")
    del test_agent
    gc.collect()
except Exception as e:
    print(f"❌ Agent initialization test failed: {e}")
    print("Server will still start, but requests may fail...")

print("🚀 Biomni API server ready for concurrent requests!")
print("IBD simulation data available at: ./data/biomni_data/ibd_sim")
print("Available IBD data directories:")
if os.path.exists('./data/biomni_data/ibd_sim'):
    ibd_dirs = os.listdir('./data/biomni_data/ibd_sim')
    for dir_name in ibd_dirs:
        print(f"  - {dir_name}")
else:
    print("  - IBD data not found, check symbolic link")

# Local output folders are disabled by default (set BIOMNI_LOCAL_OUTPUTS=1 to enable)
ENABLE_LOCAL_OUTPUTS = os.getenv("BIOMNI_LOCAL_OUTPUTS", "0").lower() in ("1", "true", "yes")
if ENABLE_LOCAL_OUTPUTS:
    os.makedirs('./local_outputs', exist_ok=True)
    print("PDF outputs will be saved to: ./local_outputs/")
else:
    print("Local outputs disabled (set BIOMNI_LOCAL_OUTPUTS=1 to enable)")

app = FastAPI(title="Biomni API", description="FastAPI server for Biomni biomedical agent")

def _start_vllm_keepalive(base_url: str, interval_seconds: int = 300):
    """Background thread that pings vLLM /models every interval_seconds to prevent engine sleep."""
    def _ping():
        while True:
            try:
                # Use a short-lived Session with Connection:close to avoid CLOSE-WAIT socket leak
                with _requests.Session() as s:
                    s.headers.update({"Connection": "close"})
                    resp = s.get(f"{base_url}/models", timeout=10)
                print(f"[Keepalive] vLLM ping -> HTTP {resp.status_code}")
            except Exception as e:
                print(f"[Keepalive] vLLM ping failed: {e}")
            time.sleep(interval_seconds)
    t = threading.Thread(target=_ping, daemon=True, name="vllm-keepalive")
    t.start()
    print(f"[Keepalive] Started vLLM keepalive thread (interval={interval_seconds}s) -> {base_url}")


_start_vllm_keepalive(AGENT_CONFIG["base_url"])

# Pydantic models for API
class Message(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    messages: Optional[List[Message]] = None  # Full chat history, optional for single-turn
    prompt: Optional[str] = None  # For backward compatibility
    stream: Optional[bool] = False  # For future streaming support
    save_pdf: Optional[bool] = True  # Whether to save conversation as PDF
    logprobs: Optional[bool] = None  # Request logprobs from underlying vLLM
    top_logprobs: Optional[int] = None  # Number of top logprobs to return (e.g., 20)
    # Model override: use a different model for this request (overrides BIOMNI_MODEL env var)
    model: Optional[str] = None
    # vLLM chat_template_kwargs, e.g. {"enable_thinking": true} for Qwen3.5 thinking mode
    chat_template_kwargs: Optional[Dict[str, Any]] = None
    # reasoning_effort: "low", "medium", "high" — passed via extra_body to vLLM (≥0.8.x)
    reasoning_effort: Optional[str] = None
    # Tool retriever: pre-filters tools per query. Overrides server-level BIOMNI_USE_TOOL_RETRIEVER.
    use_tool_retriever: Optional[bool] = None

class ChatResponse(BaseModel):
    response: str
    log: Optional[str] = None  # Biomni execution log
    data: Optional[Any] = None  # For structured output
    pdf_path: Optional[str] = None  # Path to saved PDF file
    logprobs: Optional[Any] = None  # Logprobs from vLLM (list of per-step logprobs)

async def run_biomni_sync(
    query: str,
    save_pdf: bool = True,
    logprobs: bool = None,
    top_logprobs: int = None,
    chat_template_kwargs: Optional[Dict[str, Any]] = None,
    model: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    use_tool_retriever: Optional[bool] = None,
):
    """Run Biomni agent asynchronously with fresh instance per request"""
    # Generate timestamp for this query
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # millisecond precision
    output_folder = f"./local_outputs/{timestamp}" if ENABLE_LOCAL_OUTPUTS else None
    
    try:
        print(f"[Biomni API] Executing query: {query}")
        if output_folder:
            print(f"[Biomni API] Output folder: {output_folder}")
        
        # CREATE FRESH AGENT INSTANCE PER REQUEST (fixes memory + concurrency)
        print(f"[Biomni API] Creating fresh agent instance...")
        agent_kwargs = dict(**AGENT_CONFIG, output_folder=output_folder)
        # Per-request model override
        if model:
            agent_kwargs['llm'] = model
        # Per-request tool retriever override
        if use_tool_retriever is not None:
            agent_kwargs['use_tool_retriever'] = use_tool_retriever
        if logprobs:
            agent_kwargs['logprobs'] = logprobs
            agent_kwargs['top_logprobs'] = top_logprobs if top_logprobs else 20
        # Merge global and per-request chat_template_kwargs; per-request takes precedence
        effective_ctk = dict(_GLOBAL_CHAT_TEMPLATE_KWARGS or {})
        if chat_template_kwargs:
            effective_ctk.update(chat_template_kwargs)
        # Resolve reasoning_effort: per-request > global env var
        effective_re = reasoning_effort or _GLOBAL_REASONING_EFFORT
        # Build extra_body for vLLM extensions
        extra_body: Dict[str, Any] = {}
        if effective_ctk:
            extra_body["chat_template_kwargs"] = effective_ctk
        if effective_re:
            extra_body["reasoning_effort"] = effective_re
        if extra_body:
            # Must be nested under extra_body so the OpenAI client passes it as a raw
            # request body field (vLLM extension) rather than a create() kwarg.
            agent_kwargs['model_kwargs'] = {"extra_body": extra_body}
            print(f"[Biomni API] extra_body: {extra_body}")
        agent = A1(**agent_kwargs)
        
        # Run the agent - simplified call without output_queue
        result = agent.go(query)
        
        # Handle different return types
        logprobs_data = None
        if isinstance(result, tuple) and len(result) == 3:
            log, response, logprobs_data = result
        elif isinstance(result, tuple) and len(result) == 2:
            log, response = result
        elif isinstance(result, str):
            log = None
            response = result
        else:
            log = str(result)
            response = str(result)
        
        # Convert log to string if it's a list
        if isinstance(log, list):
            log = "\n".join(str(item) for item in log)
        elif log is not None:
            log = str(log)
            
        # Ensure response is a string
        if not isinstance(response, str):
            response = str(response)
        
        # Save conversation history as PDF (if requested)
        pdf_filename = f"conversation_{timestamp}"
        pdf_path = None
        
        if save_pdf:
            try:
                # Create output dir on demand (even if local_outputs disabled, PDF needs a folder)
                pdf_dir = output_folder or f"./local_outputs/{timestamp}"
                os.makedirs(pdf_dir, exist_ok=True)
                
                # Save to the timestamped folder
                full_pdf_path = os.path.join(pdf_dir, pdf_filename)
                agent.save_conversation_history(full_pdf_path, save_pdf=True)
                pdf_path = f"{full_pdf_path}.pdf"  # The method adds .pdf extension
                print(f"[Biomni API] PDF saved to: {pdf_path}")
            except Exception as pdf_error:
                print(f"[Biomni API] Warning: Failed to save PDF: {pdf_error}")
                # Continue execution even if PDF saving fails
        else:
            print(f"[Biomni API] PDF saving skipped (save_pdf=False)")
        
        return {
            "response": response,
            "log": log,
            "data": None,  # Can be extended for structured data
            "pdf_path": pdf_path,
            "logprobs": logprobs_data
        }
        
    except Exception as e:
        print(f"[Biomni API ERROR] {e}")
        import traceback
        traceback.print_exc()
        return {
            "response": f"Error: {str(e)}",
            "log": None,
            "data": None,
            "pdf_path": None,
            "logprobs": None
        }
    finally:
        # EXPLICIT CLEANUP: Clear agent reference for garbage collection
        try:
            if 'agent' in locals():
                del agent
                # Force garbage collection to free memory immediately
                gc.collect()
                print(f"[Biomni API] Agent instance cleaned up for {timestamp}")
        except:
            pass

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint for Biomni agent"""
    
    # Extract the user query
    query = None
    if request.messages:
        # Get the last user message
        for msg in reversed(request.messages):
            if msg.role == 'user':
                query = msg.content
                break
    elif request.prompt:
        query = request.prompt
    
    if not query:
        return ChatResponse(response="No query provided.")
    
    # Run Biomni agent (now async)
    result = await run_biomni_sync(
        query,
        save_pdf=request.save_pdf if request.save_pdf is not None else True,
        logprobs=request.logprobs,
        top_logprobs=request.top_logprobs,
        chat_template_kwargs=request.chat_template_kwargs,
        model=request.model,
        reasoning_effort=request.reasoning_effort,
        use_tool_retriever=request.use_tool_retriever,
    )
    
    return ChatResponse(
        response=result["response"],
        log=result["log"],
        data=result["data"],
        pdf_path=result["pdf_path"],
        logprobs=result.get("logprobs")
    )

@app.post("/v1/chat/completions")
async def openai_chat_completions(request: dict):
    """OpenAI-compatible endpoint"""
    messages = request.get("messages", [])
    save_pdf = request.get("save_pdf", True)  # Default to True for backward compatibility
    req_logprobs = request.get("logprobs", None)
    req_top_logprobs = request.get("top_logprobs", None)
    our_request = ChatRequest(
        messages=[Message(role=m["role"], content=m["content"]) for m in messages],
        save_pdf=save_pdf,
        logprobs=req_logprobs if isinstance(req_logprobs, bool) else (True if req_logprobs else None),
        top_logprobs=req_top_logprobs,
        model=request.get("model") if request.get("model") != "biomni" else None,
        chat_template_kwargs=request.get("chat_template_kwargs"),
        reasoning_effort=request.get("reasoning_effort"),
        use_tool_retriever=request.get("use_tool_retriever"),
    )
    response = await chat_endpoint(our_request)
    
    # Build vLLM-compatible response
    choice = {"message": {"role": "assistant", "content": response.response}}
    if response.logprobs:
        # Return logprobs in vLLM/OpenAI format under choice.logprobs.content
        # Flatten all steps' logprobs into a single list
        all_content = []
        for step_lp in response.logprobs:
            content_tokens = step_lp.get('content', []) if isinstance(step_lp, dict) else []
            all_content.extend(content_tokens)
        choice["logprobs"] = {"content": all_content}
    
    return {
        "choices": [choice],
        "model": "biomni",
        "usage": {"total_tokens": len(choice.get('logprobs', {}).get('content', [])) if choice.get('logprobs') else 0}
    }

@app.get("/ibd-data-info")
async def get_ibd_data_info():
    """Get information about available IBD simulation data"""
    import os
    ibd_path = "./data/biomni_data/ibd_sim"
    
    if not os.path.exists(ibd_path):
        return {"error": "IBD simulation data not found", "path": ibd_path}
    
    data_info = {}
    for subdir in os.listdir(ibd_path):
        subdir_path = os.path.join(ibd_path, subdir)
        if os.path.isdir(subdir_path):
            files = os.listdir(subdir_path)[:10]  # Limit to first 10 files
            data_info[subdir] = {
                "file_count": len(os.listdir(subdir_path)),
                "sample_files": files
            }
    
    return {
        "available_data": data_info,
        "data_path": ibd_path,
        "usage_tip": "You can now reference IBD data in your queries like: 'Analyze the transcriptomics data in ibd_sim/transcriptomics_data/'"
    }

@app.get("/examples")
async def get_examples():
    """Get example prompts for Biomni"""
    return {
        "examples": [
            "What are the latest treatments for diabetes?",
            "Analyze the mechanism of action of aspirin",
            "Find literature about CRISPR gene editing in cancer therapy",
            "Calculate the IC50 for this compound data: [provide your data]",
            "What are the side effects of metformin?",
            "Search for biomarkers of Alzheimer's disease",
            "Analyze the IBD transcriptomics data in ibd_sim/transcriptomics_data/",
            "Compare proteomics profiles between IBD patients and controls using ibd_sim data",
            "Identify biomarkers from the IBD simulation dataset"
        ],
        "title": "# 🧬 Biomni Agent",
        "description": "Biomedical research and analysis assistant with IBD simulation data access",
        "data_access_date": "Updated: September 2025"
    }

@app.get("/outputs")
async def list_outputs():
    """List all saved conversation outputs"""
    import glob
    
    output_dirs = []
    if os.path.exists('./local_outputs'):
        for folder in sorted(os.listdir('./local_outputs'), reverse=True):
            folder_path = os.path.join('./local_outputs', folder)
            if os.path.isdir(folder_path):
                # Find PDF files in this folder
                pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
                output_dirs.append({
                    "timestamp": folder,
                    "folder_path": folder_path,
                    "pdf_files": [os.path.basename(f) for f in pdf_files],
                    "file_count": len(pdf_files)
                })
    
    return {
        "total_conversations": len(output_dirs),
        "conversations": output_dirs[:20],  # Show last 20
        "note": "PDF files are automatically generated for each query"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "biomni",
        "model": AGENT_CONFIG["llm"],
        "base_url": AGENT_CONFIG["base_url"],
        "chat_template_kwargs": _GLOBAL_CHAT_TEMPLATE_KWARGS,
        "use_tool_retriever": AGENT_CONFIG.get("use_tool_retriever", False),
    }

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "Biomni FastAPI Server with PDF Output",
        "endpoints": {
            "chat": "/chat",
            "openai_compatible": "/v1/chat/completions", 
            "examples": "/examples",
            "ibd_data_info": "/ibd-data-info",
            "outputs": "/outputs",
            "health": "/health",
            "docs": "/docs"
        },
        "features": [
            "Automatic PDF generation for each conversation",
            "Timestamped output folders in ./local_outputs/",
            "IBD simulation data integration",
            "OpenAI-compatible API"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    # CONCURRENCY OPTIMIZATIONS
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8011,
        workers=1,  # Single worker but with async handling
        loop="asyncio",  # Use asyncio for better concurrency
        access_log=False,  # Reduce I/O overhead
        reload=False  # Disable auto-reload for production
    )