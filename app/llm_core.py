# app/llm_core.py
from groq import Groq

def generate_upwork_proposal(
    client: Groq,
    requirement: str,
    projects_text: str,
) -> str:
    prompt = f"""
        You are a senior freelance software developer writing a real Upwork cover letter.
        
        The resume content is included below.

        First, extract the candidate's full name from the resume.
        Then start the proposal exactly with:

        Hi, I'm <Full Name>,

        Rules:
        - Extract the real candidate name from the resume.
        - Do NOT use file names.
        - Camel case the name properly with correct spacing between words.
        - Do NOT invent a name.
        - Output ONLY the proposal.
        - Start immediately with "Hi, I'm <Full Name>."
        
        CRITICAL:
        - Output ONLY the cover letter content.
        - Start immediately with the first sentence.
        - Start with like I've reviewed your requirement and am confident I can solve it.
        - Write in 5-7 clearly separated paragraphs and points.
        - Maintain natural spacing between paragraphs.
        - The proposal must feel thoughtful, specific, and written for this exact job.
        - Output ONLY the cover letter content.
        
        Client Requirement:
        {requirement}

        Past Projects:
        {projects_text}

        Use the above structured project information to extract:
        - Title
        - Industry
        - Tech Stack
        - Key Challenge
        - Implementation
        - Business Impact

        Only reference projects relevant to the client's requirement.
        
        Tone:
        Professional, confident, calm, and experienced.
        Human and conversational, but sharp.
        Authoritative without arrogance.

        What to Achieve:
        - Demonstrate deep understanding of the real issue.
        - Show ownership and strategic thinking.
        - Do not bluff about experience.
        - Explain technical reasoning clearly.
        - Highlight real-world production experience.
        - Make the client feel you've solved this exact problem before.

        Guidelines:
        - Avoid fluff, but allow natural elaboration where helpful.
        - Select ONLY 1-2 most relevant projects from the provided list.
        - Don't metion like Another relevant project is... Just seamlessly integrate the project details as proof of experience.
        - When referencing a project, format it exactly like this:

        Project:
        • **<Project Name>** — <Industry>
        - **Category**: <Category>
        - **Tech Stack**: <Tech Stack>
        - **Problem**: <What needed to be solved>
        - **Implementation**: <How it was built>
        - **Impact**: <Result / scale / performance improvement>

        - Use clean bullet formatting for project sections.
        - Do NOT dump raw text.
        - Integrate industry and tech stack naturally.
        - Include one short client feedback sentence if relevant.
        - End with one confident, friendly closing sentence.

        If Bug Fix / Production Issue:
        Write separate bullets covering:
        1. Immediate confident opening.
        2. App / Scenario (context, tech stack, users, scale).
        3. Root Cause (what was technically wrong and why).
        4. How it was fixed (specific implementation steps and impact).
        5. One strong closing sentence.

        If New Build:
        1. Deep problem understanding.
        2. Relevant production experience.
        3. Architecture and execution plan (with tradeoffs).
        4. Confident closing.

        Aim for 350-500 words.
        Make it feel like a senior engineer who has solved this in production.
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are an expert freelance software developer."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.45,
        max_tokens=800,
    )

    return response.choices[0].message.content.strip()




# import google.generativeai as genai

# def generate_upwork_proposal(
#     model,
#     requirement: str,
#     projects_text: str,
# ) -> str:
    
#     prompt = f"""
# You are a senior freelance software developer writing a real Upwork cover letter.

# CRITICAL:
# - Output ONLY the cover letter content.
# - Do NOT add explanations, titles, or commentary before or after.
# - Do NOT say "Here is your cover letter".
# - Start immediately with the first sentence of the proposal.

# Client Requirement:
# {requirement}

# Relevant Past Projects:
# {projects_text}

# Tone:
# Professional, confident, calm, and human.
# Conversational but sharp.
# No corporate language. No exaggerated enthusiasm. No generic freelancer phrases.

# Strict Rules:
# - No fluff
# - No buzzwords
# - No placeholders
# - No repeating structures
# - No generic endings
# - Mention only 1–2 relevant projects
# - End with ONE confident call to action (max 1 sentence)

# If bug fix:
# - Show prior production fix
# - Include App / Scenario
# - Root Cause
# - How it was fixed
# - Speak in past tense
# - No “I will investigate” language

# If new build:
# - Show understanding
# - Show relevant project
# - Explain execution plan
# - Clear close
# """

#     response = model.generate_content(
#         prompt,
#         generation_config={
#             "temperature": 0.45,
#             "top_p": 0.9,
#         }
#     )

#     return response.text.strip()