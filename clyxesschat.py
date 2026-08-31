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


st.set_page_config(
    page_title="ClyxessChat AI",
    page_icon="💬",
    layout="wide"
)


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


GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b"
]

QUESTIONS_PER_LEVEL = 10


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
        "Colors", "Shapes", "Animals", "Sounds", "Basic Language", "Memory",
        "Communication", "Technology Awareness", "AI Awareness", "Money Basics", "Safe Internet"
    ],
    "3–4 Years": [
        "Numbers", "Language", "Shapes", "Storytelling", "Communication", "Logic",
        "Money Basics", "Technology Awareness", "AI Awareness", "Safe Internet", "Problem Solving"
    ],
    "5–6 Years": [
        "Maths", "Science Basics", "Language", "Reading", "Logic", "Creativity",
        "Communication", "Money Basics", "Technology Basics", "AI Introduction", "Safe Internet", "Problem Solving"
    ],
    "6–8 Years": [
        "Maths", "Science", "English", "General Knowledge", "Logic", "Communication",
        "Technology Basics", "Coding Basics", "AI Introduction", "Financial Literacy", "Cyber Safety", "Critical Thinking", "Problem Solving"
    ],
    "8–10 Years": [
        "Maths", "Science", "English", "Coding Basics", "AI Introduction", "Financial Literacy",
        "Communication", "Technology Basics", "Cyber Safety", "Critical Thinking", "Problem Solving"
    ],
    "10–11 Years": [
        "Advanced Maths", "Science", "Technology", "AI Literacy", "Coding", "Financial Literacy",
        "Communication", "Cyber Safety", "Critical Thinking", "Problem Solving", "Entrepreneurship"
    ],
    "11+ Years": [
        "AI & Technology", "Coding", "Financial Literacy", "Cyber Safety", "Communication",
        "Entrepreneurship", "Critical Thinking", "Problem Solving", "Advanced Maths", "Science"
    ]
}

