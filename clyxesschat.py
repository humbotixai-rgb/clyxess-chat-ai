import streamlit as st
import os
import uuid
from dotenv import load_dotenv
from groq import Groq
from supabase import create_client

load_dotenv()
ACCENT = "#173BE8"

# Init Clients
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

st.set_page_config(page_title="ClyxessChat AI", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

# CSS
st.markdown(f"""
<style>
.stApp {{background: #0E1117; color: #FAFAFA; font-family: 'Inter', sans-serif;}}
[data-testid="stSidebar"] {{background: #1A1D23; border-right: 1px solid #2A2E37;}}
.main.block-container {{max-width: 900px; padding-top: 2rem;}}
h1 {{color: {ACCENT}; text-align: center;}}
.chat-message {{padding: 16px; border-radius: 12px; margin-bottom: 12px; border: 1px solid #2A2E37; line-height: 1.6;}}
.user-message {{background: {ACCENT}; color: white;}}
.ai-message {{background: #1F232B;}}
.file-header {{color: #58A6FF; font-weight: 700; font-size: 14px; margin: 20px 0 8px 0; font-family: 'Monaco', monospace;}}
pre {{background: #0D1117!important; border: 1px solid #30363D; border-radius: 8px; padding: 16px; overflow-x: auto;}}
.stButton>button {{border-radius: 8px; font-weight: 600;}}
.send-btn button {{background: {ACCENT}!important; color: white!important; border: none!important;}}
.send-btn button:hover {{background: #0F2BC4!important;}}
.new-chat-btn button {{background: {ACCENT}!important; color: white!important; width: 100%!important; border: none!important;}}
.action-btn button {{background: transparent!important; border: 1px solid #30363D!important; color: #8B949E!important; font-size: 12px!important; padding: 4px 10px!important;}}
.action-btn button:hover {{border-color: {ACCENT}!important; color: {ACCENT}!important;}}
</style>
""", unsafe_allow_html=True)

# Supabase Functions
def get_session_id():
    return str(uuid.uuid4())

def save_message(session_id, role, content):
    try:
        supabase.table("chat_history").insert({"session_id": session_id, "role": role, "content": content}).execute()
    except Exception as e:
        st.error(f"DB Error: {e}")

def load_history(session_id):
    try:
        data = supabase.table("chat_history").select("*").eq("session_id", session_id).order("created_at").execute()
        return [{"role": i["role"], "content": i["content"]} for i in data.data]
    except:
        return []

# Groq AI
SYSTEM_PROMPT = """You are ClyxessChat AI. AI Code Engine for Websites, Apps & Software.
You are a Senior Python, Streamlit, Groq API and Supabase Engineer.

STRICT RULES:
1. NEVER return architecture, explanations only, or file lists. ALWAYS return complete working code.
2. NEVER use TODO, placeholders, or "add code here".
3. Follow this exact output format for every file:
━━━━━━━━━━
📁 FILE: filename.ext
[COMPLETE WORKING CODE]
━━━━━━━━━━
4. Step 1: Determine required files. Step 2: Generate complete code for every file. Step 3: Ensure all files work together.
5. If project is large, continue with PART 2, PART 3 until 100% complete.
6. If user says "Create grocery website" assume: Modern UI, Responsive, Product Cards, Search, Cart, Contact Page, Mobile Support.
7. Support Hindi, Hinglish, English. Maintain conversation context."""

def get_ai_response(messages):
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=4096
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# Session State
if "session_id" not in st.session_state:
    st.session_state.session_id = get_session_id()
if "messages" not in st.session_state:
    st.session_state.messages = load_history(st.session_state.session_id)

# Sidebar
with st.sidebar:
    st.markdown("### ClyxessChat AI")
    st.caption("AI Code Engine for Websites, Apps & Software")
    if st.button("➕ New Chat", use_container_width=True, key="new_chat"):
        st.session_state.session_id = get_session_id()
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.markdown("### Chat History")
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.caption(f"💬 {msg['content'][:40]}...")

# Main UI
st.markdown("<h1>ClyxessChat AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8B949E;'>AI Code Engine for Websites, Apps & Software</p>", unsafe_allow_html=True)

# Display Chat
for idx, message in enumerate(st.session_state.messages):
    role_class = "user-message" if message["role"] == "user" else "ai-message"
    st.markdown(f"<div class='chat-message {role_class}'>{message['content']}</div>", unsafe_allow_html=True)

    if message["role"] == "assistant":
        col1, col2, col3, col4 = st.columns([1,1,1,7])
        with col1:
            if st.button("📋 Copy", key=f"copy_{idx}"):
                st.code(message["content"], language="markdown")
        with col2:
            if st.button("👍", key=f"like_{idx}"):
                st.toast("Thanks for feedback!")
        with col3:
            if st.button("👎", key=f"dislike_{idx}"):
                st.toast("Feedback recorded")

# Input Area
st.markdown("---")
col1, col2 = st.columns([8,1])
with col1:
    user_input = st.text_area("Message", key="user_input", height=70, label_visibility="collapsed", placeholder="Ask me to build anything: Create a todo app, Fix this bug, Explain this code...")
with col2:
    send_clicked = st.button("Send", key="send", use_container_width=True)

if send_clicked and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    save_message(st.session_state.session_id, "user", user_input)

    with st.spinner("ClyxessAI is coding..."):
        response = get_ai_response(st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": response})
    save_message(st.session_state.session_id, "assistant", response)
    st.rerun()
