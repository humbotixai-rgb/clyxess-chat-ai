import streamlit as st
from groq import Groq
from supabase import create_client, Client
import datetime
import uuid

st.set_page_config(page_title="ClyxessChat", layout="wide")

# CSS + JS for Compact Code + Copy Button
st.markdown("""
<style>
 .main {max-width: 850px; margin: auto;}
 .stCodeBlock {max-height: 350px!important; overflow-y: auto!important; border-radius: 8px; background: #1e1e1e!important;}
  [data-testid="stSidebar"] {background-color: #171717;}
 .copy-btn {background: #444; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer;}
</style>
<script>
function copyCode(id) {
  var code = document.getElementById(id).innerText;
  navigator.clipboard.writeText(code);
}
</script>
""", unsafe_allow_html=True)

# Supabase Connect
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Sidebar
with st.sidebar:
    st.title("💬 ClyxessChat")
    if st.button("+ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
    st.markdown("---")
    st.caption("Your AI Coding Assistant")

# Center Title
st.markdown("<h2 style='text-align: center;'>Where should we begin?</h2>", unsafe_allow_html=True)

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())

# Chat display
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if "```" in message["content"]:
            parts = message["content"].split("```")
            st.markdown(parts[0])
            code = parts[1].replace("html", "", 1).strip()
            code_id = f"code_{i}"
            st.code(code, language="html")
            if st.button("📋 Copy Code", key=f"copy_{i}"):
                st.markdown(f'<script>navigator.clipboard.writeText(`{code}`)</script>', unsafe_allow_html=True)
                st.toast("Code Copied!")
        else:
            st.markdown(message["content"])

# Input
if prompt := st.chat_input("Message ClyxessChat"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("ClyxessChat is thinking..."):
            system_prompt = """You are ClyxessChat, an expert coding AI.
            Rules: 
            1. Always return FULL WORKING code. No TODO or...
            2. Put entire code inside ```html... ```
            3. Make it modern, responsive with Tailwind CSS"""
            
            messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages
            
            completion = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=messages,
                temperature=0.2, # Code ke liye best
                max_tokens=8000,
            )
            response = completion.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Save to Supabase
            try:
                supabase.table("messages").insert({
                    "session_id": st.session_state.session_id,
                    "role": "user",
                    "content": prompt,
                    "created_at": datetime.datetime.now().isoformat()
                }).execute()
                supabase.table("messages").insert({
                    "session_id": st.session_state.session_id,
                    "role": "assistant", 
                    "content": response,
                    "created_at": datetime.datetime.now().isoformat()
                }).execute()
            except:
                pass
                
            st.rerun()
