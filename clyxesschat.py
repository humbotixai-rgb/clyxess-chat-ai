import streamlit as st
from groq import Groq
import pyperclip

st.set_page_config(page_title="ClyxessChat", layout="wide")

# ChatGPT wala CSS
st.markdown("""
<style>
   .main {max-width: 850px; margin: auto;}
   .stCodeBlock {
        max-height: 350px!important;
        overflow-y: auto!important;
        border-radius: 8px;
        background: #2d2d2d!important;
    }
    [data-testid="stSidebar"] {background-color: #202123;}
   .copy-btn {
        float: right;
        margin-top: -45px;
        z-index: 999;
        position: relative;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("💬 ClyxessChat")
    if st.button("+ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.caption("History")

# Center Title
st.markdown("<h2 style='text-align: center;'>Where should we begin?</h2>", unsafe_allow_html=True)

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []

# Chat display
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if "```" in message["content"]:
            parts = message["content"].split("```")
            st.markdown(parts[0])
            code = parts[1].replace("html", "", 1).strip()
            st.code(code, language="html")
            
            # Copy button
            if st.button("📋 Copy", key=f"copy_{i}"):
                st.session_state.clipboard = code
                st.toast("Code Copied!")
        else:
            st.markdown(message["content"])

# Input
if prompt := st.chat_input("Message ClyxessChat"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            system_prompt = """You are ClyxessChat. Rules: 
            1. Always return FULL working code in 1 file. 
            2. Put code inside ```html... ```
            3. Make it responsive and modern"""
            
            messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages
            completion = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=messages,
                max_tokens=8000,
            )
            response = completion.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
