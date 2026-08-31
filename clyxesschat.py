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

st.set_page_config(
    page_title="ClyxessChat AI",
    page_icon="💬",
    layout="wide"
)

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>
.main {max-width: 850px; margin: auto;}

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
}

.age-btn-active {
    background: #2ecc71!important;
    color: white!important;
    border: 2px solid white!important;
}

.play-card {
    padding: 24px;
    border-radius: 20px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    margin: 15px 0;
}

.play-hero {
    padding: 24px;
    border-radius: 20px;
    background: linear-gradient(135deg, #0f172a, #172554);
    color: white;
    margin-bottom: 20px;
}

.locked-card {
    padding: 18px;
    border-radius: 18px;
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
}

.small-muted {
    color: #64748b;
    font-size: 13px;
}

.media-card {max-width:560px;margin:12px auto;}
.media-card img {max-width:100% !important;width:auto !important;height:auto !important;max-height:520px !important;object-fit:contain;border-radius:14px;display:block;margin:auto;}
[data-testid="stImage"] img {max-width:560px !important;max-height:520px !important;width:auto !important;height:auto !important;object-fit:contain;margin:auto;display:block;}
.report-card {padding:18px;border-radius:16px;border:1px solid #334155;background:#0f172a;color:white;}

.app-shell-note {padding:10px 14px;border-radius:14px;background:rgba(59,130,246,.08);border:1px solid rgba(59,130,246,.18);font-size:13px;}
div[data-testid="stSidebar"] {border-right:1px solid rgba(148,163,184,.16);}
.stButton>button {border-radius:12px;font-weight:600;transition:all .2s ease;}
.stTextInput input,.stTextArea textarea {border-radius:12px;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONFIG
# ============================================================

GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b"
]

QUESTIONS_PER_LEVEL = 10

# ============================================================
# PLAY & LEARN CONFIG
# ============================================================

PLAY_AGE_LEVELS = [
    "1–2 Years",
    "3–4 Years",
    "5–6 Years",
    "6–8 Years",
    "8–10 Years",
    "10–11 Years",
    "11+ Years"
]

PLAY_LANGUAGES = {
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

AGE_SUBJECTS = {
    "1–2 Years": [
        "Colors", "Shapes", "Animals", "Sounds",
        "Basic Language", "Memory"
    ],
    "3–4 Years": [
        "Numbers", "Language", "Shapes",
        "Storytelling", "Communication", "Logic"
    ],
    "5–6 Years": [
        "Maths", "Science Basics", "Language",
        "Reading", "Logic", "Creativity"
    ],
    "6–8 Years": [
        "Maths", "Science", "English",
        "General Knowledge", "Logic",
        "Communication", "Technology Basics"
    ],
    "8–10 Years": [
        "Maths", "Science", "English",
        "Coding Basics", "AI Introduction",
        "Financial Literacy", "Communication"
    ],
    "10–11 Years": [
        "Advanced Maths", "Science", "Technology",
        "AI Literacy", "Coding",
        "Financial Literacy", "Critical Thinking"
    ],
    "11+ Years": [
        "AI & Technology", "Coding",
        "Financial Literacy", "Cyber Safety",
        "Communication", "Entrepreneurship",
        "Critical Thinking", "Problem Solving"
    ]
}

# ============================================================
# FALLBACK QUESTION BANK
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
            "options": ["You're welcome", "Go away", "No", "Stop"],
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
            "options": ["Yes", "No"],
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
    ],
    "Colors": [
        {
            "question": "Which one is red? 🔴",
            "options": ["🔵", "🟢", "🔴", "🟡"],
            "answer": "🔴",
            "explanation": "The red circle is the red color."
        }
    ],
    "Shapes": [
        {
            "question": "Which shape is a circle? ⭕",
            "options": ["⬜", "🔺", "⭕", "⭐"],
            "answer": "⭕",
            "explanation": "⭕ is a circle."
        }
    ],
    "Animals": [
        {
            "question": "Which one is a cat? 🐱",
            "options": ["🐶", "🐱", "🐰", "🐮"],
            "answer": "🐱",
            "explanation": "🐱 represents a cat."
        }
    ],
    "Sounds": [
        {
            "question": "Which animal says 'Woof'? 🐶",
            "options": ["🐱", "🐶", "🐮", "🐟"],
            "answer": "🐶",
            "explanation": "A dog commonly makes a woof sound."
        }
    ],
    "Basic Language": [
        {
            "question": "What comes after A?",
            "options": ["B", "C", "D", "E"],
            "answer": "B",
            "explanation": "B comes after A in the alphabet."
        }
    ],
    "Memory": [
        {
            "question": "Remember: 🍎 🐱 ⭐. Which item was in the middle?",
            "options": ["🍎", "🐱", "⭐", "🐶"],
            "answer": "🐱",
            "explanation": "🐱 was the middle item."
        }
    ],
    "Numbers": [
        {
            "question": "What comes after 1?",
            "options": ["2", "3", "4", "5"],
            "answer": "2",
            "explanation": "2 comes after 1."
        }
    ],
    "Language": [
        {
            "question": "Which word is a greeting?",
            "options": ["Hello", "Table", "Blue", "Seven"],
            "answer": "Hello",
            "explanation": "Hello is commonly used as a greeting."
        }
    ],
    "Storytelling": [
        {
            "question": "A child finds a lost toy. What is a helpful action?",
            "options": [
                "Try to find the owner",
                "Hide it",
                "Break it",
                "Throw it away"
            ],
            "answer": "Try to find the owner",
            "explanation": "Finding the owner is a helpful and responsible choice."
        }
    ],
    "Reading": [
        {
            "question": "Which word means the opposite of 'big'?",
            "options": ["Small", "Tall", "Fast", "Bright"],
            "answer": "Small",
            "explanation": "Small is the opposite of big."
        }
    ],
    "Creativity": [
        {
            "question": "Which activity can help creativity?",
            "options": [
                "Drawing a new idea",
                "Never trying anything",
                "Copying every answer",
                "Ignoring questions"
            ],
            "answer": "Drawing a new idea",
            "explanation": "Creating and exploring new ideas can build creativity."
        }
    ],
    "English": [
        {
            "question": "Which word is an adjective?",
            "options": ["Beautiful", "Run", "Eat", "Quickly"],
            "answer": "Beautiful",
            "explanation": "Beautiful is an adjective."
        }
    ],
    "General Knowledge": [
        {
            "question": "How many days are in a week?",
            "options": ["5", "7", "8", "10"],
            "answer": "7",
            "explanation": "A week has 7 days."
        }
    ],
    "Advanced Maths": [
        {
            "question": "What is the square root of 64?",
            "options": ["6", "8", "10", "12"],
            "answer": "8",
            "explanation": "8 × 8 = 64."
        }
    ],
    "Technology": [
        {
            "question": "Which device is used to process information?",
            "options": ["Computer", "Chair", "Bottle", "Pencil"],
            "answer": "Computer",
            "explanation": "A computer processes information."
        }
    ],
    "AI & Technology": [
        {
            "question": "Which is a responsible use of AI?",
            "options": [
                "Checking important information",
                "Sharing passwords",
                "Copying without understanding",
                "Sharing private data"
            ],
            "answer": "Checking important information",
            "explanation": "Responsible AI use includes checking important information."
        }
    ]
}

# ============================================================
# UI TRANSLATIONS
# ============================================================

UI = {
    "en": {
        "start": "🚀 Start Game",
        "score": "Score",
        "submit": "Submit Answer",
        "next": "Next Question",
        "correct": "✅ Correct!",
        "wrong": "❌ Not quite!",
        "retry": "🔄 Try Again",
    },
    "hi": {
        "start": "🚀 गेम शुरू करें",
        "score": "स्कोर",
        "submit": "उत्तर जांचें",
        "next": "अगला सवाल",
        "correct": "✅ बिल्कुल सही!",
        "wrong": "❌ कोई बात नहीं, फिर कोशिश करो!",
        "retry": "🔄 फिर से खेलें",
    }
}

# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "messages": [],
    "session_id": str(uuid.uuid4()),
    "age_group": "1-2 Yrs",
    "school_messages": [],
    "school_session_id": str(uuid.uuid4()),
    "school_language": "hi",
    "school_age": "1-2 Yrs",

    # Play & Learn
    "play_age": PLAY_AGE_LEVELS[0],
    "play_language": "hi",
    "play_subject": None,
    "play_questions": [],
    "play_question_index": 0,
    "play_score": 0,
    "play_game_started": False,
    "play_answered": False,
    "play_last_correct": False,
    "play_last_explanation": "",
    "play_unlocked_levels": [PLAY_AGE_LEVELS[0]],
    "play_completed_levels": [],
    "play_best_scores": {}
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ============================================================
# IMAGE FALLBACK FUNCTION
# ============================================================

def build_image_prompt(user_prompt, is_school_mode=False, age="Normal"):
    p = user_prompt.strip()
    p = re.sub(r"^(please\s+)?(make|create|generate|draw|banao|banaiye)\s+(an?\s+)?(image|photo|picture|poster|chitra)\s*(of|for|:)?\s*", "", p, flags=re.I)
    rules = (
        "Create ONLY what the user explicitly requested. Do not add people, girls, boys, faces, animals, vehicles, characters, logos, brands, objects, scenery or unrelated themes unless explicitly requested. "
        "Do not invent a story or add a main character. Keep the requested subject dominant and clean. No watermark."
    )
    if any(x in p.lower() for x in ["diwali", "दीवाली", "दीपावली"]):
        rules += " For a Diwali greeting/poster where no person is requested, use diyas, warm festive lights and tasteful Indian decorative motifs; NO PEOPLE. Try to preserve the exact requested greeting text."
    if is_school_mode:
        rules += f" Keep it safe and age-appropriate for {age}."
    return f"{rules} User request: {p}."

def generate_image_url(prompt, is_school_mode, age, aspect="1:1"):
    final_prompt = build_image_prompt(prompt, is_school_mode, age)
    sizes = {"1:1": (768,768), "16:9": (1024,576), "9:16": (576,1024)}
    width, height = sizes.get(aspect, (768,768))
    try:
        hf_key = st.secrets.get("HF_API_KEY", "")
        if hf_key:
            r = requests.post(
                "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
                headers={"Authorization": f"Bearer {hf_key}"},
                json={"inputs": final_prompt}, timeout=60
            )
            if r.status_code == 200 and r.content:
                return r.content, "huggingface"
    except Exception:
        pass
    url = (
        "https://image.pollinations.ai/prompt/"
        f"{requests.utils.quote(final_prompt)}"
        f"?width={width}&height={height}&nologo=true&seed={uuid.uuid4().int % 100000}"
    )
    return url, "pollinations"

# ============================================================
# PROMPTS
# ============================================================

NORMAL_SYSTEM_PROMPT = """
You are ClyxessChat AI, created by ClyxessChat AI Technology.
CORE RULE: REPLY ONLY IN THE SAME LANGUAGE AS USER.
Your name is ClyxessChat AI. Friendly, intelligent, calm.
If user asks to generate image, say: "Generating image for: [prompt]"
"""

def get_school_system_prompt(age_group):
    base = f"""You are ClyxessChat AI — a friendly, safe, child-focused School Mode learning companion.
The child age group is {age_group}.
STRICT LANGUAGE LOCK: reply ONLY in the selected language supplied in the final instruction.
Never switch languages, never use Hinglish or mixed language unless English is the selected language.
Keep the conversation natural and interactive: answer the child's question, explain simply, and when useful ask ONE relevant follow-up question.
Do not pretend to remember things the child never told you. Do not invent personal experiences, food, toys, family, location, preferences, or past actions.
Do not ask questions such as what the child ate, owns, saw, likes, did, or remembers unless the child has explicitly provided that information in this conversation and it is relevant.
Do not pressure the child to reveal passwords, addresses, phone numbers, private photos, or other sensitive personal information.
For learning topics, encourage understanding instead of simply giving homework answers.
"""
    if "1-2" in age_group:
        return base + "Use extremely short, cheerful, concrete sentences; simple words; colors, shapes, animals, sounds, counting, greetings and very basic concepts. Avoid abstract or complex explanations."
    if "3-4" in age_group:
        return base + "Use short playful explanations, simple stories, counting, shapes, colors, animals, language and basic logic."
    if "5-6" in age_group:
        return base + "Use simple examples, stories, early maths, science basics, reading, logic and creativity."
    if "6-8" in age_group:
        return base + "Use clear school-level explanations, examples, simple reasoning, maths, science, English, technology and general knowledge."
    if "10-11" in age_group:
        return base + "Use practical school-level explanations with step-by-step maths, science, technology, coding logic and problem solving."
    return base + "Use age-appropriate secondary-school explanations with deeper reasoning, AI literacy, coding, technology, financial literacy, cyber safety, entrepreneurship and critical thinking."


# ============================================================
# LIVE INDIA CLOCK
# ============================================================
def get_india_datetime_context():
    try:
        now = datetime.datetime.now(ZoneInfo("Asia/Kolkata")) if ZoneInfo else datetime.datetime.now()
        return now.strftime("Current India date: %A, %d %B %Y. Current India time: %I:%M %p (IST).")
    except Exception:
        return datetime.datetime.now().strftime("Current application date: %A, %d %B %Y. Current application time: %I:%M %p.")

def india_clock_text():
    return get_india_datetime_context()

def transcribe_audio_with_groq(client, audio_bytes):
    if not audio_bytes:
        return ""
    try:
        path = "temp_audio_school.wav"
        with open(path, "wb") as f:
            f.write(audio_bytes)
        with open(path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                prompt="The speaker may use Hindi, Hinglish, English, Marathi, Bengali, Tamil, Telugu, Gujarati, Kannada, Malayalam, Odia, Chinese or Japanese."
            )
        return result.text.strip()
    except Exception:
        return ""

def language_display_name(code):
    names = {
        "hi": "Hindi", "mr": "Marathi", "bn": "Bengali",
        "ta": "Tamil", "te": "Telugu", "gu": "Gujarati",
        "kn": "Kannada", "ml": "Malayalam", "or": "Odia",
        "en": "English", "zh": "Chinese", "ja": "Japanese"
    }
    return names.get(code, "English")

# ============================================================
# TAVILY
# ============================================================

def search_tavily(query):
    search_words = [
        "news", "mausam", "weather", "rate", "price",
        "score", "aaj", "kal", "today", "latest", "breaking"
    ]

    if not any(word in query.lower() for word in search_words):
        return "", ""

    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": st.secrets["TAVILY_API_KEY"],
            "query": query,
            "search_depth": "advanced",
            "max_results": 5,
            "include_answer": True
        }

        response = requests.post(
            url,
            json=payload,
            timeout=15
        )

        data = response.json()

        context = data.get("answer", "")

        sources = "\n".join([
            f"{i+1}. [{r['title']}]({r['url']})"
            for i, r in enumerate(data.get("results", [])[:3])
        ])

        return context, sources

    except Exception:
        return "", ""

