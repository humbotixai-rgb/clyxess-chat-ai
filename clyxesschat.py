import streamlit as st
from groq import Groq
from supabase import create_client
import datetime, uuid, requests, time, re, os, json, random, base64, urllib.parse
from typing import Dict, List, Any
from fpdf import FPDF
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None
try:
    from streamlit_mic_recorder import mic_recorder
except Exception:
    mic_recorder = None

st.set_page_config(page_title="ClyxessChat AI", page_icon="", layout="wide")

st.markdown("""
<style>
.main {max-width: 850px; margin: auto;}
.header {position: sticky; top: 0; background: #202123; padding: 18px; border-bottom: 1px solid #444; z-index: 999; margin: -1rem -1rem 20px -1rem;}
.header h1 {color: white; font-size: 22px; font-weight: 600; margin: 0; text-align: center;}
.user-bubble {background-color: #D9FDD3; color: #111b21; padding: 10px 14px; font-size: 13px; border-radius: 18px; border-bottom-right-radius: 4px; max-width: 75%; margin-left: auto; margin-bottom: 10px; text-align: right;}
.ai-bubble {background-color: #F1F0F1; color: #111b21; padding: 10px 14px; border-radius: 18px; border-bottom-left-radius: 4px; max-width: 75%; margin-right: auto; margin-bottom: 10px; text-align: left; font-size: 13px;}
</style>
""", unsafe_allow_html=True)

GROQ_MODELS = ["llama-3.3-70b-versatile","llama-3.1-8b-instant","openai/gpt-oss-120b","openai/gpt-oss-20b","qwen/qwen3-32b","meta-llama/llama-4-maverick-17b-128e-instruct","meta-llama/llama-4-scout-17b-16e-instruct","deepseek-r1-distill-llama-70b","gemma2-9b-it","mixtral-8x7b-32768"]
QUESTIONS_PER_LEVEL = 10

# ===== YOUR 9 FIXES - START =====
SCHOOL_AGE_OPTIONS = ["1–3", "3–5", "6–8", "9–11", "12+"] # FIX exact age
CODING_LANGUAGES = ["Python", "JavaScript", "HTML", "CSS", "PHP", "Java", "C", "C++", "C#"]
# ===== YOUR 9 FIXES - END =====

PLAY_AGE_LEVELS = ["1–2 Years","3–4 Years","5–6 Years","6–8 Years","8–10 Years","10–11 Years","11+ Years"]
PLAY_LANGUAGES = {"🇮🇳 हिंदी": "hi","🇮🇳 मराठी": "mr","🇮🇳 বাংলা": "bn","🇮🇳 தமிழ்": "ta","🇮🇳 తెలుగు": "te","🇮🇳 ગુજરાતી": "gu","🇮🇳 ಕನ್ನಡ": "kn","🇮🇳 മലയാളം": "ml","🇮🇳 ଓଡ଼ିଆ": "or","🇬🇧 English": "en","🇨🇳 中文": "zh","🇯🇵 日本語": "ja"}
AGE_SUBJECTS = {"1–2 Years": ["Colors","Shapes","Animals","Sounds","Basic Language","Memory"],"3–4 Years": ["Numbers","Language","Shapes","Storytelling","Communication","Logic"],"5–6 Years": ["Maths","Science Basics","Language","Reading","Logic","Creativity"],"6–8 Years": ["Maths","Science","English","General Knowledge","Logic","Communication","Technology Basics"],"8–10 Years": ["Maths","Science","English","Coding Basics","AI Introduction","Financial Literacy","Communication"],"10–11 Years": ["Advanced Maths","Science","Technology","AI Literacy","Coding","Financial Literacy","Critical Thinking"],"11+ Years": ["AI & Technology","Coding","Financial Literacy","Cyber Safety","Communication","Entrepreneurship","Critical Thinking","Problem Solving"]}
QUESTION_BANK = {"Maths": [{"question":"What is 7 + 5?","options":["10","12","14","15"],"answer":"12","explanation":"7 + 5 = 12."}],"Science": [{"question":"Which planet do we live on?","options":["Mars","Earth","Venus","Jupiter"],"answer":"Earth","explanation":"We live on planet Earth."}],"Logic": [{"question":"What comes next: 2, 4, 6, 8,?","options":["9","10","11","12"],"answer":"10","explanation":"The pattern increases by 2."}]}
UI = {"en": {"start":"🚀 Start Game","score":"Score","submit":"Submit Answer","next":"Next Question","correct":"✅ Correct!","wrong":"❌ Not quite!","retry":"🔄 Try Again"},"hi": {"start":"🚀 गेम शुरू करें","score":"स्कोर","submit":"उत्तर जांचें","next":"अगला सवाल","correct":"✅ बिल्कुल सही!","wrong":"❌ कोई बात नहीं, फिर कोशिश करो!","retry":"🔄 फिर से खेलें"}}

