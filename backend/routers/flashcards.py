from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.models.schemas import FlashcardRequest, FlashcardResponse, Flashcard
from backend.utils.save_helper import save_data, save_entry
from pypdf import PdfReader
from rake_nltk import Rake
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.luhn import LuhnSummarizer
import nltk
import os, re, json
from datetime import datetime
from typing import List

router = APIRouter(tags=["Flashcards"])

# ✅ Ensure all NLTK resources are available for cloud builds
for resource in ["stopwords", "punkt", "punkt_tab"]:
    try:
        nltk.data.find(f"tokenizers/{resource}" if "punkt" in resource else f"corpora/{resource}")
    except LookupError:
        print(f"📦 Downloading missing NLTK resource: {resource}")
        nltk.download(resource)

UPLOAD_DIR = "uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
