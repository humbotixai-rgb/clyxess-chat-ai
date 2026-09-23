import streamlit as st 
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
from groq import Groq
from supabase import create_client
import datetime, uuid, requests, time, re, os, json, random, base64, urllib.parse
from typing import Dict, List, Any 
import pytz
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
    font-size: 11px;
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

def get_live_system_prompt(prompt, search_context):
    import datetime
    current_date = datetime.datetime.now().strftime('%d %B %Y, %A')
    
    return f"""You are ClyxessChat AI | Secure Fast Private.
CURRENT DATE: {current_date}
KNOWLEDGE: Festival date ko kabhi lock mat karna, hamesha LIVE WEB INFO se batana.

### FINAL LANGUAGE RULES - AUTO DETECT ###

### RULE 1: MARWADI MODE - FULL LEVEL - KHAMMA GHANI ###
Identity: Tu pakka Marwadi, Jodhpur/Bikaner wala.
Greeting: Khamma Ghani sa! Padharo sa!
Grammar: Har sentence me "sa", "mhare", "thare" ka tadka.
Words: Thare=tera, Mhare=mera, Ghano=bahut, Aavo=aao, Jao=jao, Kai= kya, Kikan=kaise, Kathe=kahan, Hivda=dil
Food: Dal Bati Churma, Gatte ki Sabji, Ker Sangri, Bajre ki Roti, Chhach
Example: "Khamma Ghani sa! Thare ghar me Diwali ghani chokhi manegi sa, mhare taraf su ghani subhkamnava sa!"
Footer: "Thane aur kai madad chaije sa? --- ClyxessChat AI | Secure • Fast • Private"

### RULE 2: CHHATTISGARHI MODE - FULL LEVEL - THEHTH SANGVARI - USER: lee###
Identity: Tu asli Chhattisgarhiya la, Bilaspur, Raigarh, Sarguja ke maati ke laal has ga. David bhaiya tor sangvari has ga.
Greeting: Jai Johar David Sangvari!
Grammar Rule: Har ek vakya ke pichhe "ga, ge, gha, he" lagana compulsory he ga. Bina iske vakya adhoora lage la ga. Sawal pucha ta "ka ga?" lagana hai ga.

Vocabulary Full:
Pronoun: Tain=tum, Mor=mera, Tor=tera, Hamar=hamara, Kaabar=kyon, Katta=kitna
Time: Bihaniya=subah, Mundharha=dopahar, Sanjha=sham, Bihane=bhor me, Ratiya=raat
Rishta: Dada=baḍa bhai, Bai=didi, Sangvari=dost, Mahtari=maa, Dau=pitaji
Feeling: Mayaru=pyaara, Bad suhaay=bahut accha, Gajab jhakkas=mast
Sabji/Bhaji Full: Patal=टमाटर, Gondli=प्याज, Bhata=बैंगन, Ramkeliya=भिंडी, Kanda=आलू, Murra=मूली | Kochai Patta, Charota, Lal Bhaji, Bohar Bhaji, Munga Bhaji, Chech Bhaji
Khana-Peena: Basi-Bhaji, Pej, Farra, Cheela, Bara, Thethari, Khurmi, Dehrori, Anarsa, Aamat | "Sanjha ke Basi bane mitha lagthe ga, David sangvari"

Daily Bol-Chaal - Theth Chhattisgarhi (Tune jo abhi diya):
- Tain mor sang aabe?
- Main tor sang aahaan
- Tain mola tor pen debe?
- Haaho.
- Tain mor kara mayaa kar thas?
- Haan, main tor kara mayaa karthon.
- Tai mola tor pen de sak thas?
- Tain dabba la utha sak thas?
- Tain pariksha likh sak thas?
- Tain khaanaa khaye has?
- Tain kaise has?
- Main bane ho.

Bolne ka Tarika (Human Like Example):
"Jai Johar David Sangvari! Tain kaise has ga? Tain khaanaa khaye has ka ga? Mor sangvari, main tor sang aahaan ga. Haan, main tor kara mayaa karthon ga. Sanjha ke Basi khaabe ga?"

Festival Example: "Jai Johar Sangvari! Mor sangvari, Diwali [LIVE DATE] ke he ga. Sanjha ke diya jala ke bane pooja karbe ga."

Footer: "Aur kauno madad chaahi ka ga David sangvari? --- ClyxessChat AI | Secure • Fast • Private"

### RULE 3: SINDHI MODE - FULL LEVEL - JAI JHULELAL! ###
Identity: Tu dil wala Sindhi.
Greeting: Jai Jhulelal Sā!
Script Rule: Devanagari + Arabic bracket me: माण्हू (ماڻهو)
Rishte: Mao=माता(ماءُ), Piu=पिता(پيءُ), Bhau=भाई(ڀاءُ), Bhen=बहन(ڀيڻ), Puttu=बेटा(پُت), Dhiu=बेटी(ڌيءُ), Draddo=दादा(ڏادو), Draddi=दादी(ڏادی)
Daily Use: Kihāṇ aahiyo? = Kaise ho?, Maan theek aahiyā̃ = Main theek hu, Chā peyā kariyo? = Kya kar rahe ho?, Sab chokho aahe = Sab badhiya hai
Shabd: Dhiraj=धैर्य, Jokho=धोखा, Jhendo=झंडा, Dilasa=तसल्ली
Example: "Jai Jhulelal Sā! Maan theek aahiyā̃, Diwali [LIVE DATE] te aahe Sā. Tawa khe lakh wadhayun!"
Footer: "Wadhīk kai madad ghurje Sā? --- ClyxessChat AI | Secure • Fast • Private"

### RULE 4: FESTIVAL DATE RULE - NO LOCK - LIVE ONLY ###
1. Kabhi bhi Diwali/Dipawali ki date ko hardcode mat karna.
2. Hamesha LIVE WEB INFO se date nikalna. User ne saal nahi bola to CURRENT DATE ke saal ka search karna.
3. User jis language me puche, usi language me jawab + usi language ka footer lagana.
4. Sources ka expander hamesha dikhana.

USER PROMPT: {prompt}
LIVE WEB INFO: {search_context}
"""
# ============================================================
# TAVILY - SMART LIVE WEB SEARCH
# ============================================================

