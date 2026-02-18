#!/usr/bin/env -S conda run -n biomni_e1 python
"""
Gradio UI Demo for Biomni Agent with PDF Report Support
Launches the interactive web UI on a custom port with sandbox support
Features:
- Real-time conversation with Biomni agent
- Automatic PDF report generation after each query
- Downloadable PDF reports with full conversation history
"""

import os
import sys
import gradio as gr
from biomni.agent import A1
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage
import re
from time import time

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_OUTPUTS_DIR = os.path.join(SCRIPT_DIR, 'local_outputs')

AGENT_CONFIG = {
    'path': os.path.join(SCRIPT_DIR, 'data'),
    'llm': 'Qwen/Qwen3-Next-80B-A3B-Instruct-FP8',
    'base_url': 'https://vllm.paas-jade.astrazeneca.net/v1',
    'api_key': 'natura15tup1d1ty',
    'commercial_mode': True,
    'output_folder': None,  # Will be set dynamically per session
    'use_tool_retriever': False
}

# PDF report settings
ENABLE_PDF_REPORTS = True
HTTP_SERVER_BASE_URL = "http://alan.astrazeneca.net:8100"  # HTTP server serving local_outputs/

# Gradio-specific settings
GRADIO_PORT = int(os.getenv('GRADIO_PORT', '7861'))
SERVER_NAME = os.getenv('GRADIO_SERVER_NAME', '0.0.0.0')
SHARE = os.getenv('GRADIO_SHARE', 'False').lower() == 'true'
REQUIRE_VERIFICATION = os.getenv('GRADIO_REQUIRE_AUTH', 'False').lower() == 'true'

