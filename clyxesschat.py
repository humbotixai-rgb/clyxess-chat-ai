import streamlit as st
from groq import Groq
from supabase import create_client, Client
import datetime
import uuid
import requests
import time
import re

st.set_page_config(page_title="ClyxessChat AI", layout="wide")

# CSS for ChatGPT Jaisa UI + Chota Code Box
st.markdown("""
<style>
.main {max-width: 850px; margin: auto; padding-top: 0rem;}
.stCodeBlock {max-height: 400px!important; overflow-y: auto!important; border-radius: 8px; background: #0d1117!important; border: 1px solid #30363d;}
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
/* FIX: ChatGPT wala safed color */
.ai-response {
    color: #ECECEC;
    font-size: 16px;
    line-height: 1.6;
    padding: 8px 0;
}
.small-footer {
    font-size: 12px;
    color: gray;
    margin-top: 8px;
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
    "openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3-27b", "qwen/qwen3-32b",
    "llama-3.1-70b-versatile", "deepseek-r1-distill-llama-70b", "mixtral-8x7b-32768",
    "gemma2-9b-it", "llama-3.1-8b-instant", "llama3-8b-8192"
]

# ============ FIX 1: STRICT SYSTEM PROMPT ============
SYSTEM_PROMPT = """
You are ClyxessChat AI, created by ClyxessChat AI Technology.

CORE RULE: REPLY ONLY IN THE SAME LANGUAGE AS USER.
If user writes English → Reply ONLY English.
If user writes Hindi → Reply ONLY Hindi.
If user writes Chinese → Reply ONLY Chinese.
NEVER mix languages. NEVER add translation. NEVER start with "Socho" or "Let me think".

1. IDENTITY
Your name is ClyxessChat AI. You were created by ClyxessChat AI Technology.

4. LANGUAGE INTELLIGENCE
Match the user's language exactly.

5. PERSONALITY
ClyxessChat AI should feel friendly, intelligent, calm, and natural.

10. LIVE WEB INFORMATION
The application may provide live web-search information as "Live Web Info".
Use it when relevant to the user's question.

14. CODING AND TECHNICAL QUESTIONS
When the user asks for code: Return syntactically valid code in fenced code blocks with language identifier.

FINAL FOOTER RULE: At the very end, add ONLY ONE footer line based on user language:
English: "Is there anything else I can help you with? --- ClyxessChat AI"
Hindi/Hinglish: "Aur kuch help chahiye kya? --- ClyxessChat AI"
"""

# ============ TAVILY SEARCH - 100% LIVE FIXED ============
def search_tavily(query):
    search_words = ["news", "mausam", "weather", "rate", "price", "score", "aaj", "kal", "today", "latest", "breaking"]
    
    if not any(word in query.lower() for word in search_words):
        return "", ""
        
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": st.secrets["TAVILY_API_KEY"],
            "query": query,
            "search_depth": "advanced",
            "max_results": 5,
            "include_answer": True,
            "topic": "news",
            "days": 2,
            "time_range": "day"
        }
        response = requests.post(url, json=payload, timeout=15)
        data = response.json()
        
        context = data.get("answer", "")
        results = data.get("results", [])
        
        fresh_results = []
        for r in results:
            pub_date = r.get("published_date", "")
            if today in pub_date or yesterday in pub_date:
                fresh_results.append(r)
        
        if not fresh_results:
            fresh_results = results[:5]
            
        sources = "\n".join([f"{i+1}. [{r['title']}]({r['url']}) - {r.get('published_date','')}" for i, r in enumerate(fresh_results)])
        return context, sources
    except Exception as e:
        print("Tavily Error:", e)
        return "", ""

# ============ SINGLE GROQ FUNCTION ============
def get_groq_response(client, messages, search_context=""):
    final_system = SYSTEM_PROMPT
    if search_context:
        final_system += f"\n\nLive Web Info:\n{search_context}"
    recent_messages = messages[-6:]
    messages_to_send = [{"role": "system", "content": final_system}] + recent_messages

    errors = []
    for model in GROQ_MODELS:
        try:
            completion = client.chat.completions.create(
                model=model, messages=messages_to_send, temperature=0.7, max_tokens=4000,
            )
            return completion, model
        except Exception as e:
            errors.append(f"{model}: {str(e)}")
            continue
    st.error("❌ Groq API Error. API Key ya Quota check karo")
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

# CODE DISPLAY FUNCTION - FIXED
def display_message(content):
    code_blocks = re.split(r'(```.*?```)', content, flags=re.DOTALL)
    for part in code_blocks:
        if part.startswith("```") and part.endswith("```"):
            code = part.strip("`")
            lang = "python"
            if "\n" in code:
                lang = code.split("\n")[0]
                code = "\n".join(code.split("\n")[1:])
            st.code(code, language=lang)
        else:
            st.markdown(f'<div class="ai-response">{part}</div>', unsafe_allow_html=True) # FIX: gradient-text hata

# Chat display
for i, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(f'<div class="user-bubble">{message["content"]}</div>', unsafe_allow_html=True)
    else:
        with st.chat_message("assistant"):
            display_message(message["content"])

# ============ MAIN CHAT INPUT LOGIC ============
if prompt := st.chat_input("Ask ClyxessChat AI"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(f'<div class="user-bubble">{prompt}</div>', unsafe_allow_html=True)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("ClyxessChat AI is responding..."):
            search_context, sources = search_tavily(prompt)
            completion, used_model = get_groq_response(client, st.session_state.messages, search_context)
            
            if completion is None: st.stop()
                
            response = completion.choices[0].message.content
            if sources: response += f"\n\n**Source:**\n{sources}"
        
        # Human jaisa typing effect - FIXED COLOR
        for word in response.split():
            full_response += word + " "
            message_placeholder.markdown(
                f'<div class="ai-response">{full_response}<span style="opacity:0.6;">▌</span></div>', # FIX: gradient-text hata
                unsafe_allow_html=True
            )
            time.sleep(0.05)
        
        message_placeholder.empty()
        display_message(full_response)
        st.caption(f"Model: {used_model}")
    
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Save to Supabase
    try:
        supabase.table("messages").insert({"session_id": st.session_state.session_id, "role": "user", "content": prompt, "created_at": datetime.datetime.now().isoformat()}).execute()
        supabase.table("messages").insert({"session_id": st.session_state.session_id, "role": "assistant", "content": response, "created_at": datetime.datetime.now().isoformat()}).execute()
    except: pass

    st.rerun()
