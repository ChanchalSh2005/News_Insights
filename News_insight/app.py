# news_insights_app.py

import streamlit as st
from math import ceil
from sqlalchemy import desc
import models
from database import SessionLocal

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="News-Insights", layout="wide")

# -----------------------------
# LOGO + TITLE
# -----------------------------
st.markdown(
    """
    <div style="display:flex;align-items:center;">
        <img src="https://cdn-icons-png.flaticon.com/512/21/21601.png" width="55">
        <h1 style="margin-left:10px;">News-Insights</h1>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("### Stay updated with the latest news")

# -----------------------------
# TOPIC SELECTOR
# -----------------------------
topic = st.selectbox(
    "Choose Topic",
    ["All", "Technology", "Business", "Sports", "Health", "Science", "Entertainment"]
)

# -----------------------------
# DATABASE CONNECTION
# -----------------------------
db = SessionLocal()

# -----------------------------
# FETCH NEWS
# -----------------------------
query = db.query(models.News)

# If you later store category
if topic != "All":
    query = query.filter(models.News.source == topic)

all_news = query.order_by(desc(models.News.publishedAt)).all()

# -----------------------------
# PAGINATION
# -----------------------------
NEWS_PER_PAGE = 15

total_news = len(all_news)
total_pages = ceil(total_news / NEWS_PER_PAGE)

if "page_num" not in st.session_state:
    st.session_state.page_num = 1


def next_page():
    if st.session_state.page_num < total_pages:
        st.session_state.page_num += 1


def prev_page():
    if st.session_state.page_num > 1:
        st.session_state.page_num -= 1


start_idx = (st.session_state.page_num - 1) * NEWS_PER_PAGE
end_idx = start_idx + NEWS_PER_PAGE

news_to_show = all_news[start_idx:end_idx]

# -----------------------------
# NEWS DISPLAY
# -----------------------------
for news in news_to_show:

    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    # IMAGE LEFT
    with col1:
        if news.image:
            st.image(news.image, use_container_width=True)

    # TEXT RIGHT
    with col2:

        st.markdown(f"### {news.title}")

        # FULL SUMMARY (no truncation)
        st.write(news.summarised)

        # Source
        if news.source:
            st.markdown(
                f"<span style='color:#1f77b4;font-size:13px;'>Source: {news.source}</span>",
                unsafe_allow_html=True,
            )

        # Published time
        if news.publishedAt:
            st.markdown(
                f"<p style='color:gray;font-size:12px;'>Published: {news.publishedAt}</p>",
                unsafe_allow_html=True,
            )

        # Read full article
        if news.url:
            st.markdown(f"[Read full article]({news.url})")

# -----------------------------
# PAGINATION BUTTONS
# -----------------------------
st.markdown("---")

col1, col2, col3 = st.columns([1,2,1])

with col1:
    st.button("⬅ Previous", on_click=prev_page)

with col3:
    st.button("Next ➡", on_click=next_page)

st.markdown(f"Page **{st.session_state.page_num}** of **{total_pages}**")

# -----------------------------
# FOOTER
# -----------------------------
st.markdown(
    """
    <hr>
    <p style='text-align:center;color:gray;font-size:12px;'>
    News-Insights © 2026 | AI Powered News Summaries
    </p>
    """,
    unsafe_allow_html=True
)