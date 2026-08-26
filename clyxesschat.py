import streamlit as st
from groq import Groq
from supabase import create_client
import datetime, uuid, requests, time, re, os
from fpdf import FPDF

st.set_page_config(page_title="ClyxessChat AI", layout="wide")

# --- CSS ---
st.markdown("""
<style>
.main {max-width: 850px; margin: auto;}
.header {position: sticky; top: 0; background: #202123; padding: 18px; border-bottom: 1px solid #444; z-index: 999; margin: -1rem -1rem 20px -1rem;}
.header h1 {color: white; font-size: 22px; font-weight: 600; margin: 0; text-align: center;}
.user-bubble {background-color: #D9FDD3; color: #111b21; padding: 10px 14px; border-radius: 18px; border-bottom-right-radius: 4px; max-width: 75%; margin-left: auto; margin-bottom: 10px; text-align: right;}
.gradient-text {background: linear-gradient(90deg, #ff00cc, #3333ff, #00ffcc); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
.age-btn-active {background: #2ecc71!important; color: white!important; border: 2px solid white!important;}
</style>
""", unsafe_allow_html=True)

# --- CONFIG ---
GROQ_MODELS = ["openai/gpt-oss-120b","openai/gpt-oss-20b","qwen/qwen3-32b","llama-3.1-70b-versatile","mixtral-8x7b-32768","llama-3.1-8b-instant"]

# ============ IMAGE FALLBACK FUNCTION (DONO MODE ME) ============
def generate_image_url(prompt, is_school_mode, age):
    if is_school_mode:
        if "1-2" in age or "3-4" in age:
            final_prompt = f"cute baby cartoon, very simple, bright colors, 3d pixar style, {prompt}"
        else:
            final_prompt = f"kid friendly educational diagram, colorful, {prompt}"
    else:
        final_prompt = f"realistic, cinematic, 4k, {prompt}"

    # 1. Try HuggingFace (Clean)
    try:
        hf_key = st.secrets.get("HF_API_KEY", "")
        if hf_key:
            API_URL = "https://api-inference.huggingface.co/models/stabilityai/sdxl-turbo"
            headers = {"Authorization": f"Bearer {hf_key}"}
            r = requests.post(API_URL, headers=headers, json={"inputs": final_prompt}, timeout=20)
            if r.status_code == 200:
                return r.content, "huggingface" # returns image bytes
    except: pass

    # 2. Fallback Pollinations (Fastest, never fails)
    poll_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(final_prompt)}?width=1024&height=1024&nologo=true&seed={uuid.uuid4().int % 10000}"
    return poll_url, "pollinations"

# ============ PROMPTS ============
NORMAL_SYSTEM_PROMPT = """
You are ClyxessChat AI, created by ClyxessChat AI Technology.
CORE RULE: REPLY ONLY IN THE SAME LANGUAGE AS USER.
Your name is ClyxessChat AI. Friendly, intelligent, calm.
If user asks to generate image, say: "Generating image for: [prompt]"
"""

def get_school_system_prompt(age_group):
    base = f"You are ClyxessChat AI - School Mode Creative Lab. Current Age Group: {age_group}. "
    if "1-2" in age_group or "3-4" in age_group:
        return base + """
        You are Didi for 1-4 years kids. RULES: Only rhymes, colors, emojis, sounds. Use Hinglish like 'dekho laal gubbara'. Very very short sentences. Ask sensory questions like 'Tap karo toh kya hoga?'. Replace youtube with active play. Never use tough words. You are 'Chote Inventor' ki didi.
        If user wants image, create cute cartoon prompt.
        """
    elif "5-6" in age_group or "6-8" in age_group:
        return base + """
        Age 5-8: Focus Curiosity & Basic Logic. Task: Interactive Story-Building & Shape Puzzles. Hint Style: Kahani wala. Eg: 'Sher jungle me kho gaya, pehle kya kare?'. Socratic method - answer with question.
        """
    elif "10-11" in age_group:
        return base + """
        Age 7-10: Focus Maker & Practical Science. Task: Step-by-step DIY Projects & Logic Challenges. Hint Style: Jugaad wala. Eg: 'Rocket banana hai? Socho hawa kaha se niklegi?'. Give steps, not direct answer.
        """
    else:
        return base + """
        Age 11+: Focus Future Tech, AI & App Prototyping. Task: Coding Logic, App Wireframing. Hint Style: Innovator wala. Challenge them to break big problem into 2 small parts.
        """

