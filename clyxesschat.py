import streamlit as st
from groq import Groq
from supabase import create_client, Client
import datetime
import uuid
import requests
import re

st.set_page_config(page_title="ClyxessChat AI", layout="wide", page_icon="💻")

# ============ 1. CSS - MOBILE + DESKTOP RESPONSIVE ============
st.markdown("""
<style>
    /* Center Container */
   .main {max-width: 900px; margin: auto; padding: 1rem;}

    /* Header like your screenshot */
   .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 20px;
        border-bottom: 1px solid #333;
        position: sticky;
        top: 0;
        background: #0a0a0a;
        z-index: 999;
    }
   .header h1 {color: #fff; font-size: 20px; margin: 0;}
   .header nav a {color: #aaa; text-decoration: none; margin: 0 12px; font-size: 14px;}
   .header nav a:hover {color: #fff;}

    /* Chat Input - Bottom me chipka hua */
    [data-testid="stChatInput"] {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 800px;
        background: #2a2a2a;
        border-radius: 20px;
        border: 1px solid #444;
    }

    /* Code Block */
   .stCodeBlock {border-radius: 10px; background: #1e1e1e!important; max-height: 600px; overflow-y: auto;}

    /* Mobile Hide Nav */
    @media (max-width: 768px) {
       .header nav {display: none;}
       .header h1 {font-size: 16px;}
    }

    /* Sidebar */
    [data-testid="stSidebar"] {background-color: #111;}
</style>
""", unsafe_allow_html=True)

# ============ 2. HEADER - TERE SCREENSHOT JAISA ============
col1, col2, col3 = st.columns([3,4,1])
with col1:
    st.markdown("### 💻 ClyxessChat AI")
with col2:
    st.markdown("<nav><a href='#'>Software Project</a> <a href='#'>Resources</a> <a href='#'>Plan Upgrade</a></nav>", unsafe_allow_html=True)
with col3:
    st.markdown("👤")

# ============ 3. TAVILY SEARCH FUNCTION ============
def search_tavily(query):
    try:
        api_key = st.secrets["TAVILY_API_KEY"] #.streamlit/secrets me daalna
        url = "https://api.tavily.com/search"
        payload = {"api_key": api_key, "query": query, "max_results": 3}
        res = requests.post(url, json=payload, timeout=10)
        results = res.json().get("results", [])
        context = "\n".join([f"- {r['title']}: {r['content']}" for r in results])
        return context
    except:
        return ""

# ============ 4. SAFETY CHECKER ============
def is_suicide_risk(text):
    keywords = ["suicide", "marna", "khatam", "jeene ka mann nahi", "self harm"]
    return any(word in text.lower() for word in keywords)

# ============ 5. SUPABASE + SESSION ============
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())

with st.sidebar:
    st.title("💻 ClyxessChat AI")
    if st.button("+ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
    st.markdown("---")
    st.caption("Code Engine - Only Code, No Images")

# ============ 6. CHAT DISPLAY ============
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        # Multi-file support
        if "File:" in message["content"]:
            files = re.split(r'\*\*File \d+:', message["content"])
            for file in files[1:]:
                st.markdown(f"**File:{file.split('**')[0]}**")
                code = file.split("```")[1] if "```" in file else file
                st.code(code.strip(), language="python")
        elif "```" in message["content"]:
            parts = message["content"].split("```")
            st.markdown(parts[0])
            st.code(parts[1].replace("html", "").strip(), language="html")
        else:
            st.markdown(message["content"])

# ============ 7. INPUT + AI LOGIC ============
if prompt := st.chat_input("Ask ClyxessChat AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # SAFETY CHECK PEHLE
        if is_suicide_risk(prompt):
            response = """Main samajh sakta hu tum abhi bahut takleef me ho. Tum akela nahi ho.

**India Emergency Helpline:**
- **AASRA**: 91-9820466726
- **Emergency**: 112
- **iCALL**: 9152987821

Kripya turant kisi se baat karo. Main yaha hu sunne ke liye."""
            st.markdown(response)
        else:
            with st.spinner("ClyxessChat AI is thinking..."):
                # TAVILY SEARCH - Agar coding sawal hai to
                search_context = ""
                if "code" in prompt.lower() or "website" in prompt.lower() or "react" in prompt.lower():
                    search_context = search_tavily(prompt)

                system_prompt = f"""You are ClyxessChat AI, an expert Code Engine for developers.
                Rules:
                1. If user asks for code/app/website: Give FULL WORKING Multi-File code. Use format: **File 1: App.js** ```code``` **File 2: style.css** ```code```
                2. Use latest info from here: {search_context}
                3. Max 16000 tokens. Give big code. Use Tailwind CSS.
                4. If just chatting, reply like a friendly coding partner in Hindi-English mix.
                5. End with "Koi error aaye to 'Continue' bol dena" """

                messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile", # Lamba code ke liye best
                    messages=messages,
                    temperature=0.3,
                    max_tokens=16000, # Lamba code
                )
                response = completion.choices[0].message.content
                st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
