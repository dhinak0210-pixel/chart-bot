import streamlit as st
import os
import json
import pandas as pd
from dotenv import load_dotenv
from agent import ReActAgent

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="chart bot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto-detect credentials from the environment
env_nvidia_key = os.environ.get("NVIDIA_API_KEY", "")
env_groq_key = os.environ.get("GROQ_API_KEY", "")
env_gemini_key = os.environ.get("GEMINI_API_KEY", "")

# Prioritize NVIDIA, then Groq, then Gemini
if env_nvidia_key:
    active_provider = "nvidia"
    active_key = env_nvidia_key
elif env_groq_key:
    active_provider = "groq"
    active_key = env_groq_key
elif env_gemini_key:
    active_provider = "gemini"
    active_key = env_gemini_key
else:
    active_provider = "nvidia"
    active_key = ""

# Premium UI CSS injection for Ultra Luxury Obsidian Aesthetics
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Background and Typography Overrides */
    .stApp {
        background-color: #07090e;
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Default Header & Sidebar Padding */
    header { visibility: hidden; }
    [data-testid="stHeader"] { background: transparent; }
    
    /* Custom Title Area */
    .hero-container {
        padding: 2.5rem 1.5rem;
        margin-bottom: 2rem;
        border-radius: 24px;
        background: radial-gradient(circle at top left, rgba(139, 92, 246, 0.08), transparent 60%),
                    radial-gradient(circle at bottom right, rgba(236, 72, 153, 0.05), transparent 60%);
        border: 1px solid rgba(255, 255, 255, 0.03);
        box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.05);
    }
    
    .main-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 3.2rem;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #a78bfa 0%, #f472b6 60%, #fb7185 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.4rem;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #94a3b8;
        font-weight: 300;
        letter-spacing: 0.01em;
    }
    
    /* Glassmorphic Log Cards */
    .log-card {
        background: rgba(15, 23, 42, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        transition: transform 0.2s ease, border 0.2s ease;
    }
    .log-card:hover {
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .log-header {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 0.9rem;
        letter-spacing: 0.06em;
        display: flex;
        align-items: center;
        margin-bottom: 0.6rem;
    }
    
    .log-thought { border-left: 4px solid #8b5cf6; }
    .log-action { border-left: 4px solid #f59e0b; }
    .log-observation { border-left: 4px solid #10b981; }
    
    .log-badge {
        font-size: 0.7rem;
        text-transform: uppercase;
        font-weight: 800;
        padding: 0.25rem 0.6rem;
        border-radius: 6px;
        margin-right: 0.6rem;
        color: #fff;
    }
    
    .badge-thought { background: linear-gradient(135deg, #7c3aed, #8b5cf6); }
    .badge-action { background: linear-gradient(135deg, #d97706, #f59e0b); color: #0f172a; }
    .badge-observation { background: linear-gradient(135deg, #059669, #10b981); }
    
    /* Code block override inside logs */
    .code-container {
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.85rem;
        background-color: #080c14;
        padding: 0.6rem;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        color: #e2e8f0;
        overflow-x: auto;
    }
    
    /* Sidebar Aesthetics */
    [data-testid="stSidebar"] {
        background-color: #0c0e15 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.03) !important;
    }
    
    .sidebar-header {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 1.5rem;
        color: #f8fafc;
        margin-bottom: 1.2rem;
        background: linear-gradient(135deg, #c084fc, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.01em;
    }
    
    /* Buttons */
    .stButton>button {
        background: rgba(255, 255, 255, 0.03) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 600 !important;
        font-family: 'Outfit', sans-serif !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, rgba(167, 139, 250, 0.15), rgba(236, 72, 153, 0.1)) !important;
        color: #ffffff !important;
        border: 1px solid rgba(167, 139, 250, 0.4) !important;
        box-shadow: 0 0 15px rgba(167, 139, 250, 0.2);
    }
    
    /* Chat input override */
    [data-testid="stChatInput"] {
        background-color: #0e121e !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "latest_logs" not in st.session_state:
    st.session_state.latest_logs = []
if "active_chart" not in st.session_state:
    st.session_state.active_chart = None

# Instantiate ReActAgent silently
if "agent" not in st.session_state or st.session_state.get("current_provider") != active_provider:
    st.session_state.agent = ReActAgent(provider=active_provider, api_key=active_key)
    st.session_state.current_provider = active_provider

# Sidebar Logs Layout
with st.sidebar:
    st.markdown('<div class="sidebar-header">🛡️ chart bot Engine</div>', unsafe_allow_html=True)
    st.caption(f"Reasoning Core: {active_provider.upper()} (llama-3.3-70b)")
    st.markdown("---")
    
    st.markdown('<div style="font-family: \'Outfit\', sans-serif; font-weight:600; font-size:1.1rem; margin-bottom:0.8rem; color:#e2e8f0;">🧠 Thought Stream</div>', unsafe_allow_html=True)
    
    # Empty placeholder to render the logs dynamically in real-time
    sidebar_log_placeholder = st.empty()
    
    st.markdown("---")
    
    # Simple Controls
    if st.button("Reset Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.latest_logs = []
        st.session_state.active_chart = None
        st.session_state.agent.clear_memory()
        st.rerun()

def render_sidebar_logs():
    """Renders the ReAct thought log list inside the sidebar placeholder."""
    with sidebar_log_placeholder.container():
        if st.session_state.latest_logs:
            for log in st.session_state.latest_logs:
                step = log.get("step", 1)
                if log["type"] == "thought":
                    st.markdown(f"""
                        <div class="log-card log-thought">
                            <div class="log-header"><span class="log-badge badge-thought">Step {step}: Think</span></div>
                            <div style="font-size:0.9rem; color:#cbd5e1; line-height:1.4;">{log["thought"]}</div>
                        </div>
                    """, unsafe_allow_html=True)
                elif log["type"] == "action":
                    params_str = json.dumps(log["parameters"])
                    st.markdown(f"""
                        <div class="log-card log-action">
                            <div class="log-header"><span class="log-badge badge-action">Step {step}: Act</span></div>
                            <div style="font-size:0.85rem; color:#fef3c7; margin-bottom:0.4rem;">Calling <b>{log["tool_name"]}</b>:</div>
                            <div class="code-container">{params_str}</div>
                        </div>
                    """, unsafe_allow_html=True)
                elif log["type"] == "observation":
                    st.markdown(f"""
                        <div class="log-card log-observation">
                            <div class="log-header"><span class="log-badge badge-observation">Step {step}: Observe</span></div>
                            <div style="font-size:0.85rem; color:#d1fae5; line-height:1.4; white-space:pre-wrap;">{log["result"]}</div>
                        </div>
                    """, unsafe_allow_html=True)
                elif log["type"] == "error":
                    st.error(f"Error in Step {step}: {log['error']}")
        else:
            st.info("Agent is currently idle. Enter a prompt to stream active steps.")

# Initial render of sidebar logs
render_sidebar_logs()

# Main UI Header
st.markdown("""
    <div class="hero-container">
        <div class="main-title">chart bot</div>
        <div class="subtitle">A zero-cost, ultra-premium Agentic AI running standard ReAct reasoning loops from scratch.</div>
    </div>
""", unsafe_allow_html=True)

# Render available tools in a clean visual layout
with st.expander("🛠️ Connected Tool Registry", expanded=False):
    st.markdown("""
    This agent automatically detects context and triggers the following tools:
    * 📊 **Chart Builder (`plot_chart`)**: Renders line, bar, and area charts dynamically.
    * 🧮 **Calculator**: Evaluates complex math expressions securely using Python AST libraries.
    * 📅 **Time Sync**: Returns real-time system clock values.
    * 📖 **Wikipedia Summary**: Pulls extracts from Wikipedia API.
    * 🌤️ **Simulated Weather**: Queries mock weather data for major cities.
    """)

# Warn the user if no keys are found
if not active_key:
    st.warning("⚠️ No API keys detected in your `.env` file. Please enter them in `.env` to start querying the agent.")

# Render Messages using Premium Custom HTML Bubbles
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
            <div style="display: flex; justify-content: flex-end; margin-bottom: 1.2rem;">
                <div style="background: rgba(139, 92, 246, 0.08); 
                            border: 1px solid rgba(139, 92, 246, 0.25); 
                            border-radius: 20px 20px 0px 20px; 
                            padding: 1.1rem 1.4rem; 
                            max-width: 75%; 
                            color: #f1f5f9; 
                            box-shadow: 0 4px 20px rgba(139, 92, 246, 0.06);">
                    <div style="font-weight: 700; font-size: 0.7rem; color: #a78bfa; margin-bottom: 0.4rem; text-transform: uppercase; letter-spacing: 0.08em;">User</div>
                    <div style="font-size: 0.98rem; line-height: 1.55;">{message["content"]}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style="display: flex; justify-content: flex-start; margin-bottom: 1.2rem;">
                <div style="background: rgba(30, 41, 59, 0.35); 
                            border: 1px solid rgba(255, 255, 255, 0.05); 
                            border-radius: 20px 20px 20px 0px; 
                            padding: 1.1rem 1.4rem; 
                            max-width: 75%; 
                            color: #f1f5f9; 
                            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25); 
                            backdrop-filter: blur(10px);">
                    <div style="font-weight: 700; font-size: 0.7rem; color: #ec4899; margin-bottom: 0.4rem; text-transform: uppercase; letter-spacing: 0.08em;">chart bot Agent</div>
                    <div style="font-size: 0.98rem; line-height: 1.55; white-space: pre-wrap;">{message["content"]}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Render historical chart if present
        if "chart" in message and message["chart"]:
            chart_info = message["chart"]
            chart_type = chart_info["chart_type"]
            data = chart_info["data"]
            x_label = chart_info["x_label"]
            y_label = chart_info["y_label"]
            
            try:
                df = pd.DataFrame(data)
                with st.container():
                    st.markdown(f"""
                        <div style="background: rgba(15, 23, 42, 0.4); 
                                    border: 1px solid rgba(255, 255, 255, 0.05); 
                                    border-radius: 16px; 
                                    padding: 1.2rem; 
                                    margin-bottom: 1.2rem; 
                                    box-shadow: 0 4px 25px rgba(0,0,0,0.3);
                                    backdrop-filter: blur(10px);">
                            <div style="font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 1rem; color: #a78bfa; margin-bottom: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em;">📊 Dynamic {chart_type.upper()} Chart</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if chart_type == "line":
                        st.line_chart(df, x=x_label, y=y_label)
                    elif chart_type == "bar":
                        st.bar_chart(df, x=x_label, y=y_label)
                    elif chart_type == "area":
                        st.area_chart(df, x=x_label, y=y_label)
            except Exception as e:
                st.error(f"Error rendering chart: {str(e)}")

# User Chat Input
if prompt := st.chat_input("Input query here..."):
    # 1. Render User message instantly
    st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; margin-bottom: 1.2rem;">
            <div style="background: rgba(139, 92, 246, 0.08); 
                        border: 1px solid rgba(139, 92, 246, 0.25); 
                        border-radius: 20px 20px 0px 20px; 
                        padding: 1.1rem 1.4rem; 
                        max-width: 75%; 
                        color: #f1f5f9; 
                        box-shadow: 0 4px 20px rgba(139, 92, 246, 0.06);">
                <div style="font-weight: 700; font-size: 0.7rem; color: #a78bfa; margin-bottom: 0.4rem; text-transform: uppercase; letter-spacing: 0.08em;">User</div>
                <div style="font-size: 0.98rem; line-height: 1.55;">{prompt}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Reset thought stream logs and active chart
    st.session_state.latest_logs = []
    st.session_state.active_chart = None
    render_sidebar_logs()
    
    # 2. Agent Execution Loop
    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        answer_placeholder = st.empty()
        
        try:
            # Run the agent ReAct loop generator
            agent_generator = st.session_state.agent.run(prompt)
            
            for event in agent_generator:
                if event["type"] == "thought_start":
                    # Add thought placeholder to start streaming into it
                    st.session_state.latest_logs.append({
                        "type": "thought",
                        "step": event["step"],
                        "thought": "🧠 thinking..."
                    })
                    render_sidebar_logs()
                    
                elif event["type"] == "thought_stream":
                    # Update thought text in real-time
                    step = event["step"]
                    for log in reversed(st.session_state.latest_logs):
                        if log["type"] == "thought" and log["step"] == step:
                            log["thought"] = event["thought"]
                            break
                    render_sidebar_logs()
                    
                    status_placeholder.markdown(f"""
                        <div style="background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.15); border-radius: 12px; padding: 0.8rem 1rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.6rem;">
                            <span style="font-size: 1.1rem; color: #a78bfa;">🧠</span>
                            <div style="font-size: 0.9rem; color: #c084fc;">Agent reasoning: <i>"{event['thought']}"</i></div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                elif event["type"] == "thought":
                    # Finalized thought block for this step
                    step = event["step"]
                    for log in reversed(st.session_state.latest_logs):
                        if log["type"] == "thought" and log["step"] == step:
                            log["thought"] = event["thought"]
                            break
                    render_sidebar_logs()
                    
                elif event["type"] == "action":
                    st.session_state.latest_logs.append(event)
                    render_sidebar_logs()
                    
                    status_placeholder.markdown(f"""
                        <div style="background: rgba(245, 158, 11, 0.05); border: 1px solid rgba(245, 158, 11, 0.15); border-radius: 12px; padding: 0.8rem 1rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.6rem;">
                            <span style="font-size: 1.1rem; color: #fbbf24;">🛠️</span>
                            <div style="font-size: 0.9rem; color: #fde047;">Triggering local tool: <b>{event['tool_name']}</b></div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                elif event["type"] == "observation":
                    st.session_state.latest_logs.append(event)
                    render_sidebar_logs()
                    
                    status_placeholder.markdown(f"""
                        <div style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.15); border-radius: 12px; padding: 0.8rem 1rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.6rem;">
                            <span style="font-size: 1.1rem; color: #34d399;">👁️</span>
                            <div style="font-size: 0.9rem; color: #a7f3d0;">Observing tool result...</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                elif event["type"] == "error":
                    st.session_state.latest_logs.append(event)
                    render_sidebar_logs()
                    
                    status_placeholder.markdown(f"""
                        <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; padding: 0.8rem 1rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.6rem;">
                            <span style="font-size: 1.1rem; color: #f87171;">❌</span>
                            <div style="font-size: 0.9rem; color: #fca5a5;">Execution Error: {event['error']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                elif event["type"] == "final_answer":
                    status_placeholder.empty()
                    
                    # Pop the generated chart from session state
                    chart_to_append = st.session_state.pop("active_chart", None)
                    
                    # Render final answer bubble
                    answer_placeholder.markdown(f"""
                        <div style="display: flex; justify-content: flex-start; margin-bottom: 1.2rem;">
                            <div style="background: rgba(30, 41, 59, 0.35); 
                                        border: 1px solid rgba(255, 255, 255, 0.05); 
                                        border-radius: 20px 20px 20px 0px; 
                                        padding: 1.1rem 1.4rem; 
                                        max-width: 75%; 
                                        color: #f1f5f9; 
                                        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25); 
                                        backdrop-filter: blur(10px);">
                                <div style="font-weight: 700; font-size: 0.7rem; color: #ec4899; margin-bottom: 0.4rem; text-transform: uppercase; letter-spacing: 0.08em;">chart bot Agent</div>
                                <div style="font-size: 0.98rem; line-height: 1.55; white-space: pre-wrap;">{event['answer']}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # If chart was generated, draw it in the UI right away
                    if chart_to_append:
                        chart_type = chart_to_append["chart_type"]
                        data = chart_to_append["data"]
                        x_label = chart_to_append["x_label"]
                        y_label = chart_to_append["y_label"]
                        
                        try:
                            df = pd.DataFrame(data)
                            st.markdown(f"""
                                <div style="background: rgba(15, 23, 42, 0.4); 
                                            border: 1px solid rgba(255, 255, 255, 0.05); 
                                            border-radius: 16px; 
                                            padding: 1.2rem; 
                                            margin-bottom: 1.2rem; 
                                            box-shadow: 0 4px 25px rgba(0,0,0,0.3);
                                            backdrop-filter: blur(10px);">
                                    <div style="font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 1rem; color: #a78bfa; margin-bottom: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em;">📊 Dynamic {chart_type.upper()} Chart</div>
                                </div>
                            """, unsafe_allow_html=True)
                            if chart_type == "line":
                                st.line_chart(df, x=x_label, y=y_label)
                            elif chart_type == "bar":
                                st.bar_chart(df, x=x_label, y=y_label)
                            elif chart_type == "area":
                                st.area_chart(df, x=x_label, y=y_label)
                        except Exception as ce:
                            st.error(f"Error rendering chart: {str(ce)}")
                            
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": event["answer"],
                        "chart": chart_to_append
                    })
                
        except Exception as e:
            status_placeholder.empty()
            error_msg = f"Failed to complete ReAct loop. Error: {str(e)}"
            answer_placeholder.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            
    st.rerun()
