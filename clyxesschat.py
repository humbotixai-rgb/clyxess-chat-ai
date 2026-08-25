import streamlit as st
from groq import Groq
from supabase import create_client
import datetime, uuid, requests, time, re, os, json
from fpdf import FPDF

st.set_page_config(page_title="ClyxessChat AI", layout="wide")

# --- CSS FIX 1: Image Chota ---
st.markdown("""
<style>
.main {max-width: 850px; margin: auto;}
.header {position: sticky; top: 0; background: #202123; padding: 18px; border-bottom: 1px solid #444; z-index: 999; margin: -1rem -1rem 20px -1rem;}
.header h1 {color: white; font-size: 22px; font-weight: 600; margin: 0; text-align: center;}
.user-bubble {background-color: #D9FDD3; color: #111b21; padding: 10px 14px; border-radius: 18px; border-bottom-right-radius: 4px; max-width: 75%; margin-left: auto; margin-bottom: 10px; text-align: right;}
.game-card {background: white; padding: 15px; border-radius: 15px; border: 2px solid #eee; margin-bottom: 10px; color:#111;}
.pro-card {background: linear-gradient(135deg, #1f1f1f, #3a3a3a); color: white; padding: 20px; border-radius: 15px; border: 1px solid #555; margin-bottom: 15px;}
</style>
""", unsafe_allow_html=True)

GROQ_MODELS = ["llama-3.3-70b-versatile","llama-3.1-8b-instant","llama-3.1-70b-versatile","openai/gpt-oss-120b","qwen/qwen3-32b","mixtral-8x7b-32768"]

# ============ IMAGE FIX 2 & 3 - FREE, NO API, IMAGE + TEXT DONO ============
def generate_image_url(prompt, is_school_mode, age):
    negative_words = "no person, no girl, no boy, no human face, no woman, no child photo"
    ui_keywords = ["login", "app", "system", "dashboard", "wireframe", "diagram", "chart", "engine", "cutaway", "blueprint", "circuit", "rocket"]
    is_ui_request = any(k in prompt.lower() for k in ui_keywords)
    if is_ui_request:
        final_prompt = f"{prompt}, technical blueprint, educational diagram, vector, clean, 4k, {negative_words}"
    elif is_school_mode:
        final_prompt = f"kid friendly educational diagram, colorful, {prompt}, {negative_words}"
    else:
        final_prompt = f"realistic, cinematic, 4k, {prompt}, {negative_words}"
    poll_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(final_prompt)}?width=512&height=512&nologo=true&seed={uuid.uuid4().int % 10000}"
    return poll_url, "free"

# ============ TERA CYBER DETECTIVE FUNCTION - FINAL ME JODA ============
def fetch_mystery_from_groq(client, level, lang="Hindi"):
    try:
        system_prompt = (
            f"You are game engine for {level} level, age 11-20. Language: {lang}. "
            f"Generate cyberpunk / space / engine / coding mystery for Level {level}. "
            "Must test logic, robotics, space, coding, engine theory. "
            "Story in Hinglish + English mix. "
            'MUST respond ONLY valid JSON: {"story": "text with question...", "answer": "1-word or number only"}'
        )
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt},{"role": "user", "content": f"Generate level {level} puzzle now."}],
            response_format={"type": "json_object"},
            temperature=0.8
        )
        data = json.loads(completion.choices[0].message.content)
        return data
    except Exception as e:
        return {"story": f"Machine Overload! Level {level}: 12 ka Square kya hai? (Hint: 12*12)", "answer": "144"}

