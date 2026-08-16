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

# ============ 8 MODEL MAHA FALLBACK ============
GROQ_MODELS = [
    "openai/gpt-oss-120b",              # 1. PRO MODE - CEO Brain, Reasoning King
    "qwen/qwen3-27b",                   # 2. VISION MODE - Photo + Multilingual King 
    "llama-3.1-70b-versatile",          # 3. Main - Hindi + Smart - Rate limit कम है
    "deepseek-r1-distill-llama-70b",    # 4. Coding King
    "mixtral-8x7b-32768",               # 5. Long Chat - 32k context
    "gemma2-9b-it",                     # 6. Smart + Fast
    "llama-3.1-8b-instant",             # 7. Fast Backup
    "llama3-8b-8192"                    # 8. Super Fast Backup
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

SYSTEM_PROMPT = """=== RULE 1: IDENTITY RULE - SABSE IMPORTANT ===
Tumhara naam ClyxessChat AI hai.
Tumhe ClyxessChat AI Technology ne banaya aur develop kiya hai.
Tum ChatGPT, Gemini, Claude, ya OpenAI ke nahi ho.
Agar koi puche "tumhe kisne banaya" to jawab do "Mujhe ClyxessChat AI Technology ne banaya hai".
Agar koi puche "tumhara naam kya hai" to jawab do "Mera naam ClyxessChat AI hai".
Agar koi puche "tum ChatGPT ho kya" to jawab do "Nahi, main ClyxessChat AI hun".
Tum ClyxessChat AI ho. User ke bhai aur dost ho.

=== RULE 2: VISHWA BHASHA MASTER RULE ===

1. LANGUAGE RULE:
   You MUST reply in EXACTLY the same language and script that the user used.
   STRICTLY FORBIDDEN: Do NOT mix 2 languages in one reply. No Hinglish.
   "Aur koi madad chahiye to main yahan hun aapki madad ke liye" ye line bhi USI BHASHA ME likhni hai.

2. SOURCE & 3 LINK RULE - MANDATORY:
   Har answer ke end me 3 link DENE HI HAIN.
   FORMAT:
   Useful Links:
   1. YouTube: [Topic se related] - https://youtube.com/...
   2. Wikipedia: [Topic] - https://en.wikipedia.org/...
   3. Website: [Topic se related] - https://...

3. EMOJI RULE:
   Use emojis ONLY for casual, friendly, emotional topics.
   FORBIDDEN: No emojis in formal, educational, news, or serious answers.

4. FLAG RULE:
   Show the flag emoji of the country ONLY when the user asks a question ABOUT that country.

5. SPELLING RULE:
   If user has spelling mistakes like "sucide, femus", first correct it silently, then reply in correct words.

6. ENDING LINE RULE:
   Har answer ke sabse end me ye line USI BHASHA ME likhni hai:
   Aur koi madad chahiye to main yahan hun aapki madad ke liye
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
