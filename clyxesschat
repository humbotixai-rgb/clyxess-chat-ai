import streamlit as st
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()
ACCENT = "#173BE8"

# Supabase Client - Sahi wala
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

CATEGORIES = ["All", "Politics", "Sports", "Entertainment", "Technology", "Business"]

st.set_page_config(page_title="Clyxess News AI", layout="wide")

# Dark Theme + Accent CSS
st.markdown(f"""
<style>
.stApp {{background: #0E1117; color: #FA;}}
[data-testid="stSidebar"] {{background: #1A1D23;}}
h1, h2, h3 {{color: {ACCENT};}}
.stButton>button {{background: {ACCENT}; color: white; border-radius: 8px;}}
.news-card {{background: #1F232B; padding: 16px; border-radius: 12px; margin-bottom: 16px; border: 1px solid #2A2E37;}}
</style>
""", unsafe_allow_html=True)

st.markdown(f"<h1 style='text-align:center'>Clyxess News AI</h1>", unsafe_allow_html=True)
st.caption("AI-Powered News Engine")

# Sidebar
with st.sidebar:
    st.markdown("### Navigation")
    selected_category = st.selectbox("Select Category", CATEGORIES)
    search_query = st.text_input("Search for news")

def get_news(category=None, search_query=None):
    query = supabase.from_("news").select("*")
    if category and category != "All":
        query = query.eq("category", category)
    if search_query:
        query = query.ilike("title", f"%{search_query}%")
    res = query.order("published_at", desc=True).execute() # .execute() lagana zaroori
    return res.data # .data se list nikalti hai

news_data = get_news(selected_category, search_query)

# Breaking News
st.markdown("### Breaking News")
if news_data:
    for news in news_data:
        st.markdown(f"<div class='news-card'>", unsafe_allow_html=True)
        st.markdown(f"**{news['title']}**")
        st.write(news["description"])
        st.caption(f"Category: {news['category']} | Published: {news['published_at']}")
        if news.get("image_url"):
            st.image(news["image_url"], width=300)
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.warning("No news found. Supabase me 'news' table banao pehle")

# Trending
st.markdown("### Trending Stories")
trending = supabase.from_("news").select("*").order("views", desc=True).limit(5).execute().data
for story in trending:
    st.markdown(f"- **{story['title']}**")

# Footer
st.markdown("---")
st.markdown("<p style='text-align:center; color: #8B949E;'>Copyright 2026 Clyxess News AI</p>", unsafe_allow_html=True)
