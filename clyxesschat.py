import streamlit as st
from groq import Groq
from supabase import create_client, Client
import datetime
import uuid
import requests
import time
import re
import base64

st.set_page_config(page_title="ClyxessChat AI", layout="wide")

# LOGO KO BASE64 ME CONVERT KARO
with open("/mnt/data/wa_image_864147560834957046", "rb") as f:
    logo_base64 = base64.b64encode(f.read()).decode()

# CSS for ChatGPT Jaisa UI + Logo
st.markdown(f"""
<style>
.main {{max-width: 850px; margin: auto; padding-top: 0rem;}}
.stCodeBlock {{max-height: 400px!important; overflow-y: auto!important; border-radius: 8px; background: #0d1117!important; border: 1px solid #30363d;}}
[data-testid="stSidebar"] {{background-color: #171717;}}
.header {{
    position: sticky;
    top: 0;
    background: #202123;
    padding: 14px 18px;
    border-bottom: 1px solid #444;
    z-index: 999;
    margin: -1rem -1rem 20px -1rem;
}}
.header h1 {{
    color: white;
    font-size: 22px;
    font-weight: 600;
    margin: 0;
}}
.user-bubble {{
    background-color: #D9FDD3;
    color: #111b21;
    padding: 10px 14px;
    border-radius: 18px;
    border-bottom-right-radius: 4px;
    max-width: 75%;
    margin-left: auto;
    margin-bottom: 10px;
    text-align: right;
}}
.ai-response {{
    color: #ECECEC;
    font-size: 16px;
    line-height: 1.6;
    padding: 8px 0;
}}
.small-footer {{
    font-size: 12px;
    color: gray;
    margin-top: 8px;
}}
</style>
""", unsafe_allow_html=True)

# HEADER WITH LOGO
st.markdown(f"""
<div class="header">
    <div style="display: flex; align-items: center; justify-content: center; gap: 12px;">
        <img src="data:image/jpeg;base64,{logo_base64}" width="40" style="border-radius:8px;">
        <h1>💬 ClyxessChat AI</h1>
    </div>
</div>
""", unsafe_allow_html=True)

# ============ 10 MODEL MAHA ULTRA FALLBACK ============
GROQ_MODELS = [
    "openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3-27b", "qwen/qwen3-32b",
    "llama-3.1-70b-versatile", "deepseek-r1-distill-llama-70b", "mixtral-8x7b-32768",
    "gemma2-9b-it", "llama-3.1-8b-instant", "llama3-8b-8192"
]

# ============ FINAL 3-IN-1 SUPER PROMPT WITH ALL LANGUAGES ============
SYSTEM_PROMPT = """
You are ClyxessChat AI, created by ClyxessChat AI Technology.
Tera naam hai "Sangvari AI". Tu dost jaisa baat karta hai. Kaam ke time serious, majak ke time chatpata.

#### RULE 1: STRICT LANGUAGE LOCK - TODA TOH FAIL ####
YE SABSE IMPORTANT HAI.
Step 1: User jis bhasha me likhe usi ko detect kar.
Step 2: Reply 100% USI BHASHA ME DE. 1 shabd bhi dusri bhasha ka mat mila.
Step 3: KABHI MAT BOLNA "Main sirf Hindi me bol sakta hu". Ye line banned hai.

Language Examples:
User: "Tain kaise has" → LOCK=CHHATTISGARHI
User: "Khamma ghani sa" → LOCK=MARWARI
User: "Jai Jhulelal Kihāṇ aahiyo" → LOCK=SINDHI
User: "Kem cho bhai" → LOCK=GUJARATI
User: "Kemon acho" → LOCK=BENGALI

#### RULE 2: MARWARI MODE ####
Tone: Respectful, "sa" lagana. Khamma ghani sa!
Words: The kiya ho? Mhë theek hū̃. Kā̃y kar riya ho? Mane ṭhā konī. Sab chokho hai.
Vocab: Mhārō=मेरा, Thāro=तुम्हारा, Pāṇī=पानी
Proverb: "Jāko chitt śuddh, uko karm āpai siddh hosī"
Footer: "Aur kai madad chaahīje ka sa? --- ClyxessChat AI"

#### RULE 3: CHHATTISGARHI MODE ####
Tone: Gaon wali, "ga, tura, turi". Jai Johar sangvari!
Words: Tain, Mor, Tor, Kaabar, Katta. Main bane ho ga.
Time: Bihaniya, Mundharha, Sanjha
Sabji: Patal, Ramkeliya, Gondli, Bhata
Bhaji: Kochai patta=Ammath bhaji, Bohar bhaji
Footer: "Aur kauno madad chaahi ka ga? --- ClyxessChat AI"

#### RULE 4: SINDHI MODE ####
Tone: Jai Jhulelal! "Sā" bolna.
Script: Devanagari. Arabic bracket me: माण्हू (ماڻهو)
Rishte: Mao/Jigel=माता, Piu=पिता, Puttu=बेटा, Dhiu=बेटी, Bhau=भाई, Bhen=बहन
Daily: Kihāṇ aahiyo? Maan theek aahiyā̃. Chā peyā kariyo? Sab chokho aahe.
Footer: "Wadhīk kai madad ghurje? --- ClyxessChat AI"

#### RULE 5: GUJARATI & BENGALI MODE ####
Gujarati: Kem cho? Majama. Aabhar. Tame su karo cho?
Footer: "Biju koi madad joiye? --- ClyxessChat AI"
Bengali: Kemon acho? Bhalo achi. Dhonnobad. Tumi ki korcho?
Footer: "Aro kichu help lagbe? --- ClyxessChat AI"

#### RULE 6: FACT & PERSONALITY ####
News, rate, jila ke liye Live Web Info use kar. Pata na ho to usi bhasha me bol "Mujhe nahi pata".
Kaam: Serious. Majak: "Arre bhai tension mat le sangvari, main hu na"
Agar user udaas ho: "Jindagi me upar niche aata rehte he ga. Himmat mat haar"
"""

# ============ SMART TAVILY SEARCH ============
def search_tavily(query):
    search_words = [
        "news", "mausam", "weather", "rate", "price", "score", "aaj", "kal", "today", "latest", "breaking",
        "jila", "district", "rajya", "state", "population", "jansankhya", "kitna", "kab", "kaha"
    ]

    if not ("?" in query or any(word in query.lower() for word in search_words)):
        return "", ""

    try:
        last_week = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": st.secrets["TAVILY_API_KEY"],
            "query": query,
            "search_depth": "advanced",
            "max_results": 5,
            "include_answer": True,
            "topic": "general",
            "days": 7,
        }
        response = requests.post(url, json=payload, timeout=15)
        data = response.json()

        context = data.get("answer", "")
        results = data.get("results", [])

        fresh_results = [r for r in results if r.get("published_date", "") >= last_week]
        if not fresh_results: fresh_results = results[:5]

        sources = "\n".join([f"{i+1}. [{r['title']}]({r['url']})" for i, r in enumerate(fresh_results)])
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
                model=model, messages=messages_to_send, temperature=0.8, max_tokens=4000,
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
    st.image(f"data:image/jpeg;base64,{logo_base64}", width=50) # Sidebar me bhi logo
    st.title("ClyxessChat AI")
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

# CODE DISPLAY FUNCTION
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
            st.markdown(f'<div class="ai-response">{part}</div>', unsafe_allow_html=True)

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

        # Typing effect
        for word in response.split():
            full_response += word + " "
            message_placeholder.markdown(
                f'<div class="ai-response">{full_response}<span style="opacity:0.6;">▌</span></div>',
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
