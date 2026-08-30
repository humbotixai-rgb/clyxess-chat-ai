import streamlit as st
from groq import Groq
from supabase import create_client
import datetime, uuid, requests, re, os, json, random

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

try:
    from streamlit_mic_recorder import mic_recorder
except Exception:
    mic_recorder = None

st.set_page_config(page_title="ClyxessChat AI", page_icon="💬", layout="wide")

# ============================================================
# UI / CSS
# ============================================================
st.markdown("""
<style>
.main {max-width: 900px; margin:auto;}
.header{position:sticky;top:0;background:#202123;padding:16px;border-bottom:1px solid #444;z-index:999;margin:-1rem -1rem 18px;}
.header h1{color:white;font-size:22px;margin:0;text-align:center;}
.user-bubble{background:#D9FDD3;color:#111b21;padding:10px 14px;border-radius:18px 18px 4px 18px;max-width:75%;margin-left:auto;margin-bottom:10px;text-align:right;}
.media-card{max-width:560px;margin:12px auto;}
.media-card img{max-width:100%!important;width:auto!important;height:auto!important;max-height:520px!important;object-fit:contain;border-radius:14px;display:block;margin:auto;}
[data-testid="stImage"] img{max-width:560px!important;max-height:520px!important;width:auto!important;height:auto!important;object-fit:contain;margin:auto;display:block;}
.play-card{padding:22px;border-radius:20px;background:#f8fafc;border:1px solid #e2e8f0;margin:15px 0;}
.play-hero{padding:24px;border-radius:20px;background:linear-gradient(135deg,#0f172a,#172554);color:white;margin-bottom:20px;}
.report-card{padding:18px;border-radius:16px;border:1px solid #334155;background:#0f172a;color:white;}
.kids-input-note{text-align:center;font-size:12px;color:#64748b;margin:4px 0 8px;}
.legal-box{font-size:13px;color:#94a3b8;line-height:1.6;}
.social-logo{display:flex;align-items:center;justify-content:center;gap:9px;font-weight:600;margin-bottom:5px;}
.social-logo svg{width:20px;height:20px;}
</style>
""", unsafe_allow_html=True)

GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b"
]