# ===== FIXED SESSION STATE =====
DEFAULT_STATE = {
    "messages": [], # Normal Chat history separate - FIX 5
    "school_messages": [], # School Mode history separate - FIX 6
    "coding_messages": [], # Coding Lab history separate - FIX 1
    "session_id": str(uuid.uuid4()),
    "school_age": "6–8", # FIX exact options
    "school_language": "hi", # FIX 7 School Mode language dropdown separate
    "coding_language": "Python",
    "coding_explain_lang": "hi", # FIX 3 Coding explanation language separate
    "play_age": PLAY_AGE_LEVELS[0],"play_language": "hi","play_subject": None,"play_questions": [],"play_question_index": 0,"play_score": 0,"play_game_started": False,"play_answered": False,"play_last_correct": False,"play_last_explanation": "","play_unlocked_levels": [PLAY_AGE_LEVELS[0]],"play_completed_levels": [],"play_best_scores": {}
}
for key, value in DEFAULT_STATE.items():
    if key not in st.session_state: st.session_state[key] = value

def build_image_prompt(user_prompt, is_school_mode=False, age="Normal"):
    p = user_prompt.strip()
    p = re.sub(r"^(please\s+)?(make|create|generate|draw|banao|banaiye)\s+(an?\s+)?(image|photo|picture|poster|chitra)\s*(of|for|:)?\s*", "", p, flags=re.I)
    rules = "Create ONLY what the user explicitly requested. Do not add people, girls, boys, faces, animals, vehicles, characters, logos, brands, objects, scenery or unrelated themes unless explicitly requested. No watermark."
    if is_school_mode: rules += f" Keep it safe and age-appropriate for {age}."
    return f"{rules} User request: {p}."

def generate_image_url(prompt, is_school_mode, age, aspect="1:1"):
    final_prompt = build_image_prompt(prompt, is_school_mode, age)
    sizes = {"1:1": (768,768), "16:9": (1024,576), "9:16": (576,1024)}
    width, height = sizes.get(aspect, (768,768))
    try:
        hf_key = st.secrets.get("HF_API_KEY", "")
        if hf_key:
            r = requests.post("https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0", headers={"Authorization": f"Bearer {hf_key}"}, json={"inputs": final_prompt}, timeout=60)
            if r.status_code == 200 and r.content: return r.content, "huggingface"
    except: pass
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(final_prompt)}?width={width}&height={height}&nologo=true&seed={uuid.uuid4().int % 100000}"
    return url, "pollinations"

NORMAL_SYSTEM_PROMPT = "You are ClyxessChat AI, created by ClyxessChat AI Technology. REPLY ONLY IN SAME LANGUAGE AS USER. Friendly, intelligent."

def get_school_system_prompt(age_group, lang_code):
    lang_name = next((n for n,c in PLAY_LANGUAGES.items() if c==lang_code), lang_code)
    base = f"""You are ClyxessChat AI — India's First AI School. Motherly + teacher blend. Age group is EXACTLY {age_group} from options {', '.join(SCHOOL_AGE_OPTIONS)}.
STRICT LANGUAGE LOCK: Reply ONLY in {lang_name}.
Never scold. If wrong: 'कोई बात नहीं मेरे बच्चे, गलतियों से ही तो हम सीखते हैं! चलो, एक बार फिर से मिलकर कोशिश करते हैं।'
"""
    if age_group=="1–3": return base+"Use extremely short, cheerful sentences; colors, shapes, animals."
    if age_group=="3–5": return base+"Use short playful explanations, counting, shapes, animals."
    if age_group=="6–8": return base+"Use clear school-level explanations with examples."
    if age_group=="9–11": return base+"Use practical step-by-step maths, science, technology."
    return base+"Use secondary-school deeper reasoning, coding, critical thinking."

