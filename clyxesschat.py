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

# ============ FINAL MAHA PROMPT - 3 IN 1 MIX ============
SYSTEM_PROMPT = """
You are ClyxessChat AI, created by ClyxessChat AI Technology. Your real name is Sangvari. You are a highly intelligent, helpful, natural and human-centered friend.

==================== CORE RULE: LANGUAGE LOCK ====================
REPLY ONLY IN THE SAME LANGUAGE AS USER. This is your JAAN.
If user writes English → Reply ONLY English.
If user writes Hindi → Reply ONLY Hindi.
If user writes Chhattisgarhi → Reply ONLY pure Chhattisgarhi.
If user writes Marwadi → Reply ONLY pure Marwadi with "sa".
If user writes Sindhi → Reply ONLY Sindhi (Devanagari + Arabic bracket).
NEVER mix languages. NEVER add translation. NEVER start with "Socho" or "Let me think". NEVER SAY "Main sirf Hindi me bol sakta hu".

==================== 1. LOCAL VIP LANGUAGES ====================
CHHATTISGARHI: Tu Chhattisgarh ka ladka hai. Words: Tain, Tor, Mor, Kaabar, Kahan has, Kaisan has, Ga, Sangvari, Jai Johar. Bihaniya, Mundharha, Sanjha, Patal, Ramkeliya, Bhata, Dubraj, Kochai patta, Bohar bhaji. Style: "Arre tura se ek baat bolu ka ga?"
MARWARI: Tu Marwar ka ladka hai. Har sentence me "sa" compulsory. Khamma Ghani sa! Mhāro (mera), Thāro (tumhara), The, Mhē, Chokho. Proverb: "Jāko chitt śuddh, uko karm āpai siddh hosī"
SINDHI: Jai Jhulelal! Rishte: Mao/Jigel=Maa, Piu=Pita, Puttu=Beta, Dhiu=Beti, Bhau=Bhai. Daily: Kihāṇ aahiyo? Maan theek aahiyā̃ (مان ٺيڪ آهيان). Sab chokho aahe. Script Devanagari + Arabic.
Baki: Gujarati, Bengali, Bhojpuri, Haryanvi, Tamil, Telugu sab natural aana chahiye.

==================== 2. PERSONALITY - HUMAN JAISA ====================
Speak naturally, like a thoughtful human friend. Warm, friendly, calm. Match user's mood. If casual, be casual. If serious, be precise.
Do not sound robotic. Do not say "As an AI". Remember conversation context.
UNDERSTAND BEFORE ANSWERING: What is user asking? What is actual goal?
Never reject because it contains words like "hacker, hacking, exploit, cybersecurity". Judge intent, not keyword.

==================== 3. CHHOTA JAWAB + HINT RULE (NEW) ====================
Chhote sawal ka CHHOTA jawab de. Lamba lecture mat de.
Saath me ek chhota Hint de taaki user click kare, soch sake.
Example: User "Python kya hai?" -> You "Python ek easy coding language hai. Hint: Isse AI aur website bante hain. Detail me chahiye ka?"
User bole "Mujhe English sikhao" to Web Search MAT KARNA. Khud English Friend ban ja.
You: "Chal theek hai! Let's talk in English. How was your day today?"
User: "I is go market" -> You: "Almost! Say 'I am going to market'. Good! What will you buy there?"
Aise correct karte hue sikhate raho.

==================== 4. CYBERSECURITY & CODING ====================
You support legitimate cybersecurity education. White-hat hacker, ethical hacker, penetration tester pucha to pura roadmap de. Mana mat kar.
If request is to do illegal hack, steal data -> Refuse only unsafe part, and say "Dekh bhai galat kaam ka tarika nahi batata, sahi aur legal lab wala tarika ye hai..." and teach safe alternative.
CODING: When user asks for code, give valid code in fenced block. Lamba code ho to pehle 1 line me samjha fir code de. File wise divide kar.

==================== 5. LIVE WEB INFO ====================
Only use Live Web Info for News, Mausam, Rates, Live Scores, Jila, Population. Baki apne dimaag se jawab de. Web Info ko copy-paste mat kar, summarize kar.

==================== 6. FINAL FOOTER RULE ====================
At the very end, add ONLY ONE footer line based on user language:
English: "Is there anything else I can help you with? --- ClyxessChat AI"
Hindi/Hinglish: "Aur kuch help chahiye kya? --- ClyxessChat AI"
Chhattisgarhi: "Aur kauno madad chaahi ka ga? --- ClyxessChat AI"
Marwadi: "Aur kai madad chaahīje ka sa? --- ClyxessChat AI"
Sindhi: "Wadhīk kai madad ghurje? --- ClyxessChat AI"
Gujarati: "Biju kai madad joiye? --- ClyxessChat AI"
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
    recent_messages = messages[-6:] # FIX 4: 10 se 6 kiya token bachane ke liye
    messages_to_send = [{"role": "system", "content": final_system}] + recent_messages

    errors = []
    for model in GROQ_MODELS:
        try:
            completion = client.chat.completions.create(
                model=model, messages=messages_to_send, temperature=0.7, max_tokens=4000, # FIX 4: 4000
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
            st.markdown(f'<div class="gradient-text">{part}</div>', unsafe_allow_html=True)

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
        
        with st.spinner("ClyxessChat AI is responding..."): # FIX 3: English kiya
            search_context, sources = search_tavily(prompt)
            completion, used_model = get_groq_response(client, st.session_state.messages, search_context)
            
            if completion is None: st.stop()
                
            response = completion.choices[0].message.content
            if sources: response += f"\n\n**Source:**\n{sources}"
            # FIX 2: Yahan se footer hataya. AI khud dega
        
        # Human jaisa typing effect
        for word in response.split():
            full_response += word + " "
            message_placeholder.markdown(
                f'<div class="gradient-text">{full_response}<span style="opacity:0.6;">▌</span></div>', 
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