def main():
    # Ensure output directories exist
    os.makedirs(LOCAL_OUTPUTS_DIR, exist_ok=True)
    
    print("=" * 80)
    print("Biomni Gradio UI Demo with PDF Reports")
    print("=" * 80)
    print(f"Configuration:")
    print(f"  - Model: {AGENT_CONFIG['llm']}")
    print(f"  - Output Directory: {LOCAL_OUTPUTS_DIR}")
    print(f"  - PDF Reports: {'Enabled' if ENABLE_PDF_REPORTS else 'Disabled'}")
    if ENABLE_PDF_REPORTS:
        print(f"  - HTTP Server: {HTTP_SERVER_BASE_URL}")
    print(f"\nGradio Settings:")
    print(f"  - Port: {GRADIO_PORT}")
    print(f"  - Server: {SERVER_NAME}")
    print("=" * 80)
    
    try:
        print("\n🚀 Initializing Biomni Agent (output_folder will be set per session)...")
        # Create session-specific output folder
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        session_folder = os.path.join(LOCAL_OUTPUTS_DIR, session_id)
        os.makedirs(session_folder, exist_ok=True)
        AGENT_CONFIG['output_folder'] = session_folder
        
        agent = A1(**AGENT_CONFIG)
        print(f"✅ Agent initialized successfully!")
        print(f"📁 Session folder: {session_folder}")
        
        # Conversation tracking
        main_history_copy = []
        
        SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".pdf")
        
        def generate_pdf_report():
            """Generate PDF report and return HTTP link"""
            # Debug: write to file to track if function is called
            debug_file = os.path.join(SCRIPT_DIR, 'pdf_debug.log')
            with open(debug_file, 'a') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"generate_pdf_report called at {datetime.now()}\n")
                f.write(f"ENABLE_PDF_REPORTS: {ENABLE_PDF_REPORTS}\n")
                f.write(f"main_history_copy length: {len(main_history_copy)}\n")
            
            if not ENABLE_PDF_REPORTS:
                return None
            
            try:
                # Get session folder name from agent's output_folder
                session_folder_name = os.path.basename(agent.output_folder)
                
                # PDF filename matches the session pattern
                pdf_filename = f"conversation_{session_folder_name}.pdf"
                pdf_path = os.path.join(agent.output_folder, pdf_filename)
                
                with open(debug_file, 'a') as f:
                    f.write(f"Session folder: {session_folder_name}\n")
                    f.write(f"PDF path: {pdf_path}\n")
                
                # Populate agent.log from main_history_copy for PDF generation
                agent.log = []
                for msg in main_history_copy:
                    agent.log.append({
                        'role': msg['role'],
                        'content': msg['content'],
                        'type': 'message'
                    })
                
                with open(debug_file, 'a') as f:
                    f.write(f"Populated agent.log with {len(agent.log)} messages\n")
                    # Log first few messages for debugging
                    for i, msg in enumerate(agent.log[:3]):
                        f.write(f"  Message {i}: role={msg['role']}, content_len={len(msg['content'])}\n")
                
                # Redirect stdout/stderr to capture any errors
                import sys
                import io
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = captured_output = io.StringIO()
                sys.stderr = captured_error = io.StringIO()
                
                try:
                    # Save the conversation with the populated log
                    agent.save_conversation_history(pdf_path, save_pdf=True)
                finally:
                    # Restore stdout/stderr
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                    
                    # Log captured output
                    stdout_content = captured_output.getvalue()
                    stderr_content = captured_error.getvalue()
                    
                    with open(debug_file, 'a') as f:
                        if stdout_content:
                            f.write(f"Captured stdout:\n{stdout_content}\n")
                        if stderr_content:
                            f.write(f"Captured stderr:\n{stderr_content}\n")
                
                # Verify PDF was created
                if os.path.exists(pdf_path):
                    http_url = f"{HTTP_SERVER_BASE_URL}/{session_folder_name}/{pdf_filename}"
                    
                    with open(debug_file, 'a') as f:
                        f.write(f"✅ PDF created successfully\n")
                        f.write(f"   File size: {os.path.getsize(pdf_path)} bytes\n")
                        f.write(f"HTTP URL: {http_url}\n")
                    
                    return http_url
                else:
                    with open(debug_file, 'a') as f:
                        f.write(f"⚠️ PDF file not found after generation\n")
                        # Check if any files were created in the folder
                        folder_contents = os.listdir(agent.output_folder)
                        f.write(f"Folder contents: {folder_contents}\n")
                    return None
                    
            except Exception as e:
                with open(debug_file, 'a') as f:
                    f.write(f"❌ Error: {e}\n")
                    import traceback
                    f.write(traceback.format_exc())
                return None
        
        def generate_response(prompt_input, inner_history=None, main_history=None):
            """Generate response and create PDF report"""
            if main_history is None:
                main_history = []
            if inner_history is None:
                inner_history = []
            
            text_input = prompt_input.get("text", "")
            files = prompt_input.get("files", [])
            
            main_history_copy.append({"role": "user", "content": text_input})
            main_history.append(gr.ChatMessage(role="user", content=text_input if text_input else "[Uploaded file]"))
            
            # Add "Executor is working on it" message
            main_history.append(gr.ChatMessage(role="assistant", content="Executor is working on it 👉"))
            yield inner_history, main_history
            
            # Process uploaded files
            for file_info in files:
                text_input += f"\n\n User uploaded this file: {file_info}\n Please use it if needed."
            
            # Prepare agent messages
            agent_messages = []
            for msg in main_history_copy:
                if msg["role"] == "user":
                    agent_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    if msg["content"] not in ["Executor is working on it 👉"]:
                        agent_messages.append(AIMessage(content=msg["content"]))
            
            agent_messages.append(HumanMessage(content=text_input))
            
            # Prepare inputs
            inputs = {"messages": agent_messages, "next_step": None}
            config = {"recursion_limit": 500, "configurable": {"thread_id": 42}}
            
            t = time()
            solution_found = False
            code_execution_messages = []
            
            # Stream agent responses
            for s in agent.app.stream(inputs, stream_mode="values", config=config):
                t_step = time() - t
                message = s["messages"][-1]
                
                if message.content == text_input:
                    t = time()
                    continue
                
                if isinstance(message.content, str):
                    # Extract thinking
                    tag_positions = []
                    for tag in ["<execute>", "<solution>", "<observation>"]:
                        pos = message.content.find(tag)
                        if pos != -1:
                            tag_positions.append(pos)
                    
                    if tag_positions:
                        first_tag_pos = min(tag_positions)
                        thinking = message.content[:first_tag_pos].strip()
                        if thinking:
                            inner_history.append(
                                gr.ChatMessage(
                                    role="assistant",
                                    content=f"{thinking}",
                                    metadata={"title": "🤔 Reasoning"}
                                )
                            )
                            yield inner_history, main_history
                    
                    # Check for solution
                    solution_match = re.search(r"<solution>(.*?)</solution>", message.content, re.DOTALL)
                    if solution_match and not solution_found:
                        solution = solution_match.group(1).strip()
                        main_history.append(
                            gr.ChatMessage(
                                role="assistant",
                                content=solution,
                                metadata={"title": "✅ Answer"}
                            )
                        )
                        main_history_copy.append({"role": "assistant", "content": solution})
                        solution_found = True
                        yield inner_history, main_history
                    
                    # Check for execute tag
                    execute_match = re.search(r"<execute>(.*?)</execute>", message.content, re.DOTALL)
                    if execute_match:
                        code = execute_match.group(1).strip()
                        language = "python"
                        if code.strip().startswith("#!R"):
                            language = "r"
                            code = re.sub(r"^#!R", "", code, count=1).strip()
                        elif code.strip().startswith("#!BASH") or code.strip().startswith("#!CLI"):
                            language = "bash"
                            code = re.sub(r"^#!BASH|^#!CLI", "", code, count=1).strip()
                        
                        code_msg = gr.ChatMessage(
                            role="assistant",
                            content=f"##### Code: \n```{language}\n{code}\n```",
                            metadata={"title": "🛠️ Executing code..."}
                        )
                        inner_history.append(code_msg)
                        code_execution_messages.append(code_msg)
                        yield inner_history, main_history
                    
                    # Check for observation
                    observation_match = re.search(r"<observation>(.*?)</observation>", message.content, re.DOTALL)
                    if observation_match:
                        observation = observation_match.group(1).strip()
                        
                        inner_history.append(
                            gr.ChatMessage(
                                role="assistant",
                                content=f"##### Observation: \n```\n{observation}\n```",
                                metadata={"status": "done", "log": "Observation from code execution", "collapsed": True}
                            )
                        )
                        yield inner_history, main_history
                        
                        # Check for generated files
                        if isinstance(observation, str) and any(ext in observation for ext in SUPPORTED_EXTENSIONS):
                            matches = re.findall(r"(\S+?(?:\.png|\.jpg|\.jpeg|\.gif|\.bmp|\.webp|\.pdf))", observation)
                            
                            valid_matches = []
                            for match in matches:
                                if not (match.startswith("Warning:") or match.startswith("Error:") or match.startswith("'")):
                                    if not match.startswith("."):
                                        valid_matches.append(match)
                            
                            if valid_matches:
                                for file_path in valid_matches:
                                    file_path = file_path.strip("\"'").strip()
                                    abs_path = None
                                    
                                    if os.path.isabs(file_path) and os.path.exists(file_path):
                                        abs_path = file_path
                                    elif os.path.exists(os.path.join(os.getcwd(), file_path)):
                                        abs_path = os.path.join(os.getcwd(), file_path)
                                    elif hasattr(agent, "output_folder") and agent.output_folder and os.path.exists(os.path.join(agent.output_folder, file_path)):
                                        abs_path = os.path.join(agent.output_folder, file_path)
                                    
                                    if abs_path:
                                        if file_path.lower().endswith(".pdf"):
                                            inner_history.append(
                                                gr.ChatMessage(
                                                    role="assistant",
                                                    content=f"Found PDF at: {abs_path}",
                                                    metadata={"title": "📄 PDF File"}
                                                )
                                            )
                                        else:
                                            inner_history.append(
                                                gr.ChatMessage(
                                                    role="assistant",
                                                    content=gr.Image(abs_path),
                                                    metadata={"title": "🖼️ Image Preview"}
                                                )
                                            )
                                
                                yield inner_history, main_history
                
                t = time()
            
            # If no solution found, add final message
            if not solution_found:
                final_message = s["messages"][-1].content if s["messages"] else ""
                solution_match = re.search(r"<solution>(.*?)</solution>", final_message, re.DOTALL)
                if solution_match:
                    solution = solution_match.group(1).strip()
                    main_history.append(gr.ChatMessage(role="assistant", content=solution, metadata={"title": "✅ Solution"}))
                    main_history_copy.append({"role": "assistant", "content": solution})
                else:
                    cleaned_content = re.sub(r"<execute>.*?</execute>", "", final_message, flags=re.DOTALL)
                    cleaned_content = re.sub(r"<observation>.*?</observation>", "", cleaned_content, flags=re.DOTALL)
                    cleaned_content = re.sub(r"\n\s*\n", "\n\n", cleaned_content)
                    
                    if cleaned_content.strip():
                        main_history.append(gr.ChatMessage(role="assistant", content=cleaned_content.strip(), metadata={"title": "📝 Summary"}))
                        main_history_copy.append({"role": "assistant", "content": cleaned_content.strip()})
            
            # Add completion message
            inner_history.append(
                gr.ChatMessage(
                    role="assistant",
                    content="👈 Returning the result to the main interface...",
                    metadata={"title": "🔄 Complete"}
                )
            )
            
            # Generate PDF report
            pdf_url = generate_pdf_report()
            
            if pdf_url:
                # Add PDF link notification to chat
                main_history.append(
                    gr.ChatMessage(
                        role="assistant",
                        content=f"📄 **Conversation Report Available**\n\n[Click here to download PDF]({pdf_url})",
                        metadata={"title": "📥 PDF Report"}
                    )
                )
            
            yield inner_history, main_history
        
        # Create Gradio interface
        with gr.Blocks(title="Biomni A1 Agent") as demo:
            gr.Markdown("# Biomni A1 Agent - Interactive Biomedical Research Assistant")
            gr.Markdown("Ask questions, analyze data, and get PDF reports of your conversation.")
            
            with gr.Row():
                with gr.Column(scale=1):
                    main_chatbot = gr.Chatbot(
                        label="Biomni A1 Agent",
                        type="messages",
                        height=700,
                        show_copy_button=True,
                        show_share_button=True
                    )
                with gr.Column(scale=1):
                    innerloop_chatbot = gr.Chatbot(
                        label="Biomni Executor",
                        type="messages",
                        height=700,
                        show_copy_button=True,
                        show_share_button=True
                    )
            
            with gr.Row():
                prompt_input = gr.MultimodalTextbox(
                    interactive=True,
                    file_count="multiple",
                    placeholder="Ask something or upload a file...",
                    show_label=False,
                    scale=4
                )
            
            # Bind submission
            prompt_input.submit(
                generate_response,
                [prompt_input, innerloop_chatbot, main_chatbot],
                [innerloop_chatbot, main_chatbot]
            ).then(lambda: gr.MultimodalTextbox(value=None), None, [prompt_input])
        
        # Launch
        print(f"\n🎨 Launching Gradio UI on http://{SERVER_NAME}:{GRADIO_PORT}")
        print("   Press Ctrl+C to stop the server\n")
        demo.launch(share=SHARE, server_name=SERVER_NAME, server_port=GRADIO_PORT)
        
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