# ============ FINAL GAME LAB - ALL 18 FIX + CYBER + ENGINE ============
def practical_game_mode(client):
    if "game_level" not in st.session_state: st.session_state.game_level = 1
    if "current_story" not in st.session_state: st.session_state.current_story = None
    if "correct_answer" not in st.session_state: st.session_state.correct_answer = ""
    if "score" not in st.session_state: st.session_state.score = 0
    if "used_q" not in st.session_state: st.session_state.used_q = []
    if "eng_chat" not in st.session_state: st.session_state.eng_chat = []

    LANGS = {
        "Hindi": {"congrats": "🎉 बधाई हो! शाबाश!", "wrong": "गलत! फिर सोचो", "next": "अगला", "well": "बहुत अच्छे!", "title": "खेल"},
        "English": {"congrats": "🎉 Congratulations!", "wrong": "Wrong! Try again", "next": "Next", "well": "Well Done!", "title": "Game"},
        "Marathi": {"congrats": "🎉 अभिनंदन!", "wrong": "चूक!", "next": "पुढचा", "well": "छान!", "title": "खेळ"},
        "Bangla": {"congrats": "🎉 অভিনন্দন!", "wrong": "ভুল!", "next": "পরবর্তী", "well": "ভালো!", "title": "খেলা"},
        "Gujarati": {"congrats": "🎉 અભિનંદન!", "wrong": "ખોટું!", "next": "આગળ", "well": "સરસ!", "title": "રમત"},
        "Tamil": {"congrats": "🎉 வாழ்த்துக்கள்!", "wrong": "தவறு!", "next": "அடுத்த", "well": "நன்று!", "title": "விளையாட்டு"},
        "Telugu": {"congrats": "🎉 అభినందనలు!", "wrong": "తప్పు!", "next": "తదుపరి", "well": "బాగుంది!", "title": "ఆట"},
        "Malayalam": {"congrats": "🎉 അഭിനന്ദനങ്ങൾ!", "wrong": "തെറ്റ്!", "next": "അടുത്ത", "well": "കൊള്ളാം!", "title": "കളി"},
        "Kannada": {"congrats": "🎉 ಅಭಿನಂದನೆಗಳು!", "wrong": "ತಪ್ಪು!", "next": "ಮುಂದಿನ", "well": "ಚೆನ್ನಾಗಿದೆ!", "title": "ಆಟ"},
        "Odia": {"congrats": "🎉 ଅଭିନନ୍ଦନ!", "wrong": "ଭୁଲ!", "next": "ପରବର୍ତ୍ତୀ", "well": "ଭଲ!", "title": "ଖେଳ"},
        "Chinese": {"congrats": "🎉 恭喜！", "wrong": "错了！", "next": "下一个", "well": "做得好！", "title": "游戏"},
        "Japanese": {"congrats": "🎉 おめでとう！", "wrong": "間違い！", "next": "次", "well": "よくできました！", "title": "ゲーム"},
    }

    c1,c2,c3 = st.columns(3)
    with c1: age = st.selectbox("Age", ["1-2 Saal","3-4 Saal","5-6 Saal","6-8 Saal","10-12 Saal","11-15 Saal","16+ Saal","17-18 Saal","19-20 Saal"], key="p_age")
    with c2: sel_lang = st.selectbox("🌐 Language (12)", list(LANGS.keys()), index=0, key="game_lang_final")
    with c3: mode_type = st.selectbox("Mode", ["🎮 Game (10 Level)","💬 English Chat","🔧 PRO Engine Lab","🕵️ Cyber Detective (Groq Live)"], key="game_mode_type")

    txt = LANGS[sel_lang]

    # PRO ENGINE LAB
    if "PRO Engine" in mode_type:
        st.markdown(f"<div class='pro-card'><h2>🔧 Real Engine Lab - {age}</h2><p>4 Step Real Image + Theory</p></div>", unsafe_allow_html=True)
        part = st.selectbox("Kya seekhna hai?", ["Bike Engine 4-Stroke","Car Engine","Jet Engine","Ship Engine","Electric Motor"])
        if st.button(f"🔍 {part} kaise banta hai dikhao?", type="primary"):
            steps = [f"{part} all parts open blueprint", f"{part} assembly process", f"{part} cutaway working internal", f"{part} final fitted realistic"]
            for i,s in enumerate(steps,1):
                url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(s)}, highly detailed, engineering diagram, 4k, no person?width=512&height=512&seed={uuid.uuid4().int % 10000}"
                st.image(url, caption=f"Step {i}: {s}", width=350)
                st.write(f"**English:** {s} shows {part} working. **{sel_lang}:** {txt['well']}")

    # CYBER DETECTIVE - TERA WALA FUNCTION YAHAN USE HOGA
    if "Cyber Detective" in mode_type or ("11-15" in age) or ("16+" in age and st.session_state.game_level<=10 and mode_type=="🎮 Game (10 Level)"):
        if "Cyber Detective" in mode_type: st.title("🚀 AI Cyber Detective: Mission Mars")
        st.subheader(f"Level: {st.session_state.game_level} / 10 | Score: {st.session_state.score} | {sel_lang} | Status: Active Investigation")
        st.progress(st.session_state.game_level * 10)

        if st.session_state.current_story is None and st.session_state.game_level <= 10:
            with st.spinner(f"🕵️‍♂️ Groq AI {sel_lang} me naya case bana raha hai..."):
                mystery = fetch_mystery_from_groq(client, st.session_state.game_level, sel_lang)
                st.session_state.current_story = mystery.get("story")
                st.session_state.correct_answer = str(mystery.get("answer","")).strip().lower()

        if st.session_state.game_level <= 10:
            st.markdown("### 🔍 Secret Mission:")
            st.info(st.session_state.current_story)
            user_input = st.text_input("Secret code / Jawab:", key=f"input_lvl_{st.session_state.game_level}_{age}").strip().lower()
            colA,colB = st.columns(2)
            with colA:
                if st.button("🚀 Code Verify Karo", use_container_width=True, type="primary"):
                    if user_input == st.session_state.correct_answer:
                        st.balloons(); st.snow()
                        st.success(f"{txt['congrats']} Access Granted! 🌸🌼🎈")
                        st.session_state.game_level += 1; st.session_state.score += 10
                        st.session_state.current_story = None; time.sleep(0.5); st.rerun()
                    else:
                        st.error(f"❌ {txt['wrong']} Sahi: {st.session_state.correct_answer}")
            with colB:
                if st.button("🔄 Reset / Skip", use_container_width=True):
                    st.session_state.current_story = None; st.rerun()
        else:
            st.snow(); st.balloons()
            st.success(f"🏆 {txt['congrats']} 10 Level Complete! Master Jasoos!")
            if st.button("🔄 Mission Dobara Start", type="primary"):
                st.session_state.game_level=1; st.session_state.current_story=None; st.session_state.score=0; st.rerun()
        return

    # ENGLISH CHAT MODE
    if "English Chat" in mode_type:
        st.markdown(f"### 💬 {sel_lang} se English Sikho")
        for m in st.session_state.eng_chat:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if p := st.chat_input(f"{sel_lang} me likho..."):
            st.session_state.eng_chat.append({"role":"user","content":p})
            with st.chat_message("user"): st.markdown(p)
            with st.chat_message("assistant"):
                try:
                    comp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":f"You are English teacher. Kid lang {sel_lang}. Reply: English: [] Matlab({sel_lang}): [] Example: [] {txt['congrats']}"},{"role":"user","content":p}], max_tokens=300)
                    ans = comp.choices[0].message.content
                except: ans = f"✅ English: I need water\n💡 Matlab: Mujhe paani\n🎉 {txt['congrats']}"
                st.markdown(ans); st.session_state.eng_chat.append({"role":"assistant","content":ans})
        return

    # SIMPLE GAME FOR 1-10
    SIMPLE_DB = {
        "1-2 Saal": [{"q":"🍎 Laal kya?","opts":["🍎 Seb","🏍️ Bike"],"ans":"🍎 Seb"}]*10,
        "3-4 Saal": [{"q":"🐄 Moo kaun?","opts":["🐄 Gaay","🐱 Billi","🚗 Car"],"ans":"🐄 Gaay"}]*10,
        "5-6 Saal": [{"q":"Ship kahan?","opts":["Water","Road","Sky"],"ans":"Water"},{"q":"I need water=?","opts":["Mujhe paani","Mujhe bike"],"ans":"Mujhe paani"}]*5,
        "6-8 Saal": [{"q":"Which flies?","opts":["✈️ Aeroplane","🚢 Ship"],"ans":"✈️ Aeroplane"},{"q":"10*5?","opts":["50","10"],"ans":"50"}]*5,
        "10-12 Saal": [{"q":"Why Aeroplane flies? Bernoulli","opts":["Air pressure","Water","Wheel"],"ans":"Air pressure"},{"q":"Binary 10?","opts":["1010","1000"],"ans":"1010"}]*5,
    }
    db = SIMPLE_DB.get(age, SIMPLE_DB["6-8 Saal"])
    st.progress(len(st.session_state.used_q)/10)
    st.markdown(f"### {txt['title']}: {age} | {len(st.session_state.used_q)+1}/10 | Score {st.session_state.score}")
    if len(st.session_state.used_q)>=10:
        st.balloons(); st.success(f"{txt['congrats']} {age} Complete! Ab upar wala age karo! 🌸")
        if st.button("Next Age Unlock", type="primary"): st.session_state.used_q=[]; st.session_state.score=0; st.rerun()
        return
    remaining = [i for i in range(len(db)) if i not in st.session_state.used_q]
    if not remaining: st.session_state.used_q=[]; remaining=list(range(len(db)))
    idx = remaining[0]; cur = db[idx]
    st.markdown(f"<div class='game-card'><h3>Q{len(st.session_state.used_q)+1}: {cur['q']}</h3></div>", unsafe_allow_html=True)
    cols=st.columns(2)
    for i,opt in enumerate(cur["opts"]):
        if cols[i%2].button(opt, key=f"s_{idx}_{opt}_{len(st.session_state.used_q)}", use_container_width=True):
            if opt==cur["ans"]:
                st.session_state.score+=10; st.session_state.used_q.append(idx); st.balloons(); st.success(txt['congrats']); time.sleep(0.5); st.rerun()
            else: st.error(f"{txt['wrong']} Sahi: {cur['ans']}")

