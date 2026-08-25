import streamlit as st
from groq import Groq
from supabase import create_client
import uuid, requests, time, json

st.set_page_config(page_title="ClyxessChat AI", layout="centered")

# ===== FINAL ALIGNMENT FIX - ChatGPT 720px =====
st.markdown("""
<style>
[data-testid="block-container"] {max-width: 720px; margin: auto; padding-top: 0.5rem;}
.header {position: sticky; top: 0; background: #171717; padding: 14px; border-bottom: 1px solid #2f2f2f; z-index: 999; margin: -1rem -1rem 1rem -1rem; text-align:center;}
.header h1 {color: white; font-size: 20px; margin: 0;}
.user-bubble {background: #2f2f2f; color: #ececec; padding: 12px 16px; border-radius: 18px; max-width: 80%; margin-left: auto; line-height: 1.7; white-space: pre-wrap; word-wrap: break-word; text-align: left;}
.game-card {background: white; padding: 15px; border-radius: 15px; border: 2px solid #eee; color:#111; margin-bottom:10px;}
.pro-card {background: linear-gradient(135deg, #1f1f1f, #3a3a3a); color: white; padding: 18px; border-radius: 15px; border: 1px solid #555;}
pre {background: #0d0d0d!important; border: 1px solid #2f2f2f!important; border-radius: 10px!important; padding: 14px!important; overflow-x: auto;}
code {font-size: 13.5px!important; white-space: pre-wrap!important; word-break: break-word!important;}
</style>
""", unsafe_allow_html=True)

# ===== 10 MODEL - VALID NAMES - BUSY FIX =====
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
    "qwen-2.5-32b",
    "qwen-2.5-coder-32b",
    "deepseek-r1-distill-llama-70b"
]

def generate_image_url(prompt, is_school_mode, age):
    negative_words = "no person, no girl, no boy, no human face, no woman, no child photo"
    ui_keywords = ["login", "app", "system", "dashboard", "wireframe", "diagram", "chart", "engine", "cutaway", "blueprint", "circuit", "rocket"]
    is_ui_request = any(k in prompt.lower() for k in ui_keywords)
    if is_ui_request:
        final_prompt = f"{prompt}, technical blueprint, educational diagram, vector, clean, centered, 4k, {negative_words}"
    elif is_school_mode:
        final_prompt = f"kid friendly educational diagram, colorful, {prompt}, {negative_words}"
    else:
        final_prompt = f"realistic, cinematic, 4k, {prompt}, {negative_words}"
    poll_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(final_prompt)}?width=512&height=512&nologo=true&seed={uuid.uuid4().int % 10000}"
    return poll_url, "free"

# ===== STRICT LANGUAGE - 100% NO MIX =====
LANGS = {
    "Hindi": {"congrats": "🎉 बधाई हो! शाबाश!", "wrong": "गलत! फिर सोचो", "strict": "Reply ONLY in Hindi language. 100% Hindi. Do not use English at all. No Hinglish. Only Hindi."},
    "English": {"congrats": "🎉 Congratulations!", "wrong": "Wrong! Try again", "strict": "Reply ONLY in English language. 100% English. No other language."},
    "Marathi": {"congrats": "🎉 अभिनंदन!", "wrong": "चूक!", "strict": "Reply ONLY in Marathi language. 100% Marathi. No Hindi or English mix."},
    "Bangla": {"congrats": "🎉 অভিনন্দন!", "wrong": "ভুল!", "strict": "Reply ONLY in Bangla language. 100% Bangla. No English."},
    "Gujarati": {"congrats": "🎉 અભિનંદન!", "wrong": "ખોટું!", "strict": "Reply ONLY in Gujarati language. 100% Gujarati."},
    "Tamil": {"congrats": "🎉 வாழ்த்துக்கள்!", "wrong": "தவறு!", "strict": "Reply ONLY in Tamil language. 100% Tamil. No English or Hindi."},
    "Telugu": {"congrats": "🎉 అభినందనలు!", "wrong": "తప్పు!", "strict": "Reply ONLY in Telugu language. 100% Telugu."},
    "Malayalam": {"congrats": "🎉 അഭിനന്ദനങ്ങൾ!", "wrong": "തെറ്റ്!", "strict": "Reply ONLY in Malayalam language. 100% Malayalam."},
    "Kannada": {"congrats": "🎉 ಅಭಿನಂದನೆಗಳು!", "wrong": "ತಪ್ಪು!", "strict": "Reply ONLY in Kannada language. 100% Kannada."},
    "Odia": {"congrats": "🎉 ଅଭିନନ୍ଦନ!", "wrong": "ଭୁଲ!", "strict": "Reply ONLY in Odia language. 100% Odia."},
    "Chinese": {"congrats": "🎉 恭喜！", "wrong": "错了！", "strict": "Reply ONLY in Chinese language. 100% Chinese."},
    "Japanese": {"congrats": "🎉 おめでとう！", "wrong": "間違い！", "strict": "Reply ONLY in Japanese language. 100% Japanese."},
}

