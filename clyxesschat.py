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
