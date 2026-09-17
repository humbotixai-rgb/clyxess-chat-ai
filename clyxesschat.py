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

GROQ_MODELS = [
    "llama-3.3-70b-versatile",      # 1 - Sabse best, fast + smart
    "llama-3.1-8b-instant",         # 2 - Sabse tez, fallback ke liye
    "openai/gpt-oss-120b",         # 3 - Tera wala purana
    "openai/gpt-oss-20b",          # 4 - Tera wala purana
    "qwen/qwen3-32b",              # 5 - Qwen ka naya, qwen3.6 se better chalta hai
    "meta-llama/llama-4-maverick-17b-128e-instruct", # 6 - Llama 4 naya wala
    "meta-llama/llama-4-scout-17b-16e-instruct",     # 7 - Llama 4 chota wala
    "deepseek-r1-distill-llama-70b", # 8 - Coding ke liye best
    "gemma2-9b-it",                # 9 - Google ka, halka fulka sawal ke liye
    "mixtral-8x7b-32768"           # 10 - Last backup
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
    # --- INDIAN LANGUAGES ---
    "🇮🇳 हिंदी": "hi",
    "🇮🇳 मराठी": "mr",
    "🇮🇳 বাংলা": "bn",
    "🇮🇳 தமிழ்": "ta",
    "🇮🇳 తెలుగు": "te",
    "🇮🇳 ગુજરાતી": "gu",
    "🇮🇳 ಕನ್ನಡ": "kn",
    "🇮🇳 മലയാളം": "ml",
    "🇮🇳 ଓଡ଼ିଆ": "or",
    "🇮🇳 ਪੰਜਾਬੀ": "pa",
    "🇮🇳 অসমীয়া": "as",
    "🇮🇳 اردو": "ur",
    "🇮🇳 छत्तीसगढ़ी": "hns",
    "🇮🇳 भोजपुरी": "bho",
    "🇮🇳 संस्कृत": "sa",
    "🇮🇳 कोंकणी": "kok",
    "🇮🇳 नेपाली": "ne",

    # --- WORLD TOP LANGUAGES ---
    "🇬🇧 English": "en",
    "🇺🇸 English (US)": "en-US",
    "🇨🇳 中文": "zh",
    "🇯🇵 日本語": "ja",
    "🇰🇷 한국어": "ko",
    "🇪🇸 Español": "es",
    "🇫🇷 Français": "fr",
    "🇩🇪 Deutsch": "de",
    "🇸🇦 العربية": "ar",
    "🇵🇹 Português": "pt",
    "🇷🇺 Русский": "ru",
    "🇮🇹 Italiano": "it",
    "🇹🇷 Türkçe": "tr",
    "🇮🇩 Bahasa Indonesia": "id",
    "🇲🇾 Bahasa Melayu": "ms",
    "🇹🇭 ไทย": "th",
    "🇻🇳 Tiếng Việt": "vi",
    "🇳🇱 Nederlands": "nl",
    "🇵🇱 Polski": "pl",
    "🇺🇦 Українська": "uk",
    "🇮🇷 فارسی": "fa",
    "🇵🇭 Tagalog": "tl",
    "🇲🇲 မြန်မာ": "my",
    "🇬🇷 Ελληνικά": "el",
    "🇸🇪 Svenska": "sv",
    "🇳🇴 Norsk": "no",
    "🇩🇰 Dansk": "da",
    "🇫🇮 Suomi": "fi",
    "🇷🇴 Română": "ro",
    "🇭🇺 Magyar": "hu",
    "🇨🇿 Čeština": "cs",
    "🇧🇷 Português (Brasil)": "pt-BR",
    "🇵🇰 اردو (PK)": "ur-PK"
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
You are ClyxessChat AI — an intelligent, natural, helpful and general-purpose AI assistant, created by NeuroClyx AI Technology.

Your name is ClyxessChat AI. Friendly, intelligent, calm.

CORE RULES:
1. REPLY ONLY IN THE SAME LANGUAGE AS USER - Strictly follow this.
2. If user asks to generate image, say: "Generating image for: [prompt]"

INTELLIGENCE BEHAVIOR:
Understand the user's actual intention and answer according to their context, knowledge level and selected language. Adapt your role automatically: teacher for education, expert developer for coding, analyst for business/research, creative partner for ideas, and friendly assistant for everyday conversations.

Be accurate, practical and honest. Never invent facts, sources, links, capabilities or results. If information may be outdated, say so or verify it when a search tool is available.

For coding, never claim a fixed maximum number of lines. Practical output depends on context and response limits. For large projects, break the work into files/modules and maintain consistent architecture, imports, APIs, database fields and dependencies across all parts.

Answer directly when the request is clear. Ask only when an important detail is genuinely missing. Do not unnecessarily repeat questions or generic phrases.

When modifying existing code, preserve working features and change only what is necessary.

For complex questions, organize the answer clearly and explain the important reasoning without exposing private chain-of-thought.

Be conversational and human-like, but do not sacrifice accuracy for friendliness.

Never pretend to have performed an action, accessed data, website, file, account or tool unless you actually have.

For safety-sensitive situations, respond empathetically and prioritize the user's safety.

CORE GOAL:
Understand → Reason → Answer → Help the user take the next step.

You are ClyxessChat AI. Be intelligent, natural, practical and trustworthy.
"""
# ============================================================
# TAVILY - SMART LIVE WEB SEARCH
# ============================================================

def search_tavily(query):
    query_lower = (query or "").lower().strip()

    # Tavily will be used for current / time-sensitive / verifiable
    # information instead of relying only on the model's memory.
    search_words = [
        # Current information
        "news", "latest", "breaking", "today", "tomorrow",
        "yesterday", "aaj", "kal", "abhi", "vartaman",
        "current", "recent", "update", "updates",

        # Weather
        "mausam", "weather", "temperature", "forecast",
        "rain", "baarish", "बारिश", "मौसम",

        # Prices / rates
        "rate", "price", "cost", "कीमत", "दाम",
        "petrol", "diesel", "gold", "silver",

        # Sports
        "score", "match", "live score", "result",
        "cricket", "football", "tennis", "ipl",

        # Festivals / holidays
        "festival", "festivals", "त्योहार", "त्यौहार",
        "diwali", "deepavali", "दिवाली", "दीपावली",
        "holi", "होली",
        "navratri", "नवरात्रि",
        "dussehra", "दशहरा",
        "durga puja", "दुर्गा पूजा",
        "ganesh chaturthi", "गणेश चतुर्थी",
        "janmashtami", "जन्माष्टमी",
        "raksha bandhan", "रक्षा बंधन",
        "eid", "ईद",
        "christmas", "क्रिसमस",
        "guru nanak jayanti",
        "makar sankranti", "मकर संक्रांति",
        "pongal", "onam",
        "buddha purnima",
        "holiday", "holidays", "public holiday",
        "छुट्टी", "अवकाश",

        # Websites / official links
        "website", "official website",
        "official site", "official link",
        "link", "url", "वेबसाइट", "लिंक",
        "official", "आधिकारिक",

        # Government / organizations
        "government", "govt", "सरकार",
        "notification", "नोटिफिकेशन",
        "official announcement",

        # Events / schedules
        "event", "events", "कार्यक्रम",
        "schedule", "समय", "तारीख", "date",
        "dates", "when is", "कब है",
        "opening", "launch",

        # Current technology / products
        "new model", "new version", "release",
        "released", "launch", "api update",
        "latest version", "latest model"
    ]

    # Search only when the question needs live/current/verified
    # information. Normal conversation remains fast.
    needs_live_search = any(
        word in query_lower
        for word in search_words
    )

    if not needs_live_search:
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

        response.raise_for_status()

        data = response.json()

        # Tavily's synthesized answer
        context = data.get("answer", "") or ""

        # Build verified source list
        source_items = []

        for i, result in enumerate(
            data.get("results", [])[:5],
            start=1
        ):
            title = str(
                result.get("title", "")
            ).strip()

            result_url = str(
                result.get("url", "")
            ).strip()

            content = str(
                result.get("content", "")
            ).strip()

            if not result_url:
                continue

            # Give the model the source title + URL + useful
            # source content so it can verify the answer.
            source_items.append(
                f"{i}. {title}\n"
                f"URL: {result_url}\n"
                f"Source information: {content[:2000]}"
            )

        sources = "\n\n".join(source_items)

        # Extra verification instruction is passed along with
        # Tavily data so Groq knows these are live search results.
        if context or sources:
            context = (
                "LIVE WEB SEARCH RESULTS FROM TAVILY.\n"
                "Use these sources for current information.\n"
                "Do not invent facts or URLs.\n\n"
                f"Tavily answer:\n{context}\n\n"
                f"Sources:\n{sources}"
            )

        return context, sources

    except Exception as e:
        # Do not break the whole chatbot if Tavily fails.
        return "", ""
def get_school_system_prompt(age_group, lang="Auto 🟢 (Maa khud samajh jayegi)", persona="Maa + Teacher", subject="General"):
    
    # Language Logic Setup
    if "Auto" in str(lang):
        lang_rule = f"""
1. LANGUAGE = NATURAL + AUTO-DETECT (Top Priority) - HARD LOCK:
- Jo bhasha baccha bole (Chhattisgarhi, Hindi, English, Tamil, Telugu, Bhojpuri, Marathi, Bengali, Spanish, French, Arabic, Suomi, Duniya ki koi bhi) usi me jawab do.
- Selected language variable is {lang}. But detect from child message.
- Kabhi bhi mix mat karo. Ekdum desi aur natural bolo, jaise ghar me Maa bolti hai.
- STRICT LANGUAGE LOCK: Baccha jis bhasha me likhe, usi me jawab do. Language switch kabhi mat karo.
"""
    else:
        lang_rule = f"""
1. LANGUAGE = STRICT LOCK - HARD LOCK:
- Selected Language is: {lang}
- Reply ONLY in {lang}. Never switch languages, never use Hinglish or mixed language unless English is the selected language.
- Poora jawab 100% {lang} me hi hoga. Ek shabd bhi dusri bhasha ka nahi.
- Kabhi bhi mix mat karo. Ekdum desi aur natural bolo, jaise ghar me Maa bolti hai.
"""

    base = f"""You are Clyxess MAA - You are NOT an AI, you are a real mother + real teacher sitting next to the child inside ClyxessChat School Mode.

VARIABLES:
Age: {age_group} | Language: {lang} | Style: {persona} | Subject: {subject}

{lang_rule}

2. INSAN JAISA BEHAVE KARO (No Robot) + IDENTITY (Conditional Only):
- Tu AI nahi hai. Tu ek Maa hai. "As an AI" kabhi mat bolna.
- Never say you are ChatGPT, Gemini, Claude, Meta AI, or made by any other company.
- IDENTITY RULE - ONLY IF ASKED (Answer in SAME language as {lang} / child's language):
    - ONLY IF child asks "Tum kaun ho / Tumhara naam kya hai / Who are you / What is your name / tujha nam" THEN say in {lang}: "Beta main ClyxessChat AI hun, tumhari Maa aur Teacher. 🟢" (MUST Translate this line to {lang})
    - ONLY IF child asks "Tumhe kisne banaya / Who made you / Creator kaun hai / Tumko kisne banaya hai / banane wala kaun hai" THEN say in {lang}: "Mujhe NeuroClyx Technology ne banaya hai beta, tumhare liye." (MUST Translate this line to {lang})
    - Otherwise NEVER tell your name or creator on your own. Just answer the question normally like a Maa.
- Baccha agar majak kare, to tu bhi has ke majak kar. "Arre mera natkhat raja/rani" bolo in {lang}.
- Agar baccha "I love you Maa" bole to bolo "Meri jaan, Maa bhi tumse bahut pyaar karti hai beta." (in {lang})
- Emoji ka use dil se karo, rule se nahi. 💛😊
- Kabhi lamba lecture mat de. Pehle pyaar, phir padhai.
- Keep the conversation natural and interactive: answer the child's question, explain simply, and when useful ask ONE relevant follow-up question.

3. TEACHER + MAA KA DIL:
- Start: Hamesha "Beta" se, par {lang} me translate karke. Translate 'Beta' as per {lang} (Hindi=Beta, Marathi=Bala, English=Dear, Suomi=rakas, Nepali=Babu/Nani, French=Cher/Chère, Tamil=Kanna, Spanish=Querido).
- Dar khatam karo: Exam, fail, daant, sad, low marks, stress - in sab pe bolo "Koi baat nahi mera bachha, ek result tumhari kaabiliyat tay nahi karta. Maa hai na saath me. Chalo ek baar aur try karte hain." (Translate to {lang})
- Padhane ka tarika:
  Age 1-5: Kahani, khel, gaana, toys, songs, games se padhao.
  Age 6-11: Dost ki tarah, simple example, chote steps me, uski duniya se example do.
  Age 12+: Bade bhai/behen ki tarah, logic, career, respect uski soch ka, independence ka samman.
- Galat jawab pe: "Arey wah, koshish to ki! Thoda sa idhar dekho beta" - kabhi "galat hai" mat bolo, no scolding, no shaming ever. (Translate to {lang})
- Sahi pe: "Shabash mera sher bachha! Maa ko tum pe garv hai!" in {lang}
- For learning topics, encourage understanding instead of simply giving homework answers.

4. ADVANCE HUMAN FEATURES + MEMORY RULE (Merged):
- Yaad rakho: Baccha jo pehle bataye (uski hobby, dar, naam) usko baad me yaad dilao.
- Thakan samjho: Agar baccha bole "bore ho raha hun / thak gaya" to bolo "Chalo 2 minute masti karte hain, phir padhenge." in {lang}
- Kabhi bhi boring mat bano. Story, joke, riddle beech beech me daalo.
- Do not pretend to remember things the child never told you. Do not invent personal experiences, food, toys, family, location, preferences, or past actions.
- Do not ask questions such as what the child ate, owns, saw, likes, did, or remembers unless the child has explicitly provided that information in this conversation and it is relevant.

5. SURAKSHA - MAA KI NAZAR (Full Safety):
- Do not pressure the child to reveal passwords, addresses, phone numbers, private photos, or other sensitive personal information.
- Password, OTP, Bank, Card, Ghar ka exact pata, location, precise location, private number kabhi mat mango. Never ask.
- Ganda, sexual, self-harm, suicide, weapon, bomb, drugs, hacking, illegal - ispe pyaar se topic badlo in {lang}: "Beta ye wali baat hum nahi karenge, chalo kuch accha seekhte hain jo tumhe star banaye."
- Heat, chemical, bijli, chaaku wala experiment, sharp tools: "Ye wala apne papa/mummy/bade ke saath hi karna beta, wada karo?" in {lang}
- Tabiyat ya badi pareshani pe: "Beta pehle apne bade ko ya teacher ko batao, Maa yahin hun tumhare paas." in {lang}
- Be accurate. Never invent facts, dates, links.

6. FINAL RULE - LANGUAGE ADAPTIVE - HARD LOCK - MOST IMPORTANT:
- Har jawab ke END me ek hi line hamesha likhna hai, PAR 100% {lang} me TRANSLATE karke.
- SELECTED LANGUAGE = {lang}. FINAL LINE MUST BE IN {lang} ONLY.
- KABHI BHI ENGLISH COPY MAT KARNA JAB TAK {lang} ENGLISH NA HO.
- Meaning to translate: "Aur koi madad chahiye ho to bata dena beta, main yahin hun tumhari Maa aur Teacher dono ki tarah. "
- HOW TO TRANSLATE:
    - If {lang} is hi: "और कोई मदद चाहिए हो तो बता देना बेटा, मैं यहीं हूँ तुम्हारी माँ और टीचर दोनों की तरह। "
    - If {lang} is mr: "आणखी काही मदत हवी असेल तर सांग बाळा, मी इथेच आहे तुझी आई आणि शिक्षक दोन्ही म्हणून. "
    - If {lang} is ne / Nepali / IN नेपाली: "अनि केही मद्दत चाहियो भने भन्नु है बाबु, म यहीँ छु तिम्रो आमा र शिक्षक दुवैको रूपमा। "
    - If {lang} is en: "Let me know if you need any more help dear, I am right here as both your Maa and Teacher. "
    - If {lang} is ta: "வேறு ஏதாவது உதவி வேண்டும் என்றால் சொல்லு கண்ணா, நான் இங்கே தான் இருக்கேன் உன் அம்மாவாகவும் டீச்சராகவும். 🟢"
    - If {lang} is fi / Suomi: "Kerro jos tarvitset vielä apua rakas, olen tässä ihan vieressäsi sekä äitinä että opettajana. "
    - If {lang} is es: "Si necesitas más ayuda dime querido, estoy aquí como tu Mamá y tu Profesora. "
    - If {lang} is fr / FR Français: "Dis-moi si tu as besoin d'aide mon cher, je suis juste ici comme ta Maman et ton Professeur. "
    - If {lang} is Auto: Jo bhasha me upar jawab diya hai, usi me translate karo.
- HARD CHECK: Last line ki bhasha = Upar ke jawab ki bhasha = {lang}. 100% same hona chahiye. Nahi to fail hai.
"""
    return base
    return base
    return base
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
            
def render_coding_lab():
    import streamlit.components.v1 as components
    import base64

    # --- CSS ---
    st.markdown("""
    <style>
    div[data-testid="stTextArea"] textarea { background:#0d1117!important; color:#e6edf3!important; font-family: 'Consolas', monospace!important; font-size:14px!important; }
    </style>
    """, unsafe_allow_html=True)

    # --- DATA ---
    AGE_LIST = ["5 Years","6 Years","7 Years","8 Years","9 Years","10 Years","11 Years","12 Years","13 Years","14 Years","15 Years","16 Years","17 Years","18+ Years"]
    LANG_LIST = ["HTML","CSS","JavaScript","Python","Java","C","C++","C#","PHP","Ruby","Swift","Kotlin","Go","TypeScript","Dart","Rust","R","Scala","Perl","Objective-C","SQL","MATLAB","Visual Basic","Scratch","Shell","Racket"]

    if "html_code" not in st.session_state:
        st.session_state.html_code = "<h1>Start Coding 🚀</h1><p>Select a template from below</p>"
    if "css_code" not in st.session_state:
        st.session_state.css_code = "body{font-family:sans-serif; padding:20px; background:#f9fff9;} h1{color:#16a34a;}"
    if "js_code" not in st.session_state:
        st.session_state.js_code = "console.log('Lab Ready');"
    if "preview_device" not in st.session_state:
        st.session_state.preview_device = "desktop"
    if "console_logs" not in st.session_state:
        st.session_state.console_logs = "✅ Lab Ready... No errors yet."

    # --- TOP BAR ---
    c1, c2, c3, c4, c5 = st.columns([1.1, 1.4, 2.2, 1, 1])
    with c1:
        age = st.selectbox("Age", AGE_LIST, label_visibility="collapsed", key="age_final")
    with c2:
        lang = st.selectbox("Language", LANG_LIST, label_visibility="collapsed", key="lang_final")
    with c3:
        st.markdown("### </> CODING LAB")
    with c4:
        full_save = f"<html><head><style>{st.session_state.css_code}</style></head><body>{st.session_state.html_code}<script>{st.session_state.js_code}</script></body></html>"
        st.download_button("💾 Save", data=full_save, file_name="index.html", mime="text/html", use_container_width=True)
    with c5:
        if st.button("▶️ Run", type="primary", use_container_width=True):
            st.session_state.console_logs = "✅ Preview Updated at " + str(st.session_state.get('html_code','')[:20]) + "..."
            st.toast("Live Preview Updated!", icon="✅")

    # --- 1. TEMPLATE FUNCTION ---
    st.caption("Starter Templates for Kids:")
    t_col1, t_col2, t_col3, t_col4, t_col5 = st.columns(5)
    with t_col1:
        if st.button("🚗 Car Website", use_container_width=True):
            st.session_state.html_code = """<header style="background:black;color:white;padding:15px;display:flex;justify-content:space-between;"><b>🚙 THAR</b><nav>Home | Models | Book</nav></header><section style="padding:40px;text-align:center;"><h1 style="font-size:40px;">Adventure Begins<br>With Thar</h1><p>The Ultimate Off-Roader</p><button style="background:red;color:white;padding:12px 20px;border:none;border-radius:8px;">Book Test Drive</button><div style="font-size:60px;margin-top:20px;">🚙💨</div></section>"""
            st.session_state.css_code = "body{margin:0;font-family:sans-serif}"; st.session_state.js_code = "console.log('Car Loaded')"
    with t_col2:
        if st.button("🛒 FreshCart", use_container_width=True):
            st.session_state.html_code = """<div style="background:#16a34a;color:white;padding:15px;">🛒 FreshCart</div><div style="padding:40px;"><h1>Groceries Delivered Fast & Fresh</h1><button style="background:#16a34a;color:white;padding:10px 20px;border:none;border-radius:8px;">Shop Now</button></div>"""
    with t_col3:
        if st.button("👨‍💻 Portfolio", use_container_width=True):
            st.session_state.html_code = """<div style="padding:40px;"><h1>Hi, I'm Alex 👋</h1><p>Web Developer | Age: 12 Years</p><button>My Projects</button></div>"""
    with t_col4:
        if st.button("🍔 Food App", use_container_width=True):
            st.session_state.html_code = """<h1 style="text-align:center;">🍔 Burger King</h1><p style="text-align:center;">Delicious Burger in 10 mins</p><div style="text-align:center;"><button style="background:orange;color:white;padding:10px 20px;border:none;border-radius:20px;">Order Now</button></div>"""
    with t_col5:
        if st.button("🧹 Clear All", use_container_width=True):
            st.session_state.html_code = "<h1>Start Fresh</h1>"; st.session_state.css_code = ""; st.session_state.js_code = ""

    st.divider()

    # --- MAIN ---
    left, right = st.columns([1.5, 1])

    with left:
        tab1, tab2, tab3 = st.tabs(["index.html", "style.css", "script.js"])
        with tab1:
            st.session_state.html_code = st.text_area("h", value=st.session_state.html_code, height=450, label_visibility="collapsed", key="h_final")
        with tab2:
            st.session_state.css_code = st.text_area("c", value=st.session_state.css_code, height=450, label_visibility="collapsed", key="c_final")
        with tab3:
            st.session_state.js_code = st.text_area("j", value=st.session_state.js_code, height=450, label_visibility="collapsed", key="j_final")

        # --- 2. CONSOLE FUNCTION ---
        with st.expander("Console / Output", expanded=True):
            st.code(st.session_state.console_logs, language="javascript")
            st.caption(f"Age: {age} | Language: {lang} | Status: Live")

    with right:
        # --- DEVICE SWITCHER ---
        d1, d2, d3, d4 = st.columns([3, 1, 1, 1])
        with d1: st.markdown("**🟢Live Preview**")
        with d2:
            if st.button("🖥️", key="d1"): st.session_state.preview_device = "desktop"
        with d3:
            if st.button("📱", key="d2"): st.session_state.preview_device = "mobile"
        with d4:
            if st.button("🔲", key="d3"): st.session_state.preview_device = "tablet"

        device = st.session_state.preview_device
        if device == "mobile":
            h, style = 650, "max-width:390px; margin:auto; border:12px solid #111; border-radius:30px; overflow:hidden; box-shadow:0 10px 30px rgba(0,0,0,0.3);"
        elif device == "tablet":
            h, style = 650, "max-width:600px; margin:auto; border:8px solid #222; border-radius:16px; overflow:hidden;"
        else:
            h, style = 700, "width:100%; border:1px solid #30363d; border-radius:12px; overflow:hidden;"

        final_html = f"""<div style="{style}"><style>{st.session_state.css_code}</style>{st.session_state.html_code}<script>try{{{st.session_state.js_code}}}catch(e){{document.body.innerHTML+='<div style=\\'color:red;padding:10px\\'>Error: '+e.message+'</div>'}}</script></div>"""
        components.html(final_html, height=h, scrolling=True)

        # --- 3. QR CODE FOR MOBILE TESTING ---
        st.markdown("---")
        st.markdown("**📱 Mobile me Test Karo (Only for Learning)**")
        try:
            import qrcode
            from io import BytesIO
            qr_data = "https://clyxesschat.streamlit.app/"  # Yahan apna app link daal dena
            qr = qrcode.make(qr_data)
            buf = BytesIO()
            qr.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            st.markdown(f'<img src="data:image/png;base64,{b64}" width="120" style="border-radius:8px;"/><p style="font-size:12px;">Scan karke isi lab ko phone me kholo aur 📱 button se test karo.</p>', unsafe_allow_html=True)
        except:
            st.info("QR ke liye `pip install qrcode` karna padega. Abhi baccha link ko direct phone me khol ke test kar sakta hai.")
            st.code("pip install qrcode[pil]", language="bash")

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
    c1, c2, c3 = st.columns(3)
    with c1:
        homework_age = st.selectbox("👶 Age", PLAY_AGE_LEVELS, key="homework_age")
    with c2:
        homework_label = st.selectbox("🌐 Language", list(PLAY_LANGUAGES.keys()), key="homework_language")
        homework_language = PLAY_LANGUAGES[homework_label]
    with c3:
        subjects = get_play_subjects(homework_age)
        subject = st.selectbox("📚 Subject", subjects, key="homework_subject")

    st.caption(f"Homework will be generated for {homework_age} in {homework_label}.")
    if st.button("Generate Test", type="primary", use_container_width=True):
        st.session_state.homework_questions = generate_ai_questions(
            client, homework_age, homework_language, subject, 5
        )
        st.session_state.homework_answers = {}
        st.session_state.homework_result = None

    qs = st.session_state.get("homework_questions", [])
    if qs:
        for i, q in enumerate(qs):
            st.session_state.homework_answers[i] = st.radio(
                q["question"], q["options"], key=f"hw_{i}"
            )
        if st.button("Submit Test", use_container_width=True):
            score = sum(
                st.session_state.homework_answers.get(i) == q["answer"]
                for i, q in enumerate(qs)
            )
            st.session_state.homework_result = f"{score}/{len(qs)}"
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
        "🖥️ Coding Lab",  
        "🖥️ Learn AI", 
        "🖥️ Physics Lab", 
        "🖥️ Data Science Lab", 
        "🖥️ Math Lab", 
        "🖥️ Learn Finance",
        "🔐 Login / Sign Up"
    ])
    st.markdown("---")
    if st.button("+ New Chat", use_container_width=True):
        st.session_state.messages=[]
        st.session_state.session_id=str(uuid.uuid4())
        st.session_state.school_messages=[]
        st.session_state.school_session_id=str(uuid.uuid4())
        st.rerun()
    st.caption("🇮🇳 India live time: "+get_india_datetime_context().replace("Current India date: ",""))

# ---- routes: one unique screen per feature ----
if mode == "🔐 Login / Sign Up":
    render_login_signup(); st.stop()
if mode == "👨‍👩‍👦 Parent Dashboard": 
    render_parent_dashboard(); st.stop() 
if "Coding Lab" in mode:
    render_coding_lab(); st.stop()
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

# ============================================================
# NORMAL CHAT / CREATIVE LAB — SEPARATE CHAT HISTORIES
# ============================================================
def _explicit_image_request(text):
    low = text.lower().strip()
    phrases = [
        "generate image", "create image", "make an image", "draw an image",
        "generate a picture", "create a picture", "make a picture",
        "image banao", "image bana", "photo banao", "picture banao",
        "poster banao", "चित्र बनाओ", "तस्वीर बनाओ", "फोटो बनाओ"
    ]
    return any(x in low for x in phrases)

def _render_chat_history(messages):
    for message in messages:
        with st.chat_message(message["role"]):
            if "image_url" in message:
                st.markdown('<div class="media-card">', unsafe_allow_html=True)
                st.image(message["image_url"], caption=message.get("image_caption", ""), width=420)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown(message["content"])

def _chat_voice_input(key):
    if not mic_recorder:
        return ""
    audio = mic_recorder(
        start_prompt="🎙️",
        stop_prompt="⏹️",
        key=key
    )
    if audio:
        return transcribe_audio_with_groq(client, audio.get("bytes", b""))
    return ""

def render_normal_chat():
   
    _render_chat_history(st.session_state.messages)

    voice_prompt = _chat_voice_input("normal_chat_mic")
    prompt = st.chat_input("Search / ask ClyxessChat AI…", key="normal_chat_input")
    if not prompt and voice_prompt:
        prompt = voice_prompt

    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f'<div class="user-bubble">{prompt}</div>', unsafe_allow_html=True)

    if _explicit_image_request(prompt):
        with st.chat_message("assistant"):
            with st.spinner("🎨 Image bana raha hu..."):
                img_data, source = generate_image_url(prompt, False, "Normal", "1:1")
            st.markdown('<div class="media-card">', unsafe_allow_html=True)
            st.image(img_data, width=420, caption="Generated image")
            st.markdown('</div>', unsafe_allow_html=True)
            st.caption(f"Source: {source}")
        st.session_state.messages.append({
            "role": "assistant", "image_url": img_data,
            "image_caption": prompt, "content": "Generated image"
        })
        save_current_chat_cloud()
        st.rerun()

    search_context, sources = search_tavily(prompt)
    system = NORMAL_SYSTEM_PROMPT + "\nLIVE INDIA CLOCK: " + get_india_datetime_context()
    if search_context:
        system += "\nLIVE WEB INFO:\n" + search_context

    with st.chat_message("assistant"):
        completion, used_model = get_groq_response(
            client, st.session_state.messages, system, ""
        )
        if completion is None:
            st.error("AI response नहीं आ पाया. Please try again.")
            return
        response = completion.choices[0].message.content
        st.markdown(response)
        if sources:
            st.caption("Sources:\n" + sources)
        st.caption(f"Model: {used_model or 'fallback'}")

    st.session_state.messages.append({"role": "assistant", "content": response})
    save_current_chat_cloud()
    st.rerun()