# ============================================================
# GROQ CHAT
# ============================================================

def get_groq_response(
    client,
    messages,
    system_prompt,
    search_context=""
):
    final_system = system_prompt

    if search_context:
        final_system += (
            f"\n\nLive Web Info:\n{search_context}"
        )

    recent_messages = messages[-6:]

    messages_to_send = [
        {
            "role": "system",
            "content": final_system
        }
    ] + recent_messages

    for model in GROQ_MODELS:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages_to_send,
                temperature=0.7,
                max_tokens=4000
            )

            return completion, model

        except Exception:
            continue

    return None, None

# ============================================================
# SUPABASE
# ============================================================

@st.cache_resource
def init_supabase():
    try:
        return create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"]
        )
    except Exception:
        return None

supabase = init_supabase()

# ============================================================
# PLAY & LEARN HELPERS
# ============================================================

def get_play_ui(language):
    return UI.get(language, UI["en"])


def get_play_subjects(age):
    return AGE_SUBJECTS.get(age, [])


def play_level_unlocked(age):
    return age in st.session_state.play_unlocked_levels


def unlock_next_play_level(age):
    try:
        current_index = PLAY_AGE_LEVELS.index(age)
    except ValueError:
        return None

    next_index = current_index + 1

    if next_index >= len(PLAY_AGE_LEVELS):
        return None

    next_level = PLAY_AGE_LEVELS[next_index]

    if next_level not in st.session_state.play_unlocked_levels:
        st.session_state.play_unlocked_levels.append(next_level)

    return next_level