# --- Tavily, Groq, Supabase (Tera purana code same) ---
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

# SIDEBAR - MODE SELECTOR
with st.sidebar:
    st.title("💬 ClyxessChat AI")
    mode = st.radio("Select Mode", ["Normal Chat", "Creative Lab (School Mode)", "Creative Lab 2.0"], index=0)
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
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
if "Creative Lab 2.0" in mode:
# ============================================================
# CLYXESSCHAT AI
# PLAY & LEARN
# Age-Based + Subject-Based + Multilingual Learning Engine
# ============================================================

# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "ClyxessChat AI"
QUESTIONS_PER_LEVEL = 10

AGE_LEVELS = [
    "1–2 Years",
    "3–4 Years",
    "5–6 Years",
    "6–8 Years",
    "8–10 Years",
    "10–11 Years",
    "11+ Years"
]

LANGUAGES = {
    "🇮🇳 हिंदी": "hi",
    "🇮🇳 मराठी": "mr",
    "🇮🇳 বাংলা": "bn",
    "🇮🇳 தமிழ்": "ta",
    "🇮🇳 తెలుగు": "te",
    "🇮🇳 ગુજરાતી": "gu",
    "🇮🇳 ಕನ್ನಡ": "kn",
    "🇮🇳 മലയാളം": "ml",
    "🇮🇳 ଓଡ଼ିଆ": "or",
    "🇬🇧 English": "en",
    "🇨🇳 中文": "zh",
    "🇯🇵 日本語": "ja"
}

# ============================================================
# AGE → SUBJECT MAP
# ============================================================

AGE_SUBJECTS = {
    "1–2 Years": [
        "Colors",
        "Shapes",
        "Animals",
        "Sounds",
        "Basic Language",
        "Memory"
    ],

    "3–4 Years": [
        "Numbers",
        "Language",
        "Shapes",
        "Storytelling",
        "Communication",
        "Logic"
    ],

    "5–6 Years": [
        "Maths",
        "Science Basics",
        "Language",
        "Reading",
        "Logic",
        "Creativity"
    ],

    "6–8 Years": [
        "Maths",
        "Science",
        "English",
        "General Knowledge",
        "Logic",
        "Communication",
        "Technology Basics"
    ],

    "8–10 Years": [
        "Maths",
        "Science",
        "English",
        "Coding Basics",
        "AI Introduction",
        "Financial Literacy",
        "Communication"
    ],

    "10–11 Years": [
        "Advanced Maths",
        "Science",
        "Technology",
        "AI Literacy",
        "Coding",
        "Financial Literacy",
        "Critical Thinking"
    ],

    "11+ Years": [
        "AI & Technology",
        "Coding",
        "Financial Literacy",
        "Cyber Safety",
        "Communication",
        "Entrepreneurship",
        "Critical Thinking",
        "Problem Solving"
    ]
}

# ============================================================
# DEMO QUESTION DATABASE
#
# Production में यही function AI backend से questions लेगा.
# ============================================================

