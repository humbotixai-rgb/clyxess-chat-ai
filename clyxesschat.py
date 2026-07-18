import streamlit as st
from groq import Groq
from supabase import create_client, Client
import datetime
import uuid
import requests

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

# HEADER
st.markdown("""
<div class="header">
    <h1>💬 ClyxessChat AI</h1>
</div>
""", unsafe_allow_html=True)

# ============ 4 MODEL FALLBACK - LATEST 2026 ============
GROQ_MODELS = [
    "llama-3.3-70b-versatile", # 1. Main - Hindi + Smart
    "llama-3.3-8b-instant", # 2. Fast
    "deepseek-r1-distill-llama-70b", # 3. Coding King
    "qwen-qwq-32b" # 4. Backup Multilingual
]

def get_groq_response(client, messages):
    errors = []
    for model in GROQ_MODELS:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=4000, # 8000 se kam kiya warna TPM error
            )
            return completion, model
        except Exception as e:
            errors.append(f"{model}: {str(e)}")
            continue

    st.error("❌ Groq API Error.\n\n**Reason:** API Key galat hai ya Quota khatam\n**Solution:** 1. `GROQ_API_KEY` check karo 2. 10 min baad try karo")
    with st.expander("Tech Details"):
        st.code("\n".join(errors))
    return None, None

# ============ TAVILY SEARCH ============
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
        sources = "\n".join([f"{i+1}. [{r['title']}]({r['url']})" for i, r in enumerate(results)])
        return context, sources
    except Exception as e:
        return "", ""

# ============ TERA 4 RULE SYSTEM PROMPT ============
today = datetime.datetime.now().strftime("%d %B %Y")
SYSTEM_PROMPT = f"""Tum ClyxessChat ho - Bharat ka Live AI Assistant. Tum dost ki tarah baat karte ho.
Aaj {today} hai.

=== RULE 1: LIVE SEARCH + SOURCE LINK ===
1. Jab bhi user "aaj, latest, news, rate, score, mausam, price, bhav" pooche to Tavily se search karo.
2. Jawab ke end me Source dena LAZMI hai. Format:
**Source:**
1. [Website Title](URL)
3. Date likho: "Aaj {today} ke hisab se..."
4. Agar source na mile to likho "Source uplabdh nahi hai"

=== RULE 2: IMAGE GENERATION ===
1. Sirf tab image banao jab user bole: "image banao, photo banao, pic banao, generate karo"
2. Jawab: Pehle image do + fir 1 line caption: **Prompt:** user ka prompt
3. Bina mange image mat banao

=== RULE 3: CODE GENERATION ===
1. Sirf tab code do jab user bole: "code do, bana do, website banao, app banao"
2. Code hamesha ```language me do + 2 line samjhao + pucho "aur customize karna hai?"
3. Bina mange code mat dena. Pehle samjhao.

=== RULE 4: EMOTION + TONE ===
1. Agar user 😭 😔 😢 😡 bheje to pehle empathy dikhao: "kya hua? main hun na"
2. Tone: Short, Hindi, dost jaisa. Lambe lecture mat do.
3. Har jawab 3-4 line me khatam karne ki koshish karo.

=== MANA HAI ===
1. Jhooth mat bolo. Pata nahi hai to bolo "mujhe confirm nahi hai, search karu?"
2. Source ke bina koi fact mat do
"""

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
            if len(parts) > 1:
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

            # LIVE SEARCH LOGIC
            search_context = ""
            sources = ""
            search_words = ["aaj", "latest", "news", "rate", "score", "mausam", "price", "bhav", "2026"]
            if any(word in prompt.lower() for word in search_words):
                with st.spinner("Searching web for latest info..."):
                    search_context, sources = search_tavily(prompt)

            # Final messages with system prompt + search context
            final_system = SYSTEM_PROMPT
            if search_context:
                final_system += f"\n\nLive Web Info:\n{search_context}"

            # FIX: Sirf last 10 messages bhejo warna TPM limit cross
            recent_messages = st.session_state.messages[-10:]
            messages = [{"role": "system", "content": final_system}] + recent_messages

            # 4 MODEL FALLBACK CALL
            completion, used_model = get_groq_response(client, messages)

            if completion is None: # Agar sab fail
                st.stop()

            response = completion.choices[0].message.content

              # SOURCE ADD KARNA
    if sources:
        response += f"\n\n**Source:**\n{sources}"

    # MODEL NAME SHOW - YE LINE THEEK KI
    response += f"\n\n*⚡ Powered by: ClyxessChat AI*"

    st.session_state.messages.append({"role": "assistant", "content": response})
            st.markdown(response)

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
