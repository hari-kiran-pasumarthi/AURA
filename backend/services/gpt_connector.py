from groq import Groq
from backend.utils.save_helper import save_entry
import os, time

# ==============================
# ⚙️ GROQ CONFIGURATION
# ==============================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ Missing GROQ_API_KEY environment variable. Please set it in Railway or Render.")

client = Groq(api_key=GROQ_API_KEY)
DEFAULT_MODEL = "llama-3.1-8b-instant"


# ==============================
# 🤖 ASK GROQ FUNCTION
# ==============================
def ask_gpt(messages, model=DEFAULT_MODEL):
    """
    Send chat messages to Groq (cloud-hosted Llama3.1 model)
    and log the interaction to the unified Smart Study timeline.
    """
    try:
        start_time = time.time()

        # 🧠 Chat completion call
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )

        # Extract reply text
        reply = response.choices[0].message.content.strip()
        duration = round(time.time() - start_time, 1)
        print(f"✅ Groq replied in {duration}s: {len(reply)} chars")

        # 🗨️ Extract user query for context
        user_message = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"),
            "[No user message found]"
        )

        # 🧾 Save chat to unified Smart Study timeline
        try:
            save_entry(
                module="chatbot",
                title="Chatbot Interaction",
                content=f"User asked: {user_message[:120]}",
                metadata={
                    "model": model,
                    "user_message": user_message,
                    "assistant_reply": reply
                },
            )
        except Exception as log_err:
            print(f"⚠️ Failed to log chatbot message: {log_err}")

        # ✅ Return the AI response
        return reply

    except Exception as e:
        print("❌ Groq Llama call failed:", e)
        return "⚠️ Sorry, the Groq AI service is currently unavailable. Please try again later."
