import streamlit as st
from groq import Groq
from supabase import create_client
import datetime
import uuid
import requests
import base64

st.set_page_config(page_title="ClyxessChat AI", layout="wide", page_icon="💻")

# ============ 1. CSS - PROFESSIONAL DARK ============
st.markdown("""
<style>
.stApp {background: #212121;}
  /* SIDEBAR */
  [data-testid="stSidebar"] {background: #171717; border-right: 1px solid #2F2F2F;}
  [data-testid="stSidebar"] button {background: transparent; color: #ECECEC; border: 1px solid #565656; border-radius: 8px; text-align: left;}
  [data-testid="stSidebar"] button:hover {background: #2F2F2F;}

  /* HEADER */
.header {display: flex; justify-content: space-between; padding: 12px 20px; color: #ECECEC;}
.header a {color: #B4B4B4; text-decoration: none; margin: 0 12px; font-size: 14px;}
.header a:hover {color: white;}

  /* CENTER */
.center-wrap {text-align: center; margin-top: 12vh; color: #ECECEC;}
.center-wrap h1 {font-size: 32px; font-weight: 600;}
.center-wrap h1 span {color: #10a37f;}
.center-wrap img {width: 80px; margin-bottom: 10px;}

  /* INPUT PILL WITH + MIC SEND */
.input-wrapper {
      position: fixed;
      bottom: 30px;
      left: 50%;
      transform: translateX(-50%);
      width: 90%;
      max-width: 768px;
      background: #2F2F2F;
      border-radius: 28px;
      border: 1px solid #565656;
      display: flex;
      align-items: center;
      padding: 6px 10px;
  }
.input-wrapper input {flex: 1; background: transparent; border: none; color: #ECECEC; outline: none; padding: 10px;}
.input-icon {width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; border-radius: 50%; cursor: pointer; color: #B4B4B4;}
.input-icon:hover {background: #3E3E3E; color: white;}

  /* ACTION BAR */
.action-bar {display: flex; gap: 8px; padding: 8px 0;}
.action-icon {width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #A3A3A3;}
.action-icon:hover {background: #2F2F2F; color: #ECECEC;}
.action-icon svg {width: 18px; height: 18px; fill: currentColor;}
</style>
""", unsafe_allow_html=True)

# ============ 2. SVG ICONS ============
PLUS_ICON = """<svg viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>"""
MIC_ICON = """<svg viewBox="0 0 24 24"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.49 6-3.31 6-6.72h-1.7z"/></svg>"""
SEND_ICON = """<svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>"""
COPY_ICON = """<svg viewBox="0 0 24 24"><path d="M16 1H4c-1.1 0-2.9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2.9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>"""
LIKE_ICON = """<svg viewBox="0 0 24 24"><path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/></svg>"""
DISLIKE_ICON = """<svg viewBox="0 0 24 24"><path d="M15 3H6c-.83 0-1.54.5-1.84 1.22l-3.02 7.05c-.09.23-.14.47-.14.73v2c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0.41.17.79.44 1.06L9.83 23l6.59-6.59c.36-.36.58-.86.58-1.41V5c0-1.1-.9-2-2-2zm4 0v12h4V3h-4z"/></svg>"""

# ============ 3. SIDEBAR ============
with st.sidebar:
    st.markdown('<h2 style="color:#ECECEC;">💻 ClyxessChat</h2>', unsafe_allow_html=True)
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
    st.markdown('<hr style="border-color:#2F2F2F;">', unsafe_allow_html=True)
    st.markdown('<p style="color:#A3A3A3; font-size:12px;">CHAT HISTORY</p>', unsafe_allow_html=True)
    # Yaha baad me Supabase se chat history load karenge

# ============ 4. HEADER - LOGIN BUTTON ============
col1, col2 = st.columns([10,1])
with col1:
    st.markdown('<div class="header"><a>Software Project</a><a>Resources</a><a>Plan Upgrade</a><a>Case Studies</a></div>', unsafe_allow_html=True)
with col2:
    if st.button("Login", key="login_btn"): # ISPE BAAD ME GOOGLE LOGIN JODNA
        st.info("Login popup yaha khulega")

# ============ 5. BACKEND ============
def search_tavily(query):
    try:
        res = requests.post("https://api.tavily.com/search", json={"api_key": st.secrets["TAVILY_API_KEY"], "query": query, "max_results": 3})
        return "\n".join([f"- {r['title']}: {r['content']}" for r in res.json().get("results", [])])
    except: return ""

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.show_upload = False

# ============ 6. CHAT DISPLAY ============
if len(st.session_state.messages) == 0:
    st.markdown('<div class="center-wrap"><img src="https://i.imgur.com/YOUR_LOGO.png"><h1><span>Clyxess</span>Chat AI</h1></div>', unsafe_allow_html=True)

for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            b64 = base64.b64encode(message["content"].encode()).decode()
            st.markdown(f'<div class="action-bar"><div class="action-icon" onclick="navigator.clipboard.writeText(atob(\'{b64}\'))">{COPY_ICON}</div><div class="action-icon">{LIKE_ICON}</div><div class="action-icon">{DISLIKE_ICON}</div></div>', unsafe_allow_html=True)

# ============ 7. INPUT WITH + CAMERA UPLOAD ============
st.markdown('<div class="input-wrapper">', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns([1,10,1,1])
with c1:
    if st.button(PLUS_ICON, key="plus"):
        st.session_state.show_upload = not st.session_state.show_upload
with c2:
    prompt = st.chat_input("Ask ClyxessChat", label_visibility="collapsed")
with c3:
    st.button(MIC_ICON, key="mic")
with c4:
    st.button(SEND_ICON, key="send")
st.markdown('</div>', unsafe_allow_html=True)

# + CLICK PE CAMERA + UPLOAD
if st.session_state.show_upload:
    u1, u2, u3 = st.columns(3)
    with u1: uploaded_file = st.file_uploader("📁 Upload", type=["png","jpg","pdf","py","txt"], label_visibility="collapsed")
    with u2: camera_photo = st.camera_input("📷 Camera", label_visibility="collapsed")
    with u3: st.button("❌ Close", on_click=lambda: st.session_state.update(show_upload=False))

    if uploaded_file or camera_photo:
        prompt = "Is image/file ko analyze karke batao aur code fix karke do"

# ============ 8. AI LOGIC ============
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Thinking..."):
        search_context = search_tavily(prompt) if "code" in prompt.lower() else ""
        system_prompt = f"You are ClyxessChat AI Code Engine. Give multi-file code. Use: {search_context}. Reply in Hinglish."
        messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, max_tokens=16000)
        response = res.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
