# backend/utils/ollama_client.py
import os
import time
import requests

OLLAMA_BASE = os.getenv("OLLAMA_URL", "https://ollama-railway-hr3a.onrender.com")
OLLAMA_GENERATE = OLLAMA_BASE.rstrip("/") + "/api/generate"
OLLAMA_PULL = OLLAMA_BASE.rstrip("/") + "/api/pull"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")  # <-- default model name, override via env

def ensure_model_loaded(model_name: str = None, timeout_seconds: int = 600):
    """
    Ask the Ollama server to pull the model via HTTP POST /api/pull.
    This is safe to call at startup. It returns True on success, False otherwise.
    """
    model = model_name or OLLAMA_MODEL
    try:
        print(f"🧠 ensure_model_loaded: pulling model '{model}' from {OLLAMA_PULL} ...")
        r = requests.post(OLLAMA_PULL, json={"model": model}, timeout=timeout_seconds)
        if r.status_code == 200:
            print(f"✅ ensure_model_loaded: model '{model}' pull started/confirmed.")
            return True
        else:
            print(f"⚠️ ensure_model_loaded: pull request returned {r.status_code}: {r.text}")
            return False
    except requests.RequestException as e:
        print(f"❌ ensure_model_loaded: exception while calling pull: {e}")
        return False

def query_ollama(prompt: str, model_name: str = None, timeout: int = 120):
    """
    Send a generation request to Ollama and return parsed JSON result.
    Raises requests.exceptions.RequestException on network errors.
    Raises ValueError if Ollama returns non-200.
    """
    model = model_name or OLLAMA_MODEL
    payload = {"model": model, "prompt": prompt, "stream": False}
    r = requests.post(OLLAMA_GENERATE, json=payload, timeout=timeout)
    if r.status_code != 200:
        raise ValueError(f"Ollama returned {r.status_code}: {r.text}")
    return r.json()