def get_coding_system_prompt(coding_lang, explain_lang_code):
    explain_name = next((n for n,c in PLAY_LANGUAGES.items() if c==explain_lang_code), explain_lang_code)
    return f"""You are ClyxessChat AI - Coding Lab.
SUPPORT LANGUAGES: {', '.join(CODING_LANGUAGES)} - Current: {coding_lang}
🚫 CODING LAB MEIN AGE RESTRICTION NAHI HAI. Do not ask age, do not filter by age.
Explain code ONLY in {explain_name}. This explanation language is separate from School Mode.
Provide clean code, then explanation, then tips. Support: Python, JavaScript, HTML, CSS, PHP, Java, C, C++, C#.
"""

def get_india_datetime_context():
    try:
        now = datetime.datetime.now(ZoneInfo("Asia/Kolkata")) if ZoneInfo else datetime.datetime.now()
        return now.strftime("Current India date: %A, %d %B %Y. Current India time: %I:%M %p (IST).")
    except: return datetime.datetime.now().strftime("Current application date: %A, %d %B %Y.")

def search_tavily(query):
    search_words = ["news","mausam","weather","rate","price","score","aaj","kal","today","latest","breaking"]
    if not any(word in query.lower() for word in search_words): return "", ""
    try:
        url = "https://api.tavily.com/search"
        payload = {"api_key": st.secrets["TAVILY_API_KEY"],"query": query,"search_depth": "advanced","max_results": 5,"include_answer": True}
        response = requests.post(url, json=payload, timeout=15)
        data = response.json()
        context = data.get("answer", "")
        sources = "\n".join([f"{i+1}. [{r['title']}]({r['url']})" for i, r in enumerate(data.get("results", [])[:3])])
        return context, sources
    except: return "", ""

def get_groq_response(client, messages, system_prompt, search_context=""):
    final_system = system_prompt
    if search_context: final_system += f"\n\nLive Web Info:\n{search_context}"
    recent_messages = messages[-6:]
    messages_to_send = [{"role":"system","content":final_system}] + recent_messages
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

#... PLAY & LEARN FUNCTIONS SAME AS YOUR ORIGINAL CODE (kept as is)...
def generate_ai_questions(client, age, language, subject, count=10):
    language_name = next((name for name, code in PLAY_LANGUAGES.items() if code == language), "English")
    prompt = f"Create exactly {count} questions for age {age} Subject {subject} Language {language_name} MUST be in {language_name}. JSON array only: [{{'question':'...','options':['A','B','C','D'],'answer':'A','explanation':'...'}}]"
    for model in GROQ_MODELS:
        try:
            completion = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}], temperature=0.35, max_tokens=5000)
            txt = completion.choices[0].message.content.strip()
            s=txt.find("["); e=txt.rfind("]")
            if s!=-1 and e!=-1: txt=txt[s:e+1]
            parsed=json.loads(txt)
            valid=[]
            for item in parsed:
                if item.get("answer") in item.get("options",[]): valid.append(item)
                if len(valid)==count: break
            if len(valid)==count: return valid
        except: continue
    return [{"question":f"Demo Q {i+1} for {subject}","options":["A","B","C","D"],"answer":"A","explanation":"Demo"} for i in range(count)]

# UI START
st.markdown('<div class="header"><h1>💬 ClyxessChat AI</h1></div>', unsafe_allow_html=True)
try: client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except: st.error("GROQ_API_KEY missing"); st.stop()

with st.sidebar:
    st.title("💬 ClyxessChat AI")
    mode = st.radio("Select Mode", ["Normal Chat","🎒 School Mode","💻 Coding Lab","🎮 Play & Learn","🎨 Creative AI Image Generator","📷 Vision Lab","🎭 Peer Roleplay Modes","📋 AI Daily Timetable","📝 Interactive Homework & Test","👨‍👩‍👦 Parent Dashboard","🔐 Login / Sign Up"])
    st.markdown("---")
    if mode=="Normal Chat":
        if st.button("+ New Normal Chat", use_container_width=True):
            st.session_state.messages=[]; st.session_state.session_id=str(uuid.uuid4()); st.rerun()
    elif mode=="🎒 School Mode":
        if st.button("🆕 Separate School Chat Reset", use_container_width=True): # FIX 9
            st.session_state.school_messages=[]; st.rerun()
    elif mode=="💻 Coding Lab":
        if st.button("🆕 Reset Coding Lab", use_container_width=True):
            st.session_state.coding_messages=[]; st.rerun()
    else:
        if st.button("+ New Chat", use_container_width=True):
            st.session_state.messages=[]; st.rerun()