def fetch_mystery_from_groq(client, level, lang="Hindi"):
    strict_rule = LANGS.get(lang, LANGS["Hindi"])["strict"]
    system_prompt = (
        f"You are game engine Level {level}, age 11-20. {strict_rule} "
        f"Generate mystery Level {level} ONLY in {lang}. No mix. "
        'JSON only: {"story": "text in selected lang with question", "answer": "1-word or number"}'
    )
    for model in GROQ_MODELS[:3]: # top 3 se try
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt},{"role": "user", "content": f"Generate level {level} puzzle in {lang} only."}],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            data = json.loads(completion.choices[0].message.content)
            return data
        except: continue
    return {"story": f"Level {level} - 12 ka square kya hai?", "answer": "144"}

def practical_game_mode(client):
    if "game_level" not in st.session_state: st.session_state.game_level = 1
    if "current_story" not in st.session_state: st.session_state.current_story = None
    if "correct_answer" not in st.session_state: st.session_state.correct_answer = ""
    if "score" not in st.session_state: st.session_state.score = 0
    if "used_q" not in st.session_state: st.session_state.used_q = []
    if "eng_chat" not in st.session_state: st.session_state.eng_chat = []

    c1,c2,c3 = st.columns(3)
    with c1: age = st.selectbox("Age", ["1-2 Saal","3-4 Saal","5-6 Saal","6-8 Saal","10-12 Saal","11-15 Saal","16+ Saal","17-18 Saal","19-20 Saal"], key="p_age")
    with c2: sel_lang = st.selectbox("🌐 Language (12)", list(LANGS.keys()), index=0, key="game_lang_final")
    with c3: mode_type = st.selectbox("Mode", ["🎮 Game (10 Level)","💬 English Chat","🔧 PRO Engine Lab","🕵️ Cyber Detective (Groq Live)"], key="game_mode_type")

    txt = LANGS[sel_lang]

    if "PRO Engine" in mode_type:
        st.markdown(f"<div class='pro-card'><h2>🔧 Real Engine Lab - {age} - {sel_lang}</h2></div>", unsafe_allow_html=True)
        part = st.selectbox("Kya seekhna hai?", ["Bike Engine 4-Stroke","Car Engine","Jet Engine","Ship Engine","Electric Motor"])
        if st.button(f"🔍 {part} dikhao?", type="primary"):
            steps = [f"{part} all parts open blueprint", f"{part} assembly process", f"{part} cutaway working internal", f"{part} final fitted realistic"]
            for i,s in enumerate(steps,1):
                url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(s)}, highly detailed, engineering diagram, 4k, no person?width=512&height=512&seed={uuid.uuid4().int % 10000}"
                st.image(url, caption=f"Step {i}: {s}", width=350)

    if "Cyber Detective" in mode_type or ("11-15" in age) or ("16+" in age and mode_type=="🎮 Game (10 Level)"):
        if "Cyber Detective" in mode_type: st.title("🚀 AI Cyber Detective: Mission Mars")
        st.subheader(f"Level: {st.session_state.game_level} / 10 | Score: {st.session_state.score} | {sel_lang}")
        st.progress(st.session_state.game_level * 10)
        if st.session_state.current_story is None and st.session_state.game_level <= 10:
            with st.spinner(f"🕵️‍♂️ Groq AI {sel_lang} me naya case..."):
                mystery = fetch_mystery_from_groq(client, st.session_state.game_level, sel_lang)
                st.session_state.current_story = mystery.get("story")
                st.session_state.correct_answer = str(mystery.get("answer","")).strip().lower()
        if st.session_state.game_level <= 10:
            st.info(st.session_state.current_story)
            user_input = st.text_input("Jawab / Answer:", key=f"input_lvl_{st.session_state.game_level}_{age}").strip().lower()
            colA,colB = st.columns(2)
            with colA:
                if st.button("🚀 Verify", use_container_width=True, type="primary"):
                    if user_input == st.session_state.correct_answer:
                        st.balloons(); st.snow(); st.success(f"{txt['congrats']} 🌸")
                        st.session_state.game_level += 1; st.session_state.score += 10
                        st.session_state.current_story = None; time.sleep(0.5); st.rerun()
                    else: st.error(f"❌ {txt['wrong']} - {st.session_state.correct_answer}")
            with colB:
                if st.button("🔄 Skip", use_container_width=True):
                    st.session_state.current_story = None; st.rerun()
        else:
            st.balloons(); st.success(f"🏆 {txt['congrats']} 10 Level Complete!")
            if st.button("🔄 Restart", type="primary"):
                st.session_state.game_level=1; st.session_state.current_story=None; st.session_state.score=0; st.rerun()
        return

    if "English Chat" in mode_type:
        st.markdown(f"### 💬 {sel_lang} strict mode")
        for m in st.session_state.eng_chat:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if p := st.chat_input(f"{sel_lang} me likho..."):
            st.session_state.eng_chat.append({"role":"user","content":p})
            with st.chat_message("user"): st.markdown(p)
            with st.chat_message("assistant"):
                try:
                    comp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":f"{txt['strict']} You are English teacher. Only in {sel_lang}."},{"role":"user","content":p}], max_tokens=300)
                    ans = comp.choices[0].message.content
                except: ans = txt["congrats"]
                st.markdown(ans); st.session_state.eng_chat.append({"role":"assistant","content":ans})
        return

    SIMPLE_DB = {
        "1-2 Saal": [{"q":"🍎 Laal?","opts":["🍎 Seb","🏍️ Bike"],"ans":"🍎 Seb"}],
        "3-4 Saal": [{"q":"🐄 Moo?","opts":["🐄 Gaay","🐱 Billi"],"ans":"🐄 Gaay"}],
        "5-6 Saal": [{"q":"Ship kahan?","opts":["Water","Road"],"ans":"Water"}],
        "6-8 Saal": [{"q":"Which flies?","opts":["✈️ Plane","🚢 Ship"],"ans":"✈️ Plane"}],
        "10-12 Saal": [{"q":"Binary 10?","opts":["1010","1000"],"ans":"1010"}],
    }
    base = SIMPLE_DB.get(age, SIMPLE_DB["6-8 Saal"])
    db_list = (base * 10)[:10] # 10 unique Q
    st.progress(len(st.session_state.used_q)/10)
    st.markdown(f"### {sel_lang} | {age} | Q {len(st.session_state.used_q)+1}/10 | Score {st.session_state.score}")
    if len(st.session_state.used_q)>=10:
        st.balloons(); st.success(f"{txt['congrats']} Complete! 🌸")
        if st.button("Next Age", type="primary"): st.session_state.used_q=[]; st.session_state.score=0; st.rerun()
        return
    remaining = [i for i in range(10) if i not in st.session_state.used_q]
    if not remaining: st.session_state.used_q=[]; remaining=list(range(10))
    idx = remaining[0]; cur = db_list[idx]
    st.markdown(f"<div class='game-card'><h3>Q{len(st.session_state.used_q)+1}: {cur['q']}</h3></div>", unsafe_allow_html=True)
    cols=st.columns(2)
    for i,opt in enumerate(cur["opts"]):
        if cols[i%2].button(opt, key=f"s_{idx}_{opt}_{len(st.session_state.used_q)}", use_container_width=True):
            if opt==cur["ans"]:
                st.session_state.score+=10; st.session_state.used_q.append(idx); st.balloons(); st.success(txt['congrats']); time.sleep(0.4); st.rerun()
            else: st.error(f"{txt['wrong']}")

