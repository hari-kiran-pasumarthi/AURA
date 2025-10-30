from typing import List
from collections import Counter
import json, os, time
from groq import Groq
from backend.models.schemas import DoubtEvent, DoubtReport
from backend.utils.save_helper import save_entry

# ===================================
# ⚙️ GROQ CONFIGURATION
# ===================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ Missing GROQ_API_KEY environment variable. Please set it in your environment.")

client = Groq(api_key=GROQ_API_KEY)
MODEL_NAME = "llama-3.1-8b-instant"

# ===================================
# 💾 FILE PATHS
# ===================================
DOUBT_LOG_PATH = os.path.join("saved_data", "doubts", "saved_doubts.json")
os.makedirs(os.path.dirname(DOUBT_LOG_PATH), exist_ok=True)

# 🧭 Event classification
HARD_SIGNS = {"tab_switch", "rewind"}
SOFT_SIGNS = {"pause", "scroll_up"}


# ===================================
# 🧠 CALL GROQ LLM
# ===================================
def call_groq(question: str) -> str:
    """
    Generate a clear, student-friendly explanation using Groq Cloud.
    Fallback text ensures stability even if the API fails.
    """
    try:
        start_time = time.time()
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Explain this concept clearly and simply for a student:\n\n"
                        f"{question}\n\n"
                        f"Focus on examples, intuition, and conceptual clarity."
                    )
                }
            ],
            temperature=0.6,
            stream=True,
        )

        ai_answer = ""
        for chunk in completion:
            ai_answer += chunk.choices[0].delta.content or ""

        duration = round(time.time() - start_time, 1)
        print(f"✅ Groq responded in {duration}s. Length={len(ai_answer)} chars")

        if not ai_answer.strip():
            return "🤖 No response generated. Please try rephrasing your question."

        return ai_answer.strip()

    except Exception as e:
        return f"⚠️ Unable to reach Groq Cloud. ({e})"


# ===================================
# 🎯 CONFIDENCE COMPUTATION
# ===================================
def compute_confidence(events: List[DoubtEvent], ai_answer: str = "") -> float:
    """
    Heuristic confidence (0–100) based on confusion intensity and AI clarity.
    """
    confidence = 80.0  # base

    # Apply penalties for confusion indicators
    hard_penalty = sum(1 for e in events if e.event in HARD_SIGNS) * 10
    soft_penalty = sum(1 for e in events if e.event in SOFT_SIGNS) * 5
    confidence -= (hard_penalty + soft_penalty)

    # Reward longer, detailed answers
    length_bonus = min(len(ai_answer) / 25, 10)
    confidence += length_bonus

    # Clamp within range
    confidence = max(0, min(100, confidence))
    return round(confidence, 2)


# ===================================
# 💾 SAVE TO LOCAL HISTORY
# ===================================
def save_to_history(entry: dict):
    """
    Save the doubt clarification entry to saved_data/doubts/saved_doubts.json
    """
    try:
        if not os.path.exists(DOUBT_LOG_PATH):
            with open(DOUBT_LOG_PATH, "w") as f:
                json.dump([], f, indent=2)

        with open(DOUBT_LOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        data.append(entry)
        with open(DOUBT_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ Doubt saved locally: {entry.get('question', '')[:60]}")

    except Exception as e:
        print(f"⚠️ Could not save doubt history: {e}")


# ===================================
# 🔍 MAIN ANALYZER
# ===================================
def report(events: List[DoubtEvent]) -> DoubtReport:
    """
    Detect confusion patterns, generate Groq explanations,
    compute heuristic confidence, and persist all results.
    """
    ctr = Counter(e.event for e in events)
    ctx = [e.context for e in events if e.context]

    # Extract the main question context
    question = ctx[-1] if ctx else "No valid question provided."

    # Generate AI explanation
    ai_answer = call_groq(question)

    # Compute heuristic confidence
    confidence = compute_confidence(events, ai_answer)

    # Prepare human-readable report
    topics = [question]
    notes = [f"💬 Explanation:\n{ai_answer}\n\n🧠 Confidence Level: {confidence}%"]

    # Unified timeline logging
    try:
        save_entry(
            module="doubts",
            title=f"Doubt Clarified: {question[:60]}",
            content=f"AI explained the concept with {confidence}% confidence.",
            metadata={
                "confidence": confidence,
                "events": [e.event for e in events],
                "context": question,
                "ai_answer": ai_answer,
                "event_summary": dict(ctr),
            },
        )
    except Exception as e:
        print(f"⚠️ Failed to log doubt analysis: {e}")

    # Save locally for future use
    save_to_history({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "question": question,
        "confidence": f"{confidence}%",
        "response": ai_answer,
        "events": [e.event for e in events],
    })

    return DoubtReport(topics=topics, notes=notes)