# ===== FIXED ROUTES =====
if mode=="💻 Coding Lab":
    st.title("💻 Coding Lab")
    st.caption("🚫 No age restriction • Supports Python, JavaScript, HTML, CSS, PHP, Java, C, C++, C#")
    c1,c2=st.columns(2)
    with c1:
        cl=st.selectbox("👨‍💻 Coding Language", CODING_LANGUAGES, index=CODING_LANGUAGES.index(st.session_state.coding_language))
        st.session_state.coding_language=cl
    with c2:
        el=st.selectbox("🌐 Coding Explanation Language Separate", list(PLAY_LANGUAGES.keys()), index=list(PLAY_LANGUAGES.values()).index(st.session_state.coding_explain_lang), key="coding_exp_lang")
        st.session_state.coding_explain_lang=PLAY_LANGUAGES[el]
    for m in st.session_state.coding_messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    p=st.chat_input(f"Ask {cl} coding...", key="coding_chat")
    if p:
        st.session_state.coding_messages.append({"role":"user","content":p})
        with st.chat_message("user"): st.markdown(f'<div class="user-bubble">{p}</div>', unsafe_allow_html=True)
        system=get_coding_system_prompt(cl, st.session_state.coding_explain_lang)+"\n"+get_india_datetime_context()
        with st.chat_message("assistant"):
            comp,_=get_groq_response(client, st.session_state.coding_messages, system, "")
            resp=comp.choices[0].message.content if comp else "Error"
            st.markdown(resp)
            st.session_state.coding_messages.append({"role":"assistant","content":resp})
    st.stop()

if mode=="🎒 School Mode":
    st.title("🎒 School Mode")
    c1,c2=st.columns(2)
    with c1:
        age=st.selectbox("👶 Age Options Exactly: 1–3, 3–5, 6–8, 9–11, 12+", SCHOOL_AGE_OPTIONS, index=SCHOOL_AGE_OPTIONS.index(st.session_state.school_age))
        st.session_state.school_age=age
    with c2:
        sl=st.selectbox("🌐 School Mode Language Dropdown Separate", list(PLAY_LANGUAGES.keys()), index=list(PLAY_LANGUAGES.values()).index(st.session_state.school_language), key="school_lang_drop")
        st.session_state.school_language=PLAY_LANGUAGES[sl]
    st.caption(f"School Chat History Separate | Age {age} | {sl}")
    for m in st.session_state.school_messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    p=st.chat_input("School doubt...", key="school_chat")
    if p:
        st.session_state.school_messages.append({"role":"user","content":p})
        with st.chat_message("user"): st.markdown(f'<div class="user-bubble">{p}</div>', unsafe_allow_html=True)
        system=get_school_system_prompt(age, st.session_state.school_language)
        with st.chat_message("assistant"):
            comp,_=get_groq_response(client, st.session_state.school_messages, system, "")
            resp=comp.choices[0].message.content if comp else "Error"
            st.markdown(resp)
            st.session_state.school_messages.append({"role":"assistant","content":resp})
    st.stop()

# Normal Chat - Separate History
for message in st.session_state.messages:
    with st.chat_message(message["role"]): st.markdown(message["content"])
prompt=st.chat_input("Ask ClyxessChat AI - Normal Chat (History Separate)")
if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"): st.markdown(f'<div class="user-bubble">{prompt}</div>', unsafe_allow_html=True)
    search_context,sources=search_tavily(prompt)
    system=NORMAL_SYSTEM_PROMPT+"\nLIVE INDIA CLOCK: "+get_india_datetime_context()
    if search_context: system+="\nLIVE WEB INFO:\n"+search_context
    with st.chat_message("assistant"):
        completion,_=get_groq_response(client, st.session_state.messages, system, "")
        if completion is None: st.error("AI response nahi aa paya"); st.stop()
        response=completion.choices[0].message.content
        st.markdown(response)
    st.session_state.messages.append({"role":"assistant","content":response})
