import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the client with your key and the OpenRouter base URL
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

print("Sending request to Olmo model via OpenRouter...")

# Send a request to the Olmo chat model
response = client.chat.completions.create(
    model="allenai/olmo-3-32b-think",
    messages=[
        {
            "role": "user",
            "content": "What are 5 things to do in Seattle?",
        }
    ],
)

# Print the model's response
print("\n--- Model Response ---")
print(response.choices[0].message.content)