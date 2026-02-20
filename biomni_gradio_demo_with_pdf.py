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
from time import time, sleep
from dataclasses import dataclass, field
from typing import Optional

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

@dataclass
class HITLState:
    """Human-in-the-Loop state management for Gradio UI.
    
    Tracks approval state, plan modifications, and execution control
    without modifying the underlying agent behavior.
    """
    mode: str = "yolo"  # "yolo" (default) or "hitl"
    approval_pending: bool = False
    current_plan: Optional[str] = None
    edited_plan: Optional[str] = None
    step_approvals: dict = field(default_factory=dict)  # {step_index: bool}
    paused: bool = False
    current_step_index: int = 0
    total_steps: int = 0
    batch_approve_remaining: bool = False  # If true, auto-approve all remaining steps
    
    # New fields for blocking approval
    waiting_for_approval: bool = False
    approval_response: Optional[str] = None  # "approved", "edited", "rejected"
    continuation_prompt: Optional[str] = None  # For edited plans
    
    def reset(self):
        """Reset state for new query (keeps mode setting)"""
        self.approval_pending = False
        self.current_plan = None
        self.edited_plan = None
        self.step_approvals = {}
        self.paused = False
        self.current_step_index = 0
        self.total_steps = 0
        self.batch_approve_remaining = False
        self.waiting_for_approval = False
        self.approval_response = None
        self.continuation_prompt = None
    
    def is_step_approved(self, step_index: int) -> bool:
        """Check if a specific step is approved"""
        if self.batch_approve_remaining:
            return True
        return self.step_approvals.get(step_index, False)
    
    def approve_step(self, step_index: int):
        """Mark a step as approved"""
        self.step_approvals[step_index] = True
    
    def approve_all_remaining(self):
        """Approve all remaining steps (batch approval)"""
        self.batch_approve_remaining = True
    
    def get_active_plan(self) -> Optional[str]:
        """Get the currently active plan (edited if available, otherwise original)"""
        return self.edited_plan if self.edited_plan else self.current_plan
    
    def pause_for_approval(self):
        """Pause execution and wait for user approval."""
        self.paused = True
        self.approval_pending = True
        self.waiting_for_approval = True
    
    def resume_execution(self):
        """Resume execution after approval."""
        self.paused = False
        self.approval_pending = False
        self.waiting_for_approval = False
    
    def should_pause_for_plan_approval(self) -> bool:
        """Check if should pause for initial plan approval."""
        result = (
            self.mode == "hitl" and 
            self.current_plan is not None and 
            not self.paused and 
            self.approval_pending and
            not self.waiting_for_approval  # Don't trigger multiple times
        )
        print(f"🔍 should_pause_for_plan_approval: mode={self.mode}, plan={self.current_plan is not None}, paused={self.paused}, pending={self.approval_pending}, waiting={self.waiting_for_approval} => {result}")
        return result

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
        
        # Initialize HITL state (UI-layer only, no agent modification)
        hitl_state = HITLState()
        print(f"🤝 HITL state initialized (default mode: {hitl_state.mode})")
        
        # Conversation tracking
        main_history_copy = []
        stop_requested = [False]  # Flag to signal stop request
        
        SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".pdf")
        
        def extract_plan_from_message(message_content: str) -> Optional[str]:
            """Extract checklist plan from agent message.
            
            Agent uses format:
            1. [ ] First step
            2. [✓] Completed step  
            3. [✗] Failed step
            
            Returns tuple: (plan_text, total_steps)
            """
            if not message_content:
                return None, 0
            
            # Pattern to match numbered checklist items with [ ], [✓], or [✗]
            # Matches: "1. [ ] Step" or "2. [✓] Step" or "3. [✗] Step"
            checklist_pattern = r'^\d+\.\s*\[[ ✓✗xX]\]\s+.+$'
            
            lines = message_content.split('\n')
            plan_lines = []
            
            for line in lines:
                # Check if line matches checklist pattern
                if re.match(checklist_pattern, line.strip()):
                    plan_lines.append(line.strip())
            
            if plan_lines:
                plan_text = '\n'.join(plan_lines)
                total_steps = len(plan_lines)
                return plan_text, total_steps
            
            return None, 0
        
        def update_plan_in_hitl_state(message_content: str):
            """Check message for plan and update HITL state if found.
            
            Returns True if plan was found, False otherwise.
            """
            print(f"🔍 update_plan_in_hitl_state called: mode={hitl_state.mode}, has_plan={hitl_state.current_plan is not None}")
            if hitl_state.mode != "hitl":
                print("  ⏭️ Not HITL mode - skipping")
                return False  # Only track plans in HITL mode
            
            plan_text, total_steps = extract_plan_from_message(message_content)
            print(f"  📋 extract_plan_from_message: found={plan_text is not None}, steps={total_steps}")
            if plan_text and not hitl_state.current_plan:
                # First plan detected - store it
                hitl_state.current_plan = plan_text
                hitl_state.total_steps = total_steps
                hitl_state.approval_pending = True
                print(f"📋 Plan detected ({total_steps} steps) - approval required in HITL mode")
                print(f"  Plan text:\n{plan_text[:200]}...")
                return True
            
            return False

        
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
                # Format messages to match expected log format (with "Human Message" / "Ai Message" markers)
                agent.log = []
                for msg in main_history_copy:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    
                    # Format to match the expected log format that _normalize_log_messages parses
                    if role == 'user':
                        formatted_entry = f"================================ Human Message =================================\n\n{content}"
                    else:  # assistant
                        formatted_entry = f"================================== Ai Message ==================================\n\n{content}"
                    
                    agent.log.append(formatted_entry)
                
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
        
        def generate_response(prompt_input, inner_history=None, main_history=None, mode="🚀 YOLO (Full Automation)"):
            """Generate response and create PDF report"""
            if main_history is None:
                main_history = []
            if inner_history is None:
                inner_history = []
            
            # Reset HITL state for new query and update mode
            hitl_state.reset()
            hitl_state.mode = "hitl" if "HITL" in mode else "yolo"
            
            # Reset stop flag at start of new generation
            stop_requested[0] = False
            
            # Update UI status messages
            if hitl_state.mode == "hitl":
                # Initialize status messages for HITL mode
                initial_plan_status = "🤝 HITL mode active - waiting for plan to be generated..."
                initial_step_status = "🤝 HITL mode active - will pause before each execution step."
            else:
                initial_plan_status = "🚀 YOLO mode - automatic execution without approval"
                initial_step_status = "🚀 YOLO mode - automatic execution without approval"
            
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
            
            # Stream agent responses - may need to restart after HITL approval
            while True:  # Outer loop to allow stream restart
                stream_ended_naturally = True
                
                # Stream agent responses
                for s in agent.app.stream(inputs, stream_mode="values", config=config):
                    # Check if stop requested
                    if stop_requested[0]:
                        inner_history.append(
                            gr.ChatMessage(
                                role="assistant",
                                content="⚠️ Execution stopped by user",
                                metadata={"title": "🛑 Stopped"}
                            )
                        )
                        main_history.append(
                            gr.ChatMessage(
                                role="assistant",
                                content="Execution stopped by user",
                                metadata={"title": "🛑 Stopped"}
                            )
                        )
                        yield inner_history, main_history
                        return
                
                t_step = time() - t
                message = s["messages"][-1]
                
                # Extract and track plan if present (HITL mode only) - DO THIS FIRST
                if isinstance(message.content, str):
                    update_plan_in_hitl_state(message.content)
                
                # Check if paused for approval (HITL mode) - AFTER plan extraction
                if hitl_state.should_pause_for_plan_approval():
                    # ACTUALLY PAUSE - stop streaming and wait for user
                    hitl_state.pause_for_approval()
                    print(f"⏸️ PAUSED for plan approval in HITL mode")
                    
                    # Show plan in main chat with approval needed message
                    main_history.append(
                        gr.ChatMessage(
                            role="assistant",
                            content=f"📋 **Plan Generated ({hitl_state.total_steps} steps)**\n\nPlease review the plan in the approval section below and click a button to continue.\n\n**Generated Plan:**\n```\n{hitl_state.current_plan}\n```",
                            metadata={"title": "⏸️ Approval Required"}
                        )
                    )
                    
                    # Add pause message to executor
                    inner_history.append(
                        gr.ChatMessage(
                            role="assistant",
                            content="⏸️ **Execution Paused** - Waiting for user approval...\n\nUse the 'HITL Approval Controls' to approve or modify the plan.",
                            metadata={"title": "🤝 HITL Mode"}
                        )
                    )
                    
                    yield inner_history, main_history
                    
                    # BLOCKING WAIT - poll until user approves/rejects
                    print("⏸️ Entering blocking wait for approval...")
                    while hitl_state.waiting_for_approval:
                        sleep(0.5)  # Poll every 500ms
                        if stop_requested[0]:
                            print("🛑 Stop requested during plan approval")
                            return
                    
                    print(f"✅ Approval received: {hitl_state.approval_response}")
                    
                    # Handle different approval responses
                    if hitl_state.approval_response == "rejected":
                        main_history.append(
                            gr.ChatMessage(
                                role="assistant",
                                content="❌ Plan rejected by user. Execution cancelled.",
                                metadata={"title": "❌ Cancelled"}
                            )
                        )
                        yield inner_history, main_history
                        return
                    
                    # For approved or edited plans, we need to continue the agent
                    # The agent has generated a plan and is waiting. We need to tell it to proceed.
                    
                    if hitl_state.approval_response in ["edited_replan", "edited_execute"]:
                        # User edited plan - send back to agent
                        if hitl_state.approval_response == "edited_replan":
                            continuation_msg = f"I've reviewed your plan and made some edits. Please review my changes and revise if needed:\n\n{hitl_state.edited_plan}\n\nAfter reviewing, please proceed with execution."
                        else:  # edited_execute
                            continuation_msg = f"I've modified the plan. Please execute this plan:\n\n{hitl_state.edited_plan}\n\nProceed with execution."
                        
                        main_history.append(
                            gr.ChatMessage(
                                role="assistant",
                                content=f"✏️ Plan edited. Restarting with modified plan...",
                                metadata={"title": "✏️ Modified"}
                            )
                        )
                    else:  # approved
                        # Agent's plan is approved, tell it to proceed
                        continuation_msg = "Approved. Please proceed with executing the plan."
                        
                        main_history.append(
                            gr.ChatMessage(
                                role="assistant",
                                content="✅ Plan approved. Starting execution...",
                                metadata={"title": "✅ Approved"}
                            )
                        )
                    
                    yield inner_history, main_history
                    
                    # Add continuation message to agent and restart stream
                    agent_messages.append(HumanMessage(content=continuation_msg))
                    inputs = {"messages": agent_messages, "next_step": None}
                    
                    print(f"🔄 Restarting agent stream with continuation message...")
                    
                    # Continue with a NEW stream that includes the continuation
                    # Don't return - break out of current stream and restart below
                    break  # Exit current stream loop
                
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
                        # In HITL mode, check if we should pause before executing
                        if hitl_state.mode == "hitl" and not hitl_state.batch_approve_remaining:
                            hitl_state.current_step_index += 1
                            
                            # Check if this step is already approved
                            if not hitl_state.is_step_approved(hitl_state.current_step_index):
                                # PAUSE for step approval
                                code = execute_match.group(1).strip()
                                step_info = f"Step {hitl_state.current_step_index}/{hitl_state.total_steps}" if hitl_state.total_steps > 0 else f"Step {hitl_state.current_step_index}"
                                
                                print(f"⏸️ PAUSED at {step_info} for approval in HITL mode")
                                
                                # Show step info in executor
                                inner_history.append(
                                    gr.ChatMessage(
                                        role="assistant",
                                        content=f"⏸️ **{step_info} - Approval Required**\n\nAbout to execute code. Please approve to continue.",
                                        metadata={"title": "🤝 HITL Step Approval"}
                                    )
                                )
                                
                                # Show in main chat
                                main_history.append(
                                    gr.ChatMessage(
                                        role="assistant",
                                        content=f"⏸️ **{step_info} requires approval**\n\nReview the code in the executor panel and use step approval buttons.",
                                        metadata={"title": "⏸️ Step Approval"}
                                    )
                                )
                                
                                yield inner_history, main_history
                                
                                # BLOCKING WAIT for step approval
                                hitl_state.pause_for_approval()
                                print(f"⏸️ Waiting for step {hitl_state.current_step_index} approval...")
                                while hitl_state.waiting_for_approval:
                                    sleep(0.3)
                                    if stop_requested[0]:
                                        print("🛑 Stop requested during step approval")
                                        return
                                
                                print(f"✅ Step {hitl_state.current_step_index} approved: {hitl_state.approval_response}")
                                
                                # Handle step approval response
                                if hitl_state.approval_response == "rejected":
                                    main_history.append(
                                        gr.ChatMessage(
                                            role="assistant",
                                            content=f"❌ Step {hitl_state.current_step_index} rejected. Execution cancelled.",
                                            metadata={"title": "❌ Cancelled"}
                                        )
                                    )
                                    yield inner_history, main_history
                                    return
                                elif hitl_state.approval_response == "skip":
                                    main_history.append(
                                        gr.ChatMessage(
                                            role="assistant",
                                            content=f"⏭️ Step {hitl_state.current_step_index} skipped.",
                                            metadata={"title": "⏭️ Skipped"}
                                        )
                                    )
                                    yield inner_history, main_history
                                    continue  # Skip this step, go to next
                                elif hitl_state.approval_response == "batch_approve":
                                    hitl_state.batch_approve_remaining = True
                                    print("⏩ Batch approve activated - all remaining steps will auto-execute")
                                # else: "approved" - continue normally
                        
                        # Track step in HITL mode (for info)
                        if hitl_state.mode == "hitl":
                            if hitl_state.current_step_index == 0 or hitl_state.batch_approve_remaining:
                                hitl_state.current_step_index += 1
                            step_info = f"Step {hitl_state.current_step_index}/{hitl_state.total_steps}" if hitl_state.total_steps > 0 else f"Step {hitl_state.current_step_index}"
                            print(f"🔧 Executing {step_info} in HITL mode")
                        
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
                
                # Check if we broke out of the loop for HITL continuation
                if hitl_state.mode == "hitl" and hitl_state.approval_response in ["approved", "edited_replan", "edited_execute"]:
                    # Stream was interrupted for approval, now restart with continuation
                    print(f"🔄 Stream restarting after approval...")
                    hitl_state.approval_response = None  # Reset for next pause
                    continue  # Go back to while True loop to restart stream
                else:
                    # Stream ended naturally
                    break  # Exit while True loop
            
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
        
        def stop_execution():
            """Stop the current execution"""
            stop_requested[0] = True
            return "Stopping..."
        
        def approve_plan():
            """Approve the plan and continue execution"""
            if hitl_state.waiting_for_approval:
                hitl_state.approval_response = "approved"
                hitl_state.resume_execution()
                print("✅ Plan approved - continuing execution")
                return "✅ Plan approved. Continuing..."
            return "No plan pending approval."
        
        def edit_and_replan(edited_plan):
            """User edited the plan and wants LLM to review/revise it"""
            if edited_plan and edited_plan.strip():
                hitl_state.edited_plan = edited_plan
                hitl_state.approval_response = "edited_replan"
                hitl_state.resume_execution()
                hitl_state.continuation_prompt = f"I've reviewed your plan and made some edits. Please review my changes and revise if needed:\n\n{edited_plan}\n\nPlease analyze if this revised plan makes sense and proceed with execution (or suggest further improvements)."
                print("✏️ Plan edited - requesting re-plan")
                return "✏️ Plan edited. Requesting LLM review..."
            return "No edits provided."
        
        def edit_and_execute(edited_plan):
            """User edited the plan and wants to execute as-is without LLM review"""
            if edited_plan and edited_plan.strip():
                hitl_state.edited_plan = edited_plan
                hitl_state.approval_response = "edited_execute"
                hitl_state.resume_execution()
                hitl_state.continuation_prompt = f"I've modified the plan. Please execute this revised plan:\n\n{edited_plan}"
                print("⚡ Plan edited - executing directly")
                return "⚡ Executing edited plan..."
            return "No edits provided."
        
        def reject_plan():
            """Reject the plan and stop execution"""
            if hitl_state.waiting_for_approval:
                hitl_state.approval_response = "rejected"
                hitl_state.resume_execution()
                print("❌ Plan rejected")
                return "❌ Plan rejected. Execution stopped."
            return "No plan pending approval."
        
        def approve_this_step():
            """Approve current step and continue"""
            if hitl_state.waiting_for_approval:
                hitl_state.approval_response = "approved"
                hitl_state.resume_execution()
                print(f"✅ Step {hitl_state.current_step_index} approved")
                return f"✅ Step {hitl_state.current_step_index} approved. Continuing..."
            return "No step pending approval."
        
        def approve_all_steps():
            """Approve all remaining steps (batch approve)"""
            if hitl_state.waiting_for_approval:
                hitl_state.approval_response = "batch_approve"
                hitl_state.batch_approve_remaining = True
                hitl_state.resume_execution()
                print("⏩ Batch approval - all remaining steps will execute")
                return "⏩ All remaining steps approved. Continuing..."
            return "No step pending approval."
        
        def skip_step():
            """Skip current step"""
            if hitl_state.waiting_for_approval:
                hitl_state.approval_response = "skip"
                hitl_state.resume_execution()
                print(f"⏭️ Step {hitl_state.current_step_index} skipped")
                return f"⏭️ Step {hitl_state.current_step_index} skipped."
            return "No step pending approval."
        
        def stop_step():
            """Stop execution at current step"""
            if hitl_state.waiting_for_approval:
                hitl_state.approval_response = "rejected"
                hitl_state.resume_execution()
                print("🛑 Execution stopped by user")
                return "🛑 Execution stopped."
            return "No step pending approval."
        
        def reject_plan():
            """Reject the plan and stop execution"""
            hitl_state.reset()
            stop_requested[0] = True
            return "❌ Plan rejected. Execution stopped."
        
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
            
            # Execution mode selector
            execution_mode = gr.Radio(
                choices=[
                    "🚀 YOLO (Full Automation)",
                    "🤝 HITL (Review & Approve)"
                ],
                value="🚀 YOLO (Full Automation)",
                label="Execution Mode",
                info="YOLO: automatic execution | HITL: review plans before execution"
            )
            
            # Integrated approval controls - compact row format
            with gr.Group():
                gr.Markdown("### 🤝 HITL Approval Controls")
                
                # Plan approval - compact single row
                with gr.Row():
                    with gr.Column(scale=3):
                        plan_editor = gr.Textbox(
                            label="📋 Plan (editable in HITL mode)",
                            lines=4,
                            interactive=True,
                            placeholder="Generated plan will appear here when in HITL mode. You can edit it before approving.",
                            show_label=True
                        )
                    with gr.Column(scale=1):
                        gr.Markdown("**Plan Actions:**")
                        approve_btn = gr.Button("✅ Approve", variant="primary", size="sm")
                        edit_replan_btn = gr.Button("✏️ Edit & Re-plan", variant="secondary", size="sm")
                        edit_execute_btn = gr.Button("⚡ Edit & Execute", variant="secondary", size="sm")
                        reject_btn = gr.Button("❌ Reject", variant="stop", size="sm")
                
                # Step approval - compact single row
                with gr.Row():
                    with gr.Column(scale=3):
                        approval_status = gr.Textbox(
                            label="Status",
                            value="Ready. Select HITL mode and ask a question to start.",
                            interactive=False,
                            show_label=True,
                            lines=2
                        )
                    with gr.Column(scale=1):
                        gr.Markdown("**Step Actions:**")
                        approve_step_btn = gr.Button("✅ This Step", variant="primary", size="sm")
                        approve_all_btn = gr.Button("⏩ All Steps", variant="secondary", size="sm")
                        skip_step_btn = gr.Button("⏭️ Skip", size="sm")
                        stop_step_btn = gr.Button("🛑 Stop", variant="stop", size="sm")
            
            # Hidden fields for compatibility
            plan_display = gr.Textbox(visible=False)
            step_status = gr.Textbox(visible=False)
            current_step_display = gr.Textbox(visible=False)
            approval_accordion = gr.Accordion(visible=False)
            step_approval_accordion = gr.Accordion(visible=False)

            
            with gr.Row():
                prompt_input = gr.MultimodalTextbox(
                    interactive=True,
                    file_count="multiple",
                    placeholder="Ask something or upload a file...",
                    show_label=False,
                    scale=4
                )
                stop_btn = gr.Button("🛑 Stop", size="sm", variant="stop", scale=1)
            
            status_text = gr.Textbox(label="Status", visible=False, interactive=False)
            
            # Bind submission
            prompt_input.submit(
                generate_response,
                [prompt_input, innerloop_chatbot, main_chatbot, execution_mode],
                [innerloop_chatbot, main_chatbot]
            ).then(lambda: gr.MultimodalTextbox(value=None), None, [prompt_input])
            
            # Bind stop button
            stop_btn.click(
                stop_execution,
                outputs=[status_text]
            )
            
            # Bind approval buttons - simple flag setting, no restart
            approve_btn.click(
                approve_plan,
                outputs=[approval_status]
            )
            
            edit_replan_btn.click(
                edit_and_replan,
                inputs=[plan_editor],
                outputs=[approval_status]
            )
            
            edit_execute_btn.click(
                edit_and_execute,
                inputs=[plan_editor],
                outputs=[approval_status]
            )
            
            reject_btn.click(
                reject_plan,
                outputs=[approval_status]
            )
            
            # Bind step approval buttons - simple flag setting, no restart
            approve_step_btn.click(
                approve_this_step,
                outputs=[approval_status]
            )
            
            approve_all_btn.click(
                approve_all_steps,
                outputs=[approval_status]
            )
            
            skip_step_btn.click(
                skip_step,
                outputs=[approval_status]
            )
            
            stop_step_btn.click(
                stop_step,
                outputs=[approval_status]
            )

        
        # Launch
        print(f"\n🎨 Launching Gradio UI on http://{SERVER_NAME}:{GRADIO_PORT}")
        print("   Press Ctrl+C to stop the server\n")
        demo.launch(
            share=SHARE, 
            server_name=SERVER_NAME, 
            server_port=GRADIO_PORT,
            allowed_paths=["/data/jinc", "/tmp", LOCAL_OUTPUTS_DIR]
        )
        
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