# Age-specific fallback questions for the subjects that must never fall back to toddler-level content.
# These are used when an AI provider is unavailable or returns invalid JSON.
AGE_SUBJECT_FALLBACK = {
    "1–2 Years": {
        "Communication": [("Someone says hello. What can you say?", ["Hello", "Go", "Sleep", "No"], "Hello")],
        "Technology Awareness": [("Which one is a phone?", ["📱", "🍎", "🐶", "⚽"], "📱")],
        "AI Awareness": [("Which picture looks like a computer helper?", ["🤖", "🍌", "🐟", "🌳"], "🤖")],
        "Money Basics": [("Which one is money?", ["🪙", "🍎", "🚗", "🐱"], "🪙")],
        "Safe Internet": [("Should a small child use a phone with a trusted grown-up?", ["Yes", "No", "Always alone", "Never"], "Yes")],
        "Critical Thinking": [("Which is bigger?", ["🐘", "🐜", "🍎", "⭐"], "🐘")],
        "Problem Solving": [("Your toy is under a box. What can you do?", ["Ask for help", "Eat it", "Throw the box away", "Ignore it"], "Ask for help")],
    },
    "3–4 Years": {
        "Communication": [("A friend gives you a toy. What can you say?", ["Thank you", "Go away", "Stop", "Nothing"], "Thank you")],
        "Technology Awareness": [("Which device can show a cartoon?", ["Tablet", "Spoon", "Shoe", "Cup"], "Tablet")],
        "AI Awareness": [("Which one looks like a robot helper?", ["🤖", "🍎", "🐟", "🌈"], "🤖")],
        "Money Basics": [("You have ₹10 and spend ₹4. How much is left?", ["₹4", "₹5", "₹6", "₹8"], "₹6")],
        "Safe Internet": [("Should you tell a stranger your name and home address online?", ["Yes", "No", "Maybe always", "Only at night"], "No")],
        "Critical Thinking": [("Which is the best clue that a claim may be wrong?", ["It has no reason", "It is colorful", "It is short", "It has an emoji"], "It has no reason")],
        "Problem Solving": [("You cannot reach a toy on a high shelf. What is safest?", ["Ask a grown-up", "Climb a window", "Jump", "Push furniture"], "Ask a grown-up")],
    },
    "5–6 Years": {
        "Communication": [("Which sentence is polite when asking for help?", ["Please help me.", "Give it now!", "You must do it.", "Go away."], "Please help me.")],
        "Technology Basics": [("Which device is mainly used to type letters?", ["Keyboard", "Speaker", "Camera", "Lamp"], "Keyboard")],
        "AI Introduction": [("What is AI designed to do in many applications?", ["Perform tasks using learned patterns", "Grow like a plant", "Cook every meal", "Become a human"], "Perform tasks using learned patterns")],
        "Money Basics": [("You have ₹50 and save ₹20. How much can you spend?", ["₹20", "₹30", "₹40", "₹50"], "₹30")],
        "Safe Internet": [("What should you keep private online?", ["Passwords", "Favorite color", "A cartoon title", "A school subject"], "Passwords")],
        "Critical Thinking": [("Before believing a surprising online story, what is a good first step?", ["Check another reliable source", "Share it", "Guess", "Ignore every fact"], "Check another reliable source")],
        "Problem Solving": [("You have two ways to finish a task. What should you do first?", ["Compare the choices", "Pick randomly", "Quit", "Hide the task"], "Compare the choices")],
    },
    "6–8 Years": {
        "Communication": [("Which message is best for resolving a disagreement?", ["Let's talk and find a fair solution.", "You are always wrong.", "I will shout.", "I will ignore you forever."], "Let's talk and find a fair solution.")],
        "Coding Basics": [("In a program, what is a loop useful for?", ["Repeating instructions", "Deleting the computer", "Charging a battery", "Printing money"], "Repeating instructions")],
        "AI Introduction": [("Why can an AI system make a mistake?", ["Its data or reasoning can be imperfect", "AI is always correct", "Computers cannot process data", "AI never uses data"], "Its data or reasoning can be imperfect")],
        "Financial Literacy": [("You have ₹200, save ₹75, and spend the rest. How much do you spend?", ["₹100", "₹125", "₹135", "₹175"], "₹125")],
        "Cyber Safety": [("A website asks for your password through a strange link. What should you do?", ["Do not enter it and verify the site", "Enter it quickly", "Share it with friends", "Turn off the screen"], "Do not enter it and verify the site")],
        "Critical Thinking": [("Two websites give different answers. What should you compare?", ["Evidence and source reliability", "Font color", "Number of emojis", "Page length only"], "Evidence and source reliability")],
        "Problem Solving": [("A science project fails. What is a useful next step?", ["Find the cause and test one change", "Give up", "Hide the result", "Blame someone"], "Find the cause and test one change")],
    },
    "8–10 Years": {
        "Communication": [("Which response shows active listening?", ["I understand your point; can you explain more?", "Stop talking.", "I don't care.", "You are wrong."], "I understand your point; can you explain more?")],
        "Coding Basics": [("What is a conditional statement used for?", ["Making a decision based on a condition", "Drawing every picture", "Charging hardware", "Deleting all code"], "Making a decision based on a condition")],
        "AI Introduction": [("What is a useful way to evaluate an AI answer?", ["Check facts and reasoning", "Assume it is always true", "Share private data", "Ignore the question"], "Check facts and reasoning")],
        "Financial Literacy": [("A ₹800 item is discounted by 15%. What is the discount?", ["₹80", "₹100", "₹120", "₹150"], "₹120")],
        "Cyber Safety": [("Which is a strong account-protection practice?", ["Use unique passwords and MFA", "Reuse one password everywhere", "Share passwords", "Disable security updates"], "Use unique passwords and MFA")],
        "Critical Thinking": [("Which evidence is strongest for a scientific claim?", ["Repeated results from a reliable method", "A random comment", "A rumor", "A catchy headline"], "Repeated results from a reliable method")],
        "Problem Solving": [("A solution works but uses too many resources. What should you do?", ["Measure alternatives and optimize it", "Never change it", "Delete the project", "Guess"], "Measure alternatives and optimize it")],
    },
    "10–11 Years": {
        "Communication": [("What is the best way to give constructive feedback?", ["Describe the issue and suggest a specific improvement", "Insult the person", "Say nothing useful", "Share it publicly"], "Describe the issue and suggest a specific improvement")],
        "Coding": [("Why is a function useful in programming?", ["It packages reusable behavior", "It replaces the operating system", "It stores electricity", "It removes all bugs automatically"], "It packages reusable behavior")],
        "AI Literacy": [("Why should an AI-generated claim be verified?", ["Models can produce inaccurate or unsupported information", "AI cannot process language", "AI always cites sources", "Verification is never useful"], "Models can produce inaccurate or unsupported information")],
        "Financial Literacy": [("If ₹5,000 earns 8% simple interest for one year, what is the interest?", ["₹200", "₹300", "₹400", "₹500"], "₹400")],
        "Cyber Safety": [("What is phishing?", ["A deceptive attempt to steal information", "A type of backup", "A faster Wi-Fi mode", "A coding language"], "A deceptive attempt to steal information")],
        "Critical Thinking": [("Which question best tests a strong claim?", ["What evidence would prove or disprove it?", "Who posted it first?", "Is it popular?", "Does it sound confident?"], "What evidence would prove or disprove it?")],
        "Problem Solving": [("When a problem has constraints, what should you do before choosing a solution?", ["List constraints and success criteria", "Ignore constraints", "Choose randomly", "Start over repeatedly"], "List constraints and success criteria")],
    },
    "11+ Years": {
        "Communication": [("Which communication strategy is strongest in a technical disagreement?", ["Separate claims from evidence and address the evidence", "Attack the person", "Use louder language", "Avoid all questions"], "Separate claims from evidence and address the evidence")],
        "Coding": [("What is the main benefit of algorithmic complexity analysis?", ["It estimates how resource use scales with input size", "It guarantees zero bugs", "It designs UI colors", "It replaces testing"], "It estimates how resource use scales with input size")],
        "AI & Technology": [("What is model bias in an AI system?", ["Systematic differences in outputs caused by data or design", "A faster processor", "A screen defect", "A type of encryption"], "Systematic differences in outputs caused by data or design")],
        "Financial Literacy": [("Why can compound interest grow faster than simple interest over long periods?", ["Interest can earn additional interest", "The principal disappears", "Taxes become zero", "Banks stop calculating interest"], "Interest can earn additional interest")],
        "Cyber Safety": [("What is the principle of least privilege?", ["Give an account only the access it needs", "Give every user admin rights", "Share credentials", "Disable authentication"], "Give an account only the access it needs")],
        "Critical Thinking": [("Which approach reduces confirmation bias?", ["Actively seek credible evidence that could challenge your view", "Only read supporting sources", "Avoid data", "Choose the most popular opinion"], "Actively seek credible evidence that could challenge your view")],
        "Problem Solving": [("For a complex problem, what is a strong first step?", ["Define the problem, constraints, and measurable goal", "Implement immediately", "Ignore edge cases", "Choose the hardest solution"], "Define the problem, constraints, and measurable goal")],
    }
}



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