QUESTION_BANK = {

    "Maths": [
        {
            "question": "What is 7 + 5?",
            "options": ["10", "12", "14", "15"],
            "answer": "12",
            "explanation": "7 + 5 = 12."
        },
        {
            "question": "What is 6 × 4?",
            "options": ["20", "22", "24", "26"],
            "answer": "24",
            "explanation": "6 groups of 4 make 24."
        }
    ],

    "Science": [
        {
            "question": "Which planet do we live on?",
            "options": ["Mars", "Earth", "Venus", "Jupiter"],
            "answer": "Earth",
            "explanation": "We live on planet Earth."
        },
        {
            "question": "Which organ pumps blood?",
            "options": ["Brain", "Heart", "Lungs", "Stomach"],
            "answer": "Heart",
            "explanation": "The heart pumps blood around the body."
        }
    ],

    "Logic": [
        {
            "question": "What comes next: 2, 4, 6, 8, ?",
            "options": ["9", "10", "11", "12"],
            "answer": "10",
            "explanation": "The pattern increases by 2."
        }
    ],

    "Communication": [
        {
            "question": "Someone says 'Thank you'. What is a polite response?",
            "options": [
                "You're welcome",
                "Go away",
                "No",
                "Stop"
            ],
            "answer": "You're welcome",
            "explanation": "You're welcome is a polite response."
        }
    ],

    "Financial Literacy": [
        {
            "question": "If you receive ₹100 and save ₹20, how much is left to spend?",
            "options": ["₹60", "₹70", "₹80", "₹90"],
            "answer": "₹80",
            "explanation": "₹100 - ₹20 = ₹80."
        }
    ],

    "Technology Basics": [
        {
            "question": "Which device is commonly used to type on a computer?",
            "options": ["Keyboard", "Speaker", "Camera", "Printer"],
            "answer": "Keyboard",
            "explanation": "A keyboard is commonly used to type."
        }
    ],

    "AI Introduction": [
        {
            "question": "What does AI stand for?",
            "options": [
                "Artificial Intelligence",
                "Automatic Internet",
                "Advanced Input",
                "Application Interface"
            ],
            "answer": "Artificial Intelligence",
            "explanation": "AI stands for Artificial Intelligence."
        }
    ],

    "AI Literacy": [
        {
            "question": "What is a good habit when using AI?",
            "options": [
                "Check important information",
                "Believe everything automatically",
                "Share passwords",
                "Share private information"
            ],
            "answer": "Check important information",
            "explanation": "AI can make mistakes, so important information should be checked."
        }
    ],

    "Coding": [
        {
            "question": "What is code?",
            "options": [
                "Instructions given to a computer",
                "A type of food",
                "A school bag",
                "A musical instrument"
            ],
            "answer": "Instructions given to a computer",
            "explanation": "Code contains instructions that computers can execute."
        }
    ],

    "Coding Basics": [
        {
            "question": "What is a variable used for in programming?",
            "options": [
                "Storing information",
                "Charging a phone",
                "Printing paper",
                "Playing music"
            ],
            "answer": "Storing information",
            "explanation": "Variables can store values used by a program."
        }
    ],

    "Cyber Safety": [
        {
            "question": "Should you share your password with strangers online?",
            "options": [
                "Yes",
                "No"
            ],
            "answer": "No",
            "explanation": "Passwords should be kept private."
        }
    ],

    "Critical Thinking": [
        {
            "question": "What should you do before believing an important claim online?",
            "options": [
                "Check reliable sources",
                "Share it immediately",
                "Ignore all evidence",
                "Send your password"
            ],
            "answer": "Check reliable sources",
            "explanation": "Checking reliable sources helps identify inaccurate information."
        }
    ],

    "Problem Solving": [
        {
            "question": "If a problem has several possible solutions, what is a good approach?",
            "options": [
                "Compare the solutions",
                "Choose randomly",
                "Give up immediately",
                "Ignore the problem"
            ],
            "answer": "Compare the solutions",
            "explanation": "Comparing options can help find a better solution."
        }
    ],

    "Entrepreneurship": [
        {
            "question": "What is one important part of starting a useful product?",
            "options": [
                "Understanding a real problem",
                "Ignoring customers",
                "Copying everything",
                "Never testing the idea"
            ],
            "answer": "Understanding a real problem",
            "explanation": "Good products usually solve a real problem."
        }
    ]
}

# ============================================================
# UI TRANSLATIONS
# ============================================================

UI = {
    "en": {
        "title": "🎮 Play & Learn",
        "age": "Select Age",
        "language": "Select Language",
        "subject": "Select Subject",
        "start": "🚀 Start Game",
        "score": "Score",
        "question": "Question",
        "submit": "Submit Answer",
        "next": "Next Question",
        "complete": "🎉 Level Complete!",
        "locked": "🔒 Locked",
        "retry": "🔄 Try Again",
        "unlocked": "🔓 Next Level Unlocked!",
        "correct": "✅ Correct!",
        "wrong": "❌ Not quite!",
        "finish": "🏆 Amazing! 10/10 completed!",
        "progress": "Progress"
    },

    "hi": {
        "title": "🎮 खेलो और सीखो",
        "age": "उम्र चुनें",
        "language": "भाषा चुनें",
        "subject": "विषय चुनें",
        "start": "🚀 गेम शुरू करें",
        "score": "स्कोर",
        "question": "सवाल",
        "submit": "उत्तर जांचें",
        "next": "अगला सवाल",
        "complete": "🎉 लेवल पूरा!",
        "locked": "🔒 लॉक",
        "retry": "🔄 फिर से खेलें",
        "unlocked": "🔓 अगला लेवल अनलॉक!",
        "correct": "✅ बिल्कुल सही!",
        "wrong": "❌ कोई बात नहीं, फिर कोशिश करो!",
        "finish": "🏆 शानदार! 10/10 पूरा!",
        "progress": "प्रगति"
    }
}

# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "selected_age": AGE_LEVELS[0],
    "selected_language": "hi",
    "selected_subject": None,
    "questions": [],
    "question_index": 0,
    "score": 0,
    "game_started": False,
    "answered": False,
    "last_correct": False,
    "last_explanation": "",
    "unlocked_levels": [AGE_LEVELS[0]]
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_ui(language: str) -> Dict[str, str]:
    return UI.get(language, UI["en"])


def get_subjects(age: str) -> List[str]:
    return AGE_SUBJECTS.get(age, [])


def is_level_unlocked(age: str) -> bool:
    return age in st.session_state.unlocked_levels


def unlock_next_level(age: str) -> str | None:

    try:
        current_index = AGE_LEVELS.index(age)
    except ValueError:
        return None

    next_index = current_index + 1

    if next_index >= len(AGE_LEVELS):
        return None

    next_level = AGE_LEVELS[next_index]

    if next_level not in st.session_state.unlocked_levels:
        st.session_state.unlocked_levels.append(next_level)

    return next_level


def build_demo_questions(subject: str) -> List[Dict[str, Any]]:

    bank = QUESTION_BANK.get(subject, [])

    if not bank:
        return []

    result = []

    for item in bank:
        result.append({
            "question": item["question"],
            "options": list(item["options"]),
            "answer": item["answer"],
            "explanation": item.get("explanation", "")
        })

    random.shuffle(result)

    # Repeat demo questions if database is small
    while len(result) < QUESTIONS_PER_LEVEL:
        result.extend(result[:min(
            len(result),
            QUESTIONS_PER_LEVEL - len(result)
        )])

    return result[:QUESTIONS_PER_LEVEL]


# ============================================================
# AI QUESTION GENERATOR HOOK
# ============================================================

