import streamlit as st
import requests
from deep_translator import GoogleTranslator


st.set_page_config(page_title="NewsInsight Pro", layout="wide")


st.markdown("""
    <style>
        .news-card {
            display: flex;
            background-color: #ffffff;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            border: 1px solid #e5e7eb;
            gap: 20px;
        }
        .card-image {
            flex: 0 0 250px;
            height: 180px;
            object-fit: cover;
            border-radius: 8px;
        }
        .card-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .news-title { color: #1e3a8a; font-size: 1.3rem; font-weight: 700; margin-bottom: 8px; }
        .summary-text { color: #374151; margin-bottom: 10px; line-height: 1.5; }
        .meta-data { color: #6b7280; font-size: 0.85rem; margin-bottom: 10px; font-weight: 500; }
        .read-more { color: #2563eb; font-weight: bold; text-decoration: none; }
    </style>
""", unsafe_allow_html=True)

API_BASE = "https://newsinsights-production-61d8.up.railway.app"

def fetch_news(keyword=None):
    try:
        url = f"{API_BASE}/search" if keyword else f"{API_BASE}/news"
        params = {"keyword": keyword} if keyword else {}

        response = requests.get(url, params=params, timeout=10)

        st.write("Request URL:", url)
        st.write("Status Code:", response.status_code)

        response.raise_for_status()

        data = response.json()

        st.write("Articles fetched:", len(data))

        return data

    except Exception as e:
        st.exception(e)
        return []

# -----------------------------
# UI HEADER & CONTROLS
# -----------------------------
st.title("🌐 NewsInsight Dashboard")

# Top Control Row
c1, c2, c3, c4 = st.columns([2, 0.5, 1, 1])

with c1:
    search_query = st.text_input("Search articles...", placeholder="Enter keyword...")
with c2:
    st.write("<br>", unsafe_allow_html=True)
    search_btn = st.button("🔍")
with c3:
    st.write("<br>", unsafe_allow_html=True)
    # Translation Toggle
    btn_label = "Switch to English" if st.session_state.get('translate') else "Translate to Hindi"
    if st.button(btn_label):
        st.session_state.translate = not st.session_state.get('translate', False)
        st.rerun()
with c4:
    st.write("<br>", unsafe_allow_html=True)
    # Update Trigger
    if st.button("🔄 Update News"):
        with st.spinner("Fetching and summarizing latest news..."):
            try:
                requests.get(f"{API_BASE}/trigger-update", timeout=60)
                st.success("Update successful!")
                st.rerun()
            except Exception as e:
                st.error("Failed to trigger update.")

# -----------------------------
# RENDER CONTENT
# -----------------------------
news_items = fetch_news(search_query if search_btn else None)

if not news_items:
    st.info("No news found. Try a different keyword or trigger an update.")
else:
    for item in news_items:
        summary = item.get("summarised", "")
        
        # Translation Logic
        if st.session_state.get('translate'):
            try:
                summary = GoogleTranslator(source='en', target='hi').translate(summary)
            except:
                pass # Fallback to English if translation fails

        # Render Card
        st.markdown(f"""
            <div class="news-card">
                <img src="{item.get('image', '')}" class="card-image" onerror="this.style.display='none'">
                <div class="card-content">
                    <div class="news-title">{item.get('title')}</div>
                    <div class="summary-text">{summary}</div>
                    <div class="meta-data">
                        Source: {item.get('source')} | Published: {item.get('publishedAt')}
                    </div>
                    <a href="{item.get('url')}" target="_blank" class="read-more">Read Full Article ↗</a>
                </div>
            </div>
        """, unsafe_allow_html=True)
