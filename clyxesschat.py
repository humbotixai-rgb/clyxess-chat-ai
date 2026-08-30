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
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONFIG
# ============================================================

# ============ 8 MODEL MEGA COMBINED - 100% ACTIVE ============
GROQ_MODELS = [
    # --- Tera wala 3 - 100% sahi ---
    "openai/gpt-oss-120b",      # sabse powerful
    "openai/gpt-oss-20b",       # sabse fast
    "qwen/qwen3.6-27b",         # Qwen ka latest

    # --- Extra 5 jo 100% chalu hai ---
    "meta-llama/llama-4-scout-17b-16e-instruct",    # Meta ka new small
    "meta-llama/llama-4-maverick-17b-128e-instruct", # Meta ka new big
    "groq/compound",            # search + code wala
    "groq/compound-mini",       # uska mini version
    "moonshotai/kimi-k2-instruct" # long reasoning
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
    "school_language": "hi",

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
    return next((name.split(" ", 1)[-1] for name, value in PLAY_LANGUAGES.items() if value == code), "English")

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

def generate_ai_questions(client, age, language, subject, count=10):
    language_name = next((name for name, code in PLAY_LANGUAGES.items() if code == language), "English")
    prompt = f"""
Create exactly {count} educational multiple-choice questions for age group {age}.
Subject: {subject}
Selected language: {language_name}
STRICT LANGUAGE LOCK: question, all four options, answer and explanation MUST be entirely in {language_name}.
Never switch to English. Never use Hinglish or mixed language unless English is selected.
For ages 1–4, NEVER ask personal-experience questions such as what the child ate, owns, likes, saw, did or remembers.
Every question must be objective, age-appropriate, safe, and have exactly four options with exactly one correct answer.
Return ONLY valid JSON with this format:
[{{"question":"...","options":["A","B","C","D"],"answer":"A","explanation":"..."}}]
"""
    for model in GROQ_MODELS:
        try:
            completion = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}], temperature=0.35, max_tokens=5000)
            parsed = json.loads(clean_json_text(completion.choices[0].message.content))
            valid=[]
            for item in parsed if isinstance(parsed,list) else []:
                if not isinstance(item,dict): continue
                q=str(item.get("question","")).strip(); opts=[str(x).strip() for x in item.get("options",[]) if str(x).strip()]
                ans=str(item.get("answer","")).strip(); exp=str(item.get("explanation","")).strip()
                if not q or len(opts)!=4 or ans not in opts: continue
                if ("1–2" in age or "3–4" in age) and _personal_assumption_question(q): continue
                valid.append({"question":q,"options":opts,"answer":ans,"explanation":exp})
                if len(valid)==count: break
            if len(valid)==count:
                return valid
        except Exception:
            continue
    # Strict fallback. For non-English languages use language-neutral objective questions rather than mixed English.
    if language == "hi":
        pool = [
            {"question":"1 + 1 = ?","options":["1","2","3","4"],"answer":"2","explanation":"1 + 1 = 2।"},
            {"question":"2, 4, 6, ?","options":["7","8","9","10"],"answer":"8","explanation":"हर बार 2 बढ़ रहा है।"},
            {"question":"कौन सा आकार वृत्त है?","options":["⬜","🔺","⭕","⭐"],"answer":"⭕","explanation":"⭕ वृत्त है।"},
            {"question":"कौन सा रंग लाल है?","options":["🔴","🔵","🟢","🟡"],"answer":"🔴","explanation":"🔴 लाल रंग है।"}
        ]
    elif language == "en":
        pool = build_demo_questions(subject)
    else:
        pool = [
            {"question":"2 + 3 = ?","options":["4","5","6","7"],"answer":"5","explanation":"2 + 3 = 5"},
            {"question":"1, 2, 3, ?","options":["2","3","4","5"],"answer":"4","explanation":"1, 2, 3, 4"},
            {"question":"⭕ ?","options":["⬜","🔺","⭕","⭐"],"answer":"⭕","explanation":"⭕"},
            {"question":"🔴 + 🔴 = ?","options":["2","3","4","5"],"answer":"2","explanation":"2"}
        ]
    return (pool * ((count // max(1,len(pool)))+1))[:count]


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

        if st.session_state.play_last_explanation:
            st.info(
                f"💡 {st.session_state.play_last_explanation}"
            )

    # --------------------------------------------------------
    # Next Question / Result
    # --------------------------------------------------------

    if st.session_state.play_answered:

        if question_index < QUESTIONS_PER_LEVEL - 1:

            if st.button(
                "➡️ Next Question",
                use_container_width=True
            ):

                st.session_state.play_question_index += 1
                st.session_state.play_answered = False
                st.session_state.play_last_correct = False
                st.session_state.play_last_explanation = ""

                st.rerun()

        else:

            st.divider()

            final_score = st.session_state.play_score

            if final_score == 10:

                st.balloons()

                st.success(
                    "🏆 LEVEL COMPLETE — 10/10!"
                )

                st.session_state.play_completed_levels.append(
                    play_age
                )

                st.session_state.play_best_scores[
                    f"{play_age}:{play_subject}"
                ] = max(
                    final_score,
                    st.session_state.play_best_scores.get(
                        f"{play_age}:{play_subject}",
                        0
                    )
                )

                next_level = unlock_next_play_level(play_age)

                if next_level:

                    st.success(
                        f"🔓 Next Level Unlocked: **{next_level}**"
                    )

                    if st.button(
                        f"🚀 Play {next_level}",
                        use_container_width=True,
                        type="primary"
                    ):

                        st.session_state.play_age = next_level
                        st.session_state.play_game_started = False
                        st.session_state.play_questions = []
                        st.session_state.play_question_index = 0
                        st.session_state.play_score = 0
                        st.session_state.play_answered = False
                        st.session_state.play_last_correct = False
                        st.session_state.play_last_explanation = ""

                        st.rerun()

                else:

                    st.success(
                        "👑 Congratulations! "
                        "All available age levels are complete."
                    )

            else:

                st.warning(
                    f"⭐ Final Score: {final_score}/10"
                )

                st.info(
                    "🔒 अगला level unlock करने के लिए इस level में "
                    "10/10 करना जरूरी है."
                )

                if st.button(
                    "🔄 Retry Level",
                    use_container_width=True,
                    type="primary"
                ):

                    st.session_state.play_game_started = False
                    st.session_state.play_questions = []
                    st.session_state.play_question_index = 0
                    st.session_state.play_score = 0
                    st.session_state.play_answered = False
                    st.session_state.play_last_correct = False
                    st.session_state.play_last_explanation = ""

                    st.rerun()

    # --------------------------------------------------------
    # Reset Game
    # --------------------------------------------------------

    st.divider()

    if st.button(
        "🔄 Restart Current Game",
        use_container_width=True
    ):

        st.session_state.play_game_started = False
        st.session_state.play_questions = []
        st.session_state.play_question_index = 0
        st.session_state.play_score = 0
        st.session_state.play_answered = False
        st.session_state.play_last_correct = False
        st.session_state.play_last_explanation = ""

        st.rerun()


# ============================================================
# EXTRA FEATURES — integrated without creating duplicate core modes
# ============================================================
def analyze_image_with_groq(image_bytes, mime, question, selected_language="English"):
    if not client:
        return "Groq API key missing."
    try:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        completion = client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=[{"role":"user","content":[
                {"type":"text","text":f"Reply only in {selected_language}. {question}"},
                {"type":"image_url","image_url":{"url":f"data:{mime};base64,{b64}"}}
            ]}], temperature=0.4, max_completion_tokens=1500
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Vision error: {e}"

def save_current_chat_cloud():
    if not supabase or not st.session_state.messages:
        return False
    try:
        user=supabase.auth.get_user().user
        if not user: return False
        supabase.table("chat_sessions").upsert({
            "id":st.session_state.session_id,
            "user_id":user.id,
            "messages":st.session_state.messages,
            "updated_at":datetime.datetime.utcnow().isoformat()
        }).execute()
        return True
    except Exception:
        return False

def load_latest_chat_cloud():
    if not supabase: return
    try:
        user=supabase.auth.get_user().user
        if not user: return
        r=supabase.table("chat_sessions").select("messages").eq("user_id",user.id).order("updated_at",desc=True).limit(1).execute()
        if r.data and r.data[0].get("messages"):
            st.session_state.messages=r.data[0]["messages"]
    except Exception:
        pass

def render_login_signup():
    st.title("🔐 Login / Sign Up")
    if not supabase:
        st.warning("Add SUPABASE_URL and SUPABASE_KEY to Streamlit secrets.")
        return
    st.markdown("### ⚡ Quick Login")
    c1,c2=st.columns(2)
    with c1:
        if st.button("🔵 Continue with Google",use_container_width=True):
            try:
                r=supabase.auth.sign_in_with_oauth({"provider":"google","options":{"redirect_to":st.secrets.get("SUPABASE_REDIRECT_URL","")}})
                if getattr(r,"url",None): st.link_button("Continue to Google",r.url,use_container_width=True)
            except Exception as e: st.error(f"Google login failed: {e}")
    with c2:
        if st.button("🔷 Continue with Facebook",use_container_width=True):
            try:
                r=supabase.auth.sign_in_with_oauth({"provider":"facebook","options":{"redirect_to":st.secrets.get("SUPABASE_REDIRECT_URL","")}})
                if getattr(r,"url",None): st.link_button("Continue to Facebook",r.url,use_container_width=True)
            except Exception as e: st.error(f"Facebook login failed: {e}")
    st.caption("Google/Facebook providers must be enabled in Supabase Authentication settings.")

    tab1,tab2=st.tabs(["Log In","Sign Up"])
    with tab1:
        email=st.text_input("Email",key="login_email")
        password=st.text_input("Password",type="password",key="login_password")
        if st.button("Log In",type="primary"):
            try:
                r=supabase.auth.sign_in_with_password({"email":email,"password":password})
                st.session_state.user_email=email
                load_latest_chat_cloud()
                st.success("Logged in successfully.")
                st.rerun()
            except Exception as e: st.error(f"Login failed: {e}")
    with tab2:
        name=st.text_input("Name",key="signup_name")
        email=st.text_input("Email",key="signup_email")
        password=st.text_input("Password",type="password",key="signup_password")
        if st.button("Create Account"):
            try:
                supabase.auth.sign_up({"email":email,"password":password,"options":{"data":{"name":name}}})
                st.success("Account created. Confirm email if your Supabase project requires it.")
            except Exception as e: st.error(f"Sign up failed: {e}")

def render_image_generator():
    st.title("🎨 Creative AI Image Generator")
    prompt=st.text_area("Describe exactly what you want",placeholder="Example: Happy Diwali greeting poster with diyas, no people")
    aspect=st.selectbox("📐 Format",["1:1","16:9","9:16"])
    if st.button("🎨 Generate Image",type="primary",use_container_width=True) and prompt.strip():
        with st.spinner("🎨 Creating only the requested subject..."):
            data,source=generate_image_url(prompt,False,"Normal",aspect)
        st.markdown('<div class="media-card">',unsafe_allow_html=True)
        st.image(data,width=520,caption="Generated image")
        st.markdown('</div>',unsafe_allow_html=True)
        st.caption("Display is intentionally compact; the source image can remain high resolution.")
        if isinstance(data,bytes):
            st.download_button("⬇️ Save Image",data=data,file_name="clyxesschat_image.png",mime="image/png")
        else:
            st.link_button("🔗 Open Full Image",data)

def render_vision_lab():
    st.title("📷 Vision Lab")
    f=st.file_uploader("Upload book, homework or diagram",type=["png","jpg","jpeg","webp"])
    labels=list(PLAY_LANGUAGES.keys()); label=st.selectbox("Answer language",labels)
    question=st.text_input("What should AI explain?",value="Explain the image simply and solve any visible question.")
    if f:
        st.markdown('<div class="media-card">',unsafe_allow_html=True); st.image(f,width=480); st.markdown('</div>',unsafe_allow_html=True)
        if st.button("🧠 Analyze Image",type="primary",use_container_width=True):
            st.write(analyze_image_with_groq(f.getvalue(),f.type,question,PLAY_LANGUAGES[label]))

def render_roleplay():
    st.title("🎭 Peer Roleplay Modes")
    role=st.selectbox("Role",["Classmate","Teacher","Study Buddy","Interview Partner","Project Teammate"])
    label=st.selectbox("Language",list(PLAY_LANGUAGES.keys()),key="role_language")
    prompt=st.text_input("Start the roleplay")
    if st.button("Start Roleplay",type="primary") and prompt:
        system=f"Act as {role} for educational practice. Reply ONLY in {PLAY_LANGUAGES[label]}. Be safe, respectful and age-appropriate."
        ans,_=get_groq_response(client,[{"role":"user","content":prompt}],system,"")
        st.chat_message("assistant").write(ans.choices[0].message.content if ans else "")

def render_timetable():
    st.title("📋 AI Daily Timetable")
    age=st.selectbox("Age/Class",PLAY_AGE_LEVELS)
    subjects=st.multiselect("Subjects",get_play_subjects(age),default=get_play_subjects(age)[:3])
    hours=st.slider("Learning hours",1,6,2)
    if st.button("🗓️ Create Timetable",type="primary"):
        mins=max(20,int(hours*60/max(1,len(subjects))))
        st.session_state.timetable="\n".join([f"{i+1}. {sub} — {mins} min" for i,sub in enumerate(subjects)])
    if st.session_state.get("timetable"): st.code(st.session_state.timetable)

def render_homework_test():
    st.title("📝 Interactive Homework & Test")
    subject=st.selectbox("Subject",sorted(set(sum(AGE_SUBJECTS.values(),[]))))
    if st.button("Generate Test",type="primary"):
        st.session_state.homework_questions=generate_ai_questions(client,"8–10 Years","en",subject,5)
        st.session_state.homework_answers={}
        st.session_state.homework_result=None
    qs=st.session_state.get("homework_questions",[])
    if qs:
        for i,q in enumerate(qs):
            st.session_state.homework_answers[i]=st.radio(q["question"],q["options"],key=f"hw_{i}")
        if st.button("Submit Test"):
            score=sum(st.session_state.homework_answers[i]==q["answer"] for i,q in enumerate(qs))
            st.session_state.homework_result=f"{score}/{len(qs)}"
            st.success(f"Score: {st.session_state.homework_result}")

def learning_report():
    best=max(st.session_state.play_best_scores.values(),default=0)
    return "\n".join([
        "ClyxessChat AI — Learning Report",
        f"Generated: {india_clock_text()}",
        f"Current Level: {st.session_state.play_age}",
        f"Language: {next((n for n,c in PLAY_LANGUAGES.items() if c==st.session_state.play_language),'English')}",
        f"Completed Levels: {len(st.session_state.play_completed_levels)}",
        f"Best Score: {best}/10",
        f"Homework/Test: {st.session_state.get('homework_result') or 'Not attempted'}"
    ])

def render_parent_dashboard():
    st.title("👨‍👩‍👦 Parent Dashboard")
    best=max(st.session_state.play_best_scores.values(),default=0)
    c1,c2,c3=st.columns(3); c1.metric("Completed Levels",len(st.session_state.play_completed_levels)); c2.metric("Best Score",f"{best}/10"); c3.metric("Current Level",st.session_state.play_age)
    report=learning_report()
    st.markdown('<div class="report-card">',unsafe_allow_html=True); st.text(report); st.markdown('</div>',unsafe_allow_html=True)
    st.download_button("📄 Save Report",data=report,file_name="clyxesschat_learning_report.txt",mime="text/plain")
    st.link_button("📤 Share Report", "https://wa.me/?text="+urllib.parse.quote(report))

# ============================================================
# UI START
# ============================================================
st.markdown('<div class="header"><h1>💬 ClyxessChat AI</h1></div>', unsafe_allow_html=True)

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("GROQ_API_KEY is missing from Streamlit secrets.")
    st.stop()

with st.sidebar:
    st.title("💬 ClyxessChat AI")
    try:
        logged_user = supabase.auth.get_user().user if supabase else None
    except Exception:
        logged_user = None
    if logged_user:
        st.success(f"👤 {logged_user.email}")
        if st.button("🚪 Log Out", use_container_width=True):
            try: supabase.auth.sign_out()
            except Exception: pass
            st.rerun()
    else:
        st.caption("Not logged in — sign in to save chats and view parent progress.")

    mode = st.radio("Select Mode", [
        "Normal Chat",
        "Creative Lab (School Mode)",
        "🎮 Play & Learn",
        "🎨 Creative AI Image Generator",
        "📷 Vision Lab",
        "🎭 Peer Roleplay Modes",
        "📋 AI Daily Timetable",
        "📝 Interactive Homework & Test",
        "👨‍👩‍👦 Parent Dashboard",
        "🔐 Login / Sign Up"
    ])
    st.markdown("---")
    if st.button("+ New Chat", use_container_width=True):
        st.session_state.messages=[]
        st.session_state.session_id=str(uuid.uuid4())
        st.rerun()
    st.caption("🇮🇳 India live time: "+get_india_datetime_context().replace("Current India date: ",""))

# ---- routes: one unique screen per feature ----
if mode == "🔐 Login / Sign Up":
    render_login_signup(); st.stop()
if mode == "👨‍👩‍👦 Parent Dashboard":
    render_parent_dashboard(); st.stop()
if mode == "🎨 Creative AI Image Generator":
    render_image_generator(); st.stop()
if mode == "📷 Vision Lab":
    render_vision_lab(); st.stop()
if mode == "🎭 Peer Roleplay Modes":
    render_roleplay(); st.stop()
if mode == "📋 AI Daily Timetable":
    render_timetable(); st.stop()
if mode == "📝 Interactive Homework & Test":
    render_homework_test(); st.stop()
if mode == "🎮 Play & Learn":
    render_play_and_learn(client); st.stop()

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

# ---- Normal Chat ----
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image_url" in message:
            st.markdown('<div class="media-card">',unsafe_allow_html=True)
            st.image(message["image_url"],caption=message.get("image_caption",""),width=520)
            st.markdown('</div>',unsafe_allow_html=True)
        else:
            st.markdown(message["content"])

voice_prompt=""
if mic_recorder:
    audio=mic_recorder(start_prompt="🔴 Start Recording",stop_prompt="⏹️ Stop & Send",key="chat_mic_final")
    if audio:
        voice_prompt=transcribe_audio_with_groq(client,audio.get("bytes",b""))

prompt=st.chat_input("Ask ClyxessChat AI")
if not prompt and voice_prompt: prompt=voice_prompt

if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"): st.markdown(f'<div class="user-bubble">{prompt}</div>',unsafe_allow_html=True)

    # Image generation is explicit only. No automatic image generation for ordinary questions.
    low=prompt.lower()
    explicit_image = any(x in low for x in ["generate image","create image","make an image","draw an image","image banao","image bana","poster banao","photo banao","चित्र बनाओ","तस्वीर बनाओ"])
    if explicit_image:
        with st.chat_message("assistant"):
            with st.spinner("🎨 Image bana raha hu..."):
                img_data,source=generate_image_url(prompt,False,"Normal","1:1")
            st.markdown('<div class="media-card">',unsafe_allow_html=True)
            st.image(img_data,width=520,caption="Generated image")
            st.markdown('</div>',unsafe_allow_html=True)
            st.caption("Image display is compact; no unrelated subject was added by the prompt controller.")
            st.session_state.messages.append({"role":"assistant","image_url":img_data,"image_caption":prompt,"content":"Generated image"})
            save_current_chat_cloud()
    else:
        search_context,sources=search_tavily(prompt)
        system=NORMAL_SYSTEM_PROMPT+"\nLIVE INDIA CLOCK: "+get_india_datetime_context()
        if search_context: system += "\nLIVE WEB INFO:\n"+search_context
        with st.chat_message("assistant"):
            completion,used_model=get_groq_response(client,st.session_state.messages,system,"")
            if completion is None:
                st.error("AI response नहीं आ पाया. Please try again.")
                st.stop()
            response=completion.choices[0].message.content
            st.markdown(response)
            if sources: st.caption("Sources:\n"+sources)
            st.caption(f"Model: {used_model or 'fallback'}")
        st.session_state.messages.append({"role":"assistant","content":response})
        save_current_chat_cloud()
