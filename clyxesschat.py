import streamlit as st
from groq import Groq
from supabase import create_client
import datetime
import uuid
import requests
import base64

st.set_page_config(page_title="ClyxessChat AI", layout="wide", page_icon="💻")

# ============ 1. CSS - MOBILE + DESKTOP ============
st.markdown("""
<style>
 .stApp {background: #0a0a0a;}
 .main {max-width: 900px; margin: auto;}

  /* MOBILE HEADER */
 .mobile-header {
      display: flex;
      justify-content: space-between;
      padding: 20px;
  }
 .mobile-logo-center {
      text-align: center;
      margin-top: 20vh;
  }
 .mobile-logo-center img {width: 120px;}
 .mobile-logo-center h1 {color: white; font-size: 28px;}
 .mobile-logo-center h1 span {color: #00aaff;}

  /* DESKTOP HEADER */
 .desktop-header {
      display: none;
      justify-content: space-between;
      padding: 20px 40px;
      color: #ccc;
  }
 .desktop-header a {color: #ccc; text-decoration: none; margin: 0 15px;}
 .desktop-header a:hover {color: white;}

  /* INPUT PILL */
  [data-testid="stChatInput"] {
      position: fixed;
      bottom: 30px;
      left: 50%;
      transform: translateX(-50%);
      width: 90%;
      max-width: 750px;
      background: #e5e5e5;
      border-radius: 30px;
      padding: 5px;
  }
  [data-testid="stChatInput"] textarea {
      background: transparent!important;
      color: black!important;
      border: none!important;
  }

  /* ACTION BAR */
 .action-bar {display: flex; gap: 20px; padding: 10px 0; color: #888;}

  /* RESPONSIVE */
  @media (min-width: 768px) {
     .mobile-header,.mobile-logo-center {display: none;}
     .desktop-header {display: flex;}
  }
  #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============ 2. HEADER - MOBILE VS DESKTOP ============
# MOBILE
st.markdown("""
<div class="mobile-header">
    <div style="font-size:30px; color:white;">☰</div>
    <div style="width:38px; height:38px; border-radius:50%; background:#444; border:2px solid white;"></div>
</div>
<div class="mobile-logo-center">
    <img src="https://i.imgur.com/YOUR_LOGO.png"> <!-- Yaha apna logo daal -->
    <h1><span>Clyxess</span>Chat AI</h1>
</div>
""", unsafe_allow_html=True)

# DESKTOP
st.markdown("""
<div class="desktop-header">
    <div>
        <a href="#">Software Project</a>
        <a href="#">Resources</a>
        <a href="#">Plan Upgrade</a>
        <a href="#">Case Studies</a>
    </div>
    <div style="width:38px; height:38px; border-radius:50%; background:#444; border:2px solid white;"></div>
</div>
""", unsafe_allow_html=True)

if st.button("➕ New Chat"):
    st.session_state.messages = []
    st.rerun()

# ============ 3. BACKEND - WAHI HAI ============
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

# ============ 4. CHAT + ACTION BAR ============
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            b64 = base64.b64encode(message["content"].encode()).decode()
            st.markdown(f'<div class="action-bar"><span onclick="navigator.clipboard.writeText(atob(\'{b64}\'))">📋</span> 👍 👎 🔊 🔗 ⋮</div>', unsafe_allow_html=True)

# ============ 5. BOTTOM INPUT WITH + MIC SEND ============
col1, col2, col3, col4 = st.columns([1,8,1,1])
with col1:
    if st.button("+"): st.session_state.show_upload = not st.session_state.show_upload
with col2:
    prompt = st.chat_input("Ask ClyxessChat")
with col3:
    st.button("🎤")
with col4:
    st.button("↑")

if st.session_state.show_upload:
    c1, c2 = st.columns(2)
    with c1: uploaded_file = st.file_uploader("Upload", label_visibility="collapsed")
    with c2: camera_photo = st.camera_input("Camera", label_visibility="collapsed")
    if uploaded_file or camera_photo: prompt = "Is image ko analyze karke code fix karke do"

# ============ 6. AI LOGIC ============
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Thinking..."):
        if is_suicide_risk(prompt):
            response = "**India Help: AASRA 91-9820466726, Emergency: 112**"
        else:
            search_context = search_tavily(prompt) if "code" in prompt.lower() else ""
            system_prompt = f"You are ClyxessChat AI Code Engine. Give multi-file code. Use: {search_context}. Reply in Hinglish."
            messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, max_tokens=16000)
            response = res.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
