import streamlit as st

APP_TITLE = "Biomni Research Agent"
st.set_page_config(page_title=APP_TITLE, layout="wide", page_icon="🧬")

import os
import sys
import json
import time
import queue
import threading
import re
import requests as _requests
from pathlib import Path
from datetime import datetime
from PIL import Image
import uuid
from typing import List, Dict, Any, Optional

# =====================
# Configuration
# =====================
BIOMNI_DIR = Path(__file__).parent.absolute()
SESSION_DIR = BIOMNI_DIR / "sessions"
SESSION_DIR.mkdir(exist_ok=True, parents=True)
# Agent writes plots/outputs here (relative to API server CWD = BIOMNI_DIR)
AGENT_RESULTS_DIR = BIOMNI_DIR / "results"

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")
FILE_TYPES = ["csv", "xlsx", "xls", "tsv", "txt", "json", "md", "parquet", "py", "R"]

DEFAULT_API_URL = os.getenv("BIOMNI_UI_API_URL", "http://localhost:8020")

# =====================
# Session State Init
# =====================
def init_session_state():
    defaults = {
        "messages": [],
        "raw_logs": [],
        "running": False,
        "agent_thread": None,
        "api_result": None,       # Stores {response, log, pdf_path, result_files, error} from completed API call
        "current_session_dir": None,
        "result_files": [],
        "pdf_path": None,         # PDF report path from last run
        "execution_steps": [],
        "current_step_id": 0,
        "processed_steps": [],
        "last_api_url": None,
        "multi_turn": True,       # Whether to include prior conversation as context
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session_state()

# =====================
# Helper: Session I/O
# =====================
def create_session_dir(user_id: str = None):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"{user_id}_{timestamp}" if user_id else f"user_{timestamp}"
    d = SESSION_DIR / name
    d.mkdir(exist_ok=True)
    (d / "results").mkdir(exist_ok=True)
    (d / "data").mkdir(exist_ok=True)
    return d

def save_conversation(session_dir: Path):
    f = session_dir / "conversation.json"
    data = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_dir.name,
        "messages": st.session_state.messages,
        "raw_logs": st.session_state.raw_logs,
        "execution_steps": st.session_state.execution_steps,
    }
    with open(f, "w") as fp:
        json.dump(data, fp, indent=2)

def load_conversation(session_dir: Path) -> bool:
    f = session_dir / "conversation.json"
    if not f.exists():
        return False
    with open(f) as fp:
        data = json.load(fp)
    st.session_state.messages = data.get("messages", [])
    st.session_state.raw_logs = data.get("raw_logs", [])
    st.session_state.execution_steps = data.get("execution_steps", [])
    st.session_state.processed_steps = parse_agent_output(st.session_state.raw_logs)
    return True

