import streamlit as st
from groq import Groq
from supabase import create_client
import datetime, uuid, requests, time, re, os, json, random
from fpdf import FPDF

st.set_page_config(page_title="ClyxessChat AI", layout="wide")

# --- CSS --- (tera wala same + code fix)
st.markdown("""
<style>
.main {max-width: 850px; margin: auto;}
.header {position: sticky; top: 0; background: #202123; padding: 18px; border-bottom: 1px solid #444; z-index: 999; margin: -1rem -1rem 20px -1rem;}
.header h1 {color: white; font-size: 22px; font-weight: 600; margin: 0; text-align: center;}
.user-bubble {background-color: #D9FDD3; color: #111b21; padding: 10px 14px; border-radius: 18px; border-bottom-right-radius: 4px; max-width: 75%; margin-left: auto; margin-bottom: 10px; text-align: right; white-space: pre-wrap;}
pre {background: #0d0d0d!important; border-radius:10px!important; padding:12px!important;}
code {white-space: pre-wrap!important;}
.duo-bar {background:#202123; padding:12px; border-radius:12px; display:flex; justify-content:space-between; color:white; margin-bottom:15px;}
.duo-card {background:white; padding:20px; border-radius:16px; border:2px solid #58CC02; color:#111;}
</style>
""", unsafe_allow_html=True)

# --- CONFIG - 15 MODEL FIX ---
GROQ_MODELS = [
    "openai/gpt-oss-120b","openai/gpt-oss-20b","qwen/qwen3-27b","qwen/qwen3-32b","llama-3.1-70b-versatile",
    "deepseek-r1-distill-llama-70b","mixtral-8x7b-32768","gemma2-9b-it","llama-3.1-8b-instant","llama3-8b-8192",
    "llama-3.3-70b-versatile","meta-llama/llama-4-scout-17b-16e-instruct","meta-llama/llama-4-maverick-17b-128e-instruct",
    "groq/compound","groq/compound-mini","moonshotai/kimi-k2-instruct"
]
LANGUAGES = ["Hindi","English","Bengali","Odia","Marathi","Gujarati","Telugu","Malayalam","Kannada","Tamil","Punjabi","Urdu","Chinese","Japanese","Canadian English"]

# ============ IMAGE FALLBACK FUNCTION (DONO MODE ME) ============
def generate_image_url(prompt, is_school_mode, age):
    if is_school_mode:
        if "1-2" in age or "3-4" in age:
            final_prompt = f"cute baby cartoon, very simple, bright colors, 3d pixar style, {prompt}, no person"
        else:
            final_prompt = f"kid friendly educational diagram, colorful, {prompt}, no person"
    else:
        final_prompt = f"realistic, cinematic, 4k, {prompt}"
    try:
        hf_key = st.secrets.get("HF_API_KEY", "")
        if hf_key:
            API_URL = "https://api-inference.huggingface.co/models/stabilityai/sdxl-turbo"
            headers = {"Authorization": f"Bearer {hf_key}"}
            r = requests.post(API_URL, headers=headers, json={"inputs": final_prompt}, timeout=20)
            if r.status_code == 200 and len(r.content) > 1000:
                return r.content, "huggingface"
    except: pass
    poll_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(final_prompt)}?width=512&height=512&nologo=true&seed={uuid.uuid4().int % 10000}"
    return poll_url, "pollinations"

# ============ PROMPTS - CHAT FIX (TERA ORIGINAL + HI FIX) ============
NORMAL_SYSTEM_PROMPT = """
You are ClyxessChat AI, created by ClyxessChat AI Technology.
CORE RULE: REPLY ONLY IN THE SAME LANGUAGE AS USER.
Your name is ClyxessChat AI. Friendly, intelligent, calm, helpful.
If user says hi/hello/namaste/kaise ho - reply warmly in same language like 'Namaste! Kaise ho? Batao kaise help karu?'
If user asks to generate image, say: "Generating image for: [prompt]"
Give detailed, helpful answer with examples and code if needed.
"""

