from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import json
import time

router = APIRouter()

class ConfusionRequest(BaseModel):
    text: str

class ConfusionResponse(BaseModel):
    explanation: str

OLLAMA_URL = "https://ollama-railway-hr3a.onrender.com"

@router.post("/analyze", response_model=ConfusionResponse)
async def analyze_confusion(req: ConfusionRequest):
    topic = req.text.strip()
    if not topic:
        raise HTTPException(400, "Please provide a valid topic or question.")

    payload = {
        "model": "phi3",  # ✅ use smaller, faster model for local inference
        "prompt": (
            f"Explain the following concept in detail, step by step, "
            f"as if teaching a beginner student. Use simple language and examples.\n\n{topic}"
        ),
        "stream": True
    }

    try:
        explanation = ""
        start_time = time.time()

        with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=300) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    # Try JSON decoding (Ollama standard)
                    data = json.loads(line)
                    if "response" in data:
                        explanation += data["response"]
                except json.JSONDecodeError:
                    # Fallback for raw text chunks
                    explanation += line.decode(errors="ignore")

        duration = round(time.time() - start_time, 1)
        print(f"✅ Ollama responded in {duration}s. Length={len(explanation)} chars")

        if not explanation.strip():
            raise HTTPException(500, "🤖 AI could not generate an explanation. Try rephrasing your topic.")

        return {"explanation": explanation.strip()}

    except requests.exceptions.ConnectionError:
        raise HTTPException(500, "⚠️ Ollama is not running. Please start it with 'ollama serve'.")
    except requests.exceptions.Timeout:
        raise HTTPException(504, "⏳ Ollama took too long to respond. Try a smaller model or shorter input.")
    except Exception as e:
        raise HTTPException(500, f"Unexpected error: {str(e)}")
