#!/usr/bin/env -S conda run -n biomni_e1 python
"""
Gradio UI Demo for Biomni Agent
Launches the interactive web UI on a custom port with sandbox support
"""

import os
import sys
from biomni.agent import A1
from datetime import datetime

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_CONFIG = {
    'path': os.path.join(SCRIPT_DIR, 'data'),  # Use absolute path to avoid sandbox path issues
    'llm': 'Qwen/Qwen3-Next-80B-A3B-Instruct-FP8',
    'base_url': 'https://vllm.paas-jade.astrazeneca.net/v1',
    'api_key': 'natura15tup1d1ty',
    'commercial_mode': True,
    'output_folder': os.path.join(SCRIPT_DIR, 'local_outputs/gradio_demo'),  # Sandbox for file operations
    'use_tool_retriever': False  # Disable tool retrieval to avoid proxy issues in Gradio UI
}

# Gradio-specific settings
GRADIO_PORT = int(os.getenv('GRADIO_PORT', '7860'))  # Default 7860, override with env var
SERVER_NAME = os.getenv('GRADIO_SERVER_NAME', '0.0.0.0')  # Bind to all interfaces
SHARE = os.getenv('GRADIO_SHARE', 'False').lower() == 'true'  # Public link (default: False)
REQUIRE_VERIFICATION = os.getenv('GRADIO_REQUIRE_AUTH', 'False').lower() == 'true'  # Access code (default: False)

def main():
    # Ensure output directory exists
    os.makedirs('./local_outputs/gradio_demo', exist_ok=True)
    
    print("=" * 80)
    print("Biomni Gradio UI Demo")
    print("=" * 80)
    print(f"Configuration:")
    print(f"  - Model: {AGENT_CONFIG['llm']}")
    print(f"  - Base URL: {AGENT_CONFIG['base_url']}")
    print(f"  - Commercial Mode: {AGENT_CONFIG['commercial_mode']}")
    print(f"  - Output Folder: {AGENT_CONFIG['output_folder']}")
    print(f"\nGradio Settings:")
    print(f"  - Port: {GRADIO_PORT}")
    print(f"  - Server: {SERVER_NAME}")
    print(f"  - Share: {SHARE}")
    print(f"  - Require Auth: {REQUIRE_VERIFICATION}")
    print("=" * 80)
    
    # Test data availability
    if os.path.exists('./data/biomni_data/ibd_sim'):
        print("\n✅ IBD simulation data available")
        ibd_dirs = os.listdir('./data/biomni_data/ibd_sim')
        if ibd_dirs:
            print(f"   Datasets: {', '.join(ibd_dirs[:3])}...")
    else:
        print("\n⚠️  IBD data not found")
    
    try:
        print("\n🚀 Initializing Biomni Agent...")
        agent = A1(**AGENT_CONFIG)
        print("✅ Agent initialized successfully!")
        
        print(f"\n🎨 Launching Gradio UI on http://{SERVER_NAME}:{GRADIO_PORT}")
        print("   Press Ctrl+C to stop the server")
        print("=" * 80 + "\n")
        
        # Launch Gradio with custom port
        # Monkey-patch gradio.Blocks.launch to inject custom port
        import gradio as gr
        import types
        
        original_gr_launch = gr.Blocks.launch
        
        def custom_launch(demo_self, *args, **kwargs):
            """Inject custom port if not specified"""
            if 'server_port' not in kwargs and GRADIO_PORT != 7860:
                kwargs['server_port'] = GRADIO_PORT
            return original_gr_launch(demo_self, *args, **kwargs)
        
        # Temporarily replace Gradio's launch method
        gr.Blocks.launch = custom_launch
        
        try:
            # Launch with patched method
            agent.launch_gradio_demo(
                thread_id=42,
                share=SHARE,
                server_name=SERVER_NAME,
                require_verification=REQUIRE_VERIFICATION
            )
        finally:
            # Restore original method (though we won't reach here until server stops)
            gr.Blocks.launch = original_gr_launch
        
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Gradio UI...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error launching Gradio UI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
