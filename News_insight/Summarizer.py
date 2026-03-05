import numpy as np
import pandas as pd
import nltk
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
nltk.download('stopwords')
import re

def remove_metadata(text):

    # Remove author line
    text = re.sub(r'By\s*\.\s*.*?\s*\.', '', text, flags=re.IGNORECASE)

    # Remove PUBLISHED or UPDATED blocks
    text = re.sub(
        r'(PUBLISHED|UPDATED)\s*:\s*\.*\s*\d{1,2}:\d{2}\s*\w+,\s*\d{1,2}\s*\w+\s*\d{4}',
        '',
        text,
        flags=re.IGNORECASE
    )

    # Remove standalone datetime patterns
    text = re.sub(
        r'\d{1,2}:\d{2}\s*\w+,\s*\d{1,2}\s*\w+\s*\d{4}',
        '',
        text
    )

    # Remove pipes
    text = re.sub(r'\|', '', text)

    #remove CNN
    text = re.sub(r"\bcnn\b", "", text, flags=re.IGNORECASE)

    # Remove newlines FIRST
    text = re.sub(r'\n+', ' ', text)

    # Remove starting dots (even if spaces before them)
    text = re.sub(r'^\s*\S\s*\S\s*\.+', '', text)

    # Fix spacing after periods (important for sent_tokenize)
    text = re.sub(r'\.(\w)', r'. \1', text)

    # Normalize multiple spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


import string
exclude=string.punctuation.replace('.','').replace('!','').replace('?','')
def remove_punc(text):
    cleaned_text = re.sub(r"\.{2,}", ".", text)
    for char in exclude:
        text=text.replace(char,'')
    return text

# new_df['article']=new_df['article'].apply(remove_punc)

def to_lower_case(text):
  return text.lower()





from nltk.corpus import stopwords
def remove_stopwords(text):
  new_text=[]
  for word in text.split():
    if word not in stopwords.words('english'):
      new_text.append(word)
  return ' '.join(new_text)


nltk.download('wordnet')
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet

lemmatizer=WordNetLemmatizer()
def lemma(text):
  # Tokenize the text, lemmatize each word, and join them back
  word_list = nltk.word_tokenize(text)
  lemmatized_output = ' '.join([lemmatizer.lemmatize(w) for w in word_list])
  return lemmatized_output

nltk.download('punkt_tab')

import spacy
nlp = spacy.load("en_core_web_sm")
def sent_tokenize(text):
  doc = nlp(text)
  sentence = [sent.text for sent in doc.sents]
  return sentence


def clean_text(text):
  sentences=sent_tokenize(text)

  clean_text=[]
  for sentence in sentences:
    temp=remove_metadata(sentence)
    temp=remove_punc(temp)
    temp=to_lower_case(temp)
    temp=remove_stopwords(temp)
    temp=lemma(temp)
    clean_text.append(temp)

  return clean_text

def original_text(text):
  sentences=sent_tokenize(text)
  original_text=[]
  for sentence in sentences:
    original=remove_metadata(sentence)
    original=remove_punc(original)
    original_text.append(original)
  return original_text




def generate_summary(cleaned_sentences, original_sentences, top_n=3):

    if len(cleaned_sentences) == 0:
        return ""

    top_n = min(top_n, len(cleaned_sentences))

    with open('vectorizer.pkl','rb') as f:
      vectorizer=pickle.load(f)
    tf_idf_matrix = vectorizer.transform(cleaned_sentences)

    sentence_scores = tf_idf_matrix.sum(axis=1)
    sentence_scores = np.array(sentence_scores).flatten()

    ranked_indices = sentence_scores.argsort()[::-1]

    selected_indices = []

    for idx in ranked_indices:
        candidate_vector = tf_idf_matrix[idx]

        if len(selected_indices) == 0:
            selected_indices.append(idx)
        else:
            similarities = cosine_similarity(
                candidate_vector,
                tf_idf_matrix[selected_indices]
            )

            if max(similarities[0]) < 0.7:
                selected_indices.append(idx)

        if len(selected_indices) == top_n:
            break

    final_indices = sorted(selected_indices)

    final_summary = " ".join([original_sentences[i] for i in final_indices])

    return final_summary


class News_Summarizer:
  def __init__(self,vectorizer):
    self.vectorizer = vectorizer
  def summarize(self,text,top_n=3):
    cleaned=clean_text(text)
    originaled=original_text(text)
    summary=generate_summary(cleaned,originaled,top_n)
    return summary