def get_session_list():
    sessions = []
    for d in sorted(SESSION_DIR.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        f = d / "conversation.json"
        if not f.exists():
            continue
        try:
            with open(f) as fp:
                data = json.load(fp)
            sessions.append({
                "name": d.name,
                "path": d,
                "timestamp": data.get("timestamp", "Unknown"),
                "step_count": len(data.get("execution_steps", [])),
                "message_count": len(data.get("messages", [])),
            })
        except Exception:
            pass
    return sessions

def save_uploads(uploaded_files, dest_dir: Path) -> list:
    if not uploaded_files:
        return []
    dest_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for uf in uploaded_files:
        try:
            dest = dest_dir / Path(uf.name).name
            with open(dest, "wb") as f:
                f.write(uf.getbuffer())
            saved.append(dest)
        except Exception as e:
            print(f"[Upload] Failed to save {uf.name}: {e}")
    return saved

def scan_result_files(results_dir: Path):
    if not results_dir or not results_dir.exists():
        return []
    return sorted(f for f in results_dir.rglob("*") if f.is_file() and not f.name.startswith("."))

def is_valid_image(file_path: Path) -> bool:
    if file_path.suffix.lower() not in IMAGE_EXTS:
        return False
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False

# =====================
# Log Parsing
# =====================
def parse_agent_output(log_lines: list) -> list:
    """Parse raw log lines (from API response log field) into structured steps.
    
    The API log field contains entries like:
      "Ai Message\n\n## Plan\n☐ Step 1...\n<execute>code</execute>"
      "Tool Message\n\n<observation>output</observation>"
    
    We normalise each multi-line entry into [STDOUT]-prefixed lines for the parser.
    """
    # Normalise: split on newlines and prefix each line with [STDOUT]
    stdout_lines = []
    for entry in log_lines:
        if not entry:
            continue
        # Each entry from agent.go() is a multi-line string
        for line in str(entry).split("\n"):
            stdout_lines.append(f"[STDOUT] {line}")

    steps = []
    current_step = None
    in_execute = False
    in_observation = False
    current_code: list = []

    for line in stdout_lines:
        if not line.startswith("[STDOUT]"):
            continue
        text = line[8:].strip()

        if not text or "====" in text:
            continue

        if "## Plan" in text or "Updated Plan:" in text or text.startswith("Plan:"):
            if current_step:
                steps.append(current_step)
            current_step = {"type": "plan", "content": [text], "code": [], "observations": []}
            continue

        if "<execute>" in text:
            if current_step and current_step["type"] != "execute":
                steps.append(current_step)
            current_step = {"type": "execute", "content": [], "code": [], "observations": []}
            code_match = re.search(r"<execute>(.*?)</execute>", text, re.DOTALL)
            if code_match:
                current_step["code"].append(code_match.group(1).strip())
            elif "</execute>" not in text:
                in_execute = True
                code_start = text.split("<execute>", 1)[1]
                if code_start:
                    current_code = [code_start]
            continue

        if in_execute:
            if "</execute>" in text:
                in_execute = False
                code_end = text.split("</execute>", 1)[0]
                if code_end:
                    current_code.append(code_end)
                if current_code and current_step:
                    current_step["code"].append("\n".join(current_code))
                current_code = []
            else:
                current_code.append(text)
            continue

        if "<observation>" in text:
            obs_match = re.search(r"<observation>(.*?)</observation>", text, re.DOTALL)
            if obs_match:
                if current_step and current_step["type"] == "execute":
                    steps.append(current_step)
                current_step = {
                    "type": "observe",
                    "content": [],
                    "code": [],
                    "observations": [obs_match.group(1).strip()],
                }
            elif "</observation>" not in text:
                in_observation = True
                if not current_step or current_step["type"] != "observe":
                    if current_step:
                        steps.append(current_step)
                    current_step = {"type": "observe", "content": [], "code": [], "observations": []}
                obs_start = text.split("<observation>", 1)[1]
                current_step["observations"] = [obs_start] if obs_start else [""]
            continue

        if in_observation:
            if "</observation>" in text:
                in_observation = False
                obs_end = text.split("</observation>", 1)[0]
                if obs_end and current_step and current_step["observations"]:
                    current_step["observations"][0] += "\n" + obs_end
            else:
                if current_step and current_step["observations"]:
                    current_step["observations"][0] += "\n" + text
            continue

        if "<solution>" in text:
            if current_step:
                steps.append(current_step)
            sol_match = re.search(r"<solution>(.*?)</solution>", text, re.DOTALL)
            sol_content = sol_match.group(1).strip() if sol_match else text
            steps.append({"type": "solution", "content": [sol_content], "code": [], "observations": []})
            current_step = None
            continue

        if current_step and text and not text.startswith("==="):
            if not any(tag in text for tag in ["<execute>", "<observation>", "<solution>"]):
                current_step["content"].append(text)

    if current_step:
        steps.append(current_step)
    return steps

# =====================
# Step Rendering
# =====================
def render_step(step: dict, index: int, session_dir: Path = None):
    icons = {"plan": "📋", "execute": "⚙️", "observe": "👁️", "solution": "✅", "hitl": "🤔"}
    icon = icons.get(step["type"], "➡️")

    with st.container():
        c1, c2 = st.columns([0.05, 0.95])
        with c1:
            st.markdown(f"**{icon}**")
        with c2:
            labels = {
                "plan": f"**📋 Planning Step {index + 1}**",
                "execute": f"**⚙️ Execution Step {index + 1}**",
                "observe": f"**👁️ Observation {index + 1}**",
                "solution": "**✅ Final Solution**",
            }
            st.markdown(labels.get(step["type"], f"**Step {index + 1}**"))

        if step["type"] == "plan":
            plan_text = "\n".join(step["content"])
            st.markdown(plan_text)

        elif step["type"] == "execute":
            content = "\n".join(step["content"])
            if content.strip():
                st.markdown(content)
            for i, code in enumerate(step["code"]):
                clean = re.sub(r"^<execute>\s*", "", code)
                clean = re.sub(r"\s*</execute>$", "", clean)
                lang = "python"
                if clean.strip().startswith("#!R"):
                    lang, clean = "r", re.sub(r"^#!R\s*", "", clean)
                elif clean.strip().startswith("#!BASH"):
                    lang, clean = "bash", re.sub(r"^#!BASH\s*", "", clean)
                with st.expander(f"💻 Code Block {i + 1}", expanded=True):
                    st.code(clean, language=lang)

        elif step["type"] == "observe":
            for obs in step["observations"]:
                with st.expander("📊 Output", expanded=True):
                    st.text(obs)
                # Show any images referenced in observation — check both session dir and agent results dir
                search_dirs = [AGENT_RESULTS_DIR]
                if session_dir:
                    search_dirs.append(session_dir / "results")
                for match in re.findall(r"([\w\-\./\\]+\.(?:png|jpg|jpeg|gif|bmp|webp))", obs, re.I):
                    for base in search_dirs:
                        fp = base / Path(match).name
                        if fp.exists() and is_valid_image(fp):
                            st.image(str(fp), caption=fp.name, use_container_width=True)
                            break

        elif step["type"] == "solution":
            solution_text = "\n".join(step["content"])
            solution_text = re.sub(r"<solution>|</solution>", "", solution_text)
            st.markdown("---")
            st.markdown("### ✅ Final Solution")
            st.markdown(solution_text)

        st.divider()

# =====================
# Sidebar Step Tracker
# =====================
def render_step_tracker():
    st.sidebar.markdown("## 📊 Execution Progress")
    steps = st.session_state.processed_steps
    if not steps:
        st.sidebar.info("No steps yet")
        return

    total = len(steps)
    completed = sum(1 for s in steps if s["type"] in ("solution",))
    progress = min(1.0, (total - 1) / max(total, 1)) if total > 1 else 0.0
    st.sidebar.progress(progress, text=f"Steps: {total}")

    with st.sidebar.container(height=350):
        type_icons = {"plan": "📋", "execute": "⚙️", "observe": "👁️", "solution": "🎯"}
        for i, step in enumerate(steps):
            icon = type_icons.get(step["type"], "➡️")
            label = " ".join(step["content"][:1])[:50] if step["content"] else step["type"].title()
            st.markdown(f"**{icon} {label[:50]}{'...' if len(label) > 50 else ''}**")
            if i < total - 1:
                st.divider()

# =====================
# API Call (background thread)
# =====================
def _scan_new_files(since: float) -> list:
    """Scan AGENT_RESULTS_DIR and local_outputs/ for files created after `since` (epoch float)."""
    found = []
    for scan_dir in [AGENT_RESULTS_DIR, BIOMNI_DIR / "local_outputs"]:
        if not scan_dir.exists():
            continue
        for fp in scan_dir.rglob("*"):
            try:
                if fp.is_file() and not fp.name.startswith(".") and fp.stat().st_mtime >= since:
                    found.append(fp)
            except Exception:
                pass
    return sorted(found, key=lambda f: f.stat().st_mtime)

def call_api_background(api_url: str, query: str, result_holder: dict):
    """Called in a background thread. Writes result to result_holder dict."""
    start_epoch = result_holder.get("start_epoch", time.time())
    try:
        resp = _requests.post(
            f"{api_url.rstrip('/')}/chat",
            json={"prompt": query, "save_pdf": True},
            timeout=900,
        )
        resp.raise_for_status()
        data = resp.json()
        result_holder["response"] = data.get("response", "")
        result_holder["log"] = data.get("log", "")
        result_holder["pdf_path"] = data.get("pdf_path")
        result_holder["error"] = None
        # Scan for new files produced during this run
        result_holder["new_files"] = _scan_new_files(start_epoch)
    except Exception as e:
        result_holder["response"] = f"❌ API Error: {e}"
        result_holder["log"] = ""
        result_holder["pdf_path"] = None
        result_holder["new_files"] = []
        result_holder["error"] = str(e)
    finally:
        result_holder["done"] = True

# =====================
# Sidebar
# =====================
def render_sidebar():
    with st.sidebar:
        st.markdown(f"## 🧬 {APP_TITLE}")
        st.divider()

        with st.expander("⚙️ API Configuration", expanded=False):
            api_url = st.text_input(
                "API Endpoint",
                value=st.session_state.get("last_api_url") or DEFAULT_API_URL,
                key="sidebar_api_url",
                help="e.g. http://localhost:8020",
            )
        api_url = st.session_state.get("sidebar_api_url", DEFAULT_API_URL)

        st.divider()
        st.subheader("📁 Sessions")
        sessions = get_session_list()
        if sessions:
            opts = []
            for s in sessions:
                try:
                    ts = datetime.fromisoformat(s["timestamp"]).strftime("%m-%d %H:%M")
                except Exception:
                    ts = s["timestamp"][:16]
                opts.append(f"{s['name'][:20]} ({ts}) – {s['step_count']} steps")

            idx = st.selectbox("Available Sessions", range(len(sessions)),
                               format_func=lambda i: opts[i], key="sidebar_session_select")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📂 Load", use_container_width=True,
                             disabled=st.session_state.running, key="btn_load"):
                    sess = sessions[idx]
                    st.session_state.current_session_dir = sess["path"]
                    if load_conversation(sess["path"]):
                        st.session_state.result_files = scan_result_files(sess["path"] / "results")
                        st.success("✅ Loaded")
                        st.rerun()
                    else:
                        st.warning("No conversation history")
            with c2:
                if st.button("🗑️ Delete", use_container_width=True,
                             disabled=st.session_state.running, key="btn_delete"):
                    import shutil
                    try:
                        shutil.rmtree(sessions[idx]["path"])
                        st.success("🗑️ Deleted")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")
        else:
            st.info("No saved sessions")

        st.divider()
        st.subheader("📤 Upload Files")
        uploaded = st.file_uploader(
            "Upload data files (path injected into prompt)",
            type=FILE_TYPES,
            accept_multiple_files=True,
            key="sidebar_uploader",
        )
        if uploaded:
            st.caption(f"{len(uploaded)} file(s) ready")

        st.divider()
        if st.session_state.running:
            st.info("🔄 Running... please wait")
        else:
            st.success("✅ Ready")

        # Multi-turn toggle
        st.session_state.multi_turn = st.checkbox(
            "🔁 Multi-turn (include prior conversation as context)",
            value=st.session_state.get("multi_turn", True),
            key="cb_multi_turn",
            help="When enabled, prior Q&A is prepended to each new question so the agent maintains context.",
        )

        render_step_tracker()

    return {"api_url": api_url, "uploaded": uploaded}