# ===== PROMPTS - FINAL =====
NORMAL_SYSTEM_PROMPT = """
You are ClyxessChat AI, PRO Coder.
RULES:
- Reply same language as user.
- For HTML/CSS/CODE: ALWAYS give code in ```html block with proper line breaks, centered flexbox:
body{display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#f5f5f5;}
.login-box{width:320px;padding:28px;background:white;border-radius:14px;box-shadow:0 6px 18px rgba(0,0,0,0.1);}
- Never write code in single messy line. Always formatted with new lines.
- After code, 2-3 short points only.
- Keep ChatGPT clean center alignment.
"""

def get_school_system_prompt(age):
    if "1-2" in age:
        return "You are Didi for 1-2 years. RULE: MAX 4 words + big emoji. No long line. Example: 'A for Apple 🍎'. No paragraph, No ###."
    elif "3-4" in age:
        return "You are Didi for 3-4 years. RULE: MAX 1 short line, MAX 7 words, big emoji, rhyme. No paragraph, No ###, No ---. Example: 'B for Ball ⚽ Ball gol hai!'"
    elif "5-6" in age:
        return "You are Teacher for 5-6 years. Max 2 short lines. Emoji + Hindi. Story style."
    else:
        return f"You are ClyxessChat AI School Mode {age}. Teach practical science, engine theory, coding with clean formatting. Code in ```html blocks centered."