# PROMPTS
NORMAL_SYSTEM_PROMPT = "You are ClyxessChat AI. Reply same language as user. If image request, say Generating image for: [prompt] + explain too."
def get_school_system_prompt(age):
    return f"You are ClyxessChat AI School Mode {age}. Age 1-4 rhymes, 5-10 maker, 11-20 future tech + real engine theory + coding. Real diagrams."

def get_groq_response(client, messages, system_prompt, search_context=""):
    final_system = system_prompt + (f"\nLive:{search_context}" if search_context else "")
    msgs = [{"role":"system","content":final_system}] + messages[-6:]
    for model in GROQ_MODELS:
        try:
            comp = client.chat.completions.create(model=model, messages=msgs, temperature=0.7, max_tokens=4000)
            return comp, model
        except: continue
    return None, None

@st.cache_resource
def init_supabase():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None
supabase = init_supabase()

st.markdown('<div class="header"><h1>💬 ClyxessChat AI</h1></div>', unsafe_allow_html=True)
with st.sidebar:
    st.title("💬 ClyxessChat AI")
    mode = st.radio("Select Mode", ["Normal Chat","Creative Lab (School Mode)","🎮 Practical Game Lab"], index=0)
    st.markdown("---")
    if "Creative Lab" in mode:
        cols=st.columns(2)
        opts=["1-2 Yrs","3-4 Yrs","5-6 Yrs","6-8 Yrs","10-12 Yrs","11-15 Yrs","16+ Yrs","17-18 Yrs","19-20 Yrs"]
        for i,ag in enumerate(opts):
            if cols[i%2].button(ag, key=f"age_{ag}", use_container_width=True, type="primary" if st.session_state.get("age_group")==ag else "secondary"): st.session_state.age_group=ag
        st.success(f"Active: {st.session_state.get('age_group','1-2 Yrs')}")
    if st.button("+ New Chat", use_container_width=True):
        st.session_state.messages=[]; st.session_state.session_id=str(uuid.uuid4()); st.rerun()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])