# =====================
# Main Layout
# =====================
sidebar = render_sidebar()
api_url = sidebar["api_url"]
uploaded_files = sidebar["uploaded"]

# Check if background thread completed
if st.session_state.running:
    result = st.session_state.get("api_result")
    if result and result.get("done"):
        # Thread finished — process results
        st.session_state.running = False
        log_raw = result.get("log") or ""
        response_text = result.get("response") or ""

        # The log field from API is already a newline-joined string of pretty_print entries
        log_lines = log_raw.split("\n") if log_raw else []
        st.session_state.raw_logs.extend(log_lines)

        # Add assistant message (short response only, not full log)
        st.session_state.messages.append({"role": "assistant", "content": response_text})

        # Parse steps
        st.session_state.processed_steps = parse_agent_output(log_lines)

        # PDF report
        st.session_state.pdf_path = result.get("pdf_path")

        # Files produced during this run (plots, CSVs, etc.)
        new_files = result.get("new_files") or []
        # Also include session uploaded files
        if st.session_state.current_session_dir:
            session_files = scan_result_files(st.session_state.current_session_dir / "results")
        else:
            session_files = []
        # Merge, deduplicate by path
        all_files = {str(f): f for f in session_files}
        for f in new_files:
            all_files[str(f)] = f
        st.session_state.result_files = list(all_files.values())

        # Save session
        if st.session_state.current_session_dir:
            save_conversation(st.session_state.current_session_dir)

        st.session_state.api_result = None

