# coding_lab.py - Isko alag file bana
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq

def show_coding_lab():
    st.subheader("💻 Clyxess Coding Lab - No Age Limit")

    col1, col2 = st.columns(2)
    with col1:
        age = st.selectbox("🎂 Age:", ["5-8 Saal", "9-12 Saal", "13-17 Saal", "18+"], key="age_lab")
    with col2:
        lang = st.selectbox("💾 Language:", ["HTML", "CSS", "JavaScript", "Python", "Java", "PHP"], key="lang_lab")

    left, right = st.columns([1, 1])

    with left:
        if lang == "HTML":
            default_code = "<h1>Hello Clyxess</h1>\n<p>Mera pehla website</p>"
        elif lang == "Python":
            default_code = "print('Hello Clyxess')"
        else:
            default_code = f"// {lang} code here"

        user_code = st.text_area("Code Likho:", value=default_code, height=350, key="code_input")
        check_btn = st.button("🔍 Check & Fix Karo", use_container_width=True)

    with right:
        st.write(f"👀 Live Preview - {lang}")
        if lang in ["HTML", "CSS", "JavaScript"]:
            html_to_show = f"<style>{user_code}</style>" if lang == "CSS" else user_code
            components.html(html_to_show, height=350, scrolling=True)
        else:
            st.info(f"{lang} ka output check karne ke liye button dabao")

        if check_btn and user_code:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            prompt = f"Age {age}, Lang {lang}. Is code me galti batao aur sahi karo, Hindi me bacche ko samjhao: {user_code}"
            res = client.chat.completions.create(model="qwen/qwen3-32b", messages=[{"role":"user","content":prompt}], temperature=0.5)
            st.success(res.choices[0].message.content)