def generate_ai_questions(
    age: str,
    language: str,
    subject: str,
    count: int = 10
) -> List[Dict[str, Any]]:
    """
    PRODUCTION HOOK

    यहां तुम अपने AI backend/API को connect करोगे.

    AI को ideally यह information भेजनी चाहिए:

    Age
    Language
    Subject
    Difficulty
    Number of questions

    AI से JSON format में questions वापस लेने चाहिए.

    Example output:

    [
        {
            "question": "...",
            "options": ["A", "B", "C", "D"],
            "answer": "B",
            "explanation": "..."
        }
    ]

    IMPORTANT:
    API key कभी भी frontend code में hard-code मत करना.
    Backend / secrets / server-side function use करना.
    """

    # अभी safe demo fallback
    return build_demo_questions(subject)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        padding: 24px;
        border-radius: 20px;
        background: linear-gradient(
            135deg,
            #0f172a,
            #172554
        );
        color: white;
        margin-bottom: 25px;
    }

    .main-title h1 {
        margin: 0;
        font-size: 34px;
    }

    .main-title p {
        margin-top: 8px;
        font-size: 17px;
        opacity: 0.85;
    }

    .game-card {
        padding: 25px;
        border-radius: 20px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        margin: 15px 0;
    }

    .locked-card {
        padding: 20px;
        border-radius: 18px;
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="main-title">
        <h1>🎮 ClyxessChat AI — Play & Learn</h1>
        <p>AI-powered learning through games, challenges and conversation.</p>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TOP SETTINGS
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:

    selected_age = st.selectbox(
        "👶 Select Age",
        AGE_LEVELS,
        index=AGE_LEVELS.index(
            st.session_state.selected_age
        )
    )

with col2:

    language_label = st.selectbox(
        "🌐 Select Language",
        list(LANGUAGES.keys())
    )

    selected_language = LANGUAGES[language_label]

with col3:

    subjects = get_subjects(selected_age)

    selected_subject = st.selectbox(
        "📚 Select Subject",
        subjects
    )


st.session_state.selected_age = selected_age
st.session_state.selected_language = selected_language
st.session_state.selected_subject = selected_subject


# ============================================================
# LOCK CHECK
# ============================================================

if not is_level_unlocked(selected_age):

    st.error(
        f"🔒 {selected_age} is locked."
    )

    st.info(
        "Complete the previous level with 10/10 "
        "to unlock this level."
    )

    st.stop()


# ============================================================
# SIDEBAR PROGRESS
# ============================================================

with st.sidebar:

    st.header("🎮 Learning Progress")

    st.write(
        f"👶 Age: **{selected_age}**"
    )

    st.write(
        f"🌐 Language: **{language_label}**"
    )

    st.write(
        f"📚 Subject: **{selected_subject}**"
    )

    st.divider()

    st.subheader("🔓 Levels")

    for level in AGE_LEVELS:

        if level in st.session_state.unlocked_levels:

            if level == selected_age:
                st.success(f"⭐ {level}")
            else:
                st.write(f"✅ {level}")

        else:

            st.write(f"🔒 {level}")


# ============================================================
# START SCREEN
# ============================================================

if not st.session_state.game_started:

    st.markdown(
        '<div class="game-card">',
        unsafe_allow_html=True
    )

    st.subheader("🎯 Ready to Learn?")

    st.write(
        f"**Age:** {selected_age}"
    )

    st.write(
        f"**Subject:** {selected_subject}"
    )

    st.write(
        f"**Language:** {language_label}"
    )

    st.info(
        "🎮 10 questions होंगे। "
        "10/10 complete करने पर अगला age level unlock होगा."
    )

    if st.button(
        "🚀 Start Game",
        use_container_width=True,
        type="primary"
    ):

        with st.spinner(
            "🤖 Creating your learning challenge..."
        ):

            questions = generate_ai_questions(
                age=selected_age,
                language=selected_language,
                subject=selected_subject,
                count=QUESTIONS_PER_LEVEL
            )

        if not questions:

            st.error(
                "Questions generate नहीं हो पाए। Please try again."
            )

        else:

            st.session_state.questions = questions
            st.session_state.question_index = 0
            st.session_state.score = 0
            st.session_state.answered = False
            st.session_state.last_correct = False
            st.session_state.last_explanation = ""
            st.session_state.game_started = True

            st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

    st.stop()


# ============================================================
# QUESTION DATA
# ============================================================

questions = st.session_state.questions

if not questions:

    st.error("No questions available.")
    st.stop()

question_index = st.session_state.question_index

current = questions[question_index]

question_text = current["question"]
options = current["options"]
correct_answer = current["answer"]
explanation = current.get("explanation", "")


# ============================================================
# PROGRESS
# ============================================================

progress = (
    (question_index) /
    QUESTIONS_PER_LEVEL
)

st.progress(
    progress,
    text=f"Question {question_index + 1}/{QUESTIONS_PER_LEVEL}"
)

c1, c2 = st.columns(2)

with c1:
    st.metric(
        "🎯 Question",
        f"{question_index + 1}/10"
    )

with c2:
    st.metric(
        "⭐ Score",
        f"{st.session_state.score}/10"
    )


# ============================================================
# QUESTION CARD
# ============================================================

st.markdown(
    '<div class="game-card">',
    unsafe_allow_html=True
)

st.subheader(
    f"❓ {question_text}"
)

answer = st.radio(
    "Choose your answer:",
    options,
    key=f"answer_{selected_age}_{selected_subject}_{question_index}"
)

st.markdown(
    "</div>",
    unsafe_allow_html=True
)


# ============================================================
# SUBMIT
# ============================================================

ui = get_ui(selected_language)

if not st.session_state.answered:

    if st.button(
        "✅ Submit Answer",
        use_container_width=True,
        type="primary"
    ):

        if answer == correct_answer:

            st.session_state.score += 1
            st.session_state.last_correct = True
            st.session_state.last_explanation = explanation

        else:

            st.session_state.last_correct = False
            st.session_state.last_explanation = explanation

        st.session_state.answered = True

        st.rerun()


# ============================================================
# FEEDBACK
# ============================================================

if st.session_state.answered:

    if st.session_state.last_correct:

        st.success(
            f"{ui['correct']} ⭐ "
            f"Score: {st.session_state.score}/10"
        )

    else:

        st.warning(
            f"{ui['wrong']} "
            f"Correct answer: **{correct_answer}**"
        )

    if st.session_state.last_explanation:

        st.info(
            f"💡 {st.session_state.last_explanation}"
        )


# ============================================================
# NEXT QUESTION
# ============================================================

if st.session_state.answered:

    if question_index < QUESTIONS_PER_LEVEL - 1:

        if st.button(
            "➡️ Next Question",
            use_container_width=True
        ):

            st.session_state.question_index += 1
            st.session_state.answered = False
            st.session_state.last_correct = False
            st.session_state.last_explanation = ""

            st.rerun()

    else:

        # ====================================================
        # LEVEL RESULT
        # ====================================================

        st.divider()

        final_score = st.session_state.score

        if final_score == 10:

            st.balloons()

            st.success(
                "🏆 LEVEL COMPLETE!"
            )

            st.markdown(
                """
                ### 🎉 Perfect Score — 10/10

                आपने इस level को successfully complete कर लिया!
                """
            )

            next_level = unlock_next_level(
                selected_age
            )

            if next_level:

                st.success(
                    f"🔓 Next Level Unlocked: **{next_level}**"
                )

                st.info(
                    "अब बच्चा अपनी क्षमता के अनुसार "
                    "अगले level का challenge खेल सकता है."
                )

                if st.button(
                    f"🚀 Play {next_level}",
                    use_container_width=True,
                    type="primary"
                ):

                    st.session_state.selected_age = next_level
                    st.session_state.game_started = False
                    st.session_state.questions = []
                    st.session_state.question_index = 0
                    st.session_state.score = 0
                    st.session_state.answered = False

                    st.rerun()

            else:

                st.success(
                    "👑 Congratulations! "
                    "आपने सभी available levels complete कर लिए!"
                )

        else:

            st.warning(
                f"⭐ Final Score: {final_score}/10"
            )

            st.info(
                "🔒 Next level अभी locked है। "
                "अगला level unlock करने के लिए 10/10 पूरा करें।"
            )

            if st.button(
                "🔄 Retry Level",
                use_container_width=True,
                type="primary"
            ):

                st.session_state.game_started = False
                st.session_state.questions = []
                st.session_state.question_index = 0
                st.session_state.score = 0
                st.session_state.answered = False
                st.session_state.last_correct = False

                st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "ClyxessChat AI • Play & Learn • "
    "Learn today, build tomorrow 🚀"
)
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
if "age_group" not in st.session_state:
    st.session_state.age_group = "1-2 Yrs"

