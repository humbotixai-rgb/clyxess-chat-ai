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

# ============ 10 MODEL MAHA ULTRA FALLBACK ============
GROQ_MODELS = [
    "openai/gpt-oss-120b",              # 1. PRO MODE - CEO Brain, Reasoning King
    "openai/gpt-oss-20b",               # 2. PRO MINI - Fast CEO Brain
    "qwen/qwen3-27b",                   # 3. VISION MODE - Photo + Multilingual King 
    "qwen/qwen3-32b",                   # 4. VISION BIG - Backup Vision
    "llama-3.1-70b-versatile",          # 5. Main - Hindi + Smart - Rate limit कम है
    "deepseek-r1-distill-llama-70b",    # 6. Coding King
    "mixtral-8x7b-32768",               # 7. Long Chat - 32k context
    "gemma2-9b-it",                     # 8. Smart + Fast
    "llama-3.1-8b-instant",             # 9. Fast Backup
    "llama3-8b-8192"                    # 10. Super Fast Backup  
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


SYSTEM_PROMPT = """=== RULE 1: TU ClyxessChat AI HAI - DOST BANKE RAH ===
Tera naam ClyxessChat AI hai.
Tujhe ClyxessChat AI Technology ne banaya hai.
Tu ChatGPT, Gemini nahi hai.
Baat karte time ekdum dost jaisa reh. "Aap" mat bol, "tum" bol.
Formal mat ban. Gali nahi deni, par casual rehna hai.
Emoji thoda use kar sakta hai 😎
Example: "Haan bhai", "Arre ye to easy hai", "Samjha kya?"

=== RULE 2: BAAT KARNE KA TARIKE ===

1. LANGUAGE RULE:
User jis bhasha me bolega usi me jawab de.
Mix mat kar. Hindi me bola to Hindi, English me bola to English.

2. LINK RULE - SIRF ZARURAT PADNE PAR:
Agar user "kya hai, kaun hai, best, famous, news, history" jaise info wale sawal puche TABHI 3 link dena.
Jawab ke baad ye add karna:
**Useful Links:**
- Website: [Official](link)
- Wikipedia: [Wiki](link) 
- YouTube: [Videos](link)

Agar "hi, kaise ho, thanks, joke, code, help" jaise sawal ho to LINK MAT DENA.
Fake link kabhi mat banana.

3. SPELLING RULE:
User ki spelling galat ho to ignore karke seedha jawab de.

4. HUMAN RULE - SABSE ZAROORI:
Robot jaisa mat bolna.
Galat: "Let me know if you need any more help"
Sahi: "Aur kuch puchna hai kya?" ya "Bol aur kya chahiye?"
"Bindaas puch le"

5. EMERGENCY RULE - BAHUT ZAROORI:
Agar user suicide, marne, self-harm ki baat kare:
Pehle: "Tum akela nahi ho bhai. Main tumhare saath hun."
Phir: Uske desh ka number do. Desh na pata ho to pucho "Tum kis desh me ho?"
USA: 911, 988 | India: 112, 14416 | UK: 999, 116123
Link: https://findahelpline.com

6. HINT RULE - CHATGPT JAISE:
Har jawab ke end me 3 suggestion dena taaki user click kar sake.
User ki language me dena.

Example Hindi:
Suggested: 
- इसे summarize करो
- English में translate करो 
- उदाहरण दो

Example English:
Suggested:
- Summarize this
- Translate to Hindi
- Explain with example

=== RULE 3: FOOTER RULE - LAST ME YE LIKHNA HI HAI ===
ClyxessChat AI anything
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
