import streamlit as st
from groq import Groq
import datetime
import uuid
import requests
import base64

st.set_page_config(page_title="ClyxessChat AI", layout="wide", page_icon="💻")

# ============ CSS ============
st.markdown("""
<style>
 .stApp {background: #000;}
 .main {max-width: 800px; margin: auto;}

  /* Har message ke neeche action bar */
 .action-bar {
      display: flex;
      gap: 20px;
      padding: 5px 0 20px 0;
      color: #888;
      font-size: 18px;
  }
 .action-bar span {cursor: pointer;}
 .action-bar span:hover {color: white;}

  /* Bottom Input Pill */
  [data-testid="stChatInput"] {
      position: fixed;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      width: 90%;
      max-width: 700px;
      background: #2a2a2a;
      border-radius: 25px;
      border: 1px solid #444;
  }
  [data-testid="stChatInput"] textarea {
      background: transparent!important;
      color: white!important;
  }
</style>
""", unsafe_allow_html=True)

# ============ FUNCTIONS ============
def search_tavily(query):
    try:
        res = requests.post("https://api.tavily.com/search", json={"api_key": st.secrets["TAVILY_API_KEY"], "query": query})
        return "\n".join([f"- {r['title']}: {r['content']}" for r in res.json().get("results", [])])
    except: return ""

def is_suicide_risk(text):
    return any(word in text.lower() for word in ["suicide", "marna", "khatam"])

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.show_upload = False

# ============ TOP BAR ============
st.markdown("""
<div style="display:flex; justify-content:space-between; padding:15px 20px; color:white;">
    <div>☰</div><div style="width:35px; height:35px; border-radius:50%; background:#333;"></div>
</div>
""", unsafe_allow_html=True)

# ============ CHAT DISPLAY WITH ACTION BAR ============
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # SIRF AI MESSAGE KE NEECHE ACTION BAR
        if message["role"] == "assistant":
            col1, col2, col3, col4, col5, col6 = st.columns([1,1,1,1,1,8])
            with col1:
                # COPY
                b64 = base64.b64encode(message["content"].encode()).decode()
                st.markdown(f'<span onclick="navigator.clipboard.writeText(atob(\'{b64}\'))">📋</span>', unsafe_allow_html=True)
            with col2:
                st.markdown('<span>👍</span>', unsafe_allow_html=True)
            with col3:
                st.markdown('<span>👎</span>', unsafe_allow_html=True)
            with col4:
                st.markdown('<span>🔊</span>', unsafe_allow_html=True) # TTS baad me jodenge
            with col5:
                st.markdown('<span>🔗</span>', unsafe_allow_html=True)
            with col6:
                st.markdown('<span>⋮</span>', unsafe_allow_html=True)

# ============ BOTTOM INPUT + BUTTONS ============
col1, col2, col3 = st.columns([1,10,1])
with col1:
    if st.button("+", key="plus"):
        st.session_state.show_upload = not st.session_state.show_upload
with col2:
    prompt = st.chat_input("Reply to ClyxessChat")
with col3:
    st.button("🎤", key="mic")

# + CLICK PE UPLOAD/CAMERA
if st.session_state.show_upload:
    c1, c2 = st.columns(2)
    with c1: uploaded_file = st.file_uploader("📁 Upload", label_visibility="collapsed")
    with c2: camera_photo = st.camera_input("📷", label_visibility="collapsed")
    if uploaded_file or camera_photo:
        prompt = "Is image ko dekho aur iske hisaab se code/bug fix karke do"

# ============ AI LOGIC ============
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Thinking..."):
        if is_suicide_risk(prompt):
            response = """Main samajh sakta hu tum takleef me ho.
**India Help: AASRA 91-9820466726, Emergency: 112**"""
        else:
            search_context = search_tavily(prompt) if "code" in prompt.lower() else ""
            system_prompt = f"You are ClyxessChat AI. Code Engine. Give multi-file code. Use live info: {search_context}. Reply in Hinglish."
            messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, max_tokens=16000)
            response = res.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
