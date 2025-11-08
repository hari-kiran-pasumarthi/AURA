from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from backend.models.schemas import FlashcardRequest, FlashcardResponse, Flashcard
from backend.routers.auth import get_current_user
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
from pypdf import PdfReader
from rake_nltk import Rake
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.luhn import LuhnSummarizer
from groq import Groq
import nltk
import os, re, json, asyncio, traceback
from datetime import datetime
from typing import List

# -------------------------------------------
# 🚀 Router Setup
# -------------------------------------------
router = APIRouter(prefix="/flashcards", tags=["Flashcards"])

# -------------------------------------------
# ✅ NLP Setup
# -------------------------------------------
for resource in ["stopwords", "punkt", "punkt_tab"]:
    try:
        nltk.data.find(f"tokenizers/{resource}" if "punkt" in resource else f"corpora/{resource}")
    except LookupError:
        nltk.download(resource)

# -------------------------------------------
# ✅ Groq Setup
# -------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
GROQ_MODEL = "llama-3.1-70b-versatile"  # ✅ stable model name

# -------------------------------------------
# 📁 Storage Setup
# -------------------------------------------
UPLOAD_DIR = "uploaded_pdfs"
SAVE_DIR = os.path.join("saved_files", "flashcards")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SAVE_DIR, exist_ok=True)

SAVE_FILE = os.path.join(SAVE_DIR, "saved_flashcards.json")
if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)

# -------------------------------------------
# 📧 Email Helper
# -------------------------------------------
async def send_flashcard_email(user_email: str, title: str, count: int):
    try:
        fm = FastMail(conf)
        subject = f"🧠 AURA | Flashcards Generated: {title}"
        body = f"""
        <h3>📚 AURA Flashcards Ready</h3>
        <p><b>Title:</b> {title}</p>
        <p><b>Total Flashcards:</b> {count}</p>
        <hr>
        <p>Check your AURA app to review and practice.</p>
        """
        msg = MessageSchema(subject=subject, recipients=[user_email], body=body, subtype="html")
        await fm.send_message(msg)
    except Exception as e:
        print(f"⚠️ Email skipped: {e}")

