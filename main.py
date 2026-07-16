from fastapi import FastAPI, HTTPException, Depends, Query
import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import traceback
from newspaper import Article
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
HF_TOKEN = os.getenv("HF_TOKEN") # Add this to your Railway variables!
HF_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Scheduler without loading any ML models into RAM
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_news, 'interval', minutes=30)
    scheduler.start()
    print("Scheduler started. Using Inference API for summarization.")
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# --- HELPER FUNCTIONS ---
def summarize_text(text):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    response = requests.post(API_URL, headers={"Authorization": f"Bearer {HF_TOKEN}"}, json={"inputs": text[:1024]})
    if response.status_code == 200:
        return response.json()[0]['summary_text']
    return "Summary unavailable.

def get_article_text(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        print(f"Scraping error: {e}")
        return None

def fetch_api():
    try:
        url = f"https://gnews.io/api/v4/top-headlines?country=in&lang=en&apikey={API_KEY}&max=30"
        response = requests.get(url)
        if response.status_code != 200: return []
        return response.json().get('articles', [])
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
            
            # Use the new API summarizer
            summary_text = summarize_text(text)

            raw_date = article.get("publishedAt", "")
            try:
                pub_date = datetime.strptime(raw_date.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
            except:
                pub_date = datetime.now()

            new_article = News_model(
                title=article.get("title"),
                description=article.get("description"),
                summarised=summary_text,
                image=article.get("image"),
                url=url,
                publishedAt=pub_date,
                source=article.get("source", {}).get("name")
            )
            db.add(new_article)
        db.commit()
    except Exception as e:
        traceback.print_exc()
    finally:
        db.close()

# ... (Keep your existing @app.get routes here)

@app.get("/news")

def get_news(skip: int = Query(0, ge=0), limit: int = Query(30, gt=0), db: Session = Depends(get_db)):
    try:
        # update_news()
        News_list= db.query(News_model).order_by(
        desc(News_model.publishedAt)).offset(skip).limit(limit).all()
        return News_list
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=404,detail=str(e))

@app.get("/news/{news_id}")
def get_one_news(news_id:int,db:Session=Depends(get_db)):
    news=db.query(News_model).filter(News_model.id==news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    return news

@app.get("/search")
def search_news(keyword: str, db:Session=Depends(get_db)):
    return db.query(News_model).filter(
        News_model.title.ilike(f"%{keyword}%")
    ).all()

@app.delete("/news/{news_id}")
def delete_news(news_id: int, db:Session=Depends(get_db)):
    news = db.query(News_model).filter(News_model.id == news_id).first()

    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    db.delete(news)
    db.commit()

    return {"message": "Deleted successfully"}

@app.get("/trigger-update")
def trigger_update():
    update_news()
    return {"message": "Update triggered manually"}


