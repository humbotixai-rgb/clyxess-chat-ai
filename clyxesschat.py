import streamlit as st
from groq import Groq
from supabase import create_client, Client
import datetime
import uuid
import requests
import time

st.set_page_config(page_title="ClyxessChat AI", layout="wide")

# CSS for Compact Code + Header + White Bubble + Gradient
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
.user-bubble {
    background-color: #D9FDD3;
    color: #111b21;
    padding: 10px 14px;
    border-radius: 18px;
    border-bottom-right-radius: 4px;
    max-width: 75%;
    margin-left: auto;
    margin-bottom: 10px;
    text-align: right;
}
.gradient-text {
    background: linear-gradient(90deg, #ff00cc, #3333ff, #00ffcc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-size: 300% 300%;
    animation: gradient 3s ease infinite;
}
@keyframes gradient {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}
.small-footer {
    font-size: 12px;
    color: gray;
    margin-top: 5px;
}
</style>
""", unsafe_allow_html=True)

# HEADER
st.markdown("""
<div class="header">
    <h1>💬 ClyxessChat AI</h1>
</div>
""", unsafe_allow_html=True)

# ============ 10 MODEL MAHA ULTRA FALLBACK ============
GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3-27b",
    "qwen/qwen3-32b",
    "llama-3.1-70b-versatile",
    "deepseek-r1-distill-llama-70b",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
    "llama-3.1-8b-instant",
    "llama3-8b-8192"
]

SYSTEM_PROMPT = """
You are ClyxessChat AI, created by ClyxessChat AI Technology.
Rules:
1. Answer in the same language as user.
2. Be helpful, accurate, and concise.
3. If Live Web Info is provided below, use it to answer. Cite sources.
4. For coding, give clean code with explanation.
5. End with a closing question in user's language, then add footer: --- ClyxessChat AI
"""

# ============ TAVILY SEARCH ============
def search_tavily(query):
    # Force search if user asks about date, news, weather
    search_words = ["news", "mausam", "weather", "rate", "price", "score", "aaj", "kal", "today", "latest", "18 august", "date"]
    
    # Aaj ki date auto add kar do query me
    today = datetime.datetime.now().strftime("%d %B %Y") # 18 August 2025
    query_with_date = f"{query} {today}"
    
    if not any(word in query.lower() for word in search_words):
        return "", ""
        
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": st.secrets["TAVILY_API_KEY"],
            "query": query_with_date, # <-- yahan date wali query gayi
            "search_depth": "advanced",
            "max_results": 5, # 3 se 5 kiya taaki fresh news mile
            "include_answer": True,
            "days": 1 # <-- YE SABSE IMPORTANT HAI. Sirf last 1 din ka data la
        }
        response = requests.post(url, json=payload, timeout=15)
        data = response.json()
        
        context = data.get("answer", "")
        results = data.get("results", [])
        sources = "\n".join([f"{i+1}. [{r['title']}]({r['url']})" for i, r in enumerate(results)])
        return context, sources
    except Exception as e:
        print("Tavily Error:", e)
        return "", ""

# ============ SINGLE GROQ FUNCTION ============
def get_groq_response(client, messages, search_context=""):
    # Final messages with system prompt + search context
    final_system = SYSTEM_PROMPT
    if search_context:
        final_system += f"\n\nLive Web Info:\n{search_context}"

    # FIX: Sirf last 10 messages bhejo warna TPM limit cross
    recent_messages = messages[-10:]
    messages_to_send = [{"role": "system", "content": final_system}] + recent_messages

    errors = []
    for model in GROQ_MODELS:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages_to_send,
                temperature=0.7,
                max_tokens=4000,
            )
            return completion, model
        except Exception as e:
            errors.append(f"{model}: {str(e)}")
            continue

    st.error("❌ Groq API Error.\n\n**Reason:** API Key galat hai ya Quota khatam\n**Solution:** 1. `GROQ_API_KEY` check karo 2. 10 min baad try karo")
    with st.expander("Tech Details"):
        st.code("\n".join(errors))
    return None, None

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
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(f'<div class="user-bubble">{message["content"]}</div>', unsafe_allow_html=True)
    else:
        with st.chat_message("assistant"):
            st.markdown(f'<div class="gradient-text">{message["content"]}</div>', unsafe_allow_html=True)

# ============ MAIN CHAT INPUT LOGIC ============
if prompt := st.chat_input("Ask ClyxessChat AI"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(f'<div class="user-bubble">{prompt}</div>', unsafe_allow_html=True)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("ClyxessChat AI is thinking..."):
            search_context, sources = search_tavily(prompt)
            completion, used_model = get_groq_response(client, st.session_state.messages, search_context)
            
            if completion is None:
                st.stop()
                
            response = completion.choices[0].message.content
            
            # SOURCE ADD KARNA
            if sources:
                response += f"\n\n**Source:**\n{sources}"
        
        for word in response.split():
            full_response += word + " "
            message_placeholder.markdown(
                f'<div class="gradient-text">{full_response}<span style="opacity:0.6;">▌</span></div>', 
                unsafe_allow_html=True
            )
            time.sleep(0.02)
        
        footer = f'<div class="small-footer">--- {used_model} | --- ClyxessChat AI</div>'
        message_placeholder.markdown(
            f'<div class="gradient-text">{full_response}</div>{footer}', 
            unsafe_allow_html=True
        )
    
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