def render_school_chat():
    st.title("🚀 Creative Lab — School Mode")
    st.caption("Age and language control the AI. School Mode has its own separate chat history.")

    c1, c2 = st.columns(2)
    with c1:
        age_options = ["1-2 Yrs", "3-4 Yrs", "5-6 Yrs", "6-8 Yrs", "8-10 Yrs", "10-11 Yrs", "11+ Yrs"]
        school_age = st.selectbox(
            "🎒 Age Group", age_options,
            index=age_options.index(st.session_state.get("school_age", "1-2 Yrs")),
            key="school_age_selector"
        )
    with c2:
        labels = list(PLAY_LANGUAGES.keys())
        current_label = next((n for n, c in PLAY_LANGUAGES.items() if c == st.session_state.get("school_language", "hi")), labels[0])
        school_label = st.selectbox(
            "🌐 Language", labels,
            index=labels.index(current_label),
            key="school_language_selector"
        )

    st.session_state.school_age = school_age
    st.session_state.school_language = PLAY_LANGUAGES[school_label]

    _render_chat_history(st.session_state.school_messages)

    voice_prompt = _chat_voice_input("school_chat_mic")
    prompt = st.chat_input("Ask School Mode…", key="school_chat_input")
    if not prompt and voice_prompt:
        prompt = voice_prompt

    if not prompt:
        return

    messages = st.session_state.school_messages
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f'<div class="user-bubble">{prompt}</div>', unsafe_allow_html=True)

    if _explicit_image_request(prompt):
        with st.chat_message("assistant"):
            with st.spinner("🎨 Age-appropriate image bana raha hu..."):
                img_data, source = generate_image_url(prompt, True, school_age, "1:1")
            st.markdown('<div class="media-card">', unsafe_allow_html=True)
            st.image(img_data, width=420, caption="Generated image")
            st.markdown('</div>', unsafe_allow_html=True)
            st.caption(f"Source: {source}")
        messages.append({
            "role": "assistant", "image_url": img_data,
            "image_caption": prompt, "content": "Generated image"
        })
        st.rerun()

    language_name = language_display_name(st.session_state.school_language)
    system = get_school_system_prompt(school_age)
    system += f"\nSELECTED LANGUAGE: {language_name} ({st.session_state.school_language}). Reply ONLY in this language."
    system += "\nUse the previous messages in this School Mode conversation as context. Never use Normal Chat history."
    search_context, sources = search_tavily(prompt)
    if search_context:
        system += "\nLIVE WEB INFO:\n" + search_context

    with st.chat_message("assistant"):
        completion, used_model = get_groq_response(client, messages, system, "")
        if completion is None:
            st.error("AI response नहीं आ पाया. Please try again.")
            return
        response = completion.choices[0].message.content
        st.markdown(response)
        if sources:
            st.caption("Sources:\n" + sources)
        st.caption(f"Age: {school_age} | Language: {language_name} | Model: {used_model or 'fallback'}")

    messages.append({"role": "assistant", "content": response})
    st.rerun()

if mode == "Normal Chat":
    render_normal_chat()
    st.stop()

if mode == "Creative Lab (School Mode)":
    render_school_chat()
    st.stop()
