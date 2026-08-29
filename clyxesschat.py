import streamlit as st
from groq import Groq
from supabase import create_client
import datetime, uuid, requests, time, re, os, json, random
try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None
from typing import Dict, List, Any
from fpdf import FPDF

try:
    from streamlit_mic_recorder import mic_recorder
except ImportError:
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
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONFIG
# ============================================================

GROQ_MODELS = [
    # Primary model from the latest app code, followed by fallbacks.
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3-32b",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant"
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

def generate_image_url(prompt, is_school_mode, age):
    if is_school_mode:
        if "1-2" in age or "3-4" in age:
            final_prompt = f"cute baby cartoon, very simple, bright colors, 3d pixar style, {prompt}"
        else:
            final_prompt = f"kid friendly educational diagram, colorful, {prompt}"
    else:
        final_prompt = f"realistic, cinematic, 4k, {prompt}"

    try:
        hf_key = st.secrets.get("HF_API_KEY", "")
        if hf_key:
            API_URL = "https://api-inference.huggingface.co/models/stabilityai/sdxl-turbo"
            headers = {"Authorization": f"Bearer {hf_key}"}
            r = requests.post(
                API_URL,
                headers=headers,
                json={"inputs": final_prompt},
                timeout=20
            )
            if r.status_code == 200:
                return r.content, "huggingface"
    except Exception:
        pass

    poll_url = (
        "https://image.pollinations.ai/prompt/"
        f"{requests.utils.quote(final_prompt)}"
        f"?width=1024&height=1024&nologo=true"
        f"&seed={uuid.uuid4().int % 10000}"
    )
    return poll_url, "pollinations"

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
    base = (
        f"You are ClyxessChat AI - School Mode Creative Lab. "
        f"Current Age Group: {age_group}. "
    )

    if "1-2" in age_group:
        return base + """
        You are a gentle early-learning teacher for children aged 1-2.
        Use very short, simple, playful language and emojis.
        IMPORTANT: Never assume the child owns, ate, saw, did, likes,
        remembers, or experienced anything. Never ask personal-memory
        questions such as 'What toy do you have?', 'What fruit did you eat?'
        or 'What did you see yesterday?'.
        For learning questions, there must be exactly one clear, objective
        answer. Prefer colors, shapes, animals, sounds, simple objects,
        counting 1-5 and basic words. No abstract or difficult concepts.
        If the child is chatting rather than playing, remain warm and natural.
        If user wants image, create a cute, age-appropriate cartoon prompt.
        """

    elif "3-4" in age_group:
        return base + """
        You are Didi for 3-4 years kids. Use simple playful language,
        colors, numbers, shapes, animals, sounds, stories and basic logic.
        Never assume personal experiences or private information.
        Learning questions must have one clear objective answer.
        Never use tough or frightening words.
        """

    elif "5-6" in age_group or "6-8" in age_group:
        return base + """
        Age 5-8: Focus Curiosity & Basic Logic.
        Task: Interactive Story-Building & Shape Puzzles.
        Hint Style: Kahani wala.
        Eg: 'Sher jungle me kho gaya, pehle kya kare?'.
        Socratic method - answer with question.
        """

    elif "10-11" in age_group:
        return base + """
        Age 10-11: Focus Maker & Practical Science.
        Task: Step-by-step DIY Projects & Logic Challenges.
        Hint Style: Jugaad wala.
        Eg: 'Rocket banana hai? Socho hawa kaha se niklegi?'.
        Give steps, not direct answer.
        """

    else:
        return base + """
        Age 11+: Focus Future Tech, AI & App Prototyping.
        Task: Coding Logic, App Wireframing.
        Hint Style: Innovator wala.
        Challenge them to break big problem into 2 small parts.
        """

# ============================================================
# VOICE INPUT (OPTIONAL)
# ============================================================

def transcribe_audio_with_groq(client, audio_bytes):
    """Transcribe recorded speech using Groq Whisper when available."""
    if not audio_bytes:
        return ""
    temp_path = "clyxesschat_temp_audio.wav"
    try:
        with open(temp_path, "wb") as f:
            f.write(audio_bytes)
        with open(temp_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                prompt=(
                    "Speech may contain Hindi, Hinglish, Chhattisgarhi, "
                    "Marwadi, Sindhi, Marathi, Bengali, Tamil, Telugu, "
                    "Gujarati, Kannada, Malayalam, Odia or English."
                )
            )
        return getattr(result, "text", "") or ""
    except Exception:
        return ""
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass

# ============================================================
# TAVILY
# ============================================================

def search_tavily(query):
    search_words = [
        "news", "mausam", "weather", "rate", "price",
        "score", "aaj", "kal", "today", "latest", "breaking",
        "date", "day", "दिन", "तारीख", "वार", "त्योहार", "festival",
        "holiday", "raksha bandhan", "rakhi", "रक्षाबंधन", "राखी"
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
# LIVE INDIA DATE / TIME
# ============================================================

def get_india_datetime_context():
    try:
        now = datetime.datetime.now(ZoneInfo("Asia/Kolkata")) if ZoneInfo else datetime.datetime.now()
        return now.strftime(
            "Current India date: %A, %d %B %Y. Current India time: %I:%M %p (IST)."
        )
    except Exception:
        return datetime.datetime.now().strftime(
            "Current application date: %A, %d %B %Y. Current application time: %I:%M %p."
        )

# ============================================================
# GROQ CHAT
# ============================================================

def get_groq_response(
    client,
    messages,
    system_prompt,
    search_context=""
):
    final_system = system_prompt + "\n\nLIVE CLOCK (India/IST): " + get_india_datetime_context()

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
                "question": "Which color is the sun usually shown as? ☀️",
                "options": ["Yellow", "Blue", "Purple", "Black"],
                "answer": "Yellow",
                "explanation": "The sun is commonly shown as yellow in early learning."
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

        # Reject subjective/personal-experience questions, especially for toddlers.
        q_lower = str(question).strip().lower()
        personal_patterns = [
            "what did you", "what do you", "what is your", "which toy do you",
            "which fruit did you", "what did we", "what have you", "तुमने",
            "तुम्हारे पास", "तुम्हारा पसंदीदा", "आपने", "आपके पास",
            "हमने पहले", "तुम्हें क्या पसंद"
        ]
        if any(pattern in q_lower for pattern in personal_patterns):
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


def generate_ai_questions(
    client,
    age,
    language,
    subject,
    count=10
):
    """
    AI-generated question engine.

    Groq से questions requested language में generate होते हैं.
    JSON invalid होने पर safe demo fallback चलता है.
    """

    language_name = next(
        (
            name
            for name, code in PLAY_LANGUAGES.items()
            if code == language
        ),
        "English"
    )

    prompt = f"""
Create exactly {count} educational multiple-choice questions
for a child in age group: {age}.

Subject: {subject}
Language: {language_name}

Rules:
1. Questions MUST be age-appropriate.
2. Use simple, child-friendly language.
3. Questions must teach, not scare or shame.
4. Do not ask for personal information.
5. Do not include dangerous instructions.
6. Financial Literacy must be educational and age-appropriate.
7. AI/Technology content must focus on safe and responsible use.
8. Each question must have exactly 4 options.
9. Only one option must be correct.
10. Give a short explanation.
11. Return ONLY valid JSON.
12. Do not use markdown.
13. STRICT LANGUAGE LOCK: question, all options, answer and explanation MUST be entirely in the selected language.
14. Never silently switch to English when another language is selected.
15. Do not use Hinglish or mixed-language text unless English is the selected language.
16. Do not ask personal-experience questions such as what the child ate, owns, likes, saw or did.

JSON format:
[
  {{
    "question": "Question",
    "options": ["A", "B", "C", "D"],
    "answer": "A",
    "explanation": "Short explanation"
  }}
]
"""

    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    for model in GROQ_MODELS:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=5000
            )

            text = completion.choices[0].message.content
            parsed = json.loads(clean_json_text(text))

            valid = validate_questions(
                parsed,
                count
            )

            if len(valid) == count:
                return valid

        except Exception:
            continue

    # Strict same-language fallback for early learning.
    early_bank = {
        "hi": {"Colors": ("कौन सा रंग लाल है? 🔴", ["🔴 लाल", "🔵 नीला", "🟢 हरा", "🟡 पीला"], "🔴 लाल", "यह लाल रंग है।"),
               "Shapes": ("गोल आकार कौन सा है? ⭕", ["⬛ वर्ग", "🔺 त्रिभुज", "⭕ वृत्त", "⭐ तारा"], "⭕ वृत्त", "यह गोल आकार है।"),
               "Animals": ("कौन सा जानवर म्याऊँ करता है? 🐱", ["🐶 कुत्ता", "🐱 बिल्ली", "🐮 गाय", "🐟 मछली"], "🐱 बिल्ली", "बिल्ली म्याऊँ करती है।")},
        "en": {"Colors": ("Which color is red? 🔴", ["🔴 Red", "🔵 Blue", "🟢 Green", "🟡 Yellow"], "🔴 Red", "This is red."),
               "Shapes": ("Which shape is a circle? ⭕", ["⬛ Square", "🔺 Triangle", "⭕ Circle", "⭐ Star"], "⭕ Circle", "This is a circle."),
               "Animals": ("Which animal says meow? 🐱", ["🐶 Dog", "🐱 Cat", "🐮 Cow", "🐟 Fish"], "🐱 Cat", "A cat says meow.")},
        "zh": {"Colors": ("哪个是红色？🔴", ["🔴 红色", "🔵 蓝色", "🟢 绿色", "🟡 黄色"], "🔴 红色", "这是红色。"),
               "Shapes": ("哪个是圆形？⭕", ["⬛ 正方形", "🔺 三角形", "⭕ 圆形", "⭐ 星形"], "⭕ 圆形", "这是圆形。")},
        "ja": {"Colors": ("どの色が赤ですか？🔴", ["🔴 赤", "🔵 青", "🟢 緑", "🟡 黄色"], "🔴 赤", "これは赤色です。"),
               "Shapes": ("どれが丸ですか？⭕", ["⬛ 四角", "🔺 三角", "⭕ 丸", "⭐ 星"], "⭕ 丸", "これは丸い形です。")},
    }
    if "1–2" in age or "1-2" in age:
        item = early_bank.get(language, {}).get(subject)
        if item:
            q, opts, ans, exp = item
            base = [{"question": q, "options": opts, "answer": ans, "explanation": exp}]
            result = []
            while len(result) < count:
                result.extend([dict(base[0])])
            return result[:count]

    return build_demo_questions(subject)


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
# UI START
# ============================================================

st.markdown(
    '<div class="header"><h1>💬 ClyxessChat AI</h1></div>',
    unsafe_allow_html=True
)

# ============================================================
# GROQ CLIENT
# ============================================================

try:
    client = Groq(
        api_key=st.secrets["GROQ_API_KEY"]
    )
except Exception:
    st.error(
        "GROQ_API_KEY is missing from Streamlit secrets."
    )
    st.stop()

# ============================================================
# SIDEBAR - MODE SELECTOR
# ============================================================

with st.sidebar:

    st.title("💬 ClyxessChat AI")

    mode = st.radio(
        "Select Mode",
        [
            "Normal Chat",
            "Creative Lab (School Mode)",
            "🎮 Play & Learn"
        ],
        index=0
    )

    st.markdown("---")

    # --------------------------------------------------------
    # EXISTING CREATIVE LAB AGE SELECTOR
    # --------------------------------------------------------

    age_group = "1-2 Yrs"

    if "Creative Lab" in mode:

        st.markdown("### 🎒 Age Group Selector")
        st.caption(
            "LEARN & CREATE (SHIKHEN AUR BANAYEN)"
        )

        cols = st.columns(2)

        age_options = [
            "1-2 Yrs",
            "3-4 Yrs",
            "5-6 Yrs",
            "6-8 Yrs",
            "10-11 Yrs",
            "11+ Yrs"
        ]

        for i, ag in enumerate(age_options):

            if cols[i % 2].button(
                ag,
                key=f"age_{ag}",
                use_container_width=True,
                type=(
                    "primary"
                    if st.session_state.get(
                        "age_group",
                        "1-2 Yrs"
                    ) == ag
                    else "secondary"
                )
            ):
                st.session_state.age_group = ag

        age_group = st.session_state.get(
            "age_group",
            "1-2 Yrs"
        )

        st.success(
            f"Active: {age_group} | Focus: "
            f"{'Early Brain Development' if '1-2' in age_group else 'Creative Lab'}"
        )

    # --------------------------------------------------------
    # NEW PLAY & LEARN SIDEBAR INFO
    # --------------------------------------------------------

    if mode == "🎮 Play & Learn":

        st.markdown("### 🎮 Play & Learn")

        st.caption(
            "AI QUESTIONS • LEARNING • GAMES"
        )

        st.info(
            "10/10 complete करने पर next age level unlock होगा."
        )

    # --------------------------------------------------------
    # NEW CHAT
    # --------------------------------------------------------

    if st.button(
        "+ New Chat",
        use_container_width=True
    ):

        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())

        # Do not destroy Play & Learn progress.
        st.session_state.play_game_started = False
        st.session_state.play_questions = []
        st.session_state.play_question_index = 0
        st.session_state.play_score = 0
        st.session_state.play_answered = False
        st.session_state.play_last_correct = False
        st.session_state.play_last_explanation = ""

        st.rerun()

