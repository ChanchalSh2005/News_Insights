from Summarizer import News_Summarizer
from fastapi import FastAPI,HTTPException,Depends,Path,Query
from apscheduler.schedulers.background import BackgroundScheduler
import os
import models
from dotenv import load_dotenv
import requests
from database import engine,SessionLocal
from sqlalchemy.orm import Session
from typing import Annotated
import pickle
from database import get_db
import traceback
from datetime import datetime
from sqlalchemy import desc
from typing import List
import time
from newspaper import Article


#loading vectorizer model
with open("vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

summarizer = News_Summarizer(vectorizer)
app=FastAPI()
models.Base.metadata.create_all(bind=engine)


load_dotenv()
api_key=os.getenv('NEWS_API_KEY')
if not api_key:
    raise ValueError("NEWS_API_KEY not found in environment variables")

def get_full_article(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=10)

        article = Article(url)
        article.set_html(response.text)
        article.parse()

        return article.text

    except Exception as e:
        print("Article fetch error:", e)
        return None

def fetch_api():
    try:
        url=f"https://gnews.io/api/v4/top-headlines?country=in&lang=en&apikey={api_key}&max=30"
        response=requests.get(url)
        data=response.json()
        if response.status_code!=200:
            return None

        articles_data=data.get('articles',[])
        articles_list=[]
        for article in articles_data:
            articles_list.append({
            "id":article.get("id"),
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
        print('API fetching Error',e)
        return None



db_dependency=Annotated[Session,Depends(get_db)]




@app.get("/updateNews")
def update_news(db: db_dependency):
    try:
        articles = fetch_api()

        if not articles:
            raise HTTPException(status_code=400, detail="Failed to fetch news")

        for article in articles:
            existing_article = db.query(models.News).filter(
                models.News.url == article["url"]
            ).first()

            if existing_article:
                continue

            text_to_summarize = get_full_article(article.get("url") )
            summary = summarizer.summarize(text_to_summarize) if text_to_summarize else None

            # ✅ Convert publishedAt to proper datetime
            published_at_str = article.get("publishedAt")
            published_at = None
            if published_at_str:
                try:
                    # Remove 'Z' and convert ISO to datetime
                    published_at = datetime.strptime(published_at_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    print(f"Failed to parse datetime: {published_at_str}")

            # Create News object
            new_article = models.News(
                title=article["title"],
                description=article["description"],
                summarised=summary,
                image=article.get("image"),
                url=article["url"],
                publishedAt=published_at,  # pass datetime object
                source=article.get("source")
            )

            db.add(new_article)

        db.commit()
        return {"message": "News updated successfully"}

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    


@app.get("/news")

def get_news(skip: int = Query(0, ge=0), limit: int = Query(30, gt=0), db: Session = Depends(get_db)):
    try:
        News_list= db.query(models.News).order_by(
        desc(models.News.publishedAt)).offset(skip).limit(limit).all()
        return News_list
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=404,detail=str(e))
@app.get("/news/{news_id}")

def get_one_news(news_id:int,db:db_dependency):
    news=db.query(models.News).filter(models.News.id==news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    return news

@app.get("/search")
def search_news(keyword: str, db: db_dependency):
    return db.query(models.News).filter(
        models.News.title.ilike(f"%{keyword}%")
    ).all()

@app.delete("/news/{news_id}")
def delete_news(news_id: int, db:db_dependency):
    news = db.query(models.News).filter(models.News.id == news_id).first()

    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    db.delete(news)
    db.commit()

    return {"message": "Deleted successfully"}




#automatic updation of news 
def schedule_news_update():
    from News_insight.backend import update_news  # import your function
    from database import get_db
    db = next(get_db())  # get db session
    print(f"[{datetime.now()}] Running scheduled news update...")
    update_news(db=db)

# Create scheduler
scheduler = BackgroundScheduler()
# Run every 45 minutes
scheduler.add_job(schedule_news_update, 'interval', minutes=30)

scheduler.start()