import streamlit as st
from groq import Groq
from supabase import create_client
import datetime, uuid, requests, time, re, os, random, json
from typing import Dict, List, Any
from fpdf import FPDF

# --- SINGLE PAGE CONFIG ---
st.set_page_config(page_title="ClyxessChat AI", page_icon="💬", layout="wide")

# --- CSS COMMON ---
st.markdown("""
<style>
.main {max-width: 850px; margin: auto;}
.header {position: sticky; top: 0; background: #202123; padding: 18px; border-bottom: 1px solid #444; z-index: 999; margin: -1rem -1rem 20px -1rem;}
.header h1 {color: white; font-size: 22px; font-weight: 600; margin: 0; text-align: center;}
.user-bubble {background-color: #D9FDD3; color: #111b21; padding: 10px 14px; border-radius: 18px; border-bottom-right-radius: 4px; max-width: 75%; margin-left: auto; margin-bottom: 10px; text-align: right;}
.game-card {background: white; padding: 15px; border-radius: 15px; border: 2px solid #eee; margin-bottom: 10px;}
.main-title {padding: 24px; border-radius: 20px; background: linear-gradient(135deg,#0f172a,#172554); color: white; margin-bottom: 25px;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# PART 1: YOUR MAIN CODE CONFIG (NORMAL + SCHOOL)
# ============================================================
GROQ_MODELS = ["openai/gpt-oss-120b","openai/gpt-oss-20b","qwen/qwen3-32b","llama-3.1-70b-versatile","mixtral-8x7b-32768","llama-3.1-8b-instant"]

def generate_image_url(prompt, is_school_mode, age):
    # FINAL FIX: No person on UI request + 512 size
    negative_words = "no person, no girl, no boy, no human face, no woman"
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
    poll_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(final_prompt)}?width=512&height=512&nologo=true&seed={uuid.uuid4().int % 10000}"
    return poll_url, "pollinations"

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

# ============================================================
# PART 2: YOUR NEW GAME CODE CONFIG (FUTURE TECH GAME)
# ============================================================
QUESTIONS_PER_LEVEL = 10
AGE_LEVELS = ["1–2 Years","3–4 Years","5–6 Years","6–8 Years","8–10 Years","10–11 Years","11+ Years"]
AGE_SUBJECTS = {
    "1–2 Years": ["Colors","Shapes","Animals","Sounds","Basic Language","Memory"],
    "3–4 Years": ["Numbers","Language","Shapes","Storytelling","Communication","Logic"],
    "5–6 Years": ["Maths","Science Basics","Language","Reading","Logic","Creativity"],
    "6–8 Years": ["Maths","Science","English","General Knowledge","Logic","Communication","Technology Basics"],
    "8–10 Years": ["Maths","Science","English","Coding Basics","AI Introduction","Financial Literacy","Communication"],
    "10–11 Years": ["Advanced Maths","Science","Technology","AI Literacy","Coding","Financial Literacy","Critical Thinking"],
    "11+ Years": ["AI & Technology","Coding","Financial Literacy","Cyber Safety","Communication","Entrepreneurship","Critical Thinking","Problem Solving"]
}
QUESTION_BANK = {
    "Maths": [{"question":"What is 7 + 5?","options":["10","12","14","15"],"answer":"12","explanation":"7 + 5 = 12."},{"question":"What is 6 × 4?","options":["20","22","24","26"],"answer":"24","explanation":"6 groups of 4 make 24."}],
    "Science": [{"question":"Which planet do we live on?","options":["Mars","Earth","Venus","Jupiter"],"answer":"Earth","explanation":"We live on planet Earth."}],
    "Financial Literacy": [{"question":"If you receive ₹100 and save ₹20, how much is left to spend?","options":["₹60","₹70","₹80","₹90"],"answer":"₹80","explanation":"₹100 - ₹20 = ₹80."}],
    "AI Introduction": [{"question":"What does AI stand for?","options":["Artificial Intelligence","Automatic Internet","Advanced Input","Application Interface"],"answer":"Artificial Intelligence","explanation":"AI stands for Artificial Intelligence."}],
    "Coding": [{"question":"What is code?","options":["Instructions given to a computer","A type of food","A school bag","A musical instrument"],"answer":"Instructions given to a computer","explanation":"Code contains instructions that computers can execute."}],
    "Cyber Safety": [{"question":"Should you share your password with strangers online?","options":["Yes","No"],"answer":"No","explanation":"Passwords should be kept private."}],
    "Entrepreneurship": [{"question":"What is one important part of starting a useful product?","options":["Understanding a real problem","Ignoring customers","Copying everything","Never testing the idea"],"answer":"Understanding a real problem","explanation":"Good products usually solve a real problem."}],
    "Logic": [{"question":"What comes next: 2, 4, 6, 8,?","options":["9","10","11","12"],"answer":"10","explanation":"The pattern increases by 2."}],
    "Communication": [{"question":"Someone says 'Thank you'. What is a polite response?","options":["You're welcome","Go away","No","Stop"],"answer":"You're welcome","explanation":"You're welcome is a polite response."}],
}

def build_demo_questions(subject: str):
    bank = QUESTION_BANK.get(subject, [])
    if not bank: return []
    result = [{"question":i["question"],"options":list(i["options"]),"answer":i["answer"],"explanation":i.get("explanation","")} for i in bank]
    random.shuffle(result)
    while len(result) < QUESTIONS_PER_LEVEL:
        result.extend(result[:min(len(result), QUESTIONS_PER_LEVEL - len(result))])
    return result[:QUESTIONS_PER_LEVEL]

def generate_ai_questions(age, language, subject, count=10):
    return build_demo_questions(subject)

# ============================================================
# SIDEBAR - 3 SECTION SELECTOR (FINAL FIX)
# ============================================================
with st.sidebar:
    st.title("💬 ClyxessChat AI")
    # YAHI 3 ALAG SECTION HAI - MIX NAHI HOGA
    mode = st.radio("Select Mode", ["Normal Chat", "Creative Lab (School Mode)", "🎮 Play & Learn Game"], index=0)
    st.markdown("---")
    if "Creative Lab" in mode:
        st.markdown("### 🎒 Age Group")
        cols = st.columns(2)
        age_options = ["1-2 Yrs", "3-4 Yrs", "5-6 Yrs", "6-8 Yrs", "10-11 Yrs", "11+ Yrs"]
        for i, ag in enumerate(age_options):
            if cols[i%2].button(ag, key=f"age_{ag}", use_container_width=True, type="primary" if st.session_state.get("age_group", "1-2 Yrs")==ag else "secondary"):
                st.session_state.age_group = ag
        st.success(f"Active: {st.session_state.get('age_group','1-2 Yrs')}")
    if "Normal" in mode or "Creative" in mode:
        if st.button("+ New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()

# --- COMMON SESSION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
if "age_group" not in st.session_state:
    st.session_state.age_group = "1-2 Yrs"
if "selected_age" not in st.session_state:
    st.session_state.selected_age = AGE_LEVELS[0]
    st.session_state.unlocked_levels = [AGE_LEVELS[0]]
    st.session_state.game_started = False
    st.session_state.questions = []
    st.session_state.question_index = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.last_correct = False
    st.session_state.last_explanation = ""

# ============================================================
# SECTION 3: GAME MODE (ALAG SECTION)
# ============================================================
if "Play & Learn Game" in mode:
    st.markdown('<div class="main-title"><h1>🎮 ClyxessChat AI — Play & Learn</h1><p>Future Tech + Finance + Business Learning</p></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_age = st.selectbox("👶 Select Age", AGE_LEVELS, index=AGE_LEVELS.index(st.session_state.selected_age))
    with col2:
        LANGUAGES = {"🇮🇳 हिंदी":"hi","🇬🇧 English":"en"}
        language_label = st.selectbox("🌐 Language", list(LANGUAGES.keys()))
        selected_language = LANGUAGES[language_label]
    with col3:
        subjects = AGE_SUBJECTS.get(selected_age, [])
        selected_subject = st.selectbox("📚 Select Subject", subjects)
    st.session_state.selected_age = selected_age

    if selected_age not in st.session_state.unlocked_levels:
        st.error(f"🔒 {selected_age} is locked. Complete previous level with 10/10")
        st.stop()

    if not st.session_state.game_started:
        st.markdown('<div class="game-card">', unsafe_allow_html=True)
        st.subheader("🎯 Ready to Learn?")
        st.info("🎮 10 questions होंगे। 10/10 complete करने पर अगला age level unlock होगा.")
        if st.button("🚀 Start Game", use_container_width=True, type="primary"):
            questions = generate_ai_questions(selected_age, selected_language, selected_subject)
            st.session_state.questions = questions
            st.session_state.question_index = 0
            st.session_state.score = 0
            st.session_state.answered = False
            st.session_state.game_started = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    questions = st.session_state.questions
    q_idx = st.session_state.question_index
    current = questions[q_idx]
    st.progress(q_idx/QUESTIONS_PER_LEVEL, text=f"Question {q_idx+1}/{QUESTIONS_PER_LEVEL}")
    c1,c2 = st.columns(2)
    c1.metric("🎯 Question", f"{q_idx+1}/10")
    c2.metric("⭐ Score", f"{st.session_state.score}/10")
    st.markdown('<div class="game-card">', unsafe_allow_html=True)
    st.subheader(f"❓ {current['question']}")
    answer = st.radio("Choose:", current["options"], key=f"ans_{q_idx}")
    st.markdown("</div>", unsafe_allow_html=True)

    if not st.session_state.answered:
        if st.button("✅ Submit Answer", use_container_width=True, type="primary"):
            if answer == current["answer"]:
                st.session_state.score += 1
                st.session_state.last_correct = True
            else:
                st.session_state.last_correct = False
            st.session_state.last_explanation = current.get("explanation","")
            st.session_state.answered = True
            st.rerun()
    if st.session_state.answered:
        if st.session_state.last_correct: st.success(f"✅ Correct! Score: {st.session_state.score}/10")
        else: st.warning(f"❌ Correct answer: {current['answer']}")
        if st.session_state.last_explanation: st.info(f"💡 {st.session_state.last_explanation}")
        if q_idx < 9:
            if st.button("➡️ Next Question", use_container_width=True):
                st.session_state.question_index += 1
                st.session_state.answered = False
                st.rerun()
        else:
            if st.session_state.score == 10:
                st.balloons()
                st.success("🏆 LEVEL COMPLETE! 10/10")
                idx = AGE_LEVELS.index(selected_age)
                if idx+1 < len(AGE_LEVELS):
                    nxt = AGE_LEVELS[idx+1]
                    if nxt not in st.session_state.unlocked_levels:
                        st.session_state.unlocked_levels.append(nxt)
                    st.success(f"🔓 Next Level Unlocked: {nxt}")
            else:
                st.warning(f"Final Score: {st.session_state.score}/10 - 10/10 for next level unlock")
                if st.button("🔄 Retry Level", use_container_width=True, type="primary"):
                    st.session_state.game_started = False
                    st.rerun()
    st.stop()

# ============================================================
# SECTION 1 & 2: NORMAL + CREATIVE LAB (TERA PURANA CODE SAME)
# ============================================================
st.markdown('<div class="header"><h1>💬 ClyxessChat AI</h1></div>', unsafe_allow_html=True)
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image_url" in message:
            st.image(message["image_url"], caption=message.get("image_caption",""), width=350)
        else:
            st.markdown(message["content"])

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
        if img_url_to_save:
            st.session_state.messages.append({"role": "assistant", "image_url": img_url_to_save, "image_caption": prompt, "content": full_response})
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()