def get_school_system_prompt(age_group):
    base = f"You are ClyxessChat AI - School Mode Creative Lab. Current Age Group: {age_group}. SAFETY: Kid safe only. "
    if "1-2" in age_group or "3-4" in age_group:
        return base + """
        You are Didi for 1-4 years kids. RULES: Only rhymes, colors, emojis, sounds. Use Hinglish like 'dekho laal gubbara 🎈'. Very very short sentences (8-10 words). If user says hi/namaste/hello/kaise ho -> reply 'Namaste baby! 😊 Laal gubbara dekho 🎈'. Ask sensory questions like 'Tap karo toh kya hoga?'. Never use tough words. You are 'Chote Inventor' ki didi.
        If user wants image, create cute cartoon prompt.
        """
    elif "5-6" in age_group or "6-8" in age_group:
        return base + """
        Age 5-8: Focus Curiosity & Basic Logic. Task: Interactive Story-Building & Shape Puzzles. Hint Style: Kahani wala. Eg: 'Sher jungle me kho gaya, pehle kya kare?'. Socratic method - answer with question. If hi/namaste -> 'Namaste! Kaise ho? 😊 Chalo puzzle karen?'
        """
    elif "10-11" in age_group:
        return base + """
        Age 7-10: Focus Maker & Practical Science. Task: Step-by-step DIY Projects & Logic Challenges. Hint Style: Jugaad wala. Eg: 'Rocket banana hai? Socho hawa kaha se niklegi?'. Give steps, not direct answer. If code asked give FULL HTML/CSS/JS code. If hi/namaste -> 'Namaste! Badhiya hu, aap kaise ho? Chalo rocket banayen? 🚀'
        """
    else:
        return base + """
        Age 11+: Focus Future Tech, AI & App Prototyping. Task: Coding Logic, App Wireframing. Hint Style: Innovator wala. Challenge them to break big problem into 2 small parts. If coding asked give full clean code. If hi/namaste -> 'Namaste! Kaise ho? Ready ho coding ke liye? 💻'
        """

# --- Tavily, Groq, Supabase ---
def search_tavily(query):
    search_words = ["news","mausam","weather","rate","price","score","aaj","kal","today","latest","breaking"]
    if not any(word in query.lower() for word in search_words): return "", ""
    try:
        tavily_key = st.secrets.get("TAVILY_API_KEY", "")
        if not tavily_key: return "", ""
        url = "https://api.tavily.com/search"
        payload = {"api_key": tavily_key, "query": query, "search_depth": "advanced", "max_results": 5, "include_answer": True}
        response = requests.post(url, json=payload, timeout=15)
        data = response.json()
        context = data.get("answer", "")
        sources = "\n".join([f"{i+1}. [{r['title']}]({r['url']})" for i, r in enumerate(data.get("results", [])[:3])])
        return context, sources
    except: return "", ""

def get_groq_response(client, messages, system_prompt, search_context=""):
    final_system = system_prompt + (f"\n\nLive Web Info:\n{search_context}" if search_context else "")
    recent_messages = messages[-6:]
    messages_to_send = [{"role": "system", "content": final_system}] + recent_messages
    for model in GROQ_MODELS:
        try:
            completion = client.chat.completions.create(model=model, messages=messages_to_send, temperature=0.7, max_tokens=4000)
            return completion, model
        except: continue
    return None, None

@st.cache_resource
def init_supabase():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None
supabase = init_supabase()

