from typing import List
from collections import Counter
import json, os, requests, time
from models.schemas import DoubtEvent, DoubtReport
from backend.utils.save_helper import save_entry

# 🧭 Event classification
HARD_SIGNS = {"tab_switch", "rewind"}
SOFT_SIGNS = {"pause", "scroll_up"}

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DOUBT_LOG_PATH = os.path.join("saved_data", "doubts", "saved_doubts.json")
os.makedirs(os.path.dirname(DOUBT_LOG_PATH), exist_ok=True)


# 🔹 Call Ollama model
def call_ollama(question: str) -> str:
    """
    Generate clear, simplified explanation using local Ollama model.
    Fallback text ensures stability if Ollama isn't reachable.
    """
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "mistral",  # change to llama3/phi3 if preferred
                "prompt": (
                    f"Explain this concept clearly and simply for a student:\n\n"
                    f"{question}\n\n"
                    "Focus on examples, intuition, and conceptual clarity."
                ),
                "stream": False
            },
            timeout=45,
        )
        if response.status_code == 200:
            reply = response.json().get("response", "").strip()
            return reply or "No explanation returned from the AI model."
        else:
            return f"⚠️ Ollama error: {response.text}"
    except Exception as e:
        return f"⚠️ Unable to connect to Ollama. Please ensure it is running.\n({e})"


# 🔹 Compute realistic numeric confidence
def compute_confidence(events: List[DoubtEvent], ai_answer: str = "") -> float:
    """
    Heuristic confidence (0–100) based on confusion intensity and AI clarity.
    """
    confidence = 80.0  # base value

    # Apply penalties for confusion indicators
    hard_penalty = sum(1 for e in events if e.event in HARD_SIGNS) * 10
    soft_penalty = sum(1 for e in events if e.event in SOFT_SIGNS) * 5
    confidence -= (hard_penalty + soft_penalty)

    # Add small reward for longer, detailed answers
    length_bonus = min(len(ai_answer) / 25, 10)
    confidence += length_bonus

    # Clip to valid range
    confidence = max(0, min(100, confidence))
    return round(confidence, 2)


# 🔹 Save locally for history
def save_to_history(entry: dict):
    """
    Persist the doubt clarification entry to saved_data/doubts/saved_doubts.json
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


# 🔹 Main doubt analyzer
def report(events: List[DoubtEvent]) -> DoubtReport:
    """
    Detect confusion patterns, generate AI clarifications,
    compute heuristic confidence, and persist all results.
    """
    ctr = Counter(e.event for e in events)
    ctx = [e.context for e in events if e.context]

    # Extract the main question context
    question = ctx[-1] if ctx else "No valid question provided."

    # Generate AI response
    ai_answer = call_ollama(question)

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

    # Save locally for future viewing
    save_to_history({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "question": question,
        "confidence": f"{confidence}%",
        "response": ai_answer,
        "events": [e.event for e in events],
    })

    return DoubtReport(topics=topics, notes=notes)