PLAY_AGE_LEVELS = [
    "1–2 Years","3–4 Years","5–6 Years","6–8 Years",
    "8–10 Years","10–11 Years","11+ Years"
]

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
    "Maths":[{"question":"What is 7 + 5?","options":["10","12","14","15"],"answer":"12","explanation":"7 + 5 = 12."}],
    "Science":[{"question":"Which planet do we live on?","options":["Mars","Earth","Venus","Jupiter"],"answer":"Earth","explanation":"We live on Earth."}],
    "Science Basics":[{"question":"Which organ pumps blood?","options":["Brain","Heart","Lungs","Stomach"],"answer":"Heart","explanation":"The heart pumps blood."}],
    "Logic":[{"question":"What comes next: 2, 4, 6, 8, ?","options":["9","10","11","12"],"answer":"10","explanation":"The pattern increases by 2."}],
    "Communication":[{"question":"Someone says 'Thank you'. What is a polite response?","options":["You're welcome","Go away","No","Stop"],"answer":"You're welcome","explanation":"You're welcome is polite."}],
    "Financial Literacy":[{"question":"If you receive ₹100 and save ₹20, how much is left?","options":["₹60","₹70","₹80","₹90"],"answer":"₹80","explanation":"₹100 - ₹20 = ₹80."}],
    "Technology Basics":[{"question":"Which device is used to type on a computer?","options":["Keyboard","Speaker","Camera","Printer"],"answer":"Keyboard","explanation":"A keyboard is used for typing."}],
    "AI Introduction":[{"question":"What does AI stand for?","options":["Artificial Intelligence","Automatic Internet","Advanced Input","Application Interface"],"answer":"Artificial Intelligence","explanation":"AI means Artificial Intelligence."}],
    "AI Literacy":[{"question":"What is a good AI habit?","options":["Check important information","Share passwords","Share private data","Believe everything automatically"],"answer":"Check important information","explanation":"AI can make mistakes."}],
    "Coding":[{"question":"What is code?","options":["Instructions for a computer","A food","A bag","A musical instrument"],"answer":"Instructions for a computer","explanation":"Code gives instructions to computers."}],
    "Coding Basics":[{"question":"What is a variable used for?","options":["Storing information","Charging a phone","Printing","Playing music"],"answer":"Storing information","explanation":"Variables store values."}],
    "Cyber Safety":[{"question":"Should you share your password with strangers online?","options":["Yes","No"],"answer":"No","explanation":"Passwords should stay private."}],
    "Critical Thinking":[{"question":"Before believing an important claim online, what should you do?","options":["Check reliable sources","Share immediately","Ignore evidence","Send your password"],"answer":"Check reliable sources","explanation":"Reliable sources help verify claims."}],
    "Problem Solving":[{"question":"If there are several solutions, what is a good approach?","options":["Compare solutions","Choose randomly","Give up","Ignore it"],"answer":"Compare solutions","explanation":"Comparing options can help."}],
    "Entrepreneurship":[{"question":"What is important when starting a useful product?","options":["Understand a real problem","Ignore customers","Copy everything","Never test"],"answer":"Understand a real problem","explanation":"Useful products solve real problems."}],
    "Colors":[{"question":"Which one is red?","options":["🔵","🟢","🔴","🟡"],"answer":"🔴","explanation":"🔴 is red."}],
    "Shapes":[{"question":"Which shape is a circle?","options":["⬜","🔺","⭕","⭐"],"answer":"⭕","explanation":"⭕ is a circle."}],
    "Animals":[{"question":"Which one is a cat?","options":["🐶","🐱","🐰","🐮"],"answer":"🐱","explanation":"🐱 represents a cat."}],
    "Sounds":[{"question":"Which animal says 'Woof'?","options":["🐱","🐶","🐮","🐟"],"answer":"🐶","explanation":"A dog commonly makes a woof sound."}],
    "Basic Language":[{"question":"What comes after A?","options":["B","C","D","E"],"answer":"B","explanation":"B comes after A."}],
    "Memory":[{"question":"Remember: 🍎 🐱 ⭐. Which item was in the middle?","options":["🍎","🐱","⭐","🐶"],"answer":"🐱","explanation":"🐱 was in the middle."}],
    "Numbers":[{"question":"What comes after 1?","options":["2","3","4","5"],"answer":"2","explanation":"2 comes after 1."}],
    "Language":[{"question":"Which word is a greeting?","options":["Hello","Table","Blue","Seven"],"answer":"Hello","explanation":"Hello is a greeting."}],
    "Storytelling":[{"question":"A child finds a lost toy. What is helpful?","options":["Find the owner","Hide it","Break it","Throw it away"],"answer":"Find the owner","explanation":"Finding the owner is responsible."}],
    "Reading":[{"question":"What is the opposite of 'big'?","options":["Small","Tall","Fast","Bright"],"answer":"Small","explanation":"Small is the opposite of big."}],
    "Creativity":[{"question":"Which activity can help creativity?","options":["Drawing a new idea","Never trying","Copying everything","Ignoring questions"],"answer":"Drawing a new idea","explanation":"Creating new ideas builds creativity."}],
    "English":[{"question":"Which word is an adjective?","options":["Beautiful","Run","Eat","Quickly"],"answer":"Beautiful","explanation":"Beautiful is an adjective."}],
    "General Knowledge":[{"question":"How many days are in a week?","options":["5","7","8","10"],"answer":"7","explanation":"A week has 7 days."}],
    "Advanced Maths":[{"question":"What is the square root of 64?","options":["6","8","10","12"],"answer":"8","explanation":"8 × 8 = 64."}],
    "Technology":[{"question":"Which device is used to process information?","options":["Computer","Chair","Bottle","Pencil"],"answer":"Computer","explanation":"A computer processes information."}],
    "AI & Technology":[{"question":"Which is a responsible use of AI?","options":["Check important information","Share passwords","Copy without understanding","Share private data"],"answer":"Check important information","explanation":"Important information should be checked."}]
}

