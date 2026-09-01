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

# ============================================================
# CLYXESSCHAT AI
# NORMAL CHAT + CREATIVE LAB + PLAY & LEARN
# ============================================================

st.set_page_config(page_title="ClyxessChat AI", page_icon="💬", layout="wide")

st.markdown("""
<style>
.main {max-width: 850px; margin: auto;}
.header {position: sticky; top: 0; background: #202123; padding: 18px;
border-bottom: 1px solid #444; z-index: 999; margin: -1rem -1rem 20px -1rem;}
.header h1 {color:white;font-size:22px;font-weight:600;margin:0;text-align:center;}
.user-bubble {background-color:#D9FDD3;color:#111b21;padding:10px 14px;border-radius:18px;
border-bottom-right-radius:4px;max-width:75%;margin-left:auto;margin-bottom:10px;text-align:right;}
.gradient-text {background:linear-gradient(90deg,#ff00cc,#3333ff,#00ffcc);
-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.age-btn-active {background:#2ecc71!important;color:white!important;border:2px solid white!important;}
.play-card {padding:24px;border-radius:20px;background:#f8fafc;border:1px solid #e2e8f0;margin:15px 0;}
.play-hero {padding:24px;border-radius:20px;background:linear-gradient(135deg,#0f172a,#172554);
color:white;margin-bottom:20px;}
.locked-card {padding:18px;border-radius:18px;background:#f1f5f9;border:1px solid #cbd5e1;}
.small-muted {color:#64748b;font-size:13px;}
.media-card {max-width:560px;margin:12px auto;}
.media-card img {max-width:100%!important;width:auto!important;height:auto!important;
max-height:520px!important;object-fit:contain;border-radius:14px;display:block;margin:auto;}
[data-testid="stImage"] img {max-width:560px!important;max-height:520px!important;width:auto!important;
height:auto!important;object-fit:contain;margin:auto;display:block;}
.report-card {padding:18px;border-radius:16px;border:1px solid #334155;background:#0f172a;color:white;}
</style>
""", unsafe_allow_html=True)

GROQ_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"]
QUESTIONS_PER_LEVEL = 10

PLAY_AGE_LEVELS = ["1–2 Years","3–4 Years","5–6 Years","6–8 Years","8–10 Years","10–11 Years","11+ Years"]

PLAY_LANGUAGES = {
    "🇮🇳 हिंदी":"hi","🇮🇳 मराठी":"mr","🇮🇳 বাংলা":"bn","🇮🇳 தமிழ்":"ta",
    "🇮🇳 తెలుగు":"te","🇮🇳 ગુજરાતી":"gu","🇮🇳 ಕನ್ನಡ":"kn","🇮🇳 മലയാളം":"ml",
    "🇮🇳 ଓଡ଼ିଆ":"or","🇬🇧 English":"en","🇨🇳 中文":"zh","🇯🇵 日本語":"ja"
}

AGE_SUBJECTS = {
    "1–2 Years":["Colors","Shapes","Animals","Sounds","Basic Language","Memory"],
    "3–4 Years":["Numbers","Language","Shapes","Storytelling","Communication","Logic"],
    "5–6 Years":["Maths","Science Basics","Language","Reading","Logic","Creativity"],
    "6–8 Years":["Maths","Science","English","General Knowledge","Logic","Communication","Technology Basics"],
    "8–10 Years":["Maths","Science","English","Coding Basics","AI Introduction","Financial Literacy","Communication"],
    "10–11 Years":["Advanced Maths","Science","Technology","AI Literacy","Coding","Financial Literacy","Critical Thinking"],
    "11+ Years":["AI & Technology","Coding","Financial Literacy","Cyber Safety","Communication","Entrepreneurship","Critical Thinking","Problem Solving"]
}