# ============================================================
# PLAY & LEARN ROUTE
# ============================================================

if mode == "🎮 Play & Learn":

    render_play_and_learn(client)

    st.stop()

# ============================================================
# EXISTING CHAT DISPLAY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if "image_url" in message:

            st.image(
                message["image_url"],
                caption=message.get(
                    "image_caption",
                    ""
                )
            )

        else:

            st.markdown(
                message["content"]
            )

# ============================================================
# OPTIONAL VOICE INPUT
# ============================================================

voice_prompt = ""
if mic_recorder is not None:
    with st.sidebar:
        st.markdown("### 🎤 Voice Input")
        audio = mic_recorder(
            start_prompt="🔴 Start Recording",
            stop_prompt="⏹️ Stop & Send",
            key="clyxesschat_voice"
        )
        if audio:
            with st.spinner("🎙️ Transcribing..."):
                voice_prompt = transcribe_audio_with_groq(
                    client, audio.get("bytes", b"")
                )
            if voice_prompt:
                st.info(f"🗣️ {voice_prompt}")

# ============================================================
# CHAT INPUT
# ============================================================

chat_placeholder = (
    "Apna idea type karein ya draw karein..."
    if "Creative" in mode
    else "Ask ClyxessChat AI"
)

prompt = st.chat_input(chat_placeholder)
if not prompt and voice_prompt:
    prompt = voice_prompt

