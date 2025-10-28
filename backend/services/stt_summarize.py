from typing import List
from transformers import pipeline
from utils.save_helper import save_entry  # ✅ Unified logger for Smart Study

# Lazy global summarization model
_summarizer = None


def _get_summarizer():
    """
    Lazy-load a small summarization model to reduce startup time and memory footprint.
    """
    global _summarizer
    if _summarizer is None:
        _summarizer = pipeline("summarization", model="t5-small")
    return _summarizer


def simple_bullets(text: str, max_points: int = 8) -> List[str]:
    """
    Generate simple bullet points from text by naive sentence splitting.
    """
    parts = [p.strip() for p in text.replace("\n", " ").split(".") if p.strip()]
    bullets = []
    for p in parts:
        if len(bullets) >= max_points:
            break
        if len(p) > 10:
            bullets.append(p[:180] + ("..." if len(p) > 180 else ""))
    return bullets


def detect_emphasis(text: str, emphasize_keywords: List[str]) -> List[str]:
    """
    Detect key emphasis words or phrases present in text.
    """
    hits = []
    low = text.lower()
    for kw in emphasize_keywords:
        if kw.lower() in low:
            hits.append(kw)
    return list(sorted(set(hits)))


def process_transcript(text: str, emphasize_keywords: List[str]):
    """
    Summarize and extract highlights + bullet points from a lecture transcript.
    Automatically logs the result in Smart Study timeline.
    """
    summarizer = _get_summarizer()
    chunk = text[:2000]  # limit text size for small model

    # --- Summarize ---
    try:
        summary = summarizer(chunk, max_length=120, min_length=40, do_sample=False)[0]["summary_text"]
    except Exception:
        summary = chunk[:300]

    # --- Extract insights ---
    bullets = simple_bullets(text)
    highlights = detect_emphasis(text, emphasize_keywords)

    # --- Log to Smart Study unified dashboard ---
    try:
        save_entry(
            module="autonote",
            title="Transcript Summarized",
            content=f"Processed a transcript ({len(text)} chars) into structured notes.",
            metadata={
                "summary_preview": summary[:200] + "...",
                "highlights": highlights,
                "num_bullets": len(bullets),
                "keywords": emphasize_keywords,
            },
        )
        print("✅ Transcript summary saved to timeline.")
    except Exception as e:
        print(f"⚠️ Failed to save transcript summary log: {e}")

    return {"summary": summary, "highlights": highlights, "bullets": bullets}
