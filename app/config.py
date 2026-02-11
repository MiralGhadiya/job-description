# app/config.py
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not found in .env")

groq_client = Groq(api_key=GROQ_API_KEY)


# # app/config.py
# import os
# from dotenv import load_dotenv
# import google.generativeai as genai

# load_dotenv()

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# if not GEMINI_API_KEY:
#     raise RuntimeError("GEMINI_API_KEY not found in .env")

# genai.configure(api_key=GEMINI_API_KEY)

# gemini_model = genai.GenerativeModel("gemini-2.5-flash")