mid_col, right_col = st.columns([0.65, 0.35])

# =====================
# MIDDLE COLUMN: Conversation + Input
# =====================
with mid_col:
    st.subheader("💬 Conversation")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if st.session_state.processed_steps:
        for i, step in enumerate(st.session_state.processed_steps):
            render_step(step, i, st.session_state.current_session_dir)

    elif st.session_state.running:
        with st.spinner("🔄 Biomni agent is working... (this may take several minutes)"):
            time.sleep(2)
            st.rerun()

    # Input area
    if not st.session_state.running:
        prompt = st.text_area("Enter your research question", height=120, key="user_prompt_area",
                              value=st.session_state.get("user_prompt", ""))

        if st.button("▶️ Start Analysis", type="primary", use_container_width=True):
            if prompt and prompt.strip():
                # Save uploaded files and inject paths into prompt
                augmented_prompt = prompt.strip()
                if uploaded_files:
                    session_dir = create_session_dir()
                    st.session_state.current_session_dir = session_dir
                    saved = save_uploads(uploaded_files, session_dir / "data")
                    if saved:
                        file_list = "\n".join(f"  - {p}" for p in saved)
                        augmented_prompt += (
                            f"\n\nUploaded data files are available at:\n{file_list}\n"
                            "Please use these files in your analysis."
                        )
                else:
                    if not st.session_state.current_session_dir:
                        st.session_state.current_session_dir = create_session_dir()

                # Multi-turn: prepend prior Q&A as conversation context
                prior = [m for m in st.session_state.messages if m["role"] in ("user", "assistant")]
                if st.session_state.get("multi_turn", True) and prior:
                    history_lines = []
                    for m in prior:
                        role_label = "User" if m["role"] == "user" else "Assistant"
                        # Truncate very long assistant responses to avoid prompt bloat
                        content = m["content"]
                        if m["role"] == "assistant" and len(content) > 1000:
                            content = content[:1000] + "\n... [truncated]"
                        history_lines.append(f"{role_label}: {content}")
                    history_str = "\n\n".join(history_lines)
                    augmented_prompt = (
                        f"Prior conversation context:\n{history_str}\n\n"
                        f"New request:\n{augmented_prompt}"
                    )

                # Add user message to display history
                st.session_state.messages.append({"role": "user", "content": prompt.strip()})
                st.session_state.raw_logs = []
                st.session_state.processed_steps = []
                st.session_state.execution_steps = []
                st.session_state.current_step_id = 0
                st.session_state.last_api_url = api_url
                st.session_state.result_files = []
                st.session_state.pdf_path = None

                # Start background API call
                result_holder: dict = {"done": False, "start_epoch": time.time()}
                st.session_state.api_result = result_holder
                st.session_state.running = True

                t = threading.Thread(
                    target=call_api_background,
                    args=(api_url, augmented_prompt, result_holder),
                    daemon=True,
                )
                t.start()
                st.session_state.agent_thread = t

                st.rerun()
            else:
                st.warning("Please enter a question first.")
    else:
        if st.button("⏹️ Stop (kills API thread - use sparingly)", type="secondary"):
            # We can't easily kill the background thread or the API call
            # Best we can do is mark as not running so UI unblocks
            st.session_state.running = False
            st.session_state.messages.append({
                "role": "assistant",
                "content": "⚠️ UI stopped waiting. The API call may still be running in the background."
            })
            st.rerun()

