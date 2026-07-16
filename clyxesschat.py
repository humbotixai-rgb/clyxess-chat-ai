import streamlit as st
import os
from datetime import datetime
from supabase import create_client
from groq import Groq

# ========== CONFIG ==========
st.set_page_config(
    page_title="ClyxessChat AI",
    page_icon="💙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme + Accent Color #173BE8
st.markdown("""
<style>
   .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
   .stChatMessage {
        background-color: #1A1D23;
        border-radius: 12px;
        padding: 1rem;
    }
   .stButton>button {
        background-color: #173BE8;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
    }
   .stButton>button:hover {
        background-color: #1E4CFF;
    }
   .copy-btn,.feedback-btn {
        background: #262730;
        border: 1px solid #3A3F4B;
        border-radius: 6px;
        padding: 0.3rem 0.6rem;
        margin-right: 0.5rem;
        cursor: pointer;
        color: #FAFAFA;
    }
   .feedback-btn.active {
        background: #173BE8;
    }
    h1, h2, h3 {
        color: #173BE8;
    }
</style>
""", unsafe_allow_html=True)

# ========== CONNECT SERVICES ==========
@st.cache_resource
def init_connections():
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return supabase, groq_client

supabase, client = init_connections()

# ========== SESSION STATE ==========
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {"New Chat": []}
if "current_session" not in st.session_state:
    st.session_state.current_session = "New Chat"
if "feedback" not in st.session_state:
    st.session_state.feedback = {}

# ========== SIDEBAR ==========
with st.sidebar:
    st.title("💙 ClyxessChat AI")
    st.caption("AI Code Engine for Websites, Apps & Software")
    st.divider()

    if st.button("+ New Chat", use_container_width=True):
        new_name = f"Chat {len(st.session_state.chat_sessions) + 1}"
        st.session_state.chat_sessions[new_name] = []
        st.session_state.current_session = new_name
        st.rerun()

    st.subheader("Chat History")
    for session_name in st.session_state.chat_sessions.keys():
        if st.button(session_name, key=session_name, use_container_width=True):
            st.session_state.current_session = session_name
            st.rerun()

# ========== HEADER ==========
st.title("💙 ClyxessChat AI")
st.caption("AI Code Engine for Websites, Apps & Software")

# ========== CHAT DISPLAY ==========
chat_container = st.container()

with chat_container:
    for idx, msg in enumerate(st.session_state.chat_sessions[st.session_state.current_session]):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            if msg["role"] == "assistant":
                col1, col2, col3, col4 = st.columns([1,1,1,10])
                msg_id = f"{st.session_state.current_session}_{idx}"

                with col1:
                    if st.button("📋", key=f"copy_{msg_id}"):
                        st.toast("Copied to clipboard!")

                with col2:
                    btn_class = "active" if st.session_state.feedback.get(msg_id) == "like" else ""
                    if st.button("👍", key=f"like_{msg_id}"):
                        st.session_state.feedback[msg_id] = "like"

                with col3:
                    btn_class = "active" if st.session_state.feedback.get(msg_id) == "dislike" else ""
                    if st.button("👎", key=f"dislike_{msg_id}"):
                        st.session_state.feedback[msg_id] = "dislike"

# ========== CHAT INPUT ==========
if prompt := st.chat_input("Ask me to generate code, fix bugs, explain anything..."):
    # Add user message
    st.session_state.chat_sessions[st.session_state.current_session].append({
        "role": "user",
        "content": prompt,
        "timestamp": datetime.now().isoformat()
    })
    st.rerun()

# Process AI response
if st.session_state.chat_sessions[st.session_state.current_session]:
    last_msg = st.session_state.chat_sessions[st.session_state.current_session][-1]
    if last_msg["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("Generating code..."):
                system_prompt = """You are ClyxessChat AI, an expert coding assistant for developers and students.
Rules:
1. Always generate actual working code. Never give only architecture or file names.
2. Never use TODO or placeholders. Never say "add code here".
3. If user asks for a project, provide complete code for all required files.
4. Use format: ━━━━━━━━━━ 📁 FILE: filename.ext [FULL WORKING CODE] ━━━━━━━━━━━━━━━━━━
5. Explain code clearly after generating it."""

                messages = [{"role": "system", "content": system_prompt}]
                for m in st.session_state.chat_sessions[st.session_state.current_session]:
                    messages.append({"role": m["role"], "content": m["content"]})

                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=4000,
                )
                response = completion.choices[0].message.content
                st.markdown(response)

        # Save AI response
        st.session_state.chat_sessions[st.session_state.current_session].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })

        # Save to Supabase
        try:
            supabase.table("messages").insert({
                "session_name": st.session_state.current_session,
                "user_message": last_msg["content"],
                "ai_response": response,
                "created_at": datetime.now().isoformat()
            }).execute()
        except Exception as e:
            st.error(f"DB Error: {e}")

        st.rerun()