if prompt:

    is_school = "Creative" in mode

    current_age = (
        st.session_state.age_group
        if is_school
        else "Normal"
    )

    system_prompt = (
        get_school_system_prompt(current_age)
        if is_school
        else NORMAL_SYSTEM_PROMPT
    )

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(
            f'<div class="user-bubble">{prompt}</div>',
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # IMAGE REQUEST
    # --------------------------------------------------------

    wants_image = any(
        w in prompt.lower()
        for w in [
            "image",
            "draw",
            "banao",
            "photo",
            "picture",
            "chitra",
            "rocket",
            "diagram"
        ]
    )

    with st.chat_message("assistant"):

        if wants_image:

            with st.spinner(
                "🎨 Image bana raha hu..."
            ):

                img_data, source = generate_image_url(
                    prompt,
                    is_school,
                    current_age
                )

                st.image(
                    img_data,
                    caption=f"Generated for: {prompt}"
                )

                st.session_state.messages.append({
                    "role": "assistant",
                    "image_url": img_data,
                    "image_caption": prompt,
                    "content": (
                        f"Ye lo aapki image! ({source})"
                    )
                })

        # ----------------------------------------------------
        # TEXT RESPONSE
        # ----------------------------------------------------

        message_placeholder = st.empty()
        full_response = ""

        with st.spinner(
            "ClyxessChat AI is responding..."
        ):

            search_context, sources = search_tavily(
                prompt
            )

            completion, used_model = get_groq_response(
                client,
                st.session_state.messages,
                system_prompt,
                search_context
            )

            if completion is None:
                st.error(
                    "AI response नहीं आ पाया. "
                    "Please try again."
                )
                st.stop()

            response = (
                completion
                .choices[0]
                .message
                .content
            )

            if sources and mode != "🎮 Play & Learn":
                response += (
                    f"\n\n**Source:**\n{sources}"
                )

        for word in response.split():

            full_response += word + " "

            message_placeholder.markdown(
                full_response + "▌"
            )

            time.sleep(0.03)

        message_placeholder.markdown(
            full_response
        )

        st.caption(
            f"Mode: {mode} | "
            f"Age: {current_age} | "
            f"Model: {used_model}"
        )

    if not wants_image:

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

    st.rerun()