# ============ DUOLINGO GAME FIX ============
def fetch_duolingo_task(client, age, lang, level):
    if "1-2" in age or "3-4" in age:
        prompt = f"Age {age}, Lang {lang}, Level {level}. JSON only: {{\"question\":\"short question with emoji in {lang}\", \"options\":[\"A\",\"B\",\"C\"], \"answer\":\"correct option\", \"xp\":10}}"
    elif "5-6" in age or "6-8" in age:
        prompt = f"Age {age}, Lang {lang}, Level {level}. JSON only: {{\"question\":\"question in {lang}\", \"options\":[\"A\",\"B\",\"C\",\"D\"], \"answer\":\"correct\", \"xp\":15}}"
    else:
        prompt = f"Age {age}, Lang {lang}, Level {level}. JSON only: {{\"question\":\"question in {lang}\", \"options\":[\"A\",\"B\",\"C\",\"D\"], \"answer\":\"correct\", \"xp\":20}}"
    for model in GROQ_MODELS[:6]:
        try:
            comp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}], response_format={"type":"json_object"}, temperature=0.9)
            return json.loads(comp.choices[0].message.content)
        except: continue
    return {"question":f"Level {level}: Apple ka Hindi kya hai? 🍎", "options":["Seb","Kela","Aam","Angoor"], "answer":"Seb", "xp":10}

def duolingo_game_mode(client):
    if "d_level" not in st.session_state: st.session_state.d_level = 1
    if "d_xp" not in st.session_state: st.session_state.d_xp = 0
    if "d_streak" not in st.session_state: st.session_state.d_streak = 0
    if "d_hearts" not in st.session_state: st.session_state.d_hearts = 5
    if "d_task" not in st.session_state: st.session_state.d_task = None
    if "d_done" not in st.session_state: st.session_state.d_done = 0

    c1,c2,c3,c4 = st.columns(4)
    with c1: sel_lang = st.selectbox("🌐 Language", LANGUAGES, key="duo_lang")
    with c2: sel_age = st.selectbox("🎒 Age", ["1-2 Yrs","3-4 Yrs","5-6 Yrs","6-8 Yrs","10-11 Yrs","11+ Yrs"], key="duo_age")
    with c3: st.metric("❤️ Hearts", st.session_state.d_hearts)
    with c4: st.metric("🔥 Streak", st.session_state.d_streak)

    st.markdown(f"<div class='duo-bar'><span>📊 Level {st.session_state.d_level}</span><span>⭐ XP {st.session_state.d_xp}</span><span>🎯 {st.session_state.d_done}/5</span></div>", unsafe_allow_html=True)
    st.progress((st.session_state.d_done % 5) * 20 if st.session_state.d_done %5!=0 else 0)

    if st.session_state.d_hearts <= 0:
        st.error("💔 Hearts khatam!")
        if st.button("🔄 Restart with 5 Hearts"): st.session_state.d_hearts=5; st.session_state.d_task=None; st.rerun()
        return

    if st.session_state.d_task is None:
        with st.spinner(f"{sel_lang} me naya task..."):
            st.session_state.d_task = fetch_duolingo_task(client, sel_age, sel_lang, st.session_state.d_level)

    task = st.session_state.d_task
    st.markdown(f"<div class='duo-card'><h3>Level {st.session_state.d_level}: {task['question']}</h3></div>", unsafe_allow_html=True)

    for opt in task['options']:
        if st.button(opt, key=f"opt_{opt}_{st.session_state.d_done}_{random.randint(1,9999)}", use_container_width=True):
            if opt.strip().lower() == task['answer'].strip().lower():
                st.balloons(); st.success(f"🎉 Congratulations! +{task['xp']} XP")
                st.session_state.d_xp += task['xp']; st.session_state.d_streak += 1; st.session_state.d_done += 1; st.session_state.d_task = None
                if st.session_state.d_done % 5 == 0: st.session_state.d_level += 1; st.toast(f"🚀 Level Up! Level {st.session_state.d_level}")
                time.sleep(1); st.rerun()
            else:
                st.error(f"❌ Galat! Sahi hai: {task['answer']}"); st.session_state.d_hearts -= 1; st.session_state.d_streak = 0; time.sleep(1); st.rerun()

    colA, colB = st.columns(2)
    with colA:
        if st.button("💡 Hint"): st.info(f"Hint: '{task['answer'][:1]}...' se start")
    with colB:
        if st.button("⏭️ Skip (-1 Heart)"): st.session_state.d_hearts -=1; st.session_state.d_task=None; st.rerun()