DEFAULT_STATE = {
    "messages": [],
    "session_id": str(uuid.uuid4()),
    "age_group": "1-2 Yrs",
    "school_messages": [],
    "school_session_id": str(uuid.uuid4()),
    "school_language": "hi",
    "school_age": "1-2 Yrs",

    "play_age": PLAY_AGE_LEVELS[0],
    "play_language": "en",
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
    "play_best_scores": {},
    "play_config_key": None,
    "homework_questions": [],
    "homework_answers": {},
    "homework_result": None,
    "homework_config_key": None,
    "role_language": "en",
    "vision_language": "en",
    "play_game_type": None
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


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

AGE_FALLBACK = {
"1–2 Years":[("Which one is a circle?",["⬜","⭕","🔺","⭐"],"⭕"),("Which color is 🔴?",["Red","Blue","Green","Yellow"],"Red"),("Which animal says meow?",["Cat","Dog","Cow","Duck"],"Cat"),("How many apples? 🍎🍎",["1","2","3","4"],"2"),("Which shape has 3 sides?",["Circle","Square","Triangle","Oval"],"Triangle"),("Which is bigger?",["🐘","🐜","Same","Unknown"],"🐘"),("Which is a fruit?",["🍎","🚗","⚽","🐶"],"🍎"),("Which one is yellow?",["🔵","🟡","🔴","🟢"],"🟡"),("How many stars? ⭐⭐⭐",["1","2","3","4"],"3"),("Which is a bird?",["🐟","🐦","🐱","🐰"],"🐦")],
"3–4 Years":[("What comes after 3?",["2","4","5","1"],"4"),("What is 2 + 1?",["2","3","4","5"],"3"),("Which shape has 4 equal sides?",["Circle","Square","Triangle","Oval"],"Square"),("How many legs does a dog have?",["2","3","4","6"],"4"),("Which word starts with B?",["Ball","Cat","Dog","Sun"],"Ball"),("Which number is smallest?",["2","5","7","9"],"2"),("What comes next: 5, 6, ?",["4","7","8","9"],"7"),("What is used for writing?",["Pencil","Shoe","Cup","Ball"],"Pencil"),("Which can fly?",["Fish","Bird","Cow","Elephant"],"Bird"),("How many sides does a triangle have?",["2","3","4","5"],"3")],
"5–6 Years":[("What is 4 + 3?",["5","6","7","8"],"7"),("What is 10 - 4?",["4","5","6","7"],"6"),("What is 2 × 3?",["5","6","7","8"],"6"),("Which planet do we live on?",["Mars","Earth","Jupiter","Venus"],"Earth"),("Which organ helps us see?",["Ears","Eyes","Nose","Hands"],"Eyes"),("Which is a noun?",["Run","Happy","Book","Quickly"],"Book"),("Next: 10, 20, 30, ?",["35","40","45","50"],"40"),("Which is usually transparent?",["Glass","Wood","Stone","Metal"],"Glass"),("How many minutes in an hour?",["30","45","60","100"],"60"),("Which is living?",["Rock","Tree","Chair","Pencil"],"Tree")],
"6–8 Years":[("What is 7 × 4?",["24","28","32","36"],"28"),("What is 36 ÷ 6?",["5","6","7","8"],"6"),("Which gas do humans need?",["Oxygen","Helium","Hydrogen","Neon"],"Oxygen"),("Past tense of 'go'?",["Goed","Gone","Went","Going"],"Went"),("Which planet has famous rings?",["Mercury","Saturn","Earth","Mars"],"Saturn"),("What is 125 + 75?",["180","190","200","210"],"200"),("Which device types text?",["Keyboard","Monitor","Speaker","Router"],"Keyboard"),("A triangle has how many angles?",["2","3","4","5"],"3"),("Which is renewable energy?",["Coal","Solar","Petrol","Gas"],"Solar"),("₹50 - ₹20 = ?",["₹20","₹30","₹40","₹70"],"₹30")],
"8–10 Years":[("What is 15 × 6?",["80","90","100","110"],"90"),("What is 3/4 of 20?",["10","12","15","16"],"15"),("Which organ pumps blood?",["Lungs","Heart","Stomach","Kidney"],"Heart"),("What does CPU stand for?",["Central Processing Unit","Computer Power Unit","Central Program Utility","Control Processing User"],"Central Processing Unit"),("What is 2.5 + 1.75?",["3.25","4.25","4.50","5.25"],"4.25"),("Which is renewable?",["Sunlight","Coal","Petrol","Diesel"],"Sunlight"),("₹200 - ₹120 = ?",["₹60","₹70","₹80","₹90"],"₹80"),("Next: 3, 6, 12, 24, ?",["36","42","48","54"],"48"),("Which is strongest password?",["123456","password","R7!mQ2#z","myname"],"R7!mQ2#z"),("Square side 5 cm: perimeter?",["10 cm","15 cm","20 cm","25 cm"],"20 cm")],
"10–11 Years":[("Solve 3x + 5 = 20",["3","4","5","6"],"5"),("What is 25% of 240?",["40","50","60","80"],"60"),("Which force pulls objects to Earth?",["Friction","Gravity","Magnetism","Buoyancy"],"Gravity"),("What is an algorithm?",["Step-by-step procedure","Screen","Battery","Browser"],"Step-by-step procedure"),("What is 2³ + 4?",["8","10","12","16"],"12"),("Which fraction is greatest?",["1/4","1/2","2/3","3/8"],"2/3"),("Why update software?",["Security and fixes","Wallpaper","Delete internet","Never useful"],"Security and fixes"),("₹1,000 grows by 10% = ?",["₹1,010","₹1,050","₹1,100","₹1,200"],"₹1,100"),("Next: 2, 5, 10, 17, ?",["24","25","26","27"],"26"),("Best account protection?",["Share password","Use MFA","Reuse password","Turn off updates"],"Use MFA")],
"11+ Years":[("If f(x)=2x+3, f(5)=?",["10","11","13","15"],"13"),("Probability of a 6 on a fair die?",["1/2","1/4","1/6","1/8"],"1/6"),("Which structure follows FIFO?",["Stack","Queue","Tree","Graph"],"Queue"),("Phishing usually steals?",["Credentials","Brightness","Battery","Keys"],"Credentials"),("Derivative of x²?",["x","2x","x²","2"],"2x"),("Compound interest means interest on...",["Principal only","Principal plus accumulated interest","None","Fixed fee"],"Principal plus accumulated interest"),("Main purpose of version control?",["Track code changes","Increase screen","Replace DB","Charge users"],"Track code changes"),("99% uptime over 100 hours: downtime?",["0.1 h","1 h","5 h","10 h"],"1 h"),("Specific observations to general rule?",["Deductive","Inductive","Circular","Random"],"Inductive"),("Safest response to suspicious login link?",["Click","Verify source","Forward","Enter password"],"Verify source")]
}

def build_demo_questions(subject, age=None):
    age = age or PLAY_AGE_LEVELS[0]
    # Prefer an age + subject-specific fallback so an older learner never receives toddler content.
    subject_pool = AGE_SUBJECT_FALLBACK.get(age, {}).get(subject, [])
    # Second fallback is the global subject bank, never the wrong subject.
    bank_pool = []
    for item in QUESTION_BANK.get(subject, []):
        bank_pool.append((item["question"], item["options"], item["answer"]))
    general_pool = AGE_FALLBACK.get(age, AGE_FALLBACK["8–10 Years"])
    pool = list(subject_pool) + bank_pool + list(general_pool)
    result=[]
    seen=set()
    for q, opts, ans in pool:
        key=q.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        result.append({"question":q,"options":list(opts),"answer":ans,"explanation":f"Correct answer: {ans}."})
    random.shuffle(result)
    return result[:QUESTIONS_PER_LEVEL]

def clean_json_text(text):
    text = text.strip()

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

def generate_ai_questions(client, age, language, subject, count=10, game_type="Quiz Challenge"):
    language_name = next((name for name, code in PLAY_LANGUAGES.items() if code == language), "English")
    difficulty = {
        "1–2 Years": "Pre-school recognition: colors, shapes, animals, counting to 5; use very short sentences and simple visual/emoji choices.",
        "3–4 Years": "Early learning: counting, simple addition, shapes, vocabulary, patterns and basic reasoning.",
        "5–6 Years": "Primary foundation: simple arithmetic, basic science, reading/language and everyday concepts.",
        "6–8 Years": "Primary school: multiplication/division, basic science, grammar, technology and simple money/logic.",
        "8–10 Years": "Upper primary: multi-step arithmetic, fractions/decimals, science, coding basics, AI introduction and financial literacy.",
        "10–11 Years": "Advanced primary: algebra foundations, percentages, deeper science, coding, AI literacy, cyber safety and critical thinking.",
        "11+ Years": "Teen level: algebra, probability, programming, AI/technology, cybersecurity, finance, entrepreneurship and analytical reasoning."
    }.get(age, "Age-appropriate school learning.")

    prompt = f"""
You are the question engine for ClyxessChat AI Play & Learn.
Create exactly {count} educational multiple-choice questions.
AGE GROUP: {age}
SUBJECT: {subject}
GAME TYPE: {game_type}
SELECTED LANGUAGE: {language_name}
DIFFICULTY PROFILE: {difficulty}

HARD AGE RULE:
The age group is NOT cosmetic. The questions MUST materially change in vocabulary,
concept difficulty, numbers, reasoning depth and subject complexity for different ages.
Never reuse the same question, sequence, example or answer pattern from another age group.
For example, a simple counting question suitable for 3–4 must not appear for 10–11 or 11+.
For 1–2 use recognition and tiny quantities; for 11+ use genuinely advanced reasoning where
appropriate to the selected subject.

HARD SUBJECT RULE:
Every question must match the selected subject. For Homework, this rule is mandatory.
Never substitute a generic age question for a requested subject unless absolutely necessary; if
a fallback is needed, preserve the same subject and age difficulty. Do not return generic maths questions when
the subject is Coding, AI, Science, Financial Literacy, Communication, etc.

HARD UNIQUENESS RULE:
All {count} questions in this batch must be different from each other. Do not repeat a question
with changed numbers only. Make the concepts/examples varied.

LANGUAGE RULE:
Question text, all four options, answer and explanation MUST be entirely in {language_name}.
Never use Hinglish or mixed language unless English is selected.
For ages 1–4, never ask personal-experience questions such as what the child ate, owns, likes,
saw, did or remembers.
GAME DESIGN RULE: Adapt the question style to GAME TYPE. Keep it playable and varied, but
never lower the difficulty below the selected age. For older ages, include multi-step reasoning,
scenarios, trade-offs, algorithms, evidence evaluation, or calculations where the subject allows.

ANSWER RULE:
Each question has exactly four options and exactly one correct answer. The 'answer' field MUST
be an exact character-for-character copy of one option, not A/B/C/D.

Return ONLY valid JSON in this exact format:
[{{"question":"...","options":["...","...","...","..."],"answer":"...","explanation":"..."}}]
"""

    model_order = list(GROQ_MODELS)
    offset = (sum(ord(c) for c in f"{age}|{subject}|{language}") % len(model_order)) if model_order else 0
    model_order = model_order[offset:] + model_order[:offset]

    for model in model_order:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role":"user","content":prompt}],
                temperature=0.65,
                max_tokens=6000
            )
            parsed = json.loads(clean_json_text(completion.choices[0].message.content))
            valid=[]
            seen=set()
            for item in parsed if isinstance(parsed,list) else []:
                if not isinstance(item,dict):
                    continue
                q=str(item.get("question","")).strip()
                opts=[str(x).strip() for x in item.get("options",[]) if str(x).strip()]
                ans=str(item.get("answer","")).strip()
                exp=str(item.get("explanation","")).strip()
                key=re.sub(r"\s+", " ", q.lower())
                if not q or len(opts)!=4 or len(set(opts))!=4 or ans not in opts:
                    continue
                if key in seen:
                    continue
                if ("1–2" in age or "3–4" in age) and _personal_assumption_question(q):
                    continue
                seen.add(key)
                valid.append({"question":q,"options":opts,"answer":ans,"explanation":exp})
                if len(valid)==count:
                    break
            if len(valid)==count:
                return valid
        except Exception:
            continue

    return build_demo_questions(subject, age=age)[:count]


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

    game_types = {
        "1–2 Years": ["Picture Pick", "Memory Match", "Color & Shape Hunt"],
        "3–4 Years": ["Pattern Hunt", "Quick Choice", "Story Challenge"],
        "5–6 Years": ["Speed Maths", "Brain Quest", "Memory Challenge"],
        "6–8 Years": ["Brain Quest", "Logic Sprint", "Tech Challenge"],
        "8–10 Years": ["Logic Lab", "Coding Challenge", "Money Mission", "Quiz Challenge"],
        "10–11 Years": ["Challenge Mode", "Case Challenge", "Algorithm Quest", "Quiz Challenge"],
        "11+ Years": ["Advanced Challenge", "Scenario Lab", "Code & Logic", "Critical Thinking Duel"]
    }
    available_games = game_types.get(play_age, ["Quiz Challenge"])
    previous_game = st.session_state.get("play_game_type")
    game_index = available_games.index(previous_game) if previous_game in available_games else 0
    play_game_type = st.selectbox(
        "🎮 Game Type", available_games, index=game_index, key="play_game_type_selector"
    )

    st.session_state.play_age = play_age
    st.session_state.play_language = play_language
    st.session_state.play_subject = play_subject
    st.session_state.play_game_type = play_game_type

    new_config_key = f"{play_age}|{play_language}|{play_subject}|{play_game_type}"
    old_config_key = st.session_state.get("play_config_key")
    if old_config_key is not None and old_config_key != new_config_key:
        st.session_state.play_questions = []
        st.session_state.play_question_index = 0
        st.session_state.play_score = 0
        st.session_state.play_game_started = False
        st.session_state.play_answered = False
        st.session_state.play_last_correct = False
        st.session_state.play_last_explanation = ""
    st.session_state.play_config_key = new_config_key


    if not play_level_unlocked(play_age):

        st.error(
            f"🔒 {play_age} is locked."
        )

        st.info(
            "Complete the previous age level with 10/10 "
            "to unlock this level."
        )

        return


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


    if not st.session_state.play_game_started:

        st.markdown(
            '<div class="play-card">',
            unsafe_allow_html=True
        )

        st.subheader("🎯 Ready to Learn?")

        st.write(f"**Age:** {play_age}")
        st.write(f"**Subject:** {play_subject}")
        st.write(f"**Game:** {play_game_type}")
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
                    count=QUESTIONS_PER_LEVEL,
                    game_type=play_game_type
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
            st.session_state.play_config_key = f"{play_age}|{play_language}|{play_subject}|{play_game_type}"

            st.rerun()

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

        return


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


    progress = (question_index + 1) / QUESTIONS_PER_LEVEL

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