DEFAULTS = {
    "normal_messages":[],
    "school_messages":[],
    "normal_session_id":str(uuid.uuid4()),
    "school_session_id":str(uuid.uuid4()),
    "school_age":"6–8 Years",
    "school_language":"hi",
    "play_age":PLAY_AGE_LEVELS[0],
    "play_language":"hi",
    "play_subject":None,
    "play_questions":[],
    "play_index":0,
    "play_score":0,
    "play_started":False,
    "play_answered":False,
    "play_last_correct":False,
    "play_last_explanation":"",
    "play_unlocked":[PLAY_AGE_LEVELS[0]],
    "play_completed":[],
    "play_best_scores":{}
}

for k,v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

@st.cache_resource
def init_supabase():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception:
        return None

supabase = init_supabase()

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("GROQ_API_KEY is missing from Streamlit secrets.")
    st.stop()

def current_user():
    try:
        return supabase.auth.get_user().user if supabase else None
    except Exception:
        return None

def india_time():
    try:
        return datetime.datetime.now(ZoneInfo("Asia/Kolkata")) if ZoneInfo else datetime.datetime.now()
    except Exception:
        return datetime.datetime.now()

def messages_for(mode):
    return st.session_state.school_messages if mode=="school" else st.session_state.normal_messages

def set_messages(mode, messages):
    if mode=="school":
        st.session_state.school_messages = messages
    else:
        st.session_state.normal_messages = messages

def new_chat(mode):
    set_messages(mode, [])
    st.session_state[f"{mode}_session_id"] = str(uuid.uuid4())

def save_chat(mode):
    user = current_user()
    msgs = messages_for(mode)
    if not user or not msgs or not supabase:
        return False
    payload = {
        "id":st.session_state[f"{mode}_session_id"],
        "user_id":user.id,
        "messages":msgs,
        "updated_at":datetime.datetime.utcnow().isoformat()
    }
    try:
        payload["mode"] = mode
        supabase.table("chat_sessions").upsert(payload).execute()
        return True
    except Exception:
        # Compatibility with the old table if mode column is not yet present.
        try:
            payload.pop("mode",None)
            supabase.table("chat_sessions").upsert(payload).execute()
            return True
        except Exception:
            return False

def saved_chats(mode):
    user=current_user()
    if not user or not supabase:
        return []
    try:
        r=supabase.table("chat_sessions").select("id,messages,updated_at,mode").eq("user_id",user.id).eq("mode",mode).order("updated_at",desc=True).limit(30).execute()
        return r.data or []
    except Exception:
        return []

def load_saved(mode,row):
    set_messages(mode,row.get("messages") or [])
    st.session_state[f"{mode}_session_id"]=row.get("id",str(uuid.uuid4()))

def explicit_image(text):
    t=text.lower()
    return any(x in t for x in [
        "generate image","create image","make an image","draw an image",
        "image banao","image bana","poster banao","photo banao",
        "चित्र बनाओ","तस्वीर बनाओ","image generate"
    ])

def image_prompt(text, school=False, age="Normal"):
    p=text.strip()
    p=re.sub(r"^(please\s+)?(make|create|generate|draw|banao|banaiye)\s+(an?\s+)?(image|photo|picture|poster|chitra)\s*(of|for|:)?\s*","",p,flags=re.I)
    rules=("Create ONLY the explicitly requested subject. Do not add random people, faces, animals, vehicles, characters, logos, brands, objects or scenery unless requested. "
           "Do not invent a story or main character. Keep the requested subject dominant and clean. No watermark.")
    if school:
        rules += f" Keep it safe and age-appropriate for {age}."
    return rules+" User request: "+p

def generate_image(prompt, school=False, age="Normal", aspect="1:1"):
    sizes={"1:1":(640,640),"16:9":(896,504),"9:16":(504,896)}
    w,h=sizes.get(aspect,(640,640))
    final=image_prompt(prompt,school,age)
    try:
        key=st.secrets.get("HF_API_KEY","")
        if key:
            r=requests.post(
                "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
                headers={"Authorization":f"Bearer {key}"},
                json={"inputs":final},
                timeout=60
            )
            if r.status_code==200 and r.content:
                return r.content
    except Exception:
        pass
    return f"https://image.pollinations.ai/prompt/{requests.utils.quote(final)}?width={w}&height={h}&nologo=true&seed={uuid.uuid4().int%100000}"