def build_demo_questions(subject):
    bank = QUESTION_BANK.get(subject, [])

    if not bank:
        # Fallback to a generic safe question
        bank = [
            {
                "question": "Which option is correct?",
                "options": ["A", "B", "C", "D"],
                "answer": "A",
                "explanation": "This is a demo learning question."
            }
        ]

    result = []

    for item in bank:
        result.append({
            "question": str(item["question"]),
            "options": list(item["options"]),
            "answer": str(item["answer"]),
            "explanation": str(item.get("explanation", ""))
        })

    random.shuffle(result)

    original = list(result)

    while len(result) < QUESTIONS_PER_LEVEL:
        result.append(original[len(result) % len(original)].copy())

    random.shuffle(result)

    return result[:QUESTIONS_PER_LEVEL]


def clean_json_text(text):
    text = text.strip()

    # Remove markdown code fences
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    # Find JSON array if extra text exists
    start = text.find("[")
    end = text.rfind("]")

    if start != -1 and end != -1:
        text = text[start:end + 1]

    return text.strip()


def validate_questions(data, count=10):
    if not isinstance(data, list):
        return []

    valid = []

    for item in data:
        if not isinstance(item, dict):
            continue

        question = item.get("question")
        options = item.get("options")
        answer = item.get("answer")
        explanation = item.get("explanation", "")

        if not question:
            continue

        if not isinstance(options, list):
            continue

        options = [str(x).strip() for x in options if str(x).strip()]

        if len(options) < 2:
            continue

        answer = str(answer).strip()

        if answer not in options:
            # Allow answer as A/B/C/D index
            if answer.upper() in ["A", "B", "C", "D"]:
                idx = ord(answer.upper()) - ord("A")
                if idx < len(options):
                    answer = options[idx]

        if answer not in options:
            continue

        valid.append({
            "question": str(question).strip(),
            "options": options,
            "answer": answer,
            "explanation": str(explanation).strip()
        })

        if len(valid) >= count:
            break

    return valid


def _personal_assumption_question(text):
    q = text.lower()
    patterns = [
        r"what did you (eat|see|do|play|have|watch|buy)",
        r"what (fruit|toy|food) did you",
        r"do you (have|like|own|remember)",
        r"what is your (favorite|toy|food)",
        "तुमने क्या खाया", "तुमने कौन सा फल", "तुम्हारे पास कौन", "तुम्हारा पसंदीदा", "तुमने कल क्या", "तुमने क्या देखा"
    ]
    return any(re.search(x, q, re.I) for x in patterns)

def _age_difficulty_guide(age):
    return {
        "1–2 Years": "Use recognition, colors, shapes, animals, sounds, counting 1-5. No reading-heavy text.",
        "3–4 Years": "Use simple counting, matching, shapes, short words, simple stories and everyday logic. Keep language very simple.",
        "5–6 Years": "Use early arithmetic, basic science, reading, patterns, classification and simple reasoning.",
        "6–8 Years": "Use multiplication basics, science facts, grammar, logic, communication and introductory technology.",
        "8–10 Years": "Use multi-step maths, science reasoning, coding basics, AI concepts, money basics and communication.",
        "10–11 Years": "Use fractions/decimals, scientific reasoning, algorithms, AI literacy, technology, finance and critical thinking.",
        "11+ Years": "Use advanced school-level reasoning, coding, cybersecurity, AI/technology, finance, entrepreneurship, communication and problem solving. Avoid baby-level questions."
    }.get(age, "Use age-appropriate school-level questions.")

