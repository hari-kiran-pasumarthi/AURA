from openai import OpenAI

# Replace with your actual API key
client = OpenAI(api_key="YOUR_API_KEY")

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain polymorphism in Python."}
]

try:
    response = client.chat.completions.create(
        model="gpt-5.0-mini",  # safer than gpt-5.0
        messages=messages,
    )
    print("Raw GPT response:", response)
    print("Answer:", response.choices[0].message.content)
except Exception as e:
    print("GPT error:", e)