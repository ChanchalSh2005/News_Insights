from fastapi import FastAPI, HTTPException, Depends, Query
import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import traceback
from bs4 import BeautifulSoup # Changed from newspaper
from apscheduler.schedulers.background import BackgroundScheduler
from db import get_db, LocalSession, Base, engine
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models import News_model
from contextlib import asynccontextmanager

Base.metadata.create_all(engine)
load_dotenv()

# --- CONFIGURATION ---
API_KEY = os.getenv("NEWSAPIKEY")
HF_TOKEN = os.getenv("HF_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_news, 'interval', minutes=30)
    scheduler.start()
    print("Scheduler started. Using Inference API.")
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
def summarize_text(text):
    if not HF_TOKEN: return "HF_TOKEN missing"
    
    # HARDCODED: Using IP 3.161.109.91 instead of the domain
    # You MUST include the 'Host' header for the SSL certificate to match
    url = "https://3.161.109.91/models/facebook/bart-large-cnn"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Host": "api-inference.huggingface.co"
    }
    payload = {"inputs": text[:1024]}
    
    try:
        # verify=False is used ONLY if you get SSL errors with the hardcoded IP
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            return response.json()[0].get('summary_text', 'No summary.')
        else:
            print(f"API Debug: Status {response.status_code}, Response: {response.text}")
            return f"API Error: {response.status_code}"
    except Exception as e:
        print(f"Request exception: {e}")
        return "Connection failed."

def get_article_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Extract only <p> tags to save huge amounts of RAM
            paragraphs = [p.get_text() for p in soup.find_all('p')]
            return " ".join(paragraphs)
        return None
    except Exception as e:
        print(f"Scraping error: {e}")
        return None

def fetch_api():
    try:
        url = f"https://gnews.io/api/v4/top-headlines?country=in&lang=en&apikey={API_KEY}&max=10"
        response = requests.get(url, timeout=10)
        return response.json().get('articles', []) if response.status_code == 200 else []
    except Exception as e:
        print('API fetching Error', e)
        return []

def update_news():
    db = LocalSession()
    try:
        articles_data = fetch_api()
        for article in articles_data:
            url = article.get("url")
            if not url or db.query(News_model).filter(News_model.url == url).first():
                continue

            text = get_article_text(url)
            if not text: continue
            
            summary_text = summarize_text(text)

            raw_date = article.get("publishedAt", "")
            pub_date = datetime.now()
            try:
                pub_date = datetime.strptime(raw_date.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
            except: pass

            new_article = News_model(
                title=article.get("title"),
                description=article.get("description"),
                summarised=summary_text,
                image=article.get("image"),
                url=url,
                publishedAt=pub_date,
                source=article.get("source", {}).get("name") if isinstance(article.get("source"), dict) else article.get("source")
            )
            db.add(new_article)
        db.commit()
    except Exception as e:
        traceback.print_exc()
    finally:
        db.close()

# ... (Keep your existing @app.get routes here)
