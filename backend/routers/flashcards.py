from fastapi import APIRouter, UploadFile, File, HTTPException
from models.schemas import FlashcardRequest, FlashcardResponse, Flashcard
from utils.save_helper import save_data, save_entry
from pypdf import PdfReader
from rake_nltk import Rake
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.luhn import LuhnSummarizer
import os, re, json
from datetime import datetime
from typing import List

router = APIRouter(tags=["Flashcards"])

UPLOAD_DIR = "uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 📤 Upload PDF
@router.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    path = os.path.join(UPLOAD_DIR, file.filename)
    with open(path, "wb") as f:
        f.write(await file.read())
    return {"pdf_path": path, "filename": file.filename}


# 🧠 --- Helpers ---
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


# ⚙️ Generate Flashcards
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

    # Log to unified system
    save_entry(
        module="flashcards",
        title="Flashcards Generated",
        content=f"Generated {len(cards)} flashcards from {source}.",
        metadata={"source": source, "num_cards": len(cards)},
    )

    return FlashcardResponse(cards=cards)


# 💾 Manual Save Flashcards
@router.post("/save")
async def save_flashcards(payload: dict):
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_saved_flashcards.json"

        entry = {
            "title": payload.get("title", "Manual Flashcards"),
            "content": payload.get("content", ""),
            "metadata": payload.get("metadata", {}),
        }

        save_data(module_name="flashcards", filename=filename, entry=entry)

        save_entry(
            module="flashcards",
            title="Flashcards Saved",
            content=f"Manually saved {payload.get('metadata', {}).get('num_cards', 0)} flashcards.",
            metadata=payload.get("metadata", {}),
        )

        return {"status": "success", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