def transcribe(audio_bytes):
    if not audio_bytes:
        return ""
    path="temp_clyxesschat_audio.wav"
    try:
        with open(path,"wb") as f:
            f.write(audio_bytes)
        with open(path,"rb") as f:
            r=client.audio.transcriptions.create(
                file=f,
                model="whisper-large-v3",
                prompt="Hindi, English, Chhattisgarhi, Marathi, Bengali, Tamil, Telugu, Gujarati, Kannada, Malayalam, Odia, Chinese or Japanese."
            )
        return r.text.strip()
    except Exception:
        return ""
    finally:
        try: os.remove(path)
        except Exception: pass

def crisis_text(text):
    t=text.lower()
    words=[
        "suicide","kill myself","end my life","want to die","self harm","hurt myself",
        "मरना चाहता","आत्महत्या","खुद को मार","जान देना","खुदकुशी","मुझे बहुत अकेलापन",
        "बहुत अकेला","जीना नहीं चाहता"
    ]
    return any(x in t for x in words)

def normal_system():
    return """You are ClyxessChat AI, a friendly, intelligent and calm AI companion.
LANGUAGE LOCK: reply only in the same language as the user's latest message.
CONVERSATION CONTINUITY: use the recent conversation history. Never answer the latest message as if the previous messages did not exist.
If the user changes language, acknowledge it naturally and continue the existing topic. Do not erase the emotional/contextual state just because language changed.
Never invent memories or personal experiences.
For self-harm or suicide-related messages, be empathetic, encourage immediate contact with a trusted person and local emergency help when danger may be immediate, and never provide self-harm instructions.
If a later message is a normal follow-up, answer it normally while gently preserving relevant safety context."""

def school_system(age, language):
    return f"""You are ClyxessChat AI — a warm, safe, child-focused School Mode companion.
Age group: {age}. Selected language: {language}.
STRICT LANGUAGE LOCK: reply only in the selected language. Never mix languages.
CONVERSATION CONTINUITY: always use the supplied recent chat history. A language change does not reset the topic or emotional context.
Use simple, natural, age-appropriate and caring language. Never invent memories or ask for private information.
If the child says they want suicide, want to die, self-harm, or expresses serious loneliness/distress, respond like a caring adult/teacher: acknowledge the feeling, stay calm, say they should not handle it alone, encourage telling a trusted parent/guardian/teacher immediately, and advise local emergency help if they are in immediate danger. Do not shame, threaten, or provide harmful instructions.
For later normal messages, acknowledge the new request but do not pretend the earlier serious message never happened."""

def tavily(query):
    if not any(x in query.lower() for x in ["news","weather","mausam","rate","price","score","aaj","today","latest","breaking"]):
        return "",""
    try:
        r=requests.post(
            "https://api.tavily.com/search",
            json={"api_key":st.secrets["TAVILY_API_KEY"],"query":query,"search_depth":"advanced","max_results":5,"include_answer":True},
            timeout=15
        )
        d=r.json()
        context=d.get("answer","")
        sources="\n".join([f"{i+1}. [{x['title']}]({x['url']})" for i,x in enumerate(d.get("results",[])[:3])])
        return context,sources
    except Exception:
        return "",""

def ask_ai(history, system):
    payload=[{"role":"system","content":system}]+history[-12:]
    for model in GROQ_MODELS:
        try:
            r=client.chat.completions.create(model=model,messages=payload,temperature=.7,max_tokens=4000)
            return r.choices[0].message.content,model
        except Exception:
            continue
    return "",None

