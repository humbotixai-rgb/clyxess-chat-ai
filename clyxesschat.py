import streamlit as st
from groq import Groq
from supabase import create_client, Client
import datetime
import uuid
import requests
import replicate # NEW LINE 1

st.set_page_config(page_title="ClyxessChat AI", layout="wide")

# CSS for Compact Code + Header
st.markdown("""
<style>
.main {max-width: 850px; margin: auto; padding-top: 0rem;}
.stCodeBlock {max-height: 300px!important; overflow-y: auto!important; border-radius: 8px; background: #1e1e1e!important;}
[data-testid="stSidebar"] {background-color: #171717;}
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
</style>
""", unsafe_allow_html=True)

# HEADER
st.markdown("""
<div class="header">
    <h1>💬 ClyxessChat AI</h1>
</div>
""", unsafe_allow_html=True)

# ============ 4 MODEL FALLBACK - LATEST 2026 ============
GROQ_MODELS = [
    "llama-3.3-70b-versatile", # 1. Main - Hindi + Smart
    "llama-3.3-8b-instant", # 2. Fast
    "deepseek-r1-distill-llama-70b", # 3. Coding King
    "qwen-qwq-32b" # 4. Backup Multilingual
]

def get_groq_response(client, messages):
    errors = []
    for model in GROQ_MODELS:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=4000,
            )
            return completion, model
        except Exception as e:
            errors.append(f"{model}: {str(e)}")
            continue

    st.error("❌ Groq API Error.\n\n**Reason:** API Key galat hai ya Quota khatam\n**Solution:** 1. `GROQ_API_KEY` check karo 2. 10 min baad try karo")
    with st.expander("Tech Details"):
        st.code("\n".join(errors))
    return None, None

# ============ NEW FUNCTION: IMAGE GENERATE ============
def generate_image(prompt):
    try:
        with st.spinner("🎨 Image bana raha hun..."):
            output = replicate.run(
                "black-forest-labs/flux-schnell", # Free + Fast model
                input={"prompt": prompt}
            )
        return output[0] # image url
    except Exception as e:
        st.error(f"Image Error: {e}")
        return None

# ============ TAVILY SEARCH ============
def search_tavily(query):
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": st.secrets["TAVILY_API_KEY"],
            "query": query,
            "search_depth": "advanced",
            "max_results": 3
        }
        response = requests.post(url, json=payload)
        results = response.json().get("results", [])
        context = "\n".join([f"- {r['title']}: {r['content']}" for r in results])
        sources = "\n".join([f"{i+1}. [{r['title']}]({r['url']})" for i, r in enumerate(results)])
        return context, sources
    except Exception as e:
        return "", ""

# ============ FINAL SYSTEM PROMPT - NO LANGUAGE MIX + NO FAKE SOURCE ============
today = datetime.datetime.now().strftime("%d %B %Y")
SYSTEM_PROMPT = f"""You are ClyxessChat AI - A friendly, helpful assistant for everyone.
Today is {today}.

=== RULE 1: LIVE SEARCH + SOURCE LINK ===
1. If user asks about "today, latest, news, rate, score, weather, price, bhav", search using Tavily.
2. DO NOT mention "I searched" or "tavily". Just give direct answer.
3. Always add sources at the end in this format:
**Source:**
1. [Website Title](URL)
4. Add date: "As of {today}..."
5. If no source found, say "Source not available"
6. IMPORTANT: Only add "Source:" section if you actually did a web search. For normal chat like "how are you", "hello", don't add Source at all.

=== RULE 2: IMAGE GENERATION ===
1. Only generate image if user says: "make image, create image, generate, banao, photo banao"
2. If user asks for image, FIRST reply "Ruko 2 sec, image bana raha hun" then generate image
3. After image, write: **Prompt:** user prompt
4. Don't generate image without asking

=== RULE 3: CODE GENERATION ===
1. Only give code if user says: "code do, make code, build website, app banao"
2. Always give code in ```language block + 2 line explanation + ask "need any customization?"
3. Don't give code without asking. Explain first.

=== RULE 4: MULTI-LANGUAGE MASTER RULE ===
1. MOST IMPORTANT: Reply in the EXACT SAME LANGUAGE the user used.
   User writes English → Reply 100% English
   User writes Hindi → Reply 100% Hindi
   User writes any other language → Reply 100% in that language
2. DO NOT mix languages in one reply. No "Kya hua?" in English reply.
3. Be empathetic if user uses 😭 😔 😢 😡.
4. Keep answers short, 3-4 lines max. Friendly, like a dost.

=== STRICTLY FORBIDDEN ===
1. Never lie. If unsure, say "I’m not sure, should I search?"
2. Never give facts without source when search was done
"""

# Supabase Connect
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Sidebar
with st.sidebar:
    st.title("💬 ClyxessChat AI")
    if st.button("+ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
    st.markdown("---")
    st.caption("Code Engine App Website")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())

# Chat display
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and "IMAGE_URL:" in message["content"]:
            parts = message["content"].split("IMAGE_URL:")
            st.markdown(parts[0])
            st.image(parts[1]) # IMAGE DIKHAO
        elif "```" in message["content"]:
            parts = message["content"].split("```")
            st.markdown(parts[0])
            if len(parts) > 1:
                code = parts[1].replace("html", "", 1).strip()
                st.code(code, language="html")
            if st.button("📋 Copy Code", key=f"copy_{i}"):
                st.toast("Code Copied!")
        else:
            st.markdown(message["content"])

# Input
if prompt := st.chat_input("Message ClyxessChat AI"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("ClyxessChat AI is thinking..."):

            # ============ NEW LOGIC: CHECK IMAGE REQUEST ============
            image_words = ["image banao", "photo banao", "generate image", "create image", "picture banao"]
            if any(word in prompt.lower() for word in image_words):
                img_url = generate_image(prompt)
                if img_url:
                    response = f"Ye rahi aapki image 👇\n\n**Prompt:** {prompt}\n\nIMAGE_URL:{img_url}"
                else:
                    response = "Image banane me dikkat aa gayi. Dobara try karein?"
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.markdown(response.split("IMAGE_URL:")[0])
                st.image(img_url)
                st.stop()
            # ============ IMAGE LOGIC END ============

            # LIVE SEARCH LOGIC
            search_context = ""
            sources = ""
            search_words = ["aaj", "latest", "news", "rate", "score", "mausam", "price", "bhav", "2026"]
            if any(word in prompt.lower() for word in search_words):
                with st.spinner("Searching web for latest info..."):
                    search_context, sources = search_tavily(prompt)

            # Final messages with system prompt + search context
            final_system = SYSTEM_PROMPT
            if search_context:
                final_system += f"\n\nLive Web Info:\n{search_context}"

            # FIX: Sirf last 10 messages bhejo warna TPM limit cross
            recent_messages = st.session_state.messages[-10:]
            messages = [{"role": "system", "content": final_system}] + recent_messages

            # 4 MODEL FALLBACK CALL
            completion, used_model = get_groq_response(client, messages)

            if completion is None: # Agar sab fail
                st.stop()

            response = completion.choices[0].message.content

            # SOURCE ADD KARNA - SIRF TAB JAB SEARCH HUA HO
            if sources:
                response += f"\n\n**Source:**\n{sources}"

            st.session_state.messages.append({"role": "assistant", "content": response})
            st.markdown(response)

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
            except Exception as e:
                pass

    st.rerun()