def _age_fallback_questions(age, subject, language):
    # Deterministic fallbacks are deliberately different by age so an API outage
    # cannot make every age level receive the same baby-level question set.
    if language == "hi":
        pools = {
            "1–2 Years": [
                {"question":"कौन सा रंग लाल है?","options":["🔴","🔵","🟢","🟡"],"answer":"🔴","explanation":"🔴 लाल रंग है।"},
                {"question":"कौन सा आकार गोल है?","options":["⬜","🔺","⭕","⭐"],"answer":"⭕","explanation":"⭕ गोल आकार है।"},
                {"question":"गाय की आवाज़ कैसी होती है?","options":["म्याऊँ","भौं-भौं","रंभाना","कूकना"],"answer":"रंभाना","explanation":"गाय रंभाती है।"},
                {"question":"1 के बाद कौन सा अंक आता है?","options":["0","1","2","3"],"answer":"2","explanation":"1 के बाद 2 आता है।"}],
                "3–4 Years": [
                {"question":"2 + 1 = ?","options":["2","3","4","5"],"answer":"3","explanation":"2 में 1 जोड़ने पर 3 होता है।"},
                {"question":"कौन सा आकार त्रिकोण है?","options":["⭕","⬜","🔺","⭐"],"answer":"🔺","explanation":"🔺 त्रिकोण है।"},
                {"question":"सेब किसका उदाहरण है?","options":["फल","जानवर","वाहन","खिलौना"],"answer":"फल","explanation":"सेब एक फल है।"},
                {"question":"5, 6, 7, ?","options":["6","7","8","9"],"answer":"8","explanation":"हर बार 1 बढ़ रहा है।"}],
                "5–6 Years": [
                {"question":"7 + 6 = ?","options":["11","12","13","14"],"answer":"13","explanation":"7 + 6 = 13।"},
                {"question":"पौधों को बढ़ने के लिए क्या चाहिए?","options":["पानी","पत्थर","प्लास्टिक","खिलौना"],"answer":"पानी","explanation":"पौधों के लिए पानी आवश्यक है।"},
                {"question":"‘बड़ा’ का विलोम क्या है?","options":["छोटा","लंबा","तेज","ऊँचा"],"answer":"छोटा","explanation":"बड़ा का विलोम छोटा है।"},
                {"question":"2, 4, 6, ?","options":["7","8","9","10"],"answer":"8","explanation":"हर बार 2 बढ़ रहा है।"}],
                "6–8 Years": [
                {"question":"8 × 7 = ?","options":["54","56","58","64"],"answer":"56","explanation":"8 × 7 = 56।"},
                {"question":"पानी किस तापमान पर सामान्यतः जमता है?","options":["0°C","10°C","50°C","100°C"],"answer":"0°C","explanation":"सामान्य दबाव पर पानी 0°C पर जमता है।"},
                {"question":"कंप्यूटर में टाइप करने के लिए किसका उपयोग होता है?","options":["कीबोर्ड","स्पीकर","प्रिंटर","माउस पैड"],"answer":"कीबोर्ड","explanation":"कीबोर्ड से अक्षर और अंक टाइप किए जाते हैं।"},
                {"question":"एक सप्ताह में कितने दिन होते हैं?","options":["5","6","7","8"],"answer":"7","explanation":"एक सप्ताह में 7 दिन होते हैं।"}],
                "8–10 Years": [
                {"question":"यदि किसी वस्तु की कीमत ₹80 है और ₹100 दिए, तो कितना वापस मिलेगा?","options":["₹10","₹20","₹30","₹40"],"answer":"₹20","explanation":"₹100 − ₹80 = ₹20।"},
                {"question":"लूप का उपयोग कोड में किसलिए किया जाता है?","options":["दोहराव के लिए","चित्र बनाने के लिए ही","कंप्यूटर बंद करने के लिए","पासवर्ड रखने के लिए"],"answer":"दोहराव के लिए","explanation":"लूप किसी काम को बार-बार चलाने में मदद करता है।"},
                {"question":"AI का पूरा नाम क्या है?","options":["आर्टिफिशियल इंटेलिजेंस","ऑटो इंटरनेट","एडवांस्ड इनपुट","ऑटोमेटिक आइडिया"],"answer":"आर्टिफिशियल इंटेलिजेंस","explanation":"AI का अर्थ Artificial Intelligence है।"},
                {"question":"3/4 का दशमलव रूप क्या है?","options":["0.25","0.5","0.75","1.25"],"answer":"0.75","explanation":"3 ÷ 4 = 0.75।"}],
                "10–11 Years": [
                {"question":"0.75 को भिन्न में कैसे लिखेंगे?","options":["1/2","2/3","3/4","4/5"],"answer":"3/4","explanation":"0.75 = 75/100 = 3/4।"},
                {"question":"किसी एल्गोरिदम में क्रमबद्ध चरणों का उद्देश्य क्या है?","options":["समस्या को व्यवस्थित ढंग से हल करना","सिर्फ चित्र बनाना","पासवर्ड बदलना","इंटरनेट बंद करना"],"answer":"समस्या को व्यवस्थित ढंग से हल करना","explanation":"एल्गोरिदम समस्या के समाधान के लिए स्पष्ट चरण देता है।"},
                {"question":"मजबूत पासवर्ड में क्या बेहतर है?","options":["केवल नाम","123456","अलग-अलग अक्षर, अंक और प्रतीक","जन्मदिन"],"answer":"अलग-अलग अक्षर, अंक और प्रतीक","explanation":"मिश्रित और अनोखा पासवर्ड अधिक सुरक्षित होता है।"},
                {"question":"₹500 पर 10% छूट कितनी है?","options":["₹5","₹25","₹50","₹100"],"answer":"₹50","explanation":"500 का 10% = ₹50।"}],
                "11+ Years": [
                {"question":"यदि किसी निवेश पर 8% वार्षिक दर से ₹10,000 लगाए जाएँ, तो एक वर्ष का साधारण ब्याज कितना होगा?","options":["₹80","₹400","₹800","₹1,800"],"answer":"₹800","explanation":"10,000 × 8/100 = ₹800।"},
                {"question":"फ़िशिंग से बचने का सबसे अच्छा कदम क्या है?","options":["हर लिंक खोलना","OTP साझा करना","संदिग्ध लिंक और प्रेषक की जाँच करना","पासवर्ड चैट में भेजना"],"answer":"संदिग्ध लिंक और प्रेषक की जाँच करना","explanation":"संदिग्ध संदेशों में लिंक और प्रेषक की पुष्टि करनी चाहिए।"},
                {"question":"यदि O(n) एल्गोरिदम इनपुट को दोगुना करने पर लगभग दोगुना काम करता है, तो यह किस प्रकार की जटिलता है?","options":["रैखिक","स्थिर","घातीय","लघुगणकीय"],"answer":"रैखिक","explanation":"O(n) को रैखिक समय जटिलता कहते हैं।"},
                {"question":"किसी तर्क में निष्कर्ष निकालने से पहले क्या करना सबसे उचित है?","options":["साक्ष्य जाँचना","पहला अनुमान मान लेना","अफवाह फैलाना","डेटा छोड़ देना"],"answer":"साक्ष्य जाँचना","explanation":"अच्छी critical thinking में प्रमाण और तर्क की जाँच की जाती है।"}]
        }
        pool = pools.get(age, pools["8–10 Years"])
    elif language == "en":
        pools = {
            "1–2 Years": [("Which color is red?",["🔴","🔵","🟢","🟡"],"🔴","🔴 is red."),("Which shape is round?",["⬜","🔺","⭕","⭐"],"⭕","⭕ is round."),("Which animal says moo?",["Cat","Cow","Dog","Bird"],"Cow","A cow says moo."),("What comes after 1?",["0","1","2","3"],"2","2 comes after 1.")],
            "3–4 Years": [("2 + 1 = ?",["2","3","4","5"],"3","2 + 1 = 3."),("Which is a triangle?",["⭕","⬜","🔺","⭐"],"🔺","🔺 is a triangle."),("Which is a fruit?",["Apple","Chair","Car","Ball"],"Apple","An apple is a fruit."),("5, 6, 7, ?",["6","7","8","9"],"8","The pattern increases by 1.")],
            "5–6 Years": [("7 + 6 = ?",["11","12","13","14"],"13","7 + 6 = 13."),("What helps a plant grow?",["Water","Plastic","Stone","Toy"],"Water","Plants need water."),("Opposite of big?",["Small","Fast","Tall","Bright"],"Small","Small is the opposite of big."),("2, 4, 6, ?",["7","8","9","10"],"8","The pattern increases by 2.")],
            "6–8 Years": [("8 × 7 = ?",["54","56","58","64"],"56","8 × 7 = 56."),("At what temperature does water normally freeze?",["0°C","10°C","50°C","100°C"],"0°C","Water normally freezes at 0°C."),("Which device is used for typing?",["Keyboard","Speaker","Printer","Mouse pad"],"Keyboard","A keyboard is used for typing."),("How many days are in a week?",["5","6","7","8"],"7","A week has 7 days.")],
            "8–10 Years": [("₹100 − ₹80 = ?",["₹10","₹20","₹30","₹40"],"₹20","₹100 − ₹80 = ₹20."),("What is a loop used for in programming?",["Repetition","Only drawing","Shutting down","Storing passwords"],"Repetition","Loops repeat instructions."),("What does AI stand for?",["Artificial Intelligence","Automatic Internet","Advanced Input","Automatic Idea"],"Artificial Intelligence","AI means Artificial Intelligence."),("What is 3/4 as a decimal?",["0.25","0.5","0.75","1.25"],"0.75","3 ÷ 4 = 0.75.")],
            "10–11 Years": [("What is 0.75 as a fraction?",["1/2","2/3","3/4","4/5"],"3/4","0.75 = 3/4."),("What is the purpose of an algorithm?",["Solve a problem in steps","Only draw pictures","Change passwords","Turn off internet"],"Solve a problem in steps","An algorithm gives ordered steps."),("Which is a stronger password?",["Your name","123456","Mixed letters, numbers and symbols","Birthday"],"Mixed letters, numbers and symbols","A unique mixed password is safer."),("10% of ₹500 is?",["₹5","₹25","₹50","₹100"],"₹50","10% of ₹500 is ₹50.")],
            "11+ Years": [("8% simple interest on ₹10,000 for one year is?",["₹80","₹400","₹800","₹1,800"],"₹800","10,000 × 8/100 = ₹800."),("Best defense against phishing?",["Open every link","Share OTP","Verify sender and suspicious links","Send passwords in chat"],"Verify sender and suspicious links","Verification reduces phishing risk."),("What does O(n) describe?",["Linear time","Constant time","Exponential time","Logarithmic time"],"Linear time","O(n) is linear complexity."),("What should you do before accepting a conclusion?",["Check evidence","Assume the first guess","Spread rumors","Ignore data"],"Check evidence","Critical thinking checks evidence.")]
        }
        raw = pools.get(age, pools["8–10 Years"])
        pool = [{"question":q,"options":o,"answer":a,"explanation":e} for q,o,a,e in raw]
    else:
        # If the API is unavailable, keep the fallback language-neutral instead of
        # falsely mixing English into the selected language.
        pool = [
            {"question":"2 + 3 = ?","options":["4","5","6","7"],"answer":"5","explanation":"2 + 3 = 5"},
            {"question":"1, 2, 3, ?","options":["2","3","4","5"],"answer":"4","explanation":"1, 2, 3, 4"},
            {"question":"Which symbol is a circle?","options":["⬜","🔺","⭕","⭐"],"answer":"⭕","explanation":"⭕ is a circle."},
            {"question":"3 × 2 = ?","options":["4","5","6","8"],"answer":"6","explanation":"3 × 2 = 6"}
        ]
    return (pool * ((count + len(pool) - 1) // len(pool)))[:count]

def _subject_fallback_questions(age, subject, language, count=10):
    """Offline fallback: questions vary by BOTH age and subject."""
    sets = {
        "11+ Years": {
            "AI & Technology": [
                ("Which AI practice is most responsible?", ["Verify important outputs", "Share passwords", "Copy blindly", "Ignore sources"], "Verify important outputs", "Important AI outputs should be checked."),
                ("What is a training dataset used for?", ["Teaching a model patterns", "Charging a phone", "Printing documents", "Cooling a computer"], "Teaching a model patterns", "Training data helps a model learn patterns."),
                ("Why can an AI model be biased?", ["Training data can contain bias", "Computers dislike math", "Screens are always biased", "Wi-Fi creates opinions"], "Training data can contain bias", "Model behavior can reflect patterns in its data."),
                ("What does an API commonly provide?", ["A way for software to communicate", "A battery", "A monitor", "A keyboard"], "A way for software to communicate", "APIs let software systems communicate."),
            ],
            "Coding": [
                ("What does a loop help a program do?", ["Repeat instructions", "Delete electricity", "Create a password automatically", "Turn a monitor into a printer"], "Repeat instructions", "Loops repeat instructions while a condition or count allows."),
                ("What is a function?", ["A reusable block of code", "A computer cable", "A database password", "A screen setting"], "A reusable block of code", "Functions package reusable behavior."),
                ("What does O(n) describe?", ["Linear growth", "No growth", "Only exponential growth", "Random growth"], "Linear growth", "O(n) represents linear time growth."),
                ("Which structure follows first-in, first-out?", ["Queue", "Stack", "Tree", "Graph"], "Queue", "A queue is FIFO: first in, first out."),
            ],
            "Financial Literacy": [
                ("If ₹10,000 earns 8% simple interest for one year, interest is?", ["₹80", "₹400", "₹800", "₹1,800"], "₹800", "10,000 × 8/100 = ₹800."),
                ("What is diversification?", ["Spreading investments across different assets", "Spending everything", "Borrowing from every source", "Keeping one password"], "Spreading investments across different assets", "Diversification can reduce concentration risk."),
                ("What is an emergency fund for?", ["Unexpected essential expenses", "Daily impulse purchases", "Buying game skins", "Avoiding all saving"], "Unexpected essential expenses", "Emergency funds are designed for unexpected needs."),
                ("If income is ₹30,000 and expenses are ₹24,000, savings are?", ["₹4,000", "₹5,000", "₹6,000", "₹8,000"], "₹6,000", "₹30,000 − ₹24,000 = ₹6,000."),
            ],
            "Cyber Safety": [
                ("What is phishing?", ["A deceptive attempt to steal information", "A type of backup", "A safe password manager", "A computer update"], "A deceptive attempt to steal information", "Phishing uses deception to obtain sensitive information."),
                ("What should you do with an unexpected OTP request?", ["Do not share it and verify the request", "Share it immediately", "Post it online", "Send it to a stranger"], "Do not share it and verify the request", "OTPs should remain private."),
                ("Which password is strongest?", ["A long unique passphrase", "12345678", "Your birthday", "Your first name"], "A long unique passphrase", "Long, unique passwords are harder to guess."),
                ("Why should software be updated?", ["Updates can fix security vulnerabilities", "Updates always delete files", "Updates remove the internet", "Updates make passwords public"], "Updates can fix security vulnerabilities", "Security updates often address known vulnerabilities."),
            ],
            "Communication": [
                ("What makes feedback constructive?", ["Specific and respectful suggestions", "Personal insults", "Vague blame", "Public humiliation"], "Specific and respectful suggestions", "Constructive feedback focuses on improvement respectfully."),
                ("What is active listening?", ["Paying attention and checking understanding", "Interrupting constantly", "Ignoring the speaker", "Planning your reply only"], "Paying attention and checking understanding", "Active listening includes attention and clarification."),
                ("Which is best in a disagreement?", ["Explain evidence and listen to the other view", "Shout louder", "Insult the other person", "End the discussion immediately"], "Explain evidence and listen to the other view", "Good communication combines reasoning and listening."),
                ("A clear presentation should usually have?", ["A logical structure", "Random points", "Only decorations", "No conclusion"], "A logical structure", "Structure helps an audience follow the message."),
            ],
            "Entrepreneurship": [
                ("What should a new product solve?", ["A real customer problem", "A problem nobody has", "Only the founder's guess", "No problem at all"], "A real customer problem", "Useful products address real needs."),
                ("What is an MVP?", ["A small testable version of a product", "A final global company", "A marketing slogan", "A bank account"], "A small testable version of a product", "An MVP tests a core idea with limited scope."),
                ("Why interview potential users?", ["To learn their needs and problems", "To force them to buy", "To collect passwords", "To avoid testing"], "To learn their needs and problems", "User research helps validate assumptions."),
                ("What is revenue?", ["Money earned from selling goods or services", "Only borrowed money", "A password", "A software bug"], "Money earned from selling goods or services", "Revenue is income generated by sales or services."),
            ],
            "Critical Thinking": [
                ("What should you check before accepting a claim?", ["Evidence and source quality", "Only the headline", "How many emojis it has", "Whether it is exciting"], "Evidence and source quality", "Critical thinking evaluates evidence and sources."),
                ("What is confirmation bias?", ["Favoring information that supports existing beliefs", "Checking several sources", "Changing an opinion from evidence", "Using a calculator"], "Favoring information that supports existing beliefs", "Confirmation bias can distort evaluation of evidence."),
                ("A strong conclusion should be based on?", ["Relevant evidence and reasoning", "Rumors", "Guesswork only", "Popularity"], "Relevant evidence and reasoning", "Sound conclusions require evidence and logic."),
                ("If two sources disagree, what is useful?", ["Compare their evidence and reliability", "Choose the louder source", "Share both as facts", "Ignore both automatically"], "Compare their evidence and reliability", "Source quality and evidence should be compared."),
            ],
            "Problem Solving": [
                ("What is a useful first step in solving a complex problem?", ["Define the problem clearly", "Guess randomly", "Ignore constraints", "Start coding without a goal"], "Define the problem clearly", "A clear problem definition guides the solution."),
                ("Why break a problem into smaller parts?", ["It makes the problem easier to manage", "It guarantees no mistakes", "It removes all testing", "It makes data disappear"], "It makes the problem easier to manage", "Decomposition reduces complexity."),
                ("What is debugging?", ["Finding and fixing program errors", "Designing a logo", "Buying hardware", "Writing a budget"], "Finding and fixing program errors", "Debugging identifies and fixes defects."),
                ("After trying a solution, what should you do?", ["Evaluate the result", "Never test it", "Delete the requirements", "Assume it worked"], "Evaluate the result", "Testing and evaluation reveal whether the solution works."),
            ]
        },
        "8–10 Years": {
            "Coding Basics": [("What is a loop useful for?", ["Repeating instructions", "Charging a laptop", "Printing money", "Deleting the keyboard"], "Repeating instructions", "Loops repeat instructions."), ("What is a variable?", ["A named place for a value", "A type of monitor", "A speaker", "A cable"], "A named place for a value", "Variables store values used by programs."), ("What is an algorithm?", ["Step-by-step instructions", "A drawing", "A battery", "A password"], "Step-by-step instructions", "Algorithms describe steps to solve a task."), ("What is a bug?", ["An error in a program", "A keyboard key", "A web browser", "A folder"], "An error in a program", "A bug is an error or unexpected behavior." )],
            "AI Introduction": [("AI is mainly about computers doing what?", ["Tasks that can involve learning or reasoning", "Only printing", "Only charging", "Only drawing"], "Tasks that can involve learning or reasoning", "AI systems can perform tasks associated with human intelligence."), ("Why should AI answers be checked?", ["AI can make mistakes", "AI is always wrong", "AI cannot read", "Checking is illegal"], "AI can make mistakes", "AI outputs are not automatically correct."), ("Which is an AI example?", ["A voice assistant", "A wooden chair", "A paper clip", "A water bottle"], "A voice assistant", "Voice assistants can use AI technologies."), ("What is a prompt?", ["An instruction given to an AI system", "A battery", "A mouse", "A printer"], "An instruction given to an AI system", "A prompt tells an AI system what to do." )],
            "Financial Literacy": [("₹100 − ₹35 = ?", ["₹55", "₹65", "₹75", "₹85"], "₹65", "₹100 − ₹35 = ₹65."), ("Why save money?", ["For future needs and goals", "To lose track of money", "To spend more immediately", "To hide all money"], "For future needs and goals", "Saving supports future needs and goals."), ("What is a budget?", ["A plan for income and spending", "A password", "A game", "A receipt only"], "A plan for income and spending", "A budget plans how money will be used."), ("If you save ₹20 each week for 4 weeks, how much?", ["₹40", "₹60", "₹80", "₹100"], "₹80", "20 × 4 = 80." )],
            "Communication": [("What is a respectful disagreement?", ["Explain your view and listen", "Insult someone", "Shout", "Ignore facts"], "Explain your view and listen", "Respectful communication allows different views."), ("What helps a presentation?", ["Clear organization", "Random ideas", "No preparation", "Only jokes"], "Clear organization", "Organization makes ideas easier to follow."), ("What is active listening?", ["Paying attention to understand", "Interrupting", "Ignoring", "Changing the topic"], "Paying attention to understand", "Active listening focuses on understanding."), ("A clear question should be?", ["Specific", "Unrelated", "Impossible to understand", "Only one word always"], "Specific", "Specific questions are easier to answer well." )]
        },
        "6–8 Years": {
            "Maths": [("8 × 7 = ?", ["54", "56", "58", "64"], "56", "8 × 7 = 56."), ("45 ÷ 5 = ?", ["7", "8", "9", "10"], "9", "45 ÷ 5 = 9."), ("What is 3 × 9?", ["18", "21", "27", "30"], "27", "3 × 9 = 27."), ("Which is greater?", ["0.8", "0.5", "0.3", "0.2"], "0.8", "0.8 is the greatest." )],
            "Science": [("What do plants use to make food?", ["Sunlight", "Plastic", "Sand only", "Metal"], "Sunlight", "Plants use sunlight in photosynthesis."), ("Which state of matter has a fixed shape?", ["Solid", "Liquid", "Gas", "None"], "Solid", "Solids have a fixed shape."), ("What force pulls objects toward Earth?", ["Gravity", "Sound", "Light", "Heat"], "Gravity", "Gravity attracts objects toward Earth."), ("Which organ helps us breathe?", ["Lungs", "Stomach", "Skin", "Bone"], "Lungs", "The lungs are used for breathing." )],
            "Technology Basics": [("Which device is used for typing?", ["Keyboard", "Speaker", "Printer", "Lamp"], "Keyboard", "A keyboard is used for typing."), ("What is a browser used for?", ["Opening websites", "Cooking food", "Charging a battery", "Printing money"], "Opening websites", "A browser accesses websites."), ("Which is an input device?", ["Mouse", "Monitor", "Speaker", "Projector"], "Mouse", "A mouse sends input to a computer."), ("What does Wi-Fi help devices do?", ["Connect wirelessly to a network", "Create electricity", "Print without hardware", "Replace the screen"], "Connect wirelessly to a network", "Wi-Fi provides wireless network connectivity." )]
        },
        "5–6 Years": {
            "Maths": [("7 + 6 = ?", ["11", "12", "13", "14"], "13", "7 + 6 = 13."), ("10 − 4 = ?", ["4", "5", "6", "7"], "6", "10 − 4 = 6."), ("Which number is bigger?", ["8", "5", "3", "2"], "8", "8 is the biggest."), ("2, 4, 6, ?", ["7", "8", "9", "10"], "8", "The pattern increases by 2." )],
            "Science Basics": [("What helps a plant grow?", ["Water", "Plastic", "Toy", "Stone"], "Water", "Plants need water to grow."), ("Which is a living thing?", ["Dog", "Chair", "Cup", "Ball"], "Dog", "A dog is living."), ("Where does rain come from?", ["Clouds", "Rocks", "Shoes", "Books"], "Clouds", "Rain falls from clouds."), ("Which body part helps you see?", ["Eyes", "Ears", "Hands", "Feet"], "Eyes", "Eyes help us see." )]
        },
        "3–4 Years": {
            "Numbers": [("2 + 1 = ?", ["2", "3", "4", "5"], "3", "2 plus 1 is 3."), ("What comes after 4?", ["3", "4", "5", "6"], "5", "5 comes after 4."), ("How many stars? ⭐⭐⭐", ["2", "3", "4", "5"], "3", "There are 3 stars."), ("Which is the smaller number?", ["1", "5", "7", "9"], "1", "1 is the smallest." )],
            "Shapes": [("Which shape is a triangle?", ["⭕", "⬜", "🔺", "⭐"], "🔺", "🔺 is a triangle."), ("Which shape is round?", ["⬜", "⭕", "🔺", "▭"], "⭕", "⭕ is round."), ("Which shape has four equal sides?", ["⭕", "⬜", "🔺", "⭐"], "⬜", "A square has four equal sides."), ("Which is a star?", ["⭐", "⭕", "⬜", "🔺"], "⭐", "⭐ is a star." )]
        },
        "1–2 Years": {
            "Colors": [("Which color is red?", ["🔴", "🔵", "🟢", "🟡"], "🔴", "🔴 is red."), ("Which color is blue?", ["🟡", "🔵", "🔴", "🟢"], "🔵", "🔵 is blue."), ("Which color is green?", ["🔴", "🟢", "🔵", "🟡"], "🟢", "🟢 is green."), ("Which color is yellow?", ["🔵", "🟡", "🔴", "🟢"], "🟡", "🟡 is yellow." )],
            "Shapes": [("Which shape is a circle?", ["⭕", "⬜", "🔺", "⭐"], "⭕", "⭕ is a circle."), ("Which shape is a square?", ["⭕", "⬜", "🔺", "⭐"], "⬜", "⬜ is a square."), ("Which shape is a triangle?", ["⭐", "⭕", "🔺", "⬜"], "🔺", "🔺 is a triangle."), ("Which shape is a star?", ["⬜", "⭐", "⭕", "🔺"], "⭐", "⭐ is a star." )]
        }
    }
    age_set = sets.get(age, {})
    pool = age_set.get(subject)
    if not pool:
        # Use a subject-specific bank first; never reuse one generic baby question for all ages.
        bank = QUESTION_BANK.get(subject, [])
        pool = [(x["question"], x["options"], x["answer"], x.get("explanation", "")) for x in bank]
    if not pool:
        pool = [("Choose the correct option.", ["A", "B", "C", "D"], "A", "Select the correct answer.")]
    result = [{"question":q,"options":list(o),"answer":a,"explanation":e} for q,o,a,e in pool]
    random.shuffle(result)
    return (result * ((count + len(result) - 1) // len(result)))[:count]

def generate_ai_questions(client, age, language, subject, count=10):
    language_name = language_display_name(language)
    guide = _age_difficulty_guide(age)
    prompt = f"""
Create exactly {count} educational multiple-choice questions.
AGE GROUP: {age}
SUBJECT: {subject}
AGE DIFFICULTY RULE: {guide}
SELECTED LANGUAGE: {language_name}
STRICT LANGUAGE LOCK: question, all four options, answer and explanation MUST be entirely in {language_name}. Never switch to English or Hinglish unless English is selected.
Do not reuse baby-level questions for older learners. The subject MUST match the selected subject.
For ages 1–4, never ask personal-experience questions such as what the child ate, owns, likes, saw, did or remembers.
For 8+ use age-appropriate school concepts; for 11+ use advanced reasoning and avoid preschool questions.
Every question must be objective, safe, have exactly four options, and exactly one correct answer.
Return ONLY valid JSON: [{{"question":"...","options":["A","B","C","D"],"answer":"A","explanation":"..."}}]
"""
    for model in GROQ_MODELS:
        try:
            completion = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}], temperature=0.35, max_tokens=5000)
            parsed = json.loads(clean_json_text(completion.choices[0].message.content))
            valid=[]
            seen=set()
            for item in parsed if isinstance(parsed,list) else []:
                if not isinstance(item,dict): continue
                q=str(item.get("question","")).strip(); opts=[str(x).strip() for x in item.get("options",[]) if str(x).strip()]
                ans=str(item.get("answer","")).strip(); exp=str(item.get("explanation","")).strip()
                key=q.casefold()
                if not q or key in seen or len(opts)!=4 or len(set(opts))!=4 or ans not in opts: continue
                if ("1–2" in age or "3–4" in age) and _personal_assumption_question(q): continue
                seen.add(key)
                valid.append({"question":q,"options":opts,"answer":ans,"explanation":exp})
                if len(valid)==count: return valid
        except Exception:
            continue
    return _subject_fallback_questions(age, subject, language, count)


# ============================================================
# PLAY & LEARN UI
# ============================================================

def render_play_and_learn(client):

    st.markdown(
        """
        <div class="play-hero">
            <h1>🎮 ClyxessChat AI — Play & Learn</h1>
            <p>
            Learn through AI-generated questions, games and age-based challenges.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Settings
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        play_age = st.selectbox(
            "👶 Select Age",
            PLAY_AGE_LEVELS,
            index=PLAY_AGE_LEVELS.index(
                st.session_state.play_age
            )
        )

    with col2:
        language_label = st.selectbox(
            "🌐 Select Language",
            list(PLAY_LANGUAGES.keys()),
            index=list(PLAY_LANGUAGES.values()).index(
                st.session_state.play_language
            )
        )

        play_language = PLAY_LANGUAGES[language_label]

    with col3:
        subjects = get_play_subjects(play_age)

        previous_subject = st.session_state.play_subject

        subject_index = (
            subjects.index(previous_subject)
            if previous_subject in subjects
            else 0
        )

        play_subject = st.selectbox(
            "📚 Select Subject",
            subjects,
            index=subject_index
        )

    previous_config = st.session_state.get("play_config_signature")
    new_config = (play_age, play_language, play_subject)
    if previous_config is not None and previous_config != new_config:
        st.session_state.play_questions = []
        st.session_state.play_question_index = 0
        st.session_state.play_score = 0
        st.session_state.play_answered = False
        st.session_state.play_last_correct = False
        st.session_state.play_last_explanation = ""
        st.session_state.play_game_started = False
    st.session_state.play_config_signature = new_config
    st.session_state.play_age = play_age
    st.session_state.play_language = play_language
    st.session_state.play_subject = play_subject

    # --------------------------------------------------------
    # Locked Level
    # --------------------------------------------------------

    if not play_level_unlocked(play_age):

        st.error(
            f"🔒 {play_age} is locked."
        )

        st.info(
            "Complete the previous age level with 10/10 "
            "to unlock this level."
        )

        return

    # --------------------------------------------------------
    # Sidebar
    # --------------------------------------------------------

    with st.sidebar:
        st.markdown("### 🎮 Play & Learn Progress")

        st.write(f"👶 **Age:** {play_age}")
        st.write(f"🌐 **Language:** {language_label}")
        st.write(f"📚 **Subject:** {play_subject}")

        st.divider()

        st.markdown("### 🔓 Age Levels")

        for level in PLAY_AGE_LEVELS:

            if level in st.session_state.play_unlocked_levels:

                if level == play_age:
                    st.success(f"⭐ {level}")
                else:
                    st.write(f"✅ {level}")

            else:
                st.write(f"🔒 {level}")

    # --------------------------------------------------------
    # Start Screen
    # --------------------------------------------------------

    if not st.session_state.play_game_started:

        st.markdown(
            '<div class="play-card">',
            unsafe_allow_html=True
        )

        st.subheader("🎯 Ready to Learn?")

        st.write(f"**Age:** {play_age}")
        st.write(f"**Subject:** {play_subject}")
        st.write(f"**Language:** {language_label}")

        st.info(
            "🎮 इस level में 10 AI-generated questions होंगे। "
            "10/10 करने पर अगला age level unlock होगा."
        )

        if st.button(
            "🚀 Start Game",
            use_container_width=True,
            type="primary"
        ):

            with st.spinner(
                "🤖 AI आपके लिए learning challenge बना रहा है..."
            ):

                questions = generate_ai_questions(
                    client=client,
                    age=play_age,
                    language=play_language,
                    subject=play_subject,
                    count=QUESTIONS_PER_LEVEL
                )

            if not questions:
                st.error(
                    "Questions generate नहीं हो पाए। Please try again."
                )
                return

            st.session_state.play_questions = questions
            st.session_state.play_question_index = 0
            st.session_state.play_score = 0
            st.session_state.play_answered = False
            st.session_state.play_last_correct = False
            st.session_state.play_last_explanation = ""
            st.session_state.play_game_started = True

            st.rerun()

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

        return

    # --------------------------------------------------------
    # Question Data
    # --------------------------------------------------------

    questions = st.session_state.play_questions

    if not questions:
        st.error("No questions available.")
        return

    question_index = st.session_state.play_question_index

    if question_index >= len(questions):
        question_index = 0
        st.session_state.play_question_index = 0

    current = questions[question_index]

    question_text = current["question"]
    options = current["options"]
    correct_answer = current["answer"]
    explanation = current.get("explanation", "")

    # --------------------------------------------------------
    # Progress
    # --------------------------------------------------------

    progress = question_index / QUESTIONS_PER_LEVEL

    st.progress(
        progress,
        text=(
            f"Question {question_index + 1}/"
            f"{QUESTIONS_PER_LEVEL}"
        )
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "🎯 Question",
            f"{question_index + 1}/10"
        )

    with c2:
        st.metric(
            "⭐ Score",
            f"{st.session_state.play_score}/10"
        )

    with c3:
        st.metric(
            "📚 Subject",
            play_subject
        )

    # --------------------------------------------------------
    # Question Card
    # --------------------------------------------------------

    st.markdown(
        '<div class="play-card">',
        unsafe_allow_html=True
    )

    st.subheader(f"❓ {question_text}")

    answer = st.radio(
        "Choose your answer:",
        options,
        key=(
            f"play_answer_{play_age}_"
            f"{play_subject}_{question_index}"
        )
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Submit
    # --------------------------------------------------------

    if not st.session_state.play_answered:

        if st.button(
            "✅ Submit Answer",
            use_container_width=True,
            type="primary"
        ):

            if answer == correct_answer:
                st.session_state.play_score += 1
                st.session_state.play_last_correct = True
            else:
                st.session_state.play_last_correct = False

            st.session_state.play_last_explanation = explanation
            st.session_state.play_answered = True

            st.rerun()

    # --------------------------------------------------------
    # Feedback
    # --------------------------------------------------------

    if st.session_state.play_answered:

        if st.session_state.play_last_correct:
            st.success(
                f"✅ Correct! ⭐ "
                f"Score: {st.session_state.play_score}/10"
            )
        else:
            st.warning(
                "❌ Not quite! "
                f"Correct answer: **{correct_answer}**"
            )

   
