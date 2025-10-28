import ollama
from utils.save_helper import save_entry  # ✅ unified Smart Study logger

# Default model for Ollama
DEFAULT_MODEL = "llama3"


def ask_gpt(messages, model=DEFAULT_MODEL):
    """
    Send chat messages to Ollama (local Llama3 or other model)
    and log the interaction to the unified Smart Study timeline.
    """
    try:
        # 🔹 1. Chat with Ollama
        response = ollama.chat(
            model=model,
            messages=messages
        )

        reply = response["message"]["content"]

        # 🔹 2. Extract user query for context
        user_message = ""
        for m in reversed(messages):
            if m["role"] == "user":
                user_message = m["content"]
                break

        # 🔹 3. Save chat to unified timeline
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

        # 🔹 4. Return the AI response
        return reply

    except Exception as e:
        print("❌ Llama call failed:", e)
        return "⚠️ Sorry, the local Llama model is not available. Please make sure Ollama is running and the model is pulled."