# -------------------------------------------
# 📤 Upload PDF
# -------------------------------------------
@router.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload a PDF and associate it with the current user."""
    path = os.path.join(UPLOAD_DIR, file.filename)
    with open(path, "wb") as f:
        f.write(await file.read())
    return {"pdf_path": path, "filename": file.filename, "user": current_user["email"]}

# -------------------------------------------
# 🧠 Helper Functions
# -------------------------------------------
def _extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    return "\n".join([p.extract_text() or "" for p in reader.pages])

def _summarize_text(text: str, num_sentences: int = 10) -> str:
    clean = re.sub(r"\s+", " ", text.strip())
    try:
        parser = PlaintextParser.from_string(clean, Tokenizer("english"))
        summarizer = LuhnSummarizer()
        summary = summarizer(parser.document, num_sentences)
        summarized = " ".join(str(s) for s in summary)
        return summarized if len(summarized.split()) > 20 else clean
    except Exception as e:
        print("⚠️ Summarization failed:", e)
        return clean

def _keyword_phrases(text: str, topn: int = 30):
    r = Rake()
    r.extract_keywords_from_text(text)
    return r.get_ranked_phrases()[:topn]

def _make_cloze(sentence: str, term: str):
    return re.sub(re.escape(term), "____", sentence, flags=re.IGNORECASE)

# -------------------------------------------
# ⚙️ Generate Flashcards (NLP + Groq)
# -------------------------------------------
@router.post("/generate", response_model=FlashcardResponse)
async def generate_flashcards(req: FlashcardRequest, current_user: dict = Depends(get_current_user)):
    """Generate adaptive flashcards using NLP and Groq AI fallback."""
    try:
        # Step 1. Get text
        if req.pdf_path:
            text = _extract_text_from_pdf(req.pdf_path)
            source = os.path.basename(req.pdf_path)
        else:
            text = req.text or ""
            source = "Manual Text Input"

        if not text.strip():
            raise HTTPException(400, "No valid text found")

        word_count = len(text.split())
        num_cards = 5 if word_count < 300 else 10 if word_count < 1000 else 15
        print(f"🧠 Flashcard generation started for {current_user['email']} ({word_count} words)")

        # Step 2. NLP Generation
        summarized = _summarize_text(text, 8)
        if len(summarized.split()) < 40:
            summarized = text

        phrases = _keyword_phrases(summarized, topn=num_cards * 2)
        sentences = re.split(r"[.!?]\s+", summarized)
        cards: List[Flashcard] = []

        for term in phrases:
            for s in sentences:
                if re.search(re.escape(term), s, re.IGNORECASE) and len(s) > 25:
                    cards.append(Flashcard(q=_make_cloze(s, term), a=term, tags=["NLP"]))
                    break
            if len(cards) >= num_cards:
                break

        # Step 3. Fallback: Groq AI
        if len(cards) == 0 and client:
            print("⚙️ Falling back to Groq AI...")
            prompt = f"""
            Generate {num_cards} educational flashcards (Q&A pairs) from this text:
            {text[:4000]}

            Format strictly as:
            Q: <question> | A: <answer>
            """

            try:
                res = client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": "You generate educational flashcards."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.6,
                    max_tokens=1000,
                )

                output = res.choices[0].message.content.strip()
                print("🤖 Groq output sample:", output[:250])

                for line in output.split("\n"):
                    if "Q:" in line and "A:" in line:
                        parts = line.split("|")
                        if len(parts) >= 2:
                            q = parts[0].replace("Q:", "").strip()
                            a = parts[1].replace("A:", "").strip()
                            if q and a:
                                cards.append(Flashcard(q=q, a=a, tags=["AI"]))
                    if len(cards) >= num_cards:
                        break

                print(f"✅ Groq generated {len(cards)} flashcards")

            except Exception as e:
                print("❌ Groq API error:", e)
                traceback.print_exc()

        # Step 4. Guaranteed fallback
        if len(cards) == 0:
            cards = [Flashcard(q="What is the main topic of this text?", a=text[:150] + "...", tags=["fallback"])]

        # Step 5. Save
        entry = {
            "email": current_user["email"],
            "title": f"Flashcards from {source}",
            "content": f"{len(cards)} flashcards generated.",
            "metadata": {"source": source, "num_cards": len(cards), "cards": [c.dict() for c in cards]},
            "timestamp": datetime.utcnow().isoformat(),
        }

        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2)

        asyncio.create_task(send_flashcard_email(current_user["email"], source, len(cards)))
        print(f"💾 Saved {len(cards)} flashcards for {current_user['email']}")

        return FlashcardResponse(cards=cards)

    except Exception as e:
        print("❌ Flashcard generation error:\n", traceback.format_exc())
        raise HTTPException(500, f"Flashcard generation failed: {e}")

# -------------------------------------------
# 📚 Fetch User’s Flashcards
# -------------------------------------------
@router.get("/saved")
async def get_saved_flashcards(current_user: dict = Depends(get_current_user)):
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    user_cards = [d for d in data if d.get("email") == current_user["email"]]
    user_cards.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"entries": user_cards}

@router.get("/notes/list/flashcards")
async def get_flashcards_alias(current_user: dict = Depends(get_current_user)):
    return await get_saved_flashcards(current_user)
# -------------------------------------------
# 💾 Save Flashcards (Manual Save from Frontend)
# -------------------------------------------
# -------------------------------------------
# 💾 Save Flashcards (Manual Save from Frontend)
# -------------------------------------------
@router.post("/save")
async def save_flashcards(data: dict, current_user: dict = Depends(get_current_user)):
    """Save generated or manually edited flashcards from frontend."""
    try:
        title = data.get("title", "Untitled Flashcards")
        metadata = data.get("metadata", {})
        cards = metadata.get("cards", [])
        source = metadata.get("source", "Manual Entry")

        if not cards:
            raise HTTPException(status_code=400, detail="No flashcards to save.")

        # ✅ Include full flashcard data directly in the entry
        entry = {
            "email": current_user["email"],
            "title": title,
            "content": f"{len(cards)} flashcards saved manually.",
            "flashcards": cards,  # <-- actual card data added here
            "metadata": {
                "source": source,
                "num_cards": len(cards),
                "tags": metadata.get("tags", ["manual"]),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        # ✅ Save to master JSON
        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            data_log = json.load(f)
            data_log.append(entry)
            f.seek(0)
            json.dump(data_log, f, indent=2)

        # ✅ Also save a readable text version
        backup_path = os.path.join(
            SAVE_DIR,
            f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{current_user['email'].replace('@','_')}.txt",
        )
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(f"User: {current_user['email']}\nTitle: {title}\n\n")
            for i, c in enumerate(cards, 1):
                f.write(f"Q{i}: {c.get('q')}\nA{i}: {c.get('a')}\n\n")

        asyncio.create_task(send_flashcard_email(current_user["email"], title, len(cards)))

        print(f"💾 Saved {len(cards)} flashcards for {current_user['email']}")
        return {
            "message": "Flashcards saved successfully",
            "filename": os.path.basename(backup_path),
            "count": len(cards),
        }

    except Exception as e:
        print(f"❌ Save flashcards error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save flashcards: {e}")