# ============================================================
# SOCIAL LOGIN — Google and Facebook logos
# ============================================================
def render_social_login():
    st.markdown("### ⚡ Social Login")

    google_svg="""<svg viewBox="0 0 24 24"><path fill="#4285F4" d="M21.35 12.27c0-.79-.07-1.55-.23-2.27H12v4.3h5.24a4.48 4.48 0 0 1-1.94 2.94v2.45h3.14c1.84-1.7 2.91-4.2 2.91-7.42z"/><path fill="#34A853" d="M12 21.75c2.63 0 4.84-.87 6.45-2.36l-3.14-2.45c-.87.58-1.98.93-3.31.93-2.54 0-4.7-1.72-5.47-4.03H3.28v2.53A9.75 9.75 0 0 0 12 21.75z"/><path fill="#FBBC05" d="M6.53 13.84A5.86 5.86 0 0 1 6.22 12c0-.64.11-1.26.31-1.84V7.63H3.28A9.75 9.75 0 0 0 2.25 12c0 1.57.38 3.06 1.03 4.37l3.25-2.53z"/><path fill="#EA4335" d="M12 6.13c1.43 0 2.72.49 3.73 1.46l2.8-2.8C16.84 3.15 14.63 2.25 12 2.25a9.75 9.75 0 0 0-8.72 5.38l3.25 2.53C7.3 7.85 9.46 6.13 12 6.13z"/></svg>"""
    facebook_svg="""<svg viewBox="0 0 24 24"><path fill="#1877F2" d="M24 12.07C24 5.4 18.63 0 12 0S0 5.4 0 12.07c0 6.02 4.39 11 10.13 11.93v-8.44H7.08v-3.49h3.05V9.41c0-3.02 1.79-4.69 4.54-4.69 1.31 0 2.68.24 2.68.24v2.96h-1.51c-1.49 0-1.96.93-1.96 1.89v2.26h3.34l-.53 3.49h-2.81V24C19.61 23.07 24 18.09 24 12.07z"/></svg>"""

    c1,c2=st.columns(2)
    with c1:
        st.markdown(f'<div class="social-logo">{google_svg}<span>Google</span></div>',unsafe_allow_html=True)
        if st.button("Continue with Google",use_container_width=True,key="social_google"):
            try:
                r=supabase.auth.sign_in_with_oauth({
                    "provider":"google",
                    "options":{"redirect_to":st.secrets.get("SUPABASE_REDIRECT_URL","")}
                })
                if getattr(r,"url",None):
                    st.link_button("Open Google Login",r.url,use_container_width=True)
            except Exception as e:
                st.error(f"Google login failed: {e}")

    with c2:
        st.markdown(f'<div class="social-logo">{facebook_svg}<span>Facebook</span></div>',unsafe_allow_html=True)
        if st.button("Continue with Facebook",use_container_width=True,key="social_facebook"):
            try:
                r=supabase.auth.sign_in_with_oauth({
                    "provider":"facebook",
                    "options":{"redirect_to":st.secrets.get("SUPABASE_REDIRECT_URL","")}
                })
                if getattr(r,"url",None):
                    st.link_button("Open Facebook Login",r.url,use_container_width=True)
            except Exception as e:
                st.error(f"Facebook login failed: {e}")

def render_login():
    st.title("🔐 Login / Sign Up")
    if not supabase:
        st.warning("Add SUPABASE_URL and SUPABASE_KEY to Streamlit secrets.")
        return

    render_social_login()
    st.caption("Google/Facebook providers must also be enabled in Supabase Authentication.")

    t1,t2=st.tabs(["Log In","Sign Up"])
    with t1:
        email=st.text_input("Email",key="login_email")
        password=st.text_input("Password",type="password",key="login_password")
        if st.button("Log In",type="primary",use_container_width=True):
            try:
                supabase.auth.sign_in_with_password({"email":email,"password":password})
                st.success("Logged in successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")

    with t2:
        name=st.text_input("Name",key="signup_name")
        email=st.text_input("Email",key="signup_email")
        password=st.text_input("Password",type="password",key="signup_password")
        if st.button("Create Account",use_container_width=True):
            try:
                supabase.auth.sign_up({"email":email,"password":password,"options":{"data":{"name":name}}})
                st.success("Account created. Confirm email if your Supabase project requires it.")
            except Exception as e:
                st.error(f"Sign up failed: {e}")

