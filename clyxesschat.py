import streamlit as st
from groq import Groq
from supabase import create_client
import datetime, uuid, requests, time, re, os
from fpdf import FPDF

st.set_page_config(page_title="ClyxessChat AI", layout="wide")

# --- CSS - FIX 1: Image size chota ---
st.markdown("""
<style>
.main {max-width: 850px; margin: auto;}
.header {position: sticky; top: 0; background: #202123; padding: 18px; border-bottom: 1px solid #444; z-index: 999; margin: -1rem -1rem 20px -1rem;}
.header h1 {color: white; font-size: 22px; font-weight: 600; margin: 0; text-align: center;}
.user-bubble {background-color: #D9FDD3; color: #111b21; padding: 10px 14px; border-radius: 18px; border-bottom-right-radius: 4px; max-width: 75%; margin-left: auto; margin-bottom: 10px; text-align: right;}
.gradient-text {background: linear-gradient(90deg, #ff00cc, #3333ff, #00ffcc); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
.age-btn-active {background: #2ecc71!important; color: white!important; border: 2px solid white!important;}
.game-card {background: white; padding: 15px; border-radius: 15px; border: 2px solid #eee; margin-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

# --- CONFIG ---
GROQ_MODELS = ["openai/gpt-oss-120b","openai/gpt-oss-20b","qwen/qwen3-32b","llama-3.1-70b-versatile","mixtral-8x7b-32768","llama-3.1-8b-instant"]

# ============ IMAGE FIX 2 & 3 ============
def generate_image_url(prompt, is_school_mode, age):
    # FIX: Galat image rokne ke liye negative prompt
    negative_words = "no person, no girl, no boy, no human face, no woman"

    # Agar user ne login, app, UI bola hai to person bilkul nahi
    ui_keywords = ["login", "app", "system", "dashboard", "wireframe", "diagram", "chart", "rocket science"]
    is_ui_request = any(k in prompt.lower() for k in ui_keywords)

    if is_ui_request:
        final_prompt = f"{prompt}, app UI wireframe, educational diagram, vector illustration, clean, {negative_words}"
    elif is_school_mode:
        if "1-2" in age or "3-4" in age:
            final_prompt = f"cute baby cartoon, very simple, bright colors, 3d pixar style, {prompt}, {negative_words}"
        else:
            final_prompt = f"kid friendly educational diagram, colorful, {prompt}, {negative_words}"
    else:
        final_prompt = f"realistic, cinematic, 4k, {prompt}"

    try:
        hf_key = st.secrets.get("HF_API_KEY", "")
        if hf_key:
            API_URL = "https://api-inference.huggingface.co/models/stabilityai/sdxl-turbo"
            headers = {"Authorization": f"Bearer {hf_key}"}
            r = requests.post(API_URL, headers=headers, json={"inputs": final_prompt}, timeout=20)
            if r.status_code == 200:
                return r.content, "huggingface"
    except: pass

    # FIX: 1024 se 512 kiya taaki bada na aaye
    poll_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(final_prompt)}?width=512&height=512&nologo=true&seed={uuid.uuid4().int % 10000}"
    return poll_url, "pollinations"

# ============ NEW: PRACTICAL GAME LAB - FIX 4 to 12 ============
def practical_game_mode():
    st.markdown("### 🎮 Practical Learning Lab - Indian Baccho ke liye")

    col1, col2 = st.columns([1,1])
    with col1:
        age = st.selectbox("Age Select Karo", ["1-2 Saal", "2-3 Saal", "3-4 Saal", "5-6 Saal", "6-8 Saal", "10-11 Saal", "11-12 Saal"], key="p_age")
    with col2:
        # FIX 9: Language dropdown ONLY yahan hai, bahar kahin nahi
        lang_mode = st.selectbox("🌐 Bhasha / Language", ["🇮🇳 Hindi se English Sikho", "English Only", "Hindi Only"], key="game_lang_only")

    category = st.radio("Kya seekhna hai?", ["✈️ Fly / Udna", "🍎 Fal / Fruits", "🚗 Gaadi / Vehicle", "🦁 Janwar / Animals", "📚 Daily English"], horizontal=True)

    INDIAN_ENGLISH_DATA = {
        "✈️ Fly / Udna": {"hindi": "Hawai Jahaj udta hai", "english": "Aeroplane flies", "options": ["✈️ Aeroplane flies", "🏍️ Motorcycle flies", "🚢 Ship flies", "🚂 Train flies"], "answer": "✈️ Aeroplane flies", "meaning": "Hawai jahaj aasman me udta hai"},
        "🍎 Fal / Fruits": {"hindi": "Laal Seb", "english": "Red Apple", "options": ["🍎 Red Apple", "🍌 Yellow Banana", "🚗 Gaadi", "🐶 Kutta"], "answer": "🍎 Red Apple", "meaning": "Laal rang ka seb"},
        "🚗 Gaadi / Vehicle": {"hindi": "Paani me kaun chalta hai?", "english": "Which goes on water?", "options": ["🚢 Ship goes on water", "🏍️ Bike goes on water", "🚂 Train goes on water", "✈️ Aeroplane goes on water"], "answer": "🚢 Ship goes on water", "meaning": "Jahaj paani me chalta hai"},
        "🦁 Janwar / Animals": {"hindi": "Kaun MOO bolta hai?", "english": "Which animal says MOO?", "options": ["🐄 Gaay / Cow", "🐱 Billi / Cat", "✈️ Jahaj", "🍎 Seb"], "answer": "🐄 Gaay / Cow", "meaning": "Gaay MOO bolti hai"},
        "📚 Daily English": {"hindi": "Mujhe paani chahiye", "english": "I need water", "options": ["💧 I need water", "🏍️ I need bike", "✈️ I need aeroplane", "🚂 I need train"], "answer": "💧 I need water", "meaning": "Roz bolne wala English"}
    }

    data = INDIAN_ENGLISH_DATA[category]

    if "1-2" in age or "2-3" in age:
        options_to_show = data["options"][:2]
    elif "3-4" in age:
        options_to_show = data["options"][:3]
    else:
        options_to_show = data["options"]

    if "Hindi se English" in lang_mode:
        st.markdown(f"<div class='game-card'><h3>🇮🇳 Hindi: {data['hindi']}</h3><p>👉 English me kya hoga? <br>💡 Matlab: {data['meaning']}</p></div>", unsafe_allow_html=True)
    elif lang_mode == "English Only":
        st.markdown(f"<div class='game-card'><h3>Q: {data['english']}?</h3></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='game-card'><h3>Q: {data['hindi']}</h3></div>", unsafe_allow_html=True)

    cols = st.columns(2)
    for i, opt in enumerate(options_to_show):
        if cols[i % 2].button(opt, key=f"opt_{opt}_{age}_{category}", use_container_width=True):
            if opt == data["answer"]:
                st.balloons()
                st.snow()
                st.success(f"🎉 CONGRATULATIONS! Sahi Jawab! {data['answer']}")
                if "Hindi se English" in lang_mode:
                    st.info(f"🔊 Bolo: **{data['english']}**")
                st.markdown("### 🌸🌼 Well Done Baccha! 🌸🌼")
            else:
                st.error(f"❌ Galat hai! Sahi hai: **{data['answer']}**")
                st.warning(f"💡 Yaad Karo: {data['hindi']} = {data['english']}")

    if st.button("🔄 Reset / Next Task"):
        st.rerun()

# ============ PROMPTS ============
NORMAL_SYSTEM_PROMPT = "You are ClyxessChat AI, created by ClyxessChat AI Technology. CORE RULE: REPLY ONLY IN SAME LANGUAGE AS USER. Friendly, calm. If user asks image, say: Generating image for: [prompt]"
def get_school_system_prompt(age_group):
    base = f"You are ClyxessChat AI - School Mode Creative Lab. Age: {age_group}. "
    if "1-2" in age_group or "3-4" in age_group:
        return base + "You are Didi for 1-4 years. Only rhymes, colors, emojis. Very short."
    elif "5-6" in age_group or "6-8" in age_group:
        return base + "Age 5-8: Curiosity & Basic Logic. Story-Building & Shape Puzzles."
    elif "10-11" in age_group:
        return base + "Age 7-10: Maker & Practical Science. Step-by-step DIY."
    else:
        return base + "Age 11+: Future Tech, AI & App Prototyping."

def search_tavily(query):
    search_words = ["news","mausam","weather","rate","price","score","aaj","kal","today","latest","breaking"]
    if not any(word in query.lower() for word in search_words): return "", ""
    try:
        url = "https://api.tavily.com/search"
        payload = {"api_key": st.secrets["TAVILY_API_KEY"], "query": query, "search_depth": "advanced", "max_results": 5, "include_answer": True}
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

# --- UI START ---
st.markdown('<div class="header"><h1>💬 ClyxessChat AI</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.title("💬 ClyxessChat AI")
    # FIX: 3rd mode add kiya
    mode = st.radio("Select Mode", ["Normal Chat", "Creative Lab (School Mode)", "🎮 Practical Game Lab"], index=0)
    st.markdown("---")
    age_group = "1-2 Yrs"
    if "Creative Lab" in mode:
        st.markdown("### 🎒 Age Group")
        cols = st.columns(2)
        age_options = ["1-2 Yrs", "3-4 Yrs", "5-6 Yrs", "6-8 Yrs", "10-11 Yrs", "11+ Yrs"]
        for i, ag in enumerate(age_options):
            if cols[i%2].button(ag, key=f"age_{ag}", use_container_width=True, type="primary" if st.session_state.get("age_group", "1-2 Yrs")==ag else "secondary"):
                st.session_state.age_group = ag
        age_group = st.session_state.get("age_group", "1-2 Yrs")
        st.success(f"Active: {age_group}")
    if st.button("+ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
if "age_group" not in st.session_state:
    st.session_state.age_group = "1-2 Yrs"

# --- IF GAME MODE, SHOW GAME ONLY ---
if "Practical Game Lab" in mode:
    practical_game_mode()
    st.stop()

# DISPLAY CHAT
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image_url" in message:
            # FIX 1: width 350
            st.image(message["image_url"], caption=message.get("image_caption",""), width=350)
        else:
            st.markdown(message["content"])

# CHAT INPUT
if prompt := st.chat_input("Apna idea type karein..." if "Creative" in mode else "Ask ClyxessChat AI"):
    is_school = "Creative" in mode
    current_age = st.session_state.age_group if is_school else "Normal"
    system_prompt = get_school_system_prompt(current_age) if is_school else NORMAL_SYSTEM_PROMPT

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f'<div class="user-bubble">{prompt}</div>', unsafe_allow_html=True)

    wants_image = any(w in prompt.lower() for w in ["image", "draw", "banao", "photo", "picture", "chitra", "rocket", "diagram"])

    with st.chat_message("assistant"):
        img_url_to_save = None

        if wants_image:
            with st.spinner("🎨 Image bana raha hu..."):
                img_data, source = generate_image_url(prompt, is_school, current_age)
                st.image(img_data, caption=f"Generated for: {prompt}", width=350)
                img_url_to_save = img_data

        # FIX 3: Image ke baad bhi jawab dega - ruka nahi
        message_placeholder = st.empty()
        full_response = ""
        with st.spinner("ClyxessChat AI is responding..."):
            search_context, sources = search_tavily(prompt)
            completion, used_model = get_groq_response(client, st.session_state.messages, system_prompt, search_context)
            if completion is None: st.stop()
            response = completion.choices[0].message.content
            if sources: response += f"\n\n**Source:**\n{sources}"

        for word in response.split():
            full_response += word + " "
            message_placeholder.markdown(full_response + "▌")
            time.sleep(0.02)
        message_placeholder.markdown(full_response)
        st.caption(f"Mode: {mode} | Age: {current_age} | Model: {used_model}")

        # FIX 3: Dono save hoga
        if img_url_to_save:
            st.session_state.messages.append({"role": "assistant", "image_url": img_url_to_save, "image_caption": prompt, "content": full_response})
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    st.rerun()