if "messages" not in st.session_state: st.session_state.messages=[]; st.session_state.session_id=str(uuid.uuid4())
if "age_group" not in st.session_state: st.session_state.age_group="1-2 Yrs"
if "groq_client" not in st.session_state: st.session_state.groq_client = client

if "Practical Game Lab" in mode:
    practical_game_mode(client)
    st.stop()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image_url" in message: st.image(message["image_url"], caption=message.get("image_caption",""), width=350)
        st.markdown(message.get("content",""))

if prompt := st.chat_input("Apna idea type karein..." if "Creative" in mode else "Ask ClyxessChat AI"):
    is_school = "Creative" in mode
    current_age = st.session_state.age_group if is_school else "Normal"
    system_prompt = get_school_system_prompt(current_age) if is_school else NORMAL_SYSTEM_PROMPT
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"): st.markdown(f'<div class="user-bubble">{prompt}</div>', unsafe_allow_html=True)
    wants_image = any(w in prompt.lower() for w in ["image","draw","banao","photo","picture","diagram","engine","cutaway","blueprint"])

    with st.chat_message("assistant"):
        img_url=None
        if wants_image:
            with st.spinner("🎨 Image (Free 512px)..."):
                img_data,_ = generate_image_url(prompt, is_school, current_age)
                st.image(img_data, caption=f"Generated: {prompt}", width=350)
                img_url=img_data
        placeholder=st.empty(); full=""
        completion,used_model = get_groq_response(client, st.session_state.messages, system_prompt, "")
        if completion is None: st.error("Busy try again"); st.stop()
        response = completion.choices[0].message.content
        for w in response.split():
            full+=w+" "; placeholder.markdown(full+"▌"); time.sleep(0.015)
        placeholder.markdown(full)
        st.caption(f"Mode: {mode} | Age: {current_age} | {used_model} | FREE IMG")
        if img_url: st.session_state.messages.append({"role":"assistant","image_url":img_url,"image_caption":prompt,"content":full})
        else: st.session_state.messages.append({"role":"assistant","content":full})
    st.rerun()