QUESTION_BANK = {
"Maths":[{"question":"What is 7 + 5?","options":["10","12","14","15"],"answer":"12","explanation":"7 + 5 = 12."},
{"question":"What is 6 × 4?","options":["20","22","24","26"],"answer":"24","explanation":"6 groups of 4 make 24."}],
"Science":[{"question":"Which planet do we live on?","options":["Mars","Earth","Venus","Jupiter"],"answer":"Earth","explanation":"We live on planet Earth."},
{"question":"Which organ pumps blood?","options":["Brain","Heart","Lungs","Stomach"],"answer":"Heart","explanation":"The heart pumps blood around the body."}],
"Logic":[{"question":"What comes next: 2, 4, 6, 8, ?","options":["9","10","11","12"],"answer":"10","explanation":"The pattern increases by 2."}],
"Communication":[{"question":"Someone says 'Thank you'. What is a polite response?","options":["You're welcome","Go away","No","Stop"],"answer":"You're welcome","explanation":"You're welcome is a polite response."}],
"Financial Literacy":[{"question":"If you receive ₹100 and save ₹20, how much is left to spend?","options":["₹60","₹70","₹80","₹90"],"answer":"₹80","explanation":"₹100 - ₹20 = ₹80."}],
"Technology Basics":[{"question":"Which device is commonly used to type on a computer?","options":["Keyboard","Speaker","Camera","Printer"],"answer":"Keyboard","explanation":"A keyboard is commonly used to type."}],
"AI Introduction":[{"question":"What does AI stand for?","options":["Artificial Intelligence","Automatic Internet","Advanced Input","Application Interface"],"answer":"Artificial Intelligence","explanation":"AI stands for Artificial Intelligence."}],
"AI Literacy":[{"question":"What is a good habit when using AI?","options":["Check important information","Believe everything automatically","Share passwords","Share private information"],"answer":"Check important information","explanation":"AI can make mistakes, so important information should be checked."}],
"Coding":[{"question":"What is code?","options":["Instructions given to a computer","A type of food","A school bag","A musical instrument"],"answer":"Instructions given to a computer","explanation":"Code contains instructions that computers can execute."}],
"Coding Basics":[{"question":"What is a variable used for in programming?","options":["Storing information","Charging a phone","Printing paper","Playing music"],"answer":"Storing information","explanation":"Variables can store values used by a program."}],
"Cyber Safety":[{"question":"Should you share your password with strangers online?","options":["Yes","No"],"answer":"No","explanation":"Passwords should be kept private."}],
"Critical Thinking":[{"question":"What should you do before believing an important claim online?","options":["Check reliable sources","Share it immediately","Ignore all evidence","Send your password"],"answer":"Check reliable sources","explanation":"Checking reliable sources helps identify inaccurate information."}],
"Problem Solving":[{"question":"If a problem has several possible solutions, what is a good approach?","options":["Compare the solutions","Choose randomly","Give up immediately","Ignore the problem"],"answer":"Compare the solutions","explanation":"Comparing options can help find a better solution."}],
"Entrepreneurship":[{"question":"What is one important part of starting a useful product?","options":["Understanding a real problem","Ignoring customers","Copying everything","Never testing the idea"],"answer":"Understanding a real problem","explanation":"Good products usually solve a real problem."}],
"Colors":[{"question":"Which one is red? 🔴","options":["🔵","🟢","🔴","🟡"],"answer":"🔴","explanation":"The red circle is the red color."}],
"Shapes":[{"question":"Which shape is a circle? ⭕","options":["⬜","🔺","⭕","⭐"],"answer":"⭕","explanation":"⭕ is a circle."}],
"Animals":[{"question":"Which one is a cat? 🐱","options":["🐶","🐱","🐰","🐮"],"answer":"🐱","explanation":"🐱 represents a cat."}],
"Sounds":[{"question":"Which animal says 'Woof'? 🐶","options":["🐱","🐶","🐮","🐟"],"answer":"🐶","explanation":"A dog commonly makes a woof sound."}],
"Basic Language":[{"question":"What comes after A?","options":["B","C","D","E"],"answer":"B","explanation":"B comes after A in the alphabet."}],
"Memory":[{"question":"Remember: 🍎 🐱 ⭐. Which item was in the middle?","options":["🍎","🐱","⭐","🐶"],"answer":"🐱","explanation":"🐱 was the middle item."}],
"Numbers":[{"question":"What comes after 1?","options":["2","3","4","5"],"answer":"2","explanation":"2 comes after 1."}],
"Language":[{"question":"Which word is a greeting?","options":["Hello","Table","Blue","Seven"],"answer":"Hello","explanation":"Hello is commonly used as a greeting."}],
"Storytelling":[{"question":"A child finds a lost toy. What is a helpful action?","options":["Try to find the owner","Hide it","Break it","Throw it away"],"answer":"Try to find the owner","explanation":"Finding the owner is a helpful and responsible choice."}],
"Reading":[{"question":"Which word means the opposite of 'big'?","options":["Small","Tall","Fast","Bright"],"answer":"Small","explanation":"Small is the opposite of big."}],
"Creativity":[{"question":"Which activity can help creativity?","options":["Drawing a new idea","Never trying anything","Copying every answer","Ignoring questions"],"answer":"Drawing a new idea","explanation":"Creating and exploring new ideas can build creativity."}],
"English":[{"question":"Which word is an adjective?","options":["Beautiful","Run","Eat","Quickly"],"answer":"Beautiful","explanation":"Beautiful is an adjective."}],
"General Knowledge":[{"question":"How many days are in a week?","options":["5","7","8","10"],"answer":"7","explanation":"A week has 7 days."}],
"Advanced Maths":[{"question":"What is the square root of 64?","options":["6","8","10","12"],"answer":"8","explanation":"8 × 8 = 64."}],
"Technology":[{"question":"Which device is used to process information?","options":["Computer","Chair","Bottle","Pencil"],"answer":"Computer","explanation":"A computer processes information."}],
"AI & Technology":[{"question":"Which is a responsible use of AI?","options":["Checking important information","Sharing passwords","Copying without understanding","Sharing private data"],"answer":"Checking important information","explanation":"Responsible AI use includes checking important information."}]
}

UI={"en":{"start":"🚀 Start Game","score":"Score","submit":"Submit Answer","next":"Next Question","correct":"✅ Correct!","wrong":"❌ Not quite!","retry":"🔄 Try Again"},
"hi":{"start":"🚀 गेम शुरू करें","score":"स्कोर","submit":"उत्तर जांचें","next":"अगला सवाल","correct":"✅ बिल्कुल सही!","wrong":"❌ कोई बात नहीं, फिर कोशिश करो!","retry":"🔄 फिर से खेलें"}}

DEFAULT_STATE={
"messages":[],"school_messages":[],"session_id":str(uuid.uuid4()),"school_session_id":str(uuid.uuid4()),
"age_group":"1-2 Yrs","school_age":"6–8 Years","school_language":"hi",
"play_age":PLAY_AGE_LEVELS[0],"play_language":"hi","play_subject":None,"play_questions":[],
"play_question_index":0,"play_score":0,"play_game_started":False,"play_answered":False,
"play_last_correct":False,"play_last_explanation":"","play_unlocked_levels":[PLAY_AGE_LEVELS[0]],
"play_completed_levels":[],"play_best_scores":{},
"homework_age":"8–10 Years","homework_subject":None,"homework_language":"en",
"homework_questions":[],"homework_answers":{},"homework_result":None
}
for key,value in DEFAULT_STATE.items():
    if key not in st.session_state: st.session_state[key]=value

def build_image_prompt(user_prompt,is_school_mode=False,age="Normal"):
    p=user_prompt.strip()
    p=re.sub(r"^(please\s+)?(make|create|generate|draw|banao|banaiye)\s+(an?\s+)?(image|photo|picture|poster|chitra)\s*(of|for|:)?\s*","",p,flags=re.I)
    rules=("Create ONLY what the user explicitly requested. Do not add people, girls, boys, faces, animals, vehicles, characters, logos, brands, objects, scenery or unrelated themes unless explicitly requested. "
           "Do not invent a story or add a main character. Keep the requested subject dominant and clean. No watermark.")
    if any(x in p.lower() for x in ["diwali","दीवाली","दीपावली"]):
        rules+=" For a Diwali greeting/poster where no person is requested, use diyas, warm festive lights and tasteful Indian decorative motifs; NO PEOPLE. Try to preserve the exact requested greeting text."
    if is_school_mode: rules+=f" Keep it safe and age-appropriate for {age}."
    return f"{rules} User request: {p}."

