import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("GROQ_API_KEY not found in .env")

client = Groq(api_key=api_key)

client_requirement = """
Skills: Java, Python, SQL, JavaScript, Full Stack Development
Salary: 5 LPA - 17 LPA
Years of Experience: 0 - 4 years
Closing Application On: Soon
"""

projects = """
1. Aqua Flow – Supply Chain & Vendor Management Software
Tech: Python, Django, Flutter
Description: Vendor management, purchase orders, inventory, GST invoicing, analytics dashboards.

2. Place Finder
Tech: Flutter, Firebase
Description: Mobile app for locating places with filters, maps, and admin panel.

3. Brand Post
Tech: PHP, Laravel
Description: Social media scheduling and content management platform.
"""

prompt = f"""
You are a senior freelance software developer writing a REAL Upwork proposal.
Write like a human, not a corporate template.

Client requirement:
{client_requirement}

Relevant past projects:
{projects}

Rules:
- Write in a confident, conversational tone
- Avoid generic phrases like "I'm excited", "I'm confident", "Thank you for considering"
- Focus on HOW I would solve the problem
- Mention 1–2 most relevant projects only
- Do NOT repeat sentences or closing lines
- Do NOT use placeholders like [Client Name]
- End with ONE short, friendly call to action

Structure:
- 1 short paragraph showing understanding of the requirement
- 1 paragraph linking my experience to the requirement
- 1 paragraph explaining my approach
- 1 short closing (1–2 sentences max)

Word limit: 180–220 words
"""


response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {"role": "system", "content": "You are an expert freelance software developer."},
        {"role": "user", "content": prompt},
    ],
    temperature=0.6,
)

print(response.choices[0].message.content)
