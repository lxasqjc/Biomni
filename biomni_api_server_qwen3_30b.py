#!/usr/bin/env python3
"""
FastAPI server for Biomni agent - similar to AGATHA API server
"""
from fastapi import FastAPI, Request
from pydantic import BaseModel
from biomni.agent import A1
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

# Initialize Biomni agent
print("Initializing Biomni agent...")
agent = A1(
    path='./data', 
    llm='Qwen/Qwen3-30B-A3B-Instruct-2507-FP8',
    base_url='http://ludwig:8000/v1',
    api_key='EMPTY',
    commercial_mode=True
)
# agent = A1(
#     path='./data', 
#     llm='Qwen3-Next-80B-A3B-Instruct',
#     base_url='http://alan:8000/v1',
#     api_key='EMPTY',
#     commercial_mode=True
# )
print("Biomni agent ready!")
print("IBD simulation data available at: ./data/biomni_data/ibd_sim")
print("Available IBD data directories:")
if os.path.exists('./data/biomni_data/ibd_sim'):
    ibd_dirs = os.listdir('./data/biomni_data/ibd_sim')
    for dir_name in ibd_dirs:
        print(f"  - {dir_name}")
else:
    print("  - IBD data not found, check symbolic link")

# Ensure local_outputs directory exists
os.makedirs('./local_outputs', exist_ok=True)
print("PDF outputs will be saved to: ./local_outputs/")

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
    pdf_path: Optional[str] = None  # Path to saved PDF file

def run_biomni_sync(query: str):
    """Run Biomni agent synchronously with PDF output"""
    # Generate timestamp for this query
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # millisecond precision
    output_folder = f"./local_outputs/{timestamp}"
    
    try:
        print(f"[Biomni API] Executing query: {query}")
        print(f"[Biomni API] Output folder: {output_folder}")
        
        # Create timestamped output directory
        os.makedirs(output_folder, exist_ok=True)
        
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
        
        # Save conversation history as PDF
        pdf_filename = f"conversation_{timestamp}"
        pdf_path = None
        
        try:
            # Save to the timestamped folder
            full_pdf_path = os.path.join(output_folder, pdf_filename)
            agent.save_conversation_history(full_pdf_path, save_pdf=True)
            pdf_path = f"{full_pdf_path}.pdf"  # The method adds .pdf extension
            print(f"[Biomni API] PDF saved to: {pdf_path}")
        except Exception as pdf_error:
            print(f"[Biomni API] Warning: Failed to save PDF: {pdf_error}")
            # Continue execution even if PDF saving fails
        
        return {
            "response": response,
            "log": log,
            "data": None,  # Can be extended for structured data
            "pdf_path": pdf_path
        }
        
    except Exception as e:
        print(f"[Biomni API ERROR] {e}")
        import traceback
        traceback.print_exc()
        return {
            "response": f"Error: {str(e)}",
            "log": None,
            "data": None,
            "pdf_path": None
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
        data=result["data"],
        pdf_path=result["pdf_path"]
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
    return {"status": "healthy", "agent": "biomni", "model": "Qwen3-30B"}

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
    uvicorn.run(app, host="0.0.0.0", port=8009)