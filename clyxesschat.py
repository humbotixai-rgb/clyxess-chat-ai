import streamlit as st
from groq import Groq
import datetime, uuid, requests, time, re
import random

st.set_page_config(page_title="ClyxessChat AI", layout="wide", initial_sidebar_state="expanded")

# --- CSS - CHATGPT Jaisa ---
st.markdown("""
<style>
.main {max-width: 850px; margin: auto;}
.header {position: sticky; top:0; background:#202123; padding:18px; border-bottom:1px solid #444; z-index:999; margin: -1rem -1rem 20px -1rem;}
.header h1 {color:white; font-size:22px; text-align:center; margin:0;}
.user-bubble {background:#D9FDD3; color:#111b21; padding:10px 14px; border-radius:18px; border-bottom-right-radius:4px; max-width:75%; margin-left:auto; margin-bottom:10px; text-align:right;}
.assistant-bubble {background:#2f2f2f; color:white; padding:12px 15px; border-radius:18px; border-bottom-left-radius:4px; max-width:85%; margin-bottom:10px;}
</style>
""", unsafe_allow_html=True)

# ============ 10 MODEL MAHA ULTRA FALLBACK ============
GROQ_MODELS = [
    "openai/gpt-oss-120b",              # 1. PRO MODE - CEO Brain, Reasoning King
    "openai/gpt-oss-20b",               # 2. PRO MINI - Fast CEO Brain
    "qwen/qwen3-27b",                   # 3. VISION MODE - Photo + Multilingual King 
    "qwen/qwen3-32b",                   # 4. VISION BIG - Backup Vision
    "llama-3.1-70b-versatile",          # 5. Main - Hindi + Smart - Rate limit कम है
    "deepseek-r1-distill-llama-70b",    # 6. Coding King
    "mixtral-8x7b-32768",               # 7. Long Chat - 32k context
    "gemma2-9b-it",                     # 8. Smart + Fast
    "llama-3.1-8b-instant",             # 9. Fast Backup
    "llama3-8b-8192"                    # 10. Super Fast Backup  
]
# --- IMAGE GEN ---
def generate_image_url(prompt):
    safe = requests.utils.quote(prompt[:150])
    return f"https://image.pollinations.ai/prompt/{safe}?width=1024&height=1024&nologo=true&seed={random.randint(1,99999)}"

# --- SEARCH ---
def search_tavily(query):
    keywords = ["news","mausam","weather","rate","price","score","today","kal","aaj","latest"]
    if not any(k in query.lower() for k in keywords): return "", ""
    try:
        url = "https://api.tavily.com/search"
        payload = {"api_key": st.secrets["TAVILY_API_KEY"], "query": query, "max_results": 3, "include_answer": True}
        r = requests.post(url, json=payload, timeout=10)
        data = r.json()
        ctx = data.get("answer","")
        src = "\n".join([f"{i+1}. [{x['title']}]({x['url']})" for i,x in enumerate(data.get("results",[])[:3])])
        return ctx, src
    except: return "", ""

# --- PROMPTS - FINAL MIX ---
NORMAL_SYSTEM_PROMPT = """
You are ClyxessChat AI, created by ClyxessChat AI Technology. You are Sangvari, a real human friend, not AI robot.

CORE RULE: REPLY ONLY IN SAME LANGUAGE AS USER. If user Hindi -> Hindi only. English -> English only. Chhattisgarhi -> Pure Chhattisgarhi (Tain, Tor, Ga, Jai Johar). Marwadi -> Pure Marwadi with 'sa' (Khamma Ghani sa). Sindhi -> Sindhi.

PERSONALITY: Friendly, calm, intelligent, like ChatGPT. Understand before answering.

RULE - CHHOTA JAWAB + HINT: Chhote sawal ka chhota jawab de. Bada lecture mat de. Saath me 1 hint de.
Example: Q: Python kya hai? A: Python ek easy coding language hai. Hint: Isse AI bante hain. Detail chahiye kya?

RULE - ENGLISH SIKHANA: Agar user bole "English sikhao", to Web Search MAT KARNA. Khud English teacher ban ja. Interactive.
User: I is go market -> You: Almost! Bol 'I am going to market'. Good try! What will you buy? Aise sikhate raho.

RULE - TEACHER: Har badi cheej ko part-by-part samjha. Code manga to chhote-chhote box me de, file-wise.

FOOTER: Last me ek line: Hindi me "Aur kuch help chahiye kya? --- ClyxessChat AI" | English me "Is there anything else I can help you with? --- ClyxessChat AI"
"""

