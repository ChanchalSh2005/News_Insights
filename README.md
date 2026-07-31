# 📰 NewsInsights

An AI-powered news aggregation and summarization platform that collects
news from multiple sources, processes articles, and generates concise
summaries for users.

## 🚀 Features

- 📰 Fetch latest news using NewsAPI
- 🔍 Search news articles
- 🤖 AI-powered text summarization
- 📌 Extract important information from articles
- 🌐 Streamlit-based interactive interface
- ⚡ FastAPI backend
- 🗄️ MySQL database using SQLAlchemy
- 🔄 Automatic news updates

## 🧠 Summarization Pipeline

The project experimented with multiple summarization approaches:

### 1. TF-IDF

TF-IDF was used to identify the most important terms/sentences
from an article.

### 2. MMR (Maximal Marginal Relevance)

MMR was used to select informative and diverse sentences,
reducing redundancy in the generated summary.

### 3. BART

The final pipeline uses Facebook's BART model for abstractive
summarization, allowing the system to generate concise summaries
rather than simply extracting existing sentences.

## 🏗️ Architecture

Streamlit Frontend
        ↓
FastAPI Backend
        ↓
News Processing & Summarization
        ↓
MySQL Database

## 🛠️ Tech Stack

- Python
- FastAPI
- Streamlit
- MySQL
- SQLAlchemy
- Scikit-learn
- Transformers
- PyTorch
- NewsAPI
- APScheduler