# ============================================================
# SAVED CHATS
# ============================================================
def render_saved_chats(mode):
    user=current_user()
    if not user:
        st.caption("🔒 Login to see saved chats.")
        return

    rows=saved_chats(mode)
    if not rows:
        st.caption("No saved chats yet.")
        return

    for row in rows:
        msgs=row.get("messages") or []
        title=next((m.get("content","") for m in msgs if m.get("role")=="user"),"New Chat")
        title=str(title).replace("\n"," ")[:48]
        if len(str(title))>=48:title+="…"
        if st.button("💬 "+title,key=f"saved_{mode}_{row.get('id')}",use_container_width=True):
            load_saved(mode,row)
            st.rerun()

# ============================================================
# CHAT
# ============================================================
def render_chat(mode):
    school=mode=="school"
    history=messages_for(mode)

    if school:
        c1,c2=st.columns(2)
        with c1:
            age=st.selectbox("👶 Age",PLAY_AGE_LEVELS,index=PLAY_AGE_LEVELS.index(st.session_state.school_age) if st.session_state.school_age in PLAY_AGE_LEVELS else 3,key="school_age")
        with c2:
            labels=list(PLAY_LANGUAGES.keys())
            current_label=next((x for x,c in PLAY_LANGUAGES.items() if c==st.session_state.school_language),labels[0])
            label=st.selectbox("🌐 Language",labels,index=labels.index(current_label),key="school_language_label")
            st.session_state.school_language=PLAY_LANGUAGES[label]
        st.markdown('<div class="kids-input-note">🧸 Chat AI Kids • Ask, learn, imagine & explore safely</div>',unsafe_allow_html=True)

    for m in history:
        with st.chat_message(m["role"]):
            if m.get("image_url"):
                st.markdown('<div class="media-card">',unsafe_allow_html=True)
                st.image(m["image_url"],width=520)
                st.markdown('</div>',unsafe_allow_html=True)
            else:
                st.markdown(m.get("content",""))

    voice_prompt=""
    if mic_recorder:
        audio=mic_recorder(
            start_prompt="🎙️",
            stop_prompt="⏹️",
            key=f"mic_{mode}"
        )
        if audio:
            voice_prompt=transcribe(audio.get("bytes",b""))

    placeholder="🧸 Chat AI Kids — type your message…" if school else "Message ClyxessChat AI…"
    prompt=st.chat_input(placeholder)
    if not prompt and voice_prompt:
        prompt=voice_prompt

    if not prompt:
        return

    history.append({"role":"user","content":prompt})
    set_messages(mode,history)

    with st.chat_message("user"):
        st.markdown(f'<div class="user-bubble">{prompt}</div>',unsafe_allow_html=True)

    # Explicit image requests only — normal conversation can no longer trigger random images.
    if explicit_image(prompt):
        with st.chat_message("assistant"):
            with st.spinner("🎨 Creating the requested image…"):
                img=generate_image(prompt,school,st.session_state.school_age if school else "Normal","1:1")
            st.markdown('<div class="media-card">',unsafe_allow_html=True)
            st.image(img,width=520)
            st.markdown('</div>',unsafe_allow_html=True)
        history.append({"role":"assistant","content":"Generated image","image_url":img})
        set_messages(mode,history)
        save_chat(mode)
        st.rerun()

    context,sources=tavily(prompt)
    if school:
        system=school_system(
            st.session_state.school_age,
            next((x for x,c in PLAY_LANGUAGES.items() if c==st.session_state.school_language),"English")
        )
    else:
        system=normal_system()

    system+="\n"+india_time().strftime("Current India date/time: %A, %d %B %Y, %I:%M %p IST.")
    if context:
        system+="\nLive web information:\n"+context

    response,model=ask_ai(history,system)
    if not response:
        st.error("AI response nahi aa paya. Please try again.")
        return

    with st.chat_message("assistant"):
        st.markdown(response)
        if sources:
            st.caption("Sources:\n"+sources)

    history.append({"role":"assistant","content":response})
    set_messages(mode,history)
    save_chat(mode)

