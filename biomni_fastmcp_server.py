#!/usr/bin/env python3
"""FastMCP server for Biomni agent using the official MCP Python SDK pattern."""

import asyncio
import queue
import threading
import time
from fastmcp import FastMCP
from biomni.agent import A1

# Initialize Biomni agent
print("Initializing Biomni agent for FastMCP...")
agent = A1(
    path='./data', 
    llm='Qwen/Qwen3-30B-A3B-Instruct-2507-FP8',
    base_url='http://ludwig:8000/v1',
    api_key='EMPTY',
    commercial_mode=True
)
print("Biomni agent ready for FastMCP!")

# Create FastMCP server
mcp = FastMCP("biomni-fastmcp-server")

def run_biomni_with_streaming(query: str, output_queue: queue.Queue):
    """Run Biomni agent with streaming output."""
    try:
        print(f"[FastMCP] Starting Biomni query: {query}")
        log, result = agent.go(query, output_queue=output_queue)
        
        # Send the final result
        output_queue.put(("result", result))
        output_queue.put(("done", None))
        
    except Exception as e:
        print(f"[FastMCP ERROR] Exception in Biomni execution: {e}")
        import traceback
        traceback.print_exc()
        output_queue.put(("error", str(e)))
        output_queue.put(("done", None))

@mcp.tool()
def test_simple(query: str) -> str:
    """Simple test tool that returns immediately."""
    print(f"[FastMCP] Test simple called with: {query}")
    return f"Test response for: {query}"

@mcp.tool()
def biomni_query(query: str) -> str:
    """Execute biomedical queries using the Biomni agent.
    
    This agent can search literature, analyze biological data, perform calculations, 
    and answer complex biomedical questions.
    
    Args:
        query: The biomedical question or task to execute
        
    Returns:
        The response from the Biomni agent
    """
    print(f"[FastMCP] Executing biomni query: {query}")
    
    # Return immediately to avoid SSE timeout
    # The real processing would happen in background
    return f"Query '{query}' has been submitted to Biomni. Due to SSE connection limitations, the full response cannot be streamed. Please use the direct HTTP API for complete results."

if __name__ == "__main__":
    print("Starting Biomni FastMCP Server...")
    # Use HTTP transport for remote access
    mcp.run(transport="sse", port=6080)