def generate_image_url(prompt,is_school_mode,age,aspect="1:1"):
    final_prompt=build_image_prompt(prompt,is_school_mode,age)
    sizes={"1:1":(768,768),"16:9":(1024,576),"9:16":(576,1024)}
    width,height=sizes.get(aspect,(768,768))
    try:
        hf_key=st.secrets.get("HF_API_KEY","")
        if hf_key:
            r=requests.post("https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
                headers={"Authorization":f"Bearer {hf_key}"},json={"inputs":final_prompt},timeout=60)
            if r.status_code==200 and r.content:return r.content,"huggingface"
    except Exception: pass
    url=("https://image.pollinations.ai/prompt/"+f"{requests.utils.quote(final_prompt)}"
         f"?width={width}&height={height}&nologo=true&seed={uuid.uuid4().int%100000}")
    return url,"pollinations"

NORMAL_SYSTEM_PROMPT="""You are ClyxessChat AI, created by ClyxessChat AI Technology.
CORE RULE: REPLY ONLY IN THE SAME LANGUAGE AS USER.
Your name is ClyxessChat AI. Friendly, intelligent, calm.
If user asks to generate image, say: "Generating image for: [prompt]"
"""

def get_school_system_prompt(age_group,selected_language="hi"):
    language_name=language_display_name(selected_language)
    base=f"""You are ClyxessChat AI — a friendly, safe, child-focused School Mode learning companion.
The child age group is {age_group}.
SELECTED LANGUAGE: {language_name} (code: {selected_language}).
STRICT LANGUAGE LOCK: reply ONLY in {language_name}. Never switch languages and never use mixed language.
Keep the conversation natural and interactive. Answer the child's question, explain simply, and when useful ask ONE relevant follow-up question.
Do not pretend to remember things the child never told you. Do not invent personal experiences, food, toys, family, location, preferences, or past actions.
Do not pressure the child to reveal passwords, addresses, phone numbers, private photos, or sensitive personal information.
For learning topics, encourage understanding instead of simply giving homework answers.
"""
    if "1-2" in age_group:return base+"Use extremely short, cheerful, concrete sentences; simple words; colors, shapes, animals, sounds, counting and very basic concepts."
    if "3-4" in age_group:return base+"Use short playful explanations, simple stories, counting, shapes, language and basic logic."
    if "5-6" in age_group:return base+"Use simple examples, stories, early maths, science basics, reading, logic and creativity."
    if "6-8" in age_group:return base+"Use clear school-level explanations, examples, reasoning, maths, science, English, technology and general knowledge."
    if "8-10" in age_group:return base+"Use age-appropriate school explanations with maths, science, English, coding basics, AI introduction, financial literacy and communication."
    if "10-11" in age_group:return base+"Use practical school-level explanations with step-by-step maths, science, technology, coding logic, AI literacy and critical thinking."
    return base+"Use age-appropriate secondary-school explanations with deeper reasoning, AI, coding, technology, finance, cyber safety, entrepreneurship and critical thinking."

def get_india_datetime_context():
    try:
        now=datetime.datetime.now(ZoneInfo("Asia/Kolkata")) if ZoneInfo else datetime.datetime.now()
        return now.strftime("Current India date: %A, %d %B %Y. Current India time: %I:%M %p (IST).")
    except Exception:return datetime.datetime.now().strftime("Current application date: %A, %d %B %Y. Current application time: %I:%M %p.")

def transcribe_audio_with_groq(client,audio_bytes):
    if not audio_bytes:return ""
    try:
        path="temp_audio_school.wav"
        with open(path,"wb") as f:f.write(audio_bytes)
        with open(path,"rb") as audio_file:
            result=client.audio.transcriptions.create(file=audio_file,model="whisper-large-v3",
                prompt="The speaker may use Hindi, Hinglish, English, Marathi, Bengali, Tamil, Telugu, Gujarati, Kannada, Malayalam, Odia, Chinese or Japanese.")
        return result.text.strip()
    except Exception:return ""

def language_display_name(code):
    return next((name.split(" ",1)[-1] for name,value in PLAY_LANGUAGES.items() if value==code),"English")

def search_tavily(query):
    search_words=["news","mausam","weather","rate","price","score","aaj","kal","today","latest","breaking"]
    if not any(word in query.lower() for word in search_words):return "",""
    try:
        response=requests.post("https://api.tavily.com/search",json={"api_key":st.secrets["TAVILY_API_KEY"],
            "query":query,"search_depth":"advanced","max_results":5,"include_answer":True},timeout=15)
        data=response.json()
        context=data.get("answer","")
        sources="\n".join([f"{i+1}. [{r['title']}]({r['url']})" for i,r in enumerate(data.get("results",[])[:3])])
        return context,sources
    except Exception:return "",""

def get_groq_response(client,messages,system_prompt,search_context=""):
    final_system=system_prompt+(f"\n\nLive Web Info:\n{search_context}" if search_context else "")
    recent_messages=messages[-6:]
    for model in GROQ_MODELS:
        try:
            completion=client.chat.completions.create(model=model,messages=[{"role":"system","content":final_system}]+recent_messages,
                temperature=0.7,max_tokens=4000)
            return completion,model
        except Exception:continue
    return None,None

@st.cache_resource
def init_supabase():
    try:return create_client(st.secrets["SUPABASE_URL"],st.secrets["SUPABASE_KEY"])
    except Exception:return None
supabase=init_supabase()

def get_play_ui(language):return UI.get(language,UI["en"])
def get_play_subjects(age):return AGE_SUBJECTS.get(age,[])
def play_level_unlocked(age):return age in st.session_state.play_unlocked_levels

def unlock_next_play_level(age):
    try:i=PLAY_AGE_LEVELS.index(age)
    except ValueError:return None
    if i+1>=len(PLAY_AGE_LEVELS):return None
    nxt=PLAY_AGE_LEVELS[i+1]
    if nxt not in st.session_state.play_unlocked_levels:st.session_state.play_unlocked_levels.append(nxt)
    return nxt

def build_demo_questions(subject,age=None,language="en"):
    bank=QUESTION_BANK.get(subject,[])
    if not bank:
        # IMPORTANT: fallback remains tied to the selected subject.
        bank=[{"question":f"Which statement best matches {subject}?","options":[
            f"Learning about {subject}","A random unrelated topic","A password","None of these"],
            "answer":f"Learning about {subject}","explanation":f"This question is about {subject}."}]
    result=[{"question":str(x["question"]),"options":list(x["options"]),"answer":str(x["answer"]),
             "explanation":str(x.get("explanation",""))} for x in bank]
    random.shuffle(result)
    original=list(result)
    while len(result)<QUESTIONS_PER_LEVEL:result.append(original[len(result)%len(original)].copy())
    random.shuffle(result)
    return result[:QUESTIONS_PER_LEVEL]

def clean_json_text(text):
    text=text.strip()
    text=re.sub(r"^```(?:json)?\s*","",text,flags=re.I);text=re.sub(r"\s*```$","",text)
    start=text.find("[");end=text.rfind("]")
    return text[start:end+1].strip() if start!=-1 and end!=-1 else text

def _personal_assumption_question(text):
    q=text.lower()
    patterns=[r"what did you (eat|see|do|play|have|watch|buy)",r"what (fruit|toy|food) did you",
              r"do you (have|like|own|remember)",r"what is your (favorite|toy|food)",
              "तुमने क्या खाया","तुमने कौन सा फल","तुम्हारे पास कौन","तुम्हारा पसंदीदा","तुमने कल क्या","तुमने क्या देखा"]
    return any(re.search(x,q,re.I) for x in patterns)

def generate_ai_questions(client,age,language,subject,count=10):
    language_name=language_display_name(language)
    prompt=f"""Create exactly {count} educational multiple-choice questions for age group {age}.
Subject: {subject}
Selected language: {language_name} (code: {language})
STRICT LANGUAGE LOCK: question, options, answer and explanation MUST be entirely in {language_name}.
Never switch language. Never use Hinglish or mixed language unless English is selected.
Every question must be objective, age-appropriate, safe, and have exactly four options with exactly one correct answer.
For ages 1–4, NEVER ask personal-experience questions.
Return ONLY valid JSON:
[{{"question":"...","options":["A","B","C","D"],"answer":"A","explanation":"..."}}]"""
    for model in GROQ_MODELS:
        try:
            completion=client.chat.completions.create(model=model,messages=[{"role":"user","content":prompt}],
                temperature=0.35,max_tokens=5000)
            parsed=json.loads(clean_json_text(completion.choices[0].message.content))
            valid=[]
            for item in parsed if isinstance(parsed,list) else []:
                if not isinstance(item,dict):continue
                q=str(item.get("question","")).strip()
                opts=[str(x).strip() for x in item.get("options",[]) if str(x).strip()]
                ans=str(item.get("answer","")).strip();exp=str(item.get("explanation","")).strip()
                if not q or len(opts)!=4 or ans not in opts:continue
                if ("1–2" in age or "3–4" in age) and _personal_assumption_question(q):continue
                valid.append({"question":q,"options":opts,"answer":ans,"explanation":exp})
                if len(valid)==count:break
            if len(valid)==count:return valid
        except Exception:continue

    # Subject-aware fallback. It never falls back to one universal baby game.
    if language=="hi":
        pools={
        "Maths":[{"question":"1 + 1 = ?","options":["1","2","3","4"],"answer":"2","explanation":"1 + 1 = 2।"}],
        "Science":[{"question":"हम किस ग्रह पर रहते हैं?","options":["मंगल","पृथ्वी","शुक्र","बृहस्पति"],"answer":"पृथ्वी","explanation":"हम पृथ्वी पर रहते हैं।"}],
        "Colors":[{"question":"लाल रंग कौन सा है?","options":["🔴","🔵","🟢","🟡"],"answer":"🔴","explanation":"🔴 लाल रंग है।"}],
        "Shapes":[{"question":"वृत्त कौन सा है?","options":["⬜","🔺","⭕","⭐"],"answer":"⭕","explanation":"⭕ वृत्त है।"}],
        "Animals":[{"question":"बिल्ली कौन सी है?","options":["🐶","🐱","🐰","🐮"],"answer":"🐱","explanation":"🐱 बिल्ली है।"}],
        "Numbers":[{"question":"1 के बाद कौन सा अंक आता है?","options":["2","3","4","5"],"answer":"2","explanation":"1 के बाद 2 आता है।"}],
        "Cyber Safety":[{"question":"क्या पासवर्ड किसी अनजान व्यक्ति को देना चाहिए?","options":["हाँ","नहीं","कभी-कभी","पता नहीं"],"answer":"नहीं","explanation":"पासवर्ड निजी रखना चाहिए।"}]
        }
        pool=pools.get(subject)
        if pool:return (pool*((count//len(pool))+1))[:count]
    if language=="en":return build_demo_questions(subject,age,language)
    return build_demo_questions(subject,age,language)

def reset_play_game():
    st.session_state.play_questions=[]
    st.session_state.play_question_index=0
    st.session_state.play_score=0
    st.session_state.play_answered=False
    st.session_state.play_last_correct=False
    st.session_state.play_last_explanation=""
    st.session_state.play_game_started=False

def render_play_and_learn(client):
    st.markdown('<div class="play-hero"><h1>🎮 ClyxessChat AI — Play & Learn</h1><p>Learn through AI-generated questions, games and age-based challenges.</p></div>',unsafe_allow_html=True)

    # Detect settings changes BEFORE writing the new values.
    old_age=st.session_state.play_age
    old_lang=st.session_state.play_language
    old_subject=st.session_state.play_subject

    col1,col2,col3=st.columns(3)
    with col1:
        play_age=st.selectbox("👶 Select Age",PLAY_AGE_LEVELS,index=PLAY_AGE_LEVELS.index(old_age),key="play_age_select")
    with col2:
        labels=list(PLAY_LANGUAGES.keys())
        language_label=st.selectbox("🌐 Select Language",labels,index=labels.index(next(k for k,v in PLAY_LANGUAGES.items() if v==old_lang)),key="play_language_select")
        play_language=PLAY_LANGUAGES[language_label]
    with col3:
        subjects=get_play_subjects(play_age)
        subject_index=subjects.index(old_subject) if old_subject in subjects else 0
        play_subject=st.selectbox("📚 Select Subject",subjects,index=subject_index,key="play_subject_select")

    changed=(play_age!=old_age or play_language!=old_lang or play_subject!=old_subject)
    st.session_state.play_age=play_age
    st.session_state.play_language=play_language
    st.session_state.play_subject=play_subject
    if changed:
        reset_play_game()
        st.rerun()

    if not play_level_unlocked(play_age):
        st.error(f"🔒 {play_age} is locked.")
        st.info("Complete the previous age level with 10/10 to unlock this level.")
        return

    with st.sidebar:
        st.markdown("### 🎮 Play & Learn Progress")
        st.write(f"👶 **Age:** {play_age}");st.write(f"🌐 **Language:** {language_label}");st.write(f"📚 **Subject:** {play_subject}")
        st.divider();st.markdown("### 🔓 Age Levels")
        for level in PLAY_AGE_LEVELS:
            st.success(f"⭐ {level}" if level==play_age else f"✅ {level}") if level in st.session_state.play_unlocked_levels else st.write(f"🔒 {level}")

    if not st.session_state.play_game_started:
        st.markdown('<div class="play-card">',unsafe_allow_html=True)
        st.subheader("🎯 Ready to Learn?")
        st.write(f"**Age:** {play_age}");st.write(f"**Subject:** {play_subject}");st.write(f"**Language:** {language_label}")
        st.info("🎮 इस level में 10 AI-generated questions होंगे। 10/10 करने पर अगला age level unlock होगा.")
        if st.button("🚀 Start Game",use_container_width=True,type="primary"):
            with st.spinner("🤖 AI आपके लिए learning challenge बना रहा है..."):
                questions=generate_ai_questions(client,play_age,play_language,play_subject,QUESTIONS_PER_LEVEL)
            if not questions:st.error("Questions generate नहीं हो पाए। Please try again.");return
            st.session_state.play_questions=questions;st.session_state.play_question_index=0
            st.session_state.play_score=0;st.session_state.play_answered=False
            st.session_state.play_last_correct=False;st.session_state.play_last_explanation=""
            st.session_state.play_game_started=True;st.rerun()
        st.markdown("</div>",unsafe_allow_html=True);return

    questions=st.session_state.play_questions
    if not questions:st.error("No questions available.");return
    qi=st.session_state.play_question_index
    if qi>=len(questions):qi=0;st.session_state.play_question_index=0
    current=questions[qi];question_text=current["question"];options=current["options"];correct_answer=current["answer"];explanation=current.get("explanation","")
    st.progress(qi/QUESTIONS_PER_LEVEL,text=f"Question {qi+1}/{QUESTIONS_PER_LEVEL}")
    c1,c2,c3=st.columns(3)
    c1.metric("🎯 Question",f"{qi+1}/10");c2.metric("⭐ Score",f"{st.session_state.play_score}/10");c3.metric("📚 Subject",play_subject)
    st.markdown('<div class="play-card">',unsafe_allow_html=True);st.subheader(f"❓ {question_text}")
    answer=st.radio("Choose your answer:",options,key=f"play_answer_{play_age}_{play_language}_{play_subject}_{qi}")
    st.markdown("</div>",unsafe_allow_html=True)

    if not st.session_state.play_answered and st.button("✅ Submit Answer",use_container_width=True,type="primary"):
        st.session_state.play_last_correct=(answer==correct_answer)
        if answer==correct_answer:st.session_state.play_score+=1
        st.session_state.play_last_explanation=explanation;st.session_state.play_answered=True;st.rerun()

    if st.session_state.play_answered:
        if st.session_state.play_last_correct:st.success(f"✅ Correct! ⭐ Score: {st.session_state.play_score}/10")
        else:st.warning(f"❌ Not quite! Correct answer: **{correct_answer}**")
        if explanation:st.info(f"💡 {explanation}")
        if qi<QUESTIONS_PER_LEVEL-1:
            if st.button("➡️ Next Question",use_container_width=True):
                st.session_state.play_question_index+=1;st.session_state.play_answered=False
                st.session_state.play_last_correct=False;st.session_state.play_last_explanation="";st.rerun()
        else:
            st.divider();final_score=st.session_state.play_score
            if final_score==10:
                st.balloons();st.success("🏆 LEVEL COMPLETE — 10/10!")
                if play_age not in st.session_state.play_completed_levels:st.session_state.play_completed_levels.append(play_age)
                key=f"{play_age}:{play_subject}"
                st.session_state.play_best_scores[key]=max(final_score,st.session_state.play_best_scores.get(key,0))
                nxt=unlock_next_play_level(play_age)
                if nxt:
                    st.success(f"🔓 Next Level Unlocked: **{nxt}**")
                    if st.button(f"🚀 Play {nxt}",use_container_width=True,type="primary"):
                        st.session_state.play_age=nxt;reset_play_game();st.rerun()
                else:st.success("👑 Congratulations! All available age levels are complete.")
            else:
                st.warning(f"⭐ Final Score: {final_score}/10")
                st.info("🔒 अगला level unlock करने के लिए इस level में 10/10 करना जरूरी है.")
                if st.button("🔄 Retry Level",use_container_width=True,type="primary"):reset_play_game();st.rerun()
    st.divider()
    if st.button("🔄 Restart Current Game",use_container_width=True):reset_play_game();st.rerun()

def analyze_image_with_groq(image_bytes,mime,question,selected_language="en"):
    if not client:return "Groq API key missing."
    language_name=language_display_name(selected_language)
    try:
        b64=base64.b64encode(image_bytes).decode("utf-8")
        completion=client.chat.completions.create(model="qwen/qwen3.6-27b",messages=[{"role":"user","content":[
            {"type":"text","text":f"""Analyze the image and answer the user's request.
Selected output language: {language_name} (code: {selected_language}).
STRICT LANGUAGE LOCK: your final answer MUST be entirely in {language_name}.
Do not translate into another language. If selected language is English, answer directly in English without any unnecessary translation.
User request: {question}"""},
            {"type":"image_url","image_url":{"url":f"data:{mime};base64,{b64}"}}
        ]}],temperature=0.25,max_completion_tokens=1500)
        draft=completion.choices[0].message.content
        # English: return directly. Other languages: strict final rewrite.
        if selected_language=="en":return draft
        rewrite=client.chat.completions.create(model="qwen/qwen3.6-27b",messages=[
            {"role":"system","content":f"Rewrite the answer strictly in {language_name}. Output ONLY the final answer in {language_name}. No English, no Hinglish, no mixed language."},
            {"role":"user","content":draft}
        ],temperature=0.1,max_completion_tokens=1500)
        return rewrite.choices[0].message.content
    except Exception as e:return f"Vision error: {e}"

def save_current_chat_cloud():
    if not supabase or not st.session_state.messages:return False
    try:
        user=supabase.auth.get_user().user
        if not user:return False
        supabase.table("chat_sessions").upsert({"id":st.session_state.session_id,"user_id":user.id,
            "messages":st.session_state.messages,"updated_at":datetime.datetime.utcnow().isoformat()}).execute()
        return True
    except Exception:return False

def load_latest_chat_cloud():
    if not supabase:return
    try:
        user=supabase.auth.get_user().user
        if not user:return
        r=supabase.table("chat_sessions").select("messages").eq("user_id",user.id).order("updated_at",desc=True).limit(1).execute()
        if r.data and r.data[0].get("messages"):st.session_state.messages=r.data[0]["messages"]
    except Exception:pass

def render_login_signup():
    st.title("🔐 Login / Sign Up")
    if not supabase:st.warning("Add SUPABASE_URL and SUPABASE_KEY to Streamlit secrets.");return
    st.markdown("### ⚡ Quick Login");c1,c2=st.columns(2)
    with c1:
        if st.button("🔵 Continue with Google",use_container_width=True):
            try:
                r=supabase.auth.sign_in_with_oauth({"provider":"google","options":{"redirect_to":st.secrets.get("SUPABASE_REDIRECT_URL","")}})
                if getattr(r,"url",None):st.link_button("Continue to Google",r.url,use_container_width=True)
            except Exception as e:st.error(f"Google login failed: {e}")
    with c2:
        if st.button("🔷 Continue with Facebook",use_container_width=True):
            try:
                r=supabase.auth.sign_in_with_oauth({"provider":"facebook","options":{"redirect_to":st.secrets.get("SUPABASE_REDIRECT_URL","")}})
                if getattr(r,"url",None):st.link_button("Continue to Facebook",r.url,use_container_width=True)
            except Exception as e:st.error(f"Facebook login failed: {e}")
    st.caption("Google/Facebook providers must be enabled in Supabase Authentication settings.")
    tab1,tab2=st.tabs(["Log In","Sign Up"])
    with tab1:
        email=st.text_input("Email",key="login_email");password=st.text_input("Password",type="password",key="login_password")
        if st.button("Log In",type="primary"):
            try:
                supabase.auth.sign_in_with_password({"email":email,"password":password});st.session_state.user_email=email;load_latest_chat_cloud();st.success("Logged in successfully.");st.rerun()
            except Exception as e:st.error(f"Login failed: {e}")
    with tab2:
        name=st.text_input("Name",key="signup_name");email=st.text_input("Email",key="signup_email");password=st.text_input("Password",type="password",key="signup_password")
        if st.button("Create Account"):
            try:supabase.auth.sign_up({"email":email,"password":password,"options":{"data":{"name":name}}});st.success("Account created. Confirm email if required.")
            except Exception as e:st.error(f"Sign up failed: {e}")

def render_image_generator():
    st.title("🎨 Creative AI Image Generator")
    prompt=st.text_area("Describe exactly what you want",placeholder="Example: Happy Diwali greeting poster with diyas, no people")
    aspect=st.selectbox("📐 Format",["1:1","16:9","9:16"])
    if st.button("🎨 Generate Image",type="primary",use_container_width=True) and prompt.strip():
        with st.spinner("🎨 Creating only the requested subject..."):data,source=generate_image_url(prompt,False,"Normal",aspect)
        st.markdown('<div class="media-card">',unsafe_allow_html=True);st.image(data,width=520,caption="Generated image");st.markdown('</div>',unsafe_allow_html=True)
        if isinstance(data,bytes):st.download_button("⬇️ Save Image",data=data,file_name="clyxesschat_image.png",mime="image/png")
        else:st.link_button("🔗 Open Full Image",data)

def render_vision_lab():
    st.title("📷 Vision Lab")
    f=st.file_uploader("Upload book, homework or diagram",type=["png","jpg","jpeg","webp"],key="vision_file")
    labels=list(PLAY_LANGUAGES.keys());label=st.selectbox("Answer language",labels,key="vision_language")
    selected_language=PLAY_LANGUAGES[label]
    question=st.text_input("What should AI explain?",value="Explain the image simply and solve any visible question.",key="vision_question")
    if f:
        st.markdown('<div class="media-card">',unsafe_allow_html=True);st.image(f,width=480);st.markdown('</div>',unsafe_allow_html=True)
        if st.button("🧠 Analyze Image",type="primary",use_container_width=True):
            with st.spinner("🧠 Analyzing..."):
                result=analyze_image_with_groq(f.getvalue(),f.type,question,selected_language)
            st.markdown(result)

def render_roleplay():
    st.title("🎭 Peer Roleplay Modes")
    role=st.selectbox("Role",["Classmate","Teacher","Study Buddy","Interview Partner","Project Teammate"])
    label=st.selectbox("Language",list(PLAY_LANGUAGES.keys()),key="role_language")
    selected_language=PLAY_LANGUAGES[label]
    age=st.selectbox("Age",PLAY_AGE_LEVELS,key="role_age")
    prompt=st.text_input("Start the roleplay",key="role_prompt")
    if st.button("Start Roleplay",type="primary") and prompt:
        language_name=language_display_name(selected_language)
        system=f"""Act as {role} for educational practice.
Child age group: {age}.
Selected language: {language_name} (code: {selected_language}).
STRICT LANGUAGE LOCK: Reply ONLY in {language_name}. Never switch language or use mixed language.
Be safe, respectful and age-appropriate for {age}."""
        ans,_=get_groq_response(client,[{"role":"user","content":prompt}],system,"")
        st.chat_message("assistant").write(ans.choices[0].message.content if ans else "")

def render_timetable():
    st.title("📋 AI Daily Timetable")
    age=st.selectbox("Age/Class",PLAY_AGE_LEVELS);subjects=st.multiselect("Subjects",get_play_subjects(age),default=get_play_subjects(age)[:3]);hours=st.slider("Learning hours",1,6,2)
    if st.button("🗓️ Create Timetable",type="primary"):
        mins=max(20,int(hours*60/max(1,len(subjects))));st.session_state.timetable="\n".join([f"{i+1}. {sub} — {mins} min" for i,sub in enumerate(subjects)])
    if st.session_state.get("timetable"):st.code(st.session_state.timetable)

def reset_homework():
    st.session_state.homework_questions=[];st.session_state.homework_answers={};st.session_state.homework_result=None

def render_homework_test():
    st.title("📝 Interactive Homework & Test")
    old_age=st.session_state.homework_age;old_subject=st.session_state.homework_subject;old_lang=st.session_state.homework_language
    labels=list(PLAY_LANGUAGES.keys())
    c1,c2,c3=st.columns(3)
    with c1:age=st.selectbox("👶 Age",PLAY_AGE_LEVELS,index=PLAY_AGE_LEVELS.index(old_age),key="hw_age_select")
    with c2:
        subjects=get_play_subjects(age)
        subject=st.selectbox("📚 Subject",subjects,index=(subjects.index(old_subject) if old_subject in subjects else 0),key="hw_subject_select")
    with c3:
        label=st.selectbox("🌐 Language",labels,index=labels.index(next(k for k,v in PLAY_LANGUAGES.items() if v==old_lang)),key="hw_language_select")
        language=PLAY_LANGUAGES[label]

    changed=(age!=old_age or subject!=old_subject or language!=old_lang)
    st.session_state.homework_age=age;st.session_state.homework_subject=subject;st.session_state.homework_language=language
    if changed:reset_homework();st.rerun()

    st.info(f"Age: {age}  •  Subject: {subject}  •  Language: {label}")
    if st.button("Generate Test",type="primary"):
        st.session_state.homework_questions=generate_ai_questions(client,age,language,subject,5)
        st.session_state.homework_answers={};st.session_state.homework_result=None
        st.rerun()
    qs=st.session_state.homework_questions
    if qs:
        for i,q in enumerate(qs):
            st.session_state.homework_answers[i]=st.radio(q["question"],q["options"],key=f"hw_{age}_{language}_{subject}_{i}")
        if st.button("Submit Test"):
            score=sum(st.session_state.homework_answers.get(i)==q["answer"] for i,q in enumerate(qs))
            st.session_state.homework_result=f"{score}/{len(qs)}";st.success(f"Score: {st.session_state.homework_result}")

def learning_report():
    best=max(st.session_state.play_best_scores.values(),default=0)
    return "\n".join(["ClyxessChat AI — Learning Report",f"Generated: {get_india_datetime_context()}",
        f"Current Level: {st.session_state.play_age}",
        f"Language: {language_display_name(st.session_state.play_language)}",
        f"Completed Levels: {len(st.session_state.play_completed_levels)}",f"Best Score: {best}/10",
        f"Homework/Test: {st.session_state.get('homework_result') or 'Not attempted'}"])

def render_parent_dashboard():
    st.title("👨‍👩‍👦 Parent Dashboard")
    best=max(st.session_state.play_best_scores.values(),default=0)
    c1,c2,c3=st.columns(3);c1.metric("Completed Levels",len(st.session_state.play_completed_levels));c2.metric("Best Score",f"{best}/10");c3.metric("Current Level",st.session_state.play_age)
    report=learning_report();st.markdown('<div class="report-card">',unsafe_allow_html=True);st.text(report);st.markdown('</div>',unsafe_allow_html=True)
    st.download_button("📄 Save Report",data=report,file_name="clyxesschat_learning_report.txt",mime="text/plain")
    st.link_button("📤 Share Report","https://wa.me/?text="+urllib.parse.quote(report))

# ============================================================
# SEPARATE NORMAL CHAT / SCHOOL MODE
# ============================================================

def render_normal_chat():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if "image_url" in message:
                st.markdown('<div class="media-card">',unsafe_allow_html=True);st.image(message["image_url"],caption=message.get("image_caption",""),width=520);st.markdown('</div>',unsafe_allow_html=True)
            else:st.markdown(message["content"])

    voice_prompt=""
    if mic_recorder:
        audio=mic_recorder(start_prompt="🔴 Start Recording",stop_prompt="⏹️ Stop & Send",key="chat_mic_normal")
        if audio:voice_prompt=transcribe_audio_with_groq(client,audio.get("bytes",b""))
    prompt=st.chat_input("Ask ClyxessChat AI",key="normal_chat_input")
    if not prompt and voice_prompt:prompt=voice_prompt
    if not prompt:return

    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):st.markdown(f'<div class="user-bubble">{prompt}</div>',unsafe_allow_html=True)
    low=prompt.lower()
    explicit_image=any(x in low for x in ["generate image","create image","make an image","draw an image","image banao","image bana","poster banao","photo banao","चित्र बनाओ","तस्वीर बनाओ"])
    if explicit_image:
        with st.chat_message("assistant"):
            with st.spinner("🎨 Image bana raha hu..."):img_data,source=generate_image_url(prompt,False,"Normal","1:1")
            st.markdown('<div class="media-card">',unsafe_allow_html=True);st.image(img_data,width=520,caption="Generated image");st.markdown('</div>',unsafe_allow_html=True)
            st.session_state.messages.append({"role":"assistant","image_url":img_data,"image_caption":prompt,"content":"Generated image"});save_current_chat_cloud()
    else:
        search_context,sources=search_tavily(prompt)
        system=NORMAL_SYSTEM_PROMPT+"\nLIVE INDIA CLOCK: "+get_india_datetime_context()
        if search_context:system+="\nLIVE WEB INFO:\n"+search_context
        with st.chat_message("assistant"):
            completion,used_model=get_groq_response(client,st.session_state.messages,system,"")
            if completion is None:st.error("AI response नहीं आ पाया. Please try again.");return
            response=completion.choices[0].message.content;st.markdown(response)
            if sources:st.caption("Sources:\n"+sources)
            st.caption(f"Model: {used_model or 'fallback'}")
        st.session_state.messages.append({"role":"assistant","content":response});save_current_chat_cloud()

def render_school_chat():
    st.title("🏫 Creative Lab (School Mode)")
    c1,c2=st.columns(2)
    old_age=st.session_state.school_age;old_lang=st.session_state.school_language
    with c1:
        age=st.selectbox("👶 School Age",PLAY_AGE_LEVELS,index=PLAY_AGE_LEVELS.index(old_age),key="school_age_select")
    with c2:
        labels=list(PLAY_LANGUAGES.keys())
        label=st.selectbox("🌐 School Language",labels,index=labels.index(next(k for k,v in PLAY_LANGUAGES.items() if v==old_lang)),key="school_language_select")
        language=PLAY_LANGUAGES[label]

    # School chat has its own history and settings; Normal Chat history is never used here.
    if age!=old_age or language!=old_lang:
        st.session_state.school_age=age;st.session_state.school_language=language
        st.session_state.school_messages=[]
        st.session_state.school_session_id=str(uuid.uuid4())
        st.rerun()

    for message in st.session_state.school_messages:
        with st.chat_message(message["role"]):
            if "image_url" in message:
                st.image(message["image_url"],width=520)
            else:st.markdown(message["content"])

    prompt=st.chat_input("School Mode में पूछो...",key="school_chat_input")
    if not prompt:return
    st.session_state.school_messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):st.markdown(f'<div class="user-bubble">{prompt}</div>',unsafe_allow_html=True)

    search_context,sources=search_tavily(prompt)
    system=get_school_system_prompt(age,language)+"\nLIVE INDIA CLOCK: "+get_india_datetime_context()
    if search_context:system+="\nLIVE WEB INFO:\n"+search_context
    with st.chat_message("assistant"):
        completion,_=get_groq_response(client,st.session_state.school_messages,system,"")
        if completion is None:st.error("School AI response नहीं आ पाया. Please try again.");return
        response=completion.choices[0].message.content;st.markdown(response)
    st.session_state.school_messages.append({"role":"assistant","content":response})

# ============================================================
# UI START
# ============================================================
st.markdown('<div class="header"><h1>💬 ClyxessChat AI</h1></div>',unsafe_allow_html=True)

try:client=Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("GROQ_API_KEY is missing from Streamlit secrets.");st.stop()

with st.sidebar:
    st.title("💬 ClyxessChat AI")
    try:logged_user=supabase.auth.get_user().user if supabase else None
    except Exception:logged_user=None
    if logged_user:
        st.success(f"👤 {logged_user.email}")
        if st.button("🚪 Log Out",use_container_width=True):
            try:supabase.auth.sign_out()
            except Exception:pass
            st.rerun()
    else:st.caption("Not logged in — sign in to save chats and view parent progress.")

    mode=st.radio("Select Mode",[
        "Normal Chat","Creative Lab (School Mode)","🎮 Play & Learn","🎨 Creative AI Image Generator",
        "📷 Vision Lab","🎭 Peer Roleplay Modes","📋 AI Daily Timetable","📝 Interactive Homework & Test",
        "👨‍👩‍👦 Parent Dashboard","🔐 Login / Sign Up"],key="main_mode")
    st.markdown("---")
    if st.button("+ New Chat",use_container_width=True):
        st.session_state.messages=[];st.session_state.session_id=str(uuid.uuid4());st.rerun()
    st.caption("🇮🇳 India live time: "+get_india_datetime_context().replace("Current India date: ",""))

if mode=="🔐 Login / Sign Up":render_login_signup();st.stop()
if mode=="👨‍👩‍👦 Parent Dashboard":render_parent_dashboard();st.stop()
if mode=="🎨 Creative AI Image Generator":render_image_generator();st.stop()
if mode=="📷 Vision Lab":render_vision_lab();st.stop()
if mode=="🎭 Peer Roleplay Modes":render_roleplay();st.stop()
if mode=="📋 AI Daily Timetable":render_timetable();st.stop()
if mode=="📝 Interactive Homework & Test":render_homework_test();st.stop()
if mode=="🎮 Play & Learn":render_play_and_learn(client);st.stop()
if mode=="Creative Lab (School Mode)":render_school_chat();st.stop()
if mode=="Normal Chat":render_normal_chat();st.stop()
