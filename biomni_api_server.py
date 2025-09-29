#!/usr/bin/env python3
"""
FastAPI server for Biomni agent - similar to AGATHA API server
"""
from fastapi import FastAPI, Request
from pydantic import BaseModel
from biomni.agent import A1
from typing import List, Optional, Dict, Any

# Initialize Biomni agent
print("Initializing Biomni agent...")
agent = A1(
    path='./data', 
    llm='Qwen/Qwen3-30B-A3B-Instruct-2507-FP8',
    base_url='http://ludwig:8000/v1',
    api_key='EMPTY',
    commercial_mode=True
)
print("Biomni agent ready!")
print("IBD simulation data available at: ./data/biomni_data/ibd_sim")
print("Available IBD data directories:")
import os
if os.path.exists('./data/biomni_data/ibd_sim'):
    ibd_dirs = os.listdir('./data/biomni_data/ibd_sim')
    for dir_name in ibd_dirs:
        print(f"  - {dir_name}")
else:
    print("  - IBD data not found, check symbolic link")

app = FastAPI(title="Biomni API", description="FastAPI server for Biomni biomedical agent")

# Pydantic models for API
class Message(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    messages: Optional[List[Message]] = None  # Full chat history, optional for single-turn
    prompt: Optional[str] = None  # For backward compatibility
    stream: Optional[bool] = False  # For future streaming support

class ChatResponse(BaseModel):
    response: str
    log: Optional[str] = None  # Biomni execution log
    data: Optional[Any] = None  # For structured output

def run_biomni_sync(query: str):
    """Run Biomni agent synchronously"""
    try:
        print(f"[Biomni API] Executing query: {query}")
        
        # Run the agent - simplified call without output_queue
        result = agent.go(query)
        
        # Handle different return types
        if isinstance(result, tuple) and len(result) == 2:
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
        
        return {
            "response": response,
            "log": log,
            "data": None  # Can be extended for structured data
        }
        
    except Exception as e:
        print(f"[Biomni API ERROR] {e}")
        import traceback
        traceback.print_exc()
        return {
            "response": f"Error: {str(e)}",
            "log": None,
            "data": None
        }

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
    
    # Run Biomni agent
    result = run_biomni_sync(query)
    
    return ChatResponse(
        response=result["response"],
        log=result["log"],
        data=result["data"]
    )

@app.post("/v1/chat/completions")
async def openai_chat_completions(request: dict):
    """OpenAI-compatible endpoint"""
    messages = request.get("messages", [])
    our_request = ChatRequest(messages=[
        Message(role=m["role"], content=m["content"]) 
        for m in messages
    ])
    response = await chat_endpoint(our_request)
    
    # Return in OpenAI format
    return {
        "choices": [{"message": {"role": "assistant", "content": response.response}}],
        "model": "biomni",
        "usage": {"total_tokens": 0}
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "biomni", "model": "Qwen3-30B"}

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "Biomni FastAPI Server",
        "endpoints": {
            "chat": "/chat",
            "openai_compatible": "/v1/chat/completions", 
            "examples": "/examples",
            "health": "/health",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)