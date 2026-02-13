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
AGENT_CONFIG = {
    'path': os.path.join(SCRIPT_DIR, 'data'),
    'llm': 'Qwen/Qwen3-Next-80B-A3B-Instruct-FP8',
    'base_url': 'https://vllm.paas-jade.astrazeneca.net/v1',
    'api_key': 'natura15tup1d1ty',
    'commercial_mode': True,
    'output_folder': os.path.join(SCRIPT_DIR, 'local_outputs/gradio_demo'),
    'use_tool_retriever': False
}

# PDF report settings
PDF_OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'local_outputs/gradio_demo/reports')
ENABLE_PDF_REPORTS = True

# Gradio-specific settings
GRADIO_PORT = int(os.getenv('GRADIO_PORT', '7861'))
SERVER_NAME = os.getenv('GRADIO_SERVER_NAME', '0.0.0.0')
SHARE = os.getenv('GRADIO_SHARE', 'False').lower() == 'true'
REQUIRE_VERIFICATION = os.getenv('GRADIO_REQUIRE_AUTH', 'False').lower() == 'true'

def main():
    # Ensure output directories exist
    os.makedirs(AGENT_CONFIG['output_folder'], exist_ok=True)
    if ENABLE_PDF_REPORTS:
        os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
    
    print("=" * 80)
    print("Biomni Gradio UI Demo with PDF Reports")
    print("=" * 80)
    print(f"Configuration:")
    print(f"  - Model: {AGENT_CONFIG['llm']}")
    print(f"  - Output Folder: {AGENT_CONFIG['output_folder']}")
    print(f"  - PDF Reports: {'Enabled' if ENABLE_PDF_REPORTS else 'Disabled'}")
    if ENABLE_PDF_REPORTS:
        print(f"  - PDF Directory: {PDF_OUTPUT_DIR}")
    print(f"\nGradio Settings:")
    print(f"  - Port: {GRADIO_PORT}")
    print(f"  - Server: {SERVER_NAME}")
    print("=" * 80)
    
    try:
        print("\n🚀 Initializing Biomni Agent...")
        agent = A1(**AGENT_CONFIG)
        print("✅ Agent initialized successfully!")
        
        # Conversation tracking
        main_history_copy = []
        conversation_counter = [0]  # Use list to make it mutable in nested functions
        latest_pdf_path = [None]
        
        SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".pdf")
        
        def generate_pdf_report():
            """Generate PDF report for current conversation"""
            if not ENABLE_PDF_REPORTS:
                return None
            
            try:
                conversation_counter[0] += 1
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_filename = f"biomni_report_{timestamp}_{conversation_counter[0]:03d}.pdf"
                pdf_path = os.path.join(PDF_OUTPUT_DIR, pdf_filename)
                
                print(f"\n📄 Generating PDF report: {pdf_filename}")
                agent.save_conversation_history(pdf_path, save_pdf=True)
                latest_pdf_path[0] = pdf_path
                
                return pdf_path
            except Exception as e:
                print(f"❌ Error generating PDF: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        def generate_response(prompt_input, inner_history=None, main_history=None, pdf_file=None):
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
            yield inner_history, main_history, None
            
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
                            yield inner_history, main_history, None
                    
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
                        yield inner_history, main_history, None
                    
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
                        yield inner_history, main_history, None
                    
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
                        yield inner_history, main_history, None
                        
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
                                
                                yield inner_history, main_history, None
                
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
            pdf_path = generate_pdf_report()
            
            if pdf_path and os.path.exists(pdf_path):
                # Add PDF download notification
                main_history.append(
                    gr.ChatMessage(
                        role="assistant",
                        content=f"📄 Conversation report saved: {os.path.basename(pdf_path)}",
                        metadata={"title": "📥 Download Available"}
                    )
                )
            
            yield inner_history, main_history, pdf_path if pdf_path else None
        
        def download_latest_pdf():
            """Return the latest PDF for download"""
            if latest_pdf_path[0] and os.path.exists(latest_pdf_path[0]):
                return latest_pdf_path[0]
            return None
        
        # Create Gradio interface
        with gr.Blocks(title="Biomni A1 Agent") as demo:
            gr.Markdown("# Biomni A1 Agent - Interactive Biomedical Research Assistant")
            gr.Markdown("Ask questions, analyze data, and download PDF reports of your conversation.")
            
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
            
            with gr.Row():
                pdf_output = gr.File(label="📄 Download Conversation Report", visible=True, interactive=False)
                download_btn = gr.Button("⬇️ Download Latest PDF", size="sm", visible=ENABLE_PDF_REPORTS)
            
            # Bind submission
            prompt_input.submit(
                generate_response,
                [prompt_input, innerloop_chatbot, main_chatbot, pdf_output],
                [innerloop_chatbot, main_chatbot, pdf_output]
            ).then(lambda: gr.MultimodalTextbox(value=None), None, [prompt_input])
            
            # Bind download button
            if ENABLE_PDF_REPORTS:
                download_btn.click(
                    download_latest_pdf,
                    outputs=[pdf_output]
                )
        
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