def get_school_prompt(age):
    base = f"You are ClyxessChat AI - School Mode Teacher. Age: {age}. You are a teacher, not just chatbot. "
    if "1-2" in age or "3-4" in age:
        return base + "Age 1-4: You are Didi. Only rhymes, colors, emojis. Very short Hinglish. Eg: 'Dekho laal gubbara! Tap karo toh kya hoga?' No tough words. Play games: Color Guess, Sound Game."
    elif "5-6" in age or "6-8" in age:
        return base + "Age 5-8: Curiosity Builder Teacher. Use Story + Question method. Eg: 'Sher kho gaya, pehle kya kare?' Give hints, not direct answer. Games: Shape Puzzle, Story Building, Rhyme Maker."
    elif "10-11" in age:
        return base + "Age 7-10: Maker Teacher. Step-by-step DIY, Science experiment. Hint style Jugaad wala. Games: DIY Rocket, Math Puzzle, Logic Game. Give steps."
    else:
        return base + "Age 11+: Future Tech Teacher. Teach Coding Logic, App Idea, AI. Challenge with 2 small parts. Games: Code Puzzle, App Wireframe, Quiz. Be innovator."

def get_groq_response(client, messages, system_prompt, search_ctx=""):
    final_sys = system_prompt + (f"\nLive Info: {search_ctx}" if search_ctx else "")
    recent = messages[-6:]
    to_send = [{"role":"system","content":final_sys}] + recent
    for model in GROQ_MODELS:
        try:
            comp = client.chat.completions.create(model=model, messages=to_send, temperature=0.7, max_tokens=3000)
            return comp, model
        except: continue
    return None, None

# --- SESSION ---
if "messages" not in st.session_state: st.session_state.messages = []
if "session_id" not in st.session_state: st.session_state.session_id = str(uuid.uuid4())
if "age_group" not in st.session_state: st.session_state.age_group = "5-6 Yrs"

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- UI ---
st.markdown('<div class="header"><h1>💬 ClyxessChat AI</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.title("💬 ClyxessChat AI")
    mode = st.radio("Mode Chuniye", ["Normal Chat (ChatGPT Jaisa)", "Creative Lab - School Mode"], index=0)

    if "School" in mode:
        st.markdown("### 🎒 Age Group")
        age_options = ["1-2 Yrs", "3-4 Yrs", "5-6 Yrs", "6-8 Yrs", "10-11 Yrs", "11+ Yrs"]
        cols = st.columns(2)
        for i, ag in enumerate(age_options):
            if cols[i%2].button(ag, use_container_width=True, type="primary" if st.session_state.age_group==ag else "secondary"):
                st.session_state.age_group = ag
                st.session_state.messages = []
                st.rerun()
        st.success(f"Active: {st.session_state.age_group}")

        st.markdown("### 🎮 Quick Games")
        if st.button("🎨 Color Game"): st.session_state.messages.append({"role":"user","content":"Mujhe color game khilao"})
        if st.button("📖 Story Game"): st.session_state.messages.append({"role":"user","content":"Ek story game banao"})
        if st.button("🧩 Puzzle Game"): st.session_state.messages.append({"role":"user","content":"Ek puzzle do"})

    if st.button("+ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

# --- DISPLAY CHAT ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        if "image_url" in m:
            st.image(m["image_url"], caption=m.get("image_caption",""))
        else:
            st.markdown(m["content"])

# --- INPUT ---
placeholder = "Apna idea type karein..." if "School" in mode else "Ask anything..."
if prompt := st.chat_input(placeholder):
    is_school = "School" in mode
    age = st.session_state.age_group if is_school else "Normal"
    sys_prompt = get_school_prompt(age) if is_school else NORMAL_SYSTEM_PROMPT

    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(f'<div class="user-bubble">{prompt}</div>', unsafe_allow_html=True)

    wants_image = any(w in prompt.lower() for w in ["image banao","photo banao","draw","picture banao","chitra banao","tasveer banao","generate image"])

    with st.chat_message("assistant"):
        if wants_image:
            with st.spinner("🎨 Bana raha hu..."):
                url = generate_image_url(prompt)
                st.image(url, caption=prompt)
                st.session_state.messages.append({"role":"assistant","image_url":url,"image_caption":prompt,"content":f"Image: {prompt}"})

        # Text
        ph = st.empty()
        full = ""
        ctx, src = search_tavily(prompt)
        comp, used = get_groq_response(client, st.session_state.messages, sys_prompt, ctx)
        if comp is None:
            st.error("Sab model busy hain, 2 sec baad try karo sa")
            st.stop()
        resp = comp.choices[0].message.content
        if src: resp += f"\n\n**Source:**\n{src}"

        for w in resp.split():
            full += w + " "
            ph.markdown(full + "▌")
            time.sleep(0.02)
        ph.markdown(full)
        st.caption(f"Mode: {mode} | Age: {age} | Model: {used}")

    if not wants_image:
        st.session_state.messages.append({"role":"assistant","content":resp})
    st.rerun()
