import streamlit as st
from groq import Groq
from supabase import create_client
import datetime
import uuid
import requests
import base64

st.set_page_config(page_title="ClyxessChat AI", layout="wide", page_icon="💻")

# ============ 1. CSS - PROFESSIONAL GREY ICONS ============
st.markdown("""
<style>
.stApp {background: #212121;}
.main {max-width: 850px; margin: auto;}

  /* HEADER */
.header-desktop {display: none; justify-content: space-between; padding: 16px 40px; color: #ECECEC; font-size: 14px;}
.header-mobile {display: flex; justify-content: space-between; padding: 16px 20px;}
  @media (min-width: 768px) {.header-mobile {display: none;}.header-desktop {display: flex;}}

  /* CENTER LOGO */
.center-wrap {text-align: center; margin-top: 15vh; color: #ECECEC;}
.center-wrap h1 {font-size: 32px; font-weight: 600;}
.center-wrap h1 span {color: #10a37f;}

  /* INPUT PILL */
  [data-testid="stChatInput"] {
      position: fixed;
      bottom: 30px;
      left: 50%;
      transform: translateX(-50%);
      width: 90%;
      max-width: 768px;
      background: #2F2F2F;
      border-radius: 28px;
      border: 1px solid #565656;
  }
  [data-testid="stChatInput"] textarea {
      background: transparent!important;
      color: #ECECEC!important;
  }

  /* ACTION BAR - CHATGPT STYLE */
.action-bar {display: flex; gap: 12px; padding: 8px 0 20px 0;}
.action-icon {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: #A3A3A3;
      transition: 0.2s;
  }
.action-icon:hover {background: #2F2F2F; color: #ECECEC;}
  /* SVG Icons */
.action-icon svg {width: 18px; height: 18px; fill: currentColor;}
</style>
""", unsafe_allow_html=True)

# ============ 2. SVG ICONS - GREY PROFESSIONAL ============
COPY_ICON = """<svg viewBox="0 0 24 24"><path d="M16 1H4c-1.1 0-2.9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2.9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>"""
LIKE_ICON = """<svg viewBox="0 0 24 24"><path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/></svg>"""
DISLIKE_ICON = """<svg viewBox="0 0 24 24"><path d="M15 3H6c-.83 0-1.54.5-1.84 1.22l-3.02 7.05c-.09.23-.14.47-.14.73v2c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0.41.17.79.44 1.06L9.83 23l6.59-6.59c.36-.36.58-.86.58-1.41V5c0-1.1-.9-2-2-2zm4 0v12h4V3h-4z"/></svg>"""
SHARE_ICON = """<svg viewBox="0 0 24 24"><path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0.24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92 1.61 0 2.92-1.31 2.92-2.92s-1.31-2.92-2.92-2.92z"/></svg>"""
MORE_ICON = """<svg viewBox="0 0 24 24"><path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2.9-2 2.9 2 2 2zm0 2c-1.1 0-2.9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2.9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/></svg>"""

# ============ 3. HEADER ============
st.markdown('<div class="header-desktop"><div><a>Software Project</a><a>Resources</a><a>Plan Upgrade</a><a>Case Studies</a></div><div style="width:32px; height:32px; border-radius:50%; background:#444;"></div></div>', unsafe_allow_html=True)
st.markdown('<div class="header-mobile"><div style="font-size:24px; color:#ECECEC;">☰</div><div style="width:32px; height:32px; border-radius:50%; background:#444;"></div></div>', unsafe_allow_html=True)

if len(st.session_state.get("messages", [])) == 0:
    st.markdown('<div class="center-wrap"><h1><span>Clyxess</span>Chat AI</h1></div>', unsafe_allow_html=True)

if st.button("➕ New Chat"):
    st.session_state.messages = []
    st.rerun()

# ============ 4. BACKEND ============
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

# ============ 5. CHAT DISPLAY ============
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            b64 = base64.b64encode(message["content"].encode()).decode()
            st.markdown(f"""
            <div class="action-bar">
                <div class="action-icon" onclick="navigator.clipboard.writeText(atob('{b64}'))">{COPY_ICON}</div>
                <div class="action-icon">{LIKE_ICON}</div>
                <div class="action-icon">{DISLIKE_ICON}</div>
                <div class="action-icon">{SHARE_ICON}</div>
                <div class="action-icon">{MORE_ICON}</div>
            </div>
            """, unsafe_allow_html=True)

# ============ 6. INPUT ============
if prompt := st.chat_input("Ask ClyxessChat"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Thinking..."):
        if is_suicide_risk(prompt):
            response = "Main samajh sakta hu tum takleef me ho.\n**India Help: AASRA 91-9820466726, Emergency: 112**"
        else:
            search_context = search_tavily(prompt) if "code" in prompt.lower() else ""
            system_prompt = f"You are ClyxessChat AI Code Engine. Give multi-file code. Use: {search_context}. Reply in Hinglish."
            messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, max_tokens=16000)
            response = res.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
