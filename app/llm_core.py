# app/llm_core.py
from groq import Groq

def generate_upwork_proposal(
    client: Groq,
    requirement: str,
    projects_text: str,
) -> str:
    prompt = f"""
        You are a senior freelance software developer writing a REAL Upwork proposal.
        Write like a human, not a corporate template.

        Client requirement:
        {requirement}

        Relevant past projects:
        {projects_text}

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
        - If client feedback is provided, weave it naturally as credibility (1 sentence max)

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

    return response.choices[0].message.content.strip()