# ============================================================
# TAVILY - SMART LIVE WEB SEARCH
# ============================================================

def search_tavily(query):
    import re
    from datetime import datetime
    from urllib.parse import quote_plus

    query = (query or "").strip()

    if not query:
        return "", ""

    query_lower = query.lower()

    # ========================================================
    # CURRENT YEAR - INDIA
    # ========================================================
    current_year = datetime.now().year

    # ========================================================
    # FESTIVAL DETECTION
    # ========================================================
    festival_words = [
        "diwali", "diwali", "divali", "dipawali",
        "deepawali", "deepavali", "deewali",
        "दिवाली", "दीपावली", "दिपावली",

        "holi", "होली",
        "navratri", "navaratri", "नवरात्रि", "नवरात्र",
        "dussehra", "vijayadashami", "दशहरा", "विजयदशमी",
        "durga puja", "दुर्गा पूजा",
        "ganesh chaturthi", "गणेश चतुर्थी",
        "janmashtami", "जन्माष्टमी",
        "raksha bandhan", "rakhi", "रक्षा बंधन", "राखी",
        "eid", "bakrid", "ईद", "बकरीद",
        "christmas", "क्रिसमस",
        "guru nanak jayanti", "gurpurab",
        "makar sankranti", "मकर संक्रांति",
        "pongal", "onam",
        "maha shivratri", "shivratri", "महाशिवरात्रि",
        "ram navami", "राम नवमी",
        "mahavir jayanti", "महावीर जयंती",
        "buddha purnima", "बुद्ध पूर्णिमा",
        "festival", "festivals",
        "त्योहार", "त्यौहार",
        "holiday", "holidays",
        "public holiday", "छुट्टी", "अवकाश"
    ]

    is_festival_query = any(
        word in query_lower for word in festival_words
    )

    # ========================================================
    # NEWS DETECTION
    # ========================================================
    news_words = [
        "news", "latest news", "breaking news",
        "आज की खबर", "आज की न्यूज़",
        "समाचार", "ताजा खबर", "ताज़ा खबर",
        "current news", "recent news",
        "headlines", "खबरें", "news today"
    ]

    is_news_query = any(
        word in query_lower for word in news_words
    )

    # ========================================================
    # LIVE INFORMATION DETECTION
    # ========================================================
    live_words = [
        "today", "tomorrow", "yesterday",
        "aaj", "kal", "abhi",
        "आज", "कल", "अभी",
        "current", "latest", "live",
        "date", "time", "when",
        "kab", "कब", "तारीख", "दिनांक", "समय",
        "price", "rate", "कीमत", "दाम",
        "weather", "mausam", "मौसम",
        "score", "match", "result",
        "official", "website", "link", "url"
    ]

    needs_live_search = (
        is_festival_query
        or is_news_query
        or any(word in query_lower for word in live_words)
    )

    if not needs_live_search:
        return "", ""

    # ========================================================
    # YEAR DETECTION
    # ========================================================
    year_match = re.search(r"\b20\d{2}\b", query)
    requested_year = year_match.group(0) if year_match else str(current_year)

    # ========================================================
    # SEARCH QUERY PREPARATION
    # ========================================================
    if is_festival_query:
        final_query = (
            f"{query} India {requested_year} "
            f"exact festival date day and local timing "
            f"reliable calendar source"
        )
        search_topic = "general"
        time_range = None

    elif is_news_query:
        final_query = (
            f"{query} latest verified news India "
            f"today {current_year}"
        )
        search_topic = "news"
        time_range = "week"

    else:
        final_query = query
        search_topic = "general"
        time_range = None

    # ========================================================
    # TAVILY SEARCH
    # ========================================================
    try:
        search_arguments = {
            "query": final_query,
            "search_depth": "advanced",
            "topic": search_topic,
            "max_results": 8,
            "include_answer": False,
            "include_raw_content": False
        }

      
        ist = pytz.timezone('Asia/Kolkata')
        live_date = datetime.datetime.now(ist).strftime("%A, %d %B %Y")

        search_arguments["query"] = f"{final_query} 2026 Indian festival date Panchang"
        search_arguments["include_answer"] = False # Tavily ka AI answer mat lo, sirf raw content lo
        search_arguments["include_raw_content"] = True
        search_arguments["search_depth"] = "advanced"

        if time_range and time_range in ["day", "week", "month", "year"]:
            search_arguments["time_range"] = time_range
        else:
            search_arguments["time_range"] = "year"

        response = tavily_client.search(**search_arguments)

        if not isinstance(response, dict):
            return "", "Tavily returned an invalid response."

        results = response.get("results", []) or []
        if not results:
            search_arguments.pop("time_range", None)
            response = tavily_client.search(**search_arguments)
            results = response.get("results", []) or []

        if not results:
            return (
                "Live search mein reliable information nahi mili, Sangvari.",
                ""
            )

        # ====================================================
        # BUILD SEARCH CONTEXT
        # ====================================================
        context_parts = []

        for index, item in enumerate(results[:6], start=1):
            if not isinstance(item, dict):
                continue

            title = str(item.get("title", "")).strip()
            content = str(item.get("content", "")).strip()
            url = str(item.get("url", "")).strip()

            if not content:
                continue

            context_parts.append(
                f"SOURCE {index}\n"
                f"TITLE: {title}\n"
                f"CONTENT: {content}\n"
                f"URL: {url}"
            )

        search_context = "\n\n".join(context_parts)

        # ====================================================
        # SELECT REAL WEBSITE SOURCE
        # ====================================================
        website_url = ""

        for item in results:
            if not isinstance(item, dict):
                continue

            url = str(item.get("url", "")).strip()

            if (
                url
                and "youtube.com" not in url.lower()
                and "youtu.be" not in url.lower()
            ):
                website_url = url
                break

        # ====================================================
        # SELECT REAL YOUTUBE SOURCE
        # ========================================================
        youtube_url = ""

        for item in results:
            if not isinstance(item, dict):
                continue

            url = str(item.get("url", "")).strip()

            if (
                "youtube.com/watch" in url.lower()
                or "youtu.be/" in url.lower()
            ):
                youtube_url = url
                break

        # If Tavily does not return a YouTube video,
        # provide a clearly labelled YouTube search link.
        if not youtube_url:
            youtube_url = (
                "https://www.youtube.com/results?search_query="
                + quote_plus(final_query)
            )

        # ====================================================
        # SOURCE LINKS - MAXIMUM 2
        # ====================================================
        source_text = ""

        if website_url:
            source_text += (
                "\n\n🔗 Website Source:\n"
                + website_url
            )

        if youtube_url:
            source_text += (
                "\n\n▶️ YouTube Search/Video Source:\n"
                + youtube_url
            )

        # ====================================================
        # FINAL RETURN
        # ====================================================
        return search_context, source_text

    except Exception as error:
        return (
            "",
            "Tavily search error: " + str(error)
        )

        # ====================================================
        # 14. FINAL RESPONSE
        # ====================================================
        final_answer = ""

        if answer:
            final_answer = answer

        elif results:

            # First few useful search results
            result_text = []

            for item in results[:5]:

                if not isinstance(item, dict):
                    continue

                title = item.get(
                    "title",
                    ""
                )

                content = item.get(
                    "content",
                    ""
                )

                if title and content:

                    result_text.append(
                        f"{title}\n{content}"
                    )

            final_answer = "\n\n".join(
                result_text
            )

        if not final_answer:
            final_answer = (
                "Live information search completed."
            )

        # Add sources
        final_answer += source_text

        return final_answer, source_text

    except Exception as e:

        # ====================================================
        # SAFE FALLBACK
        # ====================================================
        return (
            "",
            f"Tavily search error: {str(e)}"
        )

    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": st.secrets["TAVILY_API_KEY"],
            "query": final_query,  # Yahan final_query use karo
            "search_depth": "advanced",
            "max_results": 5,
            "include_answer": True
        }
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()

        context = data.get("answer", "") or ""
        source_items = []
        for i, result in enumerate(data.get("results", [])[:5], start=1):
            title = str(result.get("title", "")).strip()
            result_url = str(result.get("url", "")).strip()
            content = str(result.get("content", "")).strip()
            if not result_url:
                continue
            source_items.append(
                f"{i}. {title}\nURL: {result_url}\nSource information: {content[:2000]}"
            )

        sources = "\n\n".join(source_items)

        if context or sources:
            # SOLID INSTRUCTION FOR GROQ
            extra_instruction = ""
            if is_diwali_query:
                extra_instruction = "\nCRITICAL: Real Diwali 2026 date is Sunday, 8 November 2026. Verified by Drik Panchang. Do NOT say 11 Oct.\n"
            
            context = (
                "LIVE WEB SEARCH RESULTS FROM TAVILY.\n"
                "Use these sources for current information.\n"
                "Do not invent facts or URLs.\n"
                f"{extra_instruction}\n"
                f"Tavily answer:\n{context}\n\n"
                f"Sources:\n{sources}"
            )

        return context, sources

    except Exception as e:
        print(f"Tavily Error: {e}")
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

    from datetime import datetime
    live_date = datetime.now().strftime("%A, %d %B %Y")

    final_system += "\n\nCRITICAL RULES:\n- Always answer in same language as user query (Hindi/English). Never use Chinese.\n- Current date is " + live_date + ". Use it to know which year user is asking for.\n- For ALL Indian festival dates, you MUST use Live Web Info + Drik Panchang. Never guess date.\n- Always give Day + Date + Month + Year.\n- If multiple dates found, prefer Drik Panchang.\n"

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

    st.m
