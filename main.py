from sqlalchemy.orm import Session
from models import News_model
from fastapi import FastAPI
from fastapi import HTTPException,Depends,Query,Path
import os
import requests
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from datetime import datetime
import traceback
from newspaper import Article
from apscheduler.schedulers.background import BackgroundScheduler
from db import get_db,LocalSession
from sqlalchemy import desc
from contextlib import asynccontextmanager
from db import Base,engine

Base.metadata.create_all(engine)
load_dotenv()
api_key=os.getenv("NEWSAPIKEY")
# Summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
summarizer = None

# Change your global variable
tokenizer = None
model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global tokenizer, model
    print("Loading model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("./bart_local")
    model = AutoModelForSeq2SeqLM.from_pretrained("./bart_local")
    
    # Start Scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_news, 'interval', minutes=30)
    scheduler.start()
    print("Model loaded and scheduler started.")
    
    yield
    
    # Shutdown Scheduler
    scheduler.shutdown()
    tokenizer = None
    model = None

def get_article_text(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        print(f"Scraping error: {e}")
        return None
app=FastAPI(lifespan=lifespan)
def fetch_api():
    try:
        url = f"https://gnews.io/api/v4/top-headlines?country=in&lang=en&apikey={api_key}&max=30"
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code != 200:
            print(f"API Error: Status code {response.status_code}")
            return [] # Return empty list instead of None
            
        data = response.json()
        articles_data = data.get('articles', [])
        
        # Your existing mapping logic
        articles_list = []
        for article in articles_data:
            articles_list.append({
                "id": article.get("id"),
                "title": article.get("title"),
                "description": article.get("description"),
                "content": article.get("content"),
                "image": article.get("image"),
                "url": article.get("url"),
                "publishedAt": article.get("publishedAt"),
                "source": article.get("source", {}).get("name")
            })
        return articles_list
    except Exception as e:
        print('API fetching Error', e)
        return [] # Return empty list here as well

def update_news():
    db = LocalSession()
    global tokenizer, model
    try:
        articles_data = fetch_api()
        
        # 1. Ensure we have data
        if not articles_data or not isinstance(articles_data, list):
            print("No articles fetched or data format error.")
            return

        for article in articles_data:
            # 2. Use .get() to prevent KeyErrors
            url = article.get("url")
            title = article.get("title")
            
            # Skip if we don't have the bare minimum
            if not url or not title:
                continue

            # 3. Check existence
            if db.query(News_model).filter(News_model.url == url).first():
                continue

            # 4. Fetch the actual text content
            text = get_article_text(url)
            if not text:
                continue
            
            # 5. Generate Summary
            inputs = tokenizer(text[:1024], return_tensors="pt", truncation=True)
            summary_ids = model.generate(inputs["input_ids"], max_length=250, min_length=30, num_beams=4, early_stopping=True)
            summary_text = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

            # 6. Safe Date Parsing
            raw_date = article.get("publishedAt", "")
            try:
                pub_date = datetime.strptime(raw_date.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
            except:
                pub_date = datetime.now()

            # 7. Use .get() for ALL fields to avoid 'str' or 'None' attribute errors
            new_article = News_model(
                title=title,
                description=article.get("description"),
                summarised=summary_text,
                image=article.get("image"),
                url=url,
                publishedAt=pub_date,
                source=article.get("source") # Assuming source is a string or dict
            )
            db.add(new_article)
        
        db.commit()
        db.refresh(new_article )
        print("Update complete.")
    except Exception as e:
        print(f"Update error: {e}")
        traceback.print_exc() # This will show you exactly which line failed
    finally:
        db.close()
    


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


