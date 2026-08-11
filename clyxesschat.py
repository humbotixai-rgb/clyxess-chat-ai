import streamlit as st
from groq import Groq
import base64
from audio_recorder_streamlit import audio_recorder

# 1. MOBILE FRIENDLY + LOGIN
st.set_page_config(page_title="ClyxessChat AI", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

# Simple Login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 ClyxessChat AI Login")
    user = st.text_input("Username")
    passw = st.text_input("Password", type="password")
    if st.button("Login"):
        if user and passw: # abhi koi bhi login kar lega. baad me check lagana
            st.session_state.logged_in = True
            st.session_state.username = user
            st.rerun()
    st.stop()

# 2. GROQ SETUP - Tera 4 Model wala system
client = Groq(api_key=st.secrets["GROQ_API_KEY"]) # secrets me key daal de

GROQ_MODELS = [
    "llama-3.3-70b-versatile", # Main
    "llama-3.3-8b-instant", # Fast
    "deepseek-r1-distill-llama-70b", # Coding
    "qwen-qwen3-32b" # Vision + Backup
]

def get_groq_response(messages, is_image=False):
    models = GROQ_MODELS if is_image else GROQ_MODELS[:3] # image ho to 4th wala use ho
    for model in models:
        try:
            completion = client.chat.completions.create(model=model, messages=messages, max_tokens=4000)
            return completion.choices[0].message.content
        except:
            continue
    return "Bhai sabhi model so gaye. Thodi der me try kar."

# 3. CHAT HISTORY
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title(f"🤖 ClyxessChat AI - Welcome {st.session_state.username}")

# 4. VOICE + IMAGE INPUT
col1, col2 = st.columns(2)
with col1:
    audio_bytes = audio_recorder(text="🎤 Bol ke pucho")
with col2:
    uploaded_file = st.file_uploader("📸 Image Upload", type=["png", "jpg", "jpeg"])

user_input = st.chat_input("Yaha type kar ya voice/image use kar")

# Voice ko text me convert
if audio_bytes:
    with st.spinner("Sun raha hun..."):
        transcription = client.audio.transcriptions.create(file=("audio.wav", audio_bytes), model="whisper-large-v3-turbo")
        user_input = transcription.text

# Image ko handle
messages = []
is_image = False
if uploaded_file and user_input:
    bytes_data = uploaded_file.read()
    base64_image = base64.b64encode(bytes_data).decode('utf-8')
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": user_input},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
    }]
    is_image = True
    st.image(uploaded_file)

# Chat chalao
if user_input and not is_image:
    messages = [{"role": "user", "content": user_input}]

if messages:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Caffeine chal raha hai... soch raha hun"):
        response = get_groq_response(messages, is_image)
    st.session_state.messages.append({"role": "assistant", "content": response})

# Chat dikhao
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