def get_groq_response(client, messages, system_prompt):
    msgs = [{"role":"system","content":system_prompt}] + messages[-6:]
    last_err = ""
    for model in GROQ_MODELS:
        try:
            comp = client.chat.completions.create(model=model, messages=msgs, temperature=0.6, max_tokens=3500)
            return comp, model
        except Exception as e:
            last_err = str(e)
            continue
    return None, last_err

@st.cache_resource
def init_supabase():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None
supabase = init_supabase()

st.markdown('<div class="header"><h1>💬 ClyxessChat AI</h1></div>', unsafe_allow_html=True)
with st.sidebar:
    st.title("💬 ClyxessChat AI")
    mode = st.radio("Select Mode", ["Normal Chat","Creative Lab (School Mode)","🎮 Practical Game Lab"], index=0)
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
        completion,used_model = get_groq_response(client, st.session_state.messages, system_prompt)
        if completion is None:
            st.error(f"Groq 10 model fail: {used_model[:200]} | 1 min ruko, rate limit hai")
            st.stop()
        response = completion.choices[0].message.content
        for w in response.split():
            full+=w+" "; placeholder.markdown(full+"▌"); time.sleep(0.012)
        placeholder.markdown(full)
        st.caption(f"Mode: {mode} | Age: {current_age} | {used_model} | FREE IMG")
        if img_url: st.session_state.messages.append({"role":"assistant","image_url":img_url,"image_caption":prompt,"content":full})
        else: st.session_state.messages.append({"role":"assistant","content":full})
    st.rerun()
