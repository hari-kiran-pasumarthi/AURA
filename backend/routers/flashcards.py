from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from backend.models.schemas import FlashcardRequest, FlashcardResponse, Flashcard
from backend.utils.save_helper import save_data, save_entry
from pypdf import PdfReader
from rake_nltk import Rake
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.luhn import LuhnSummarizer
import nltk
import os, re, json, glob
from datetime import datetime
from typing import List, Optional

# -------------------------------------------
# ✅ Router Setup
# -------------------------------------------
router = APIRouter(prefix="/flashcards", tags=["Flashcards"])

# -------------------------------------------
# ✅ Ensure NLTK dependencies exist (for cloud)
# -------------------------------------------
for resource in ["stopwords", "punkt", "punkt_tab"]:
    try:
        nltk.data.find(f"tokenizers/{resource}" if "punkt" in resource else f"corpora/{resource}")
    except LookupError:
        print(f"📦 Downloading missing NLTK resource: {resource}")
        nltk.download(resource)

UPLOAD_DIR = "uploaded_pdfs"
SAVE_DIR = os.path.join("saved_data", "flashcards")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SAVE_DIR, exist_ok=True)

# -------------------------------------------
# 📤 Upload PDF
# -------------------------------------------
@router.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    path = os.path.join(UPLOAD_DIR, file.filename)
    with open(path, "wb") as f:
        f.write(await file.read())
    return {"pdf_path": path, "filename": file.filename}


# -------------------------------------------
# 🧠 Helpers
# -------------------------------------------
def _extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    buf = [p.extract_text() or "" for p in reader.pages]
    return "\n".join(buf)


def _summarize_text(text: str, num_sentences: int = 10) -> str:
    clean_text = re.sub(r"\s+", " ", text.strip())
    try:
        parser = PlaintextParser.from_string(clean_text, Tokenizer("english"))
        summarizer = LuhnSummarizer()
        summary = summarizer(parser.document, num_sentences)
        summarized = " ".join(str(sentence) for sentence in summary)
        return summarized if len(summarized.split()) > 20 else clean_text
    except Exception as e:
        print(f"⚠️ Summarization failed: {e}")
        return clean_text


def _keyword_phrases(text: str, topn: int = 30) -> List[str]:
    r = Rake()
    r.extract_keywords_from_text(text)
    return r.get_ranked_phrases()[:topn]


def _make_cloze(sentence: str, term: str):
    pat = re.compile(re.escape(term), re.IGNORECASE)
    return pat.sub("____", sentence)


# -------------------------------------------
# ⚙️ Generate Flashcards
# -------------------------------------------
@router.post("/generate", response_model=FlashcardResponse)
async def generate_flashcards(req: FlashcardRequest):
    if req.pdf_path:
        text = _extract_text_from_pdf(req.pdf_path)
        source = os.path.basename(req.pdf_path)
    else:
        text = req.text or ""
        source = "Manual Text Input"

    if not text.strip():
        raise HTTPException(status_code=400, detail="No valid text found")

    summarized_text = _summarize_text(text, num_sentences=10)
    phrases = _keyword_phrases(summarized_text, topn=req.num * 2)
    sentences = re.split(r"[\.!?]\s+", summarized_text)
    cards: List[Flashcard] = []

    for term in phrases:
        for s in sentences:
            if re.search(re.escape(term), s, re.IGNORECASE) and len(s) > 30:
                q = _make_cloze(s, term)
                a = term
                cards.append(Flashcard(q=q, a=a, tags=["auto"]))
                break
        if len(cards) >= req.num:
            break

    # 🧠 Save flashcards automatically
    filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_flashcards.json"
    entry = {
        "title": f"Flashcards from {source}",
        "content": f"{len(cards)} flashcards generated.",
        "metadata": {
            "source": source,
            "num_cards": len(cards),
            "cards": [card.dict() for card in cards],
            "tags": ["auto"],
        },
    }
    save_data(module_name="flashcards", filename=filename, entry=entry)

    save_entry(
        module="flashcards",
        title="Flashcards Generated",
        content=f"Generated {len(cards)} flashcards from {source}.",
        metadata={"source": source, "num_cards": len(cards)},
    )

    return FlashcardResponse(cards=cards)


# -------------------------------------------
# 💾 Manual Save Flashcards
# -------------------------------------------
@router.post("/save")
async def save_flashcards(payload: dict):
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_saved_flashcards.json"
        filepath = os.path.join(SAVE_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        save_entry(
            module="flashcards",
            title=payload.get("title", "Manual Flashcards"),
            content=f"Saved {payload.get('metadata', {}).get('num_cards', 0)} flashcards.",
            metadata=payload.get("metadata", {}),
        )

        return {"status": "success", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------
# 🧠 MemoryVault (Load, Search, Delete)
# -------------------------------------------
@router.get("/all")
async def get_all_flashcards():
    """Return all saved flashcards."""
    try:
        files = sorted(glob.glob(os.path.join(SAVE_DIR, "*.json")), reverse=True)
        data = []
        for fpath in files:
            with open(fpath, "r", encoding="utf-8") as f:
                data.append(json.load(f))
        return {"count": len(data), "flashcards": data}
    except Exception as e:
        raise HTTPException(500, f"Failed to load flashcards: {e}")


@router.get("/search")
async def search_flashcards(query: str = Query(..., min_length=2)):
    """Search flashcards by keyword."""
    try:
        matches = []
        for fpath in glob.glob(os.path.join(SAVE_DIR, "*.json")):
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                content = json.dumps(data).lower()
                if query.lower() in content:
                    matches.append(data)
        return {"query": query, "matches": matches, "count": len(matches)}
    except Exception as e:
        raise HTTPException(500, f"Search failed: {e}")


@router.delete("/delete/{filename}")
async def delete_flashcard(filename: str):
    """Delete a saved flashcard file."""
    try:
        fpath = os.path.join(SAVE_DIR, filename)
        if os.path.exists(fpath):
            os.remove(fpath)
            return {"status": "deleted", "filename": filename}
        else:
            raise HTTPException(404, f"File {filename} not found.")
    except Exception as e:
        raise HTTPException(500, f"Failed to delete flashcard: {e}")