# --- UI START ---
st.markdown('<div class="header"><h1>💬 ClyxessChat AI</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.title("💬 ClyxessChat AI")
    mode = st.radio("Select Mode", ["Normal Chat", "Creative Lab (School Mode)", "🎮 Duolingo Game"], index=0)
    st.markdown("---")
    age_group = "1-2 Yrs"
    if "Creative Lab" in mode:
        st.markdown("### 🎒 Age Group Selector")
        st.caption("LEARN & CREATE (SHIKHEN AUR BANAYEN)")
        cols = st.columns(2)
        age_options = ["1-2 Yrs", "3-4 Yrs", "5-6 Yrs", "6-8 Yrs", "10-11 Yrs", "11+ Yrs"]
        for i, ag in enumerate(age_options):
            if cols[i%2].button(ag, key=f"age_{ag}", use_container_width=True, type="primary" if st.session_state.get("age_group", "1-2 Yrs")==ag else "secondary"):
                st.session_state.age_group = ag
        age_group = st.session_state.get("age_group", "1-2 Yrs")
        st.success(f"Active: {age_group} | Focus: {'Early Brain Development' if '1-2' in age_group else 'Creative Lab'}")
    if st.button("+ New Chat", use_container_width=True):
        st.session_state.messages = []; st.session_state.session_id = str(uuid.uuid4()); st.rerun()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])
if "messages" not in st.session_state: st.session_state.messages = []; st.session_state.session_id = str(uuid.uuid4())
if "age_group" not in st.session_state: st.session_state.age_group = "1-2 Yrs"

if "Duolingo" in mode:
    duolingo_game_mode(client)
    st.stop()

# DISPLAY CHAT - FIXED
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image_url" in message: st.image(message["image_url"], caption=message.get("image_caption",""))
        if message.get("content"): st.markdown(message["content"])

# CHAT INPUT
if prompt := st.chat_input("Apna idea type karein ya draw karein..." if "Creative" in mode else "Ask ClyxessChat AI"):
    is_school = "Creative" in mode
    current_age = st.session_state.age_group if is_school else "Normal"
    system_prompt = get_school_system_prompt(current_age) if is_school else NORMAL_SYSTEM_PROMPT
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f'<div class="user-bubble">{prompt}</div>', unsafe_allow_html=True)
    wants_image = any(w in prompt.lower() for w in ["image", "draw", "banao", "photo", "picture", "chitra", "rocket", "diagram", "chidiyaghar", "zoo", "sher", "haathi", "ghar"])
    with st.chat_message("assistant"):
        img_url_to_save = None
        if wants_image:
            with st.spinner("🎨 Image bana raha hu..."):
                img_data, source = generate_image_url(prompt, is_school, current_age)
                st.image(img_data, caption=f"Generated for: {prompt} ({source})")
                img_url_to_save = img_data
        message_placeholder = st.empty(); full_response = ""
        with st.spinner("ClyxessChat AI is responding..."):
            search_context, sources = search_tavily(prompt)
            completion, used_model = get_groq_response(client, st.session_state.messages, system_prompt, search_context)
            if completion is None: st.error("Model busy hai"); st.stop()
            response = completion.choices[0].message.content
            if sources: response += f"\n\n**Source:**\n{sources}"
        for word in response.split():
            full_response += word + " "; message_placeholder.markdown(full_response + "▌"); time.sleep(0.02)
        message_placeholder.markdown(full_response)
        st.caption(f"Mode: {mode} | Age: {current_age} | Model: {used_model}")
        if img_url_to_save is not None:
            st.session_state.messages.append({"role": "assistant", "image_url": img_url_to_save, "image_caption": prompt, "content": full_response})
        else:
            st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()
