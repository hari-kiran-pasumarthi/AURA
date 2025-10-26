from openai import OpenAI
import os

# Make sure your API key is set as an environment variable
# For example, in Windows PowerShell: setx OPENAI_API_KEY "sk-xxxxxxxxxx"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    models = client.models.list()
    print("Models available to your account:")
    for m in models.data:
        print(m.id)
except Exception as e:
    print("Error listing models:", e)