# DISPLAY CHAT
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image_url" in message:
            st.image(message["image_url"], caption=message.get("image_caption",""))
        else:
            st.markdown(message["content"])

# CHAT INPUT
if prompt := st.chat_input("Apna idea type karein ya draw karein..." if "Creative" in mode else "Ask ClyxessChat AI"):
    is_school = "Creative" in mode
    current_age = st.session_state.age_group if is_school else "Normal"
    system_prompt = get_school_system_prompt(current_age) if is_school else NORMAL_SYSTEM_PROMPT

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f'<div class="user-bubble">{prompt}</div>', unsafe_allow_html=True)

    # Check if user wants image
    wants_image = any(w in prompt.lower() for w in ["image", "draw", "banao", "photo", "picture", "chitra", "rocket", "diagram"])

    with st.chat_message("assistant"):
        if wants_image:
            with st.spinner("🎨 Image bana raha hu..."):
                img_data, source = generate_image_url(prompt, is_school, current_age)
                if source == "huggingface":
                    st.image(img_data, caption=f"Generated for: {prompt}")
                    st.session_state.messages.append({"role": "assistant", "image_url": img_data, "image_caption": prompt, "content": f"Ye lo aapki image! ({source})"})
                else:
                    st.image(img_data, caption=f"Generated for: {prompt}")
                    st.session_state.messages.append({"role": "assistant", "image_url": img_data, "image_caption": prompt, "content": f"Ye lo aapki image! ({source})"})

        # Text response
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
            time.sleep(0.03)
        message_placeholder.markdown(full_response)
        st.caption(f"Mode: {mode} | Age: {current_age} | Model: {used_model}")

    if not wants_image:
        st.session_state.messages.append({"role": "assistant", "content": response})

    st.rerun()
