import streamlit as st
from groq import Groq
from supabase import create_client, Client
import datetime
import uuid
import requests # 1. YE NAYA ADD KIYA

st.set_page_config(page_title="ClyxessChat AI", layout="wide")

# CSS for Compact Code + Header
st.markdown("""
<style>
.main {max-width: 850px; margin: auto; padding-top: 0rem;}
.stCodeBlock {max-height: 300px!important; overflow-y: auto!important; border-radius: 8px; background: #1e1e1e!important;}
[data-testid="stSidebar"] {background-color: #171717;}
.header {
    position: sticky;
    top: 0;
    background: #202123;
    padding: 18px;
    border-bottom: 1px solid #444;
    z-index: 999;
    margin: -1rem -1rem 20px -1rem;
}
.header h1 {
    color: white;
    font-size: 22px;
    font-weight: 600;
    margin: 0;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# HEADER - TOP PER
st.markdown("""
<div class="header">
    <h1>💬 ClyxessChat AI</h1>
</div>
""", unsafe_allow_html=True)

# ============ 2. TAVILY FUNCTION NAYA ADD ============
def search_tavily(query):
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": st.secrets["TAVILY_API_KEY"],
            "query": query,
            "search_depth": "advanced",
            "max_results": 3
        }
        response = requests.post(url, json=payload)
        results = response.json().get("results", [])
        context = "\n".join([f"- {r['title']}: {r['content']}" for r in results])
        return context
    except Exception as e:
        return ""

# Supabase Connect
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Sidebar
with st.sidebar:
    st.title("💬 ClyxessChat AI")
    if st.button("+ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
    st.markdown("---")
    st.caption("Code Engine App Website")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())

# Chat display
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if "```" in message["content"]:
            parts = message["content"].split("```")
            st.markdown(parts[0])
            code = parts[1].replace("html", "", 1).strip()
            st.code(code, language="html")
            if st.button("📋 Copy Code", key=f"copy_{i}"):
                st.toast("Code Copied!")
        else:
            st.markdown(message["content"])

# Input
if prompt := st.chat_input("Message ClyxessChat AI"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("ClyxessChat AI is thinking..."):

            # 3. YE NAYA LOGIC ADD KIYA - LIVE SEARCH
            search_context = ""
            if any(word in prompt.lower() for word in ["latest", "2025", "2026", "news", "code", "error", "update"]):
                with st.spinner("Searching web for latest info..."):
                    search_context = search_tavily(prompt)

            system_prompt = f"""You are ClyxessChat AI, an expert AI assistant like ChatGPT.
            Use this live web information if relevant: {search_context}

            Rules:
            1. If user asks for code, website, app, landing page - then give FULL WORKING code in 1 file inside ```html... ```
            2. If user is just chatting like "hi", "hello", "thanks" - then reply normally in text. Do NOT give code.
            3. Use Tailwind CSS for modern design.
            4. If live info is given above, use it to answer. Mention "According to latest info"."""

            messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

            completion = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=messages,
                temperature=0.2,
                max_tokens=8000,
            )
            response = completion.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": response})

            # Save to Supabase
            try:
                supabase.table("messages").insert({
                    "session_id": st.session_state.session_id,
                    "role": "user",
                    "content": prompt,
                    "created_at": datetime.datetime.now().isoformat()
                }).execute()
                supabase.table("messages").insert({
                    "session_id": st.session_state.session_id,
                    "role": "assistant",
                    "content": response,
                    "created_at": datetime.datetime.now().isoformat()
                }).execute()
            except Exception as e:
                pass

            st.rerun()