# ============================================================
# IMAGE GENERATOR
# ============================================================
def render_image_generator():
    st.title("🎨 Creative AI Image Generator")
    prompt=st.text_area("Describe exactly what you want",placeholder="Example: Happy Diwali greeting poster with diyas, no people")
    aspect=st.selectbox("📐 Format",["1:1","16:9","9:16"])
    if st.button("🎨 Generate Image",type="primary",use_container_width=True) and prompt.strip():
        img=generate_image(prompt,False,"Normal",aspect)
        st.markdown('<div class="media-card">',unsafe_allow_html=True)
        st.image(img,width=520)
        st.markdown('</div>',unsafe_allow_html=True)
        if isinstance(img,bytes):
            st.download_button("⬇️ Save Image",data=img,file_name="clyxesschat_image.png",mime="image/png")
        else:
            st.link_button("🔗 Open Full Image",img)

# ============================================================
# PLAY & LEARN
# ============================================================
def build_questions(subject):
    pool=QUESTION_BANK.get(subject,[{"question":"Which option is correct?","options":["A","B","C","D"],"answer":"A","explanation":"Demo question."}])
    result=[]
    while len(result)<10:
        result.extend([dict(x) for x in pool])
    random.shuffle(result)
    return result[:10]

def render_play():
    st.markdown('<div class="play-hero"><h1>🎮 ClyxessChat AI — Play & Learn</h1><p>Age-based learning challenges.</p></div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    with c1:
        age=st.selectbox("👶 Select Age",PLAY_AGE_LEVELS,index=PLAY_AGE_LEVELS.index(st.session_state.play_age))
    with c2:
        labels=list(PLAY_LANGUAGES.keys())
        label=st.selectbox("🌐 Select Language",labels,index=list(PLAY_LANGUAGES.values()).index(st.session_state.play_language))
        lang=PLAY_LANGUAGES[label]
    with c3:
        subjects=AGE_SUBJECTS[age]
        subject=st.selectbox("📚 Select Subject",subjects,index=subjects.index(st.session_state.play_subject) if st.session_state.play_subject in subjects else 0)

    st.session_state.play_age=age
    st.session_state.play_language=lang
    st.session_state.play_subject=subject

    if age not in st.session_state.play_unlocked:
        st.error("🔒 This age level is locked.")
        return

    if not st.session_state.play_started:
        st.info("🎯 10 questions. Get 10/10 to unlock the next age level.")
        if st.button("🚀 Start Game",type="primary",use_container_width=True):
            st.session_state.play_questions=build_questions(subject)
            st.session_state.play_index=0
            st.session_state.play_score=0
            st.session_state.play_answered=False
            st.session_state.play_started=True
            st.rerun()
        return

    qs=st.session_state.play_questions
    i=st.session_state.play_index
    q=qs[i]
    st.progress(i/10,text=f"Question {i+1}/10")
    st.subheader("❓ "+q["question"])
    answer=st.radio("Choose your answer:",q["options"],key=f"play_{age}_{subject}_{i}")

    if not st.session_state.play_answered:
        if st.button("✅ Submit Answer",type="primary",use_container_width=True):
            st.session_state.play_last_correct=answer==q["answer"]
            if answer==q["answer"]:
                st.session_state.play_score+=1
            st.session_state.play_last_explanation=q.get("explanation","")
            st.session_state.play_answered=True
            st.rerun()
    else:
        if st.session_state.play_last_correct:
            st.success(f"✅ Correct! Score: {st.session_state.play_score}/10")
        else:
            st.warning(f"❌ Correct answer: {q['answer']}")
        st.info("💡 "+st.session_state.play_last_explanation)

        if i<9:
            if st.button("➡️ Next Question",use_container_width=True):
                st.session_state.play_index+=1
                st.session_state.play_answered=False
                st.rerun()
        else:
            score=st.session_state.play_score
            if score==10:
                st.balloons()
                st.success("🏆 LEVEL COMPLETE — 10/10!")
                if age not in st.session_state.play_completed:
                    st.session_state.play_completed.append(age)
                st.session_state.play_best_scores[f"{age}:{subject}"]=10
                try:
                    nxt=PLAY_AGE_LEVELS[PLAY_AGE_LEVELS.index(age)+1]
                    if nxt not in st.session_state.play_unlocked:
                        st.session_state.play_unlocked.append(nxt)
                        st.success(f"🔓 Next Level Unlocked: {nxt}")
                except Exception:
                    pass
            else:
                st.warning(f"⭐ Final Score: {score}/10 — retry for 10/10.")

            if st.button("🔄 Restart Game",use_container_width=True):
                st.session_state.play_started=False
                st.session_state.play_questions=[]
                st.session_state.play_index=0
                st.session_state.play_score=0
                st.session_state.play_answered=False
                st.rerun()

# ============================================================
# LEGAL
# ============================================================
def render_legal():
    st.title("📜 Terms • Privacy • Cookies")

    st.subheader("Terms & Conditions")
    st.write("Use ClyxessChat AI responsibly. AI-generated responses may be incorrect. Verify important information.")

    st.subheader("Privacy Policy")
    st.write("Saved chats are connected to the signed-in account. Logged-out users cannot see account-saved chats.")

    st.subheader("Cookies & Storage")
    st.write("The application may use browser/session storage needed for authentication and app functionality.")

    st.subheader("School Mode & Children")
    st.write("School Mode is intended for age-appropriate learning. Parents or guardians should supervise use where appropriate.")

    st.caption("Prototype legal text — obtain professional legal/privacy review before production launch.")

# ============================================================
# PARENT DASHBOARD
# ============================================================
def render_parent_dashboard():
    st.title("👨‍👩‍👦 Parent Dashboard")
    best=max(st.session_state.play_best_scores.values(),default=0)
    c1,c2,c3=st.columns(3)
    c1.metric("Completed Levels",len(st.session_state.play_completed))
    c2.metric("Best Score",f"{best}/10")
    c3.metric("Current Level",st.session_state.play_age)

# ============================================================
# SIDEBAR
# ============================================================
st.markdown('<div class="header"><h1>💬 ClyxessChat AI</h1></div>',unsafe_allow_html=True)

user=current_user()

with st.sidebar:
    st.title("💬 ClyxessChat AI")

    # Login moved to the circular icon position near the top.
    if user:
        st.success(f"👤 {user.email}")
        if st.button("🚪 Log Out",use_container_width=True):
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            st.rerun()
    else:
        if st.button("◉  🔐 Login / Sign Up",use_container_width=True,key="sidebar_login"):
            st.session_state.sidebar_mode="login"
            st.rerun()

    mode=st.radio("Select Mode",[
        "Normal Chat",
        "Creative Lab (School Mode)",
        "🎮 Play & Learn",
        "🎨 Creative AI Image Generator",
        "📜 Terms • Privacy • Cookies",
        "👨‍👩‍👦 Parent Dashboard"
    ],key="main_mode")

    st.markdown("---")

    if mode in ["Normal Chat","Creative Lab (School Mode)"]:
        chat_mode="school" if mode.startswith("Creative") else "normal"

        if st.button("+ New Chat",use_container_width=True,key=f"new_{chat_mode}"):
            new_chat(chat_mode)
            st.rerun()

        st.markdown("### 💾 Saved Chats")
        render_saved_chats(chat_mode)

    st.caption("🇮🇳 India live time: "+india_time().strftime("%A, %d %B %Y • %I:%M %p IST"))

# ============================================================
# ROUTING
# ============================================================
if st.session_state.get("sidebar_mode")=="login":
    render_login()
    st.stop()

if mode=="🎨 Creative AI Image Generator":
    render_image_generator()
    st.stop()

if mode=="🎮 Play & Learn":
    render_play()
    st.stop()

if mode=="📜 Terms • Privacy • Cookies":
    render_legal()
    st.stop()

if mode=="👨‍👩‍👦 Parent Dashboard":
    render_parent_dashboard()
    st.stop()

if mode=="Creative Lab (School Mode)":
    render_chat("school")
    st.stop()

render_chat("normal")
