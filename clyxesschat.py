import streamlit as st
import os
import time
from datetime import datetime
from supabase import create_client
from groq import Groq, RateLimitError

st.set_page_config(page_title="ClyxessChat AI", page_icon="💙", layout="wide")

# ========== CHATGPT STYLE CSS - NO HEADER/FOOTER ==========
st.markdown("""
<style>
  #MainMenu {visibility: hidden;} /* Top right menu hide */
  footer {visibility: hidden;} /* "Made with Streamlit" hide */
  header {visibility: hidden;} /* Top header hide */

 .stApp {background-color: #0E1117;}

  [data-testid="stSidebar"] {
        background-color: #111419;
        border-right: 1px solid #2A2E36;
    }
  [data-testid="stSidebar"] * {color: #FFFFFF!important;}

 .stChatMessage {background: transparent; padding: 1.5rem 0; border-bottom: 1px solid #1F2329;}
 .stChatMessage p,.stChatMessage div,.stMarkdown {color: #FFFFFF!important; font-size: 16px;}

  [data-testid="stChatMessage"]:nth-child(odd) {background-color: #1A1D23;}

 .stChatInput input {
        color: #FFFFFF!important;
        background-color: #1A1D23!important;
        border: 1px solid #3A3F4B!important;
        border-radius: 12px!important;
    }
 .stChatInput input:focus {border: 1px solid #173BE8!important; box-shadow: 0 0 0 2px #173BE8;}

 .stButton>button {
        background-color: #173BE8; color: white; border-radius: 8px;
        border: none; font-weight: 600; width: 100%;
    }
 .stButton>button:hover {background-color: #1E4CFF;}
</style>
""", unsafe_allow_html=True)

# ========== CONNECT ==========
@st.cache_resource
def init_connections():
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return supabase, groq_client

supabase, client = init_connections()

# ========== SESSION ==========
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {"New Chat": []}
if "current_session" not in st.session_state:
    st.session_state.current_session = "New Chat"

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("### 💙 ClyxessChat AI")
    st.caption("AI Code Engine for Websites, Apps & Software")
    st.markdown("<hr style='border: 1px solid #2A2E36;'>", unsafe_allow_html=True)

    if st.button("+ New Chat", use_container_width=True):
        new_name = f"Chat {len(st.session_state.chat_sessions) + 1}"
        st.session_state.chat_sessions[new_name] = []
        st.session_state.current_session = new_name
        st.rerun()

    st.markdown("### Chat History")
    for session_name in st.session_state.chat_sessions.keys():
        if st.button(session_name, key=session_name, use_container_width=True):
            st.session_state.current_session = session_name
            st.rerun()

# ========== MAIN CHAT ==========
# Header hata diya
# st.title("ClyxessChat AI") <- ye line hata di

# Chat display
for idx, msg in enumerate(st.session_state.chat_sessions[st.session_state.current_session]):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            c1, c2, c3 = st.columns([0.1, 0.1, 0.8])
            with c1: st.button("📋", key=f"copy_{idx}")
            with c2: st.button("👍", key=f"like_{idx}")
            with c3: st.button("👎", key=f"dislike_{idx}")

# Input
if prompt := st.chat_input("Message ClyxessChat AI..."):
    st.session_state.chat_sessions[st.session_state.current_session].append(
        {"role": "user", "content": prompt, "timestamp": datetime.now().isoformat()}
    )

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            system_prompt = """You are ClyxessChat AI, an expert coding assistant.
Rules: 1. Always generate actual working code. 2. Never use TODO or placeholders.
3. Format: ━━━━━━━━━━ 📁 FILE: filename.ext [FULL WORKING CODE] ━━━━━━━━━━"""

            messages = [{"role": "system", "content": system_prompt}]
            for m in st.session_state.chat_sessions[st.session_state.current_session]:
                messages.append({"role": m["role"], "content": m["content"]})

            try:
                completion = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=messages, temperature=0.7, max_tokens=4000,
                )
                response = completion.choices[0].message.content

            except RateLimitError:
                st.error("⚠️ Groq API Limit Khatam. 1 minute ruko ya dusri API key use karo.")
                response = "Rate limit exceeded. Please try again in 60 seconds."
                time.sleep(1)

            except Exception as e:
                st.error(f"Error: {e}")
                response = "Kuch error aa gaya. Dobara try karo."

            st.markdown(response)

    if "Rate limit" not in response:
        st.session_state.chat_sessions[st.session_state.current_session].append(
            {"role": "assistant", "content": response, "timestamp": datetime.now().isoformat()}
        )
        supabase.table("messages").insert({
            "session_name": st.session_state.current_session,
            "user_message": prompt, "ai_response": response,
            "created_at": datetime.now().isoformat()
        }).execute()

    st.rerun()