# =====================
# RIGHT COLUMN: Results & Logs
# =====================
with right_col:
    tab1, tab2 = st.tabs(["📊 Results", "📋 Logs"])

    with tab1:
        st.subheader("Generated Files")

        # PDF Report download (prominent, at top)
        if st.session_state.get("pdf_path"):
            pdf_p = Path(st.session_state.pdf_path)
            if pdf_p.exists():
                with open(pdf_p, "rb") as f:
                    st.download_button(
                        label="📄 Download PDF Report",
                        data=f.read(),
                        file_name=pdf_p.name,
                        mime="application/pdf",
                        key=f"pdf_{pdf_p.stem}",
                        type="primary",
                        use_container_width=True,
                    )
                st.caption(f"Saved: `{pdf_p}`")
                st.divider()

        if st.session_state.result_files:
            for fp in st.session_state.result_files:
                # Skip the PDF (already shown above) and hidden files
                if fp.suffix.lower() == ".pdf" or fp.name.startswith("."):
                    continue
                name = fp.name
                try:
                    size = fp.stat().st_size
                except Exception:
                    continue

                if is_valid_image(fp):
                    try:
                        st.image(str(fp), caption=name, use_container_width=True)
                    except Exception:
                        pass

                try:
                    with open(fp, "rb") as f:
                        st.download_button(
                            label=f"⬇️ {name} ({size:,} bytes)",
                            data=f.read(),
                            file_name=name,
                            key=f"dl_{fp.stem}_{size}",
                        )
                except Exception:
                    st.caption(f"📄 {name}")

        elif not st.session_state.get("pdf_path"):
            st.info("No results yet")
            st.caption("Plots and files saved to `./results/` by the agent will appear here after a run.")

    with tab2:
        st.subheader("Execution Logs")
        show_debug = st.checkbox("Show all log lines", value=False, key="show_debug")

        if st.session_state.raw_logs:
            logs_to_show = st.session_state.raw_logs
            if not show_debug:
                # Show only substantive lines (skip config banners, keepalive)
                skip_patterns = ["====", "Keepalive", "DEFAULT CONFIG", "BIOMNI CONFIGURATION",
                                  "AGENT LLM", "Temperature:", "Use Tool Retriever",
                                  "Commercial Mode", "Path:", "Timeout"]
                logs_to_show = [l for l in logs_to_show
                                if l.strip() and not any(p in l for p in skip_patterns)]
            with st.expander("View Logs", expanded=True):
                st.code("\n".join(logs_to_show), language="text", line_numbers=False)
        else:
            st.info("No logs yet")

# Auto-refresh while running
if st.session_state.running:
    time.sleep(2)
    st.rerun()

st.divider()
st.caption("🧬 Biomni Research Agent · Adapted from qb-phx-tool-daqc_agent UI")