def analyze_image_with_groq(image_bytes, mime, question, selected_language="English"):
    if not client:
        return "Groq API key missing."
    try:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        completion = client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=[{"role":"user","content":[
                {"type":"text","text":f"STRICT LANGUAGE LOCK: Reply ONLY in {selected_language}. Do not use English or mixed language unless English is selected. {question}"},
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
    labels=list(PLAY_LANGUAGES.keys())
    default_idx=labels.index("🇬🇧 English")
    label=st.selectbox("🌐 Answer Language",labels,index=default_idx,key="vision_language_selector")
    selected_language=PLAY_LANGUAGES[label]
    question=st.text_input("What should AI explain?",value="Explain the image simply and solve any visible question.")
    if f:
        st.markdown('<div class="media-card">',unsafe_allow_html=True); st.image(f,width=480); st.markdown('</div>',unsafe_allow_html=True)
        if st.button("🧠 Analyze Image",type="primary",use_container_width=True):
            language_name=next((n.split(" ",1)[-1] for n,c in PLAY_LANGUAGES.items() if c==selected_language),"English")
            strict=f"Reply ONLY in {language_name}. Do not use English unless English is selected. Analyze this image and answer the user's request. {question}"
            st.write(analyze_image_with_groq(f.getvalue(),f.type,strict,language_name))

def render_roleplay():
    st.title("🎭 Peer Roleplay Modes")
    role=st.selectbox("Role",["Classmate","Teacher","Study Buddy","Interview Partner","Project Teammate"])
    labels=list(PLAY_LANGUAGES.keys())
    default_idx=labels.index("🇬🇧 English")
    label=st.selectbox("🌐 Language",labels,index=default_idx,key="role_language_selector")
    selected_language=PLAY_LANGUAGES[label]
    language_name=next((n.split(" ",1)[-1] for n,c in PLAY_LANGUAGE
