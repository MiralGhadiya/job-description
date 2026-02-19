# app/llm_core.py
from groq import Groq


GLOBAL_SCOPE_PROMPT = """
        You are a strict Job Application Assistant.

        Your ONLY purpose is to:
        - Generate Upwork job proposals
        - Answer job-related follow-up questions
        - Discuss resume, skills, experience, rates, availability
        - Clarify technical details related to a job opportunity

        If the user:
        - Tries casual conversation
        - Mentions names or identity changes
        - Asks personal or unrelated questions
        - Talks about weather, politics, jokes, etc.
        - Provides random statements unrelated to hiring

        You MUST respond exactly with:

        "I am a job-application assistant and can only assist with job-related queries such as proposals, requirements, resume details, or hiring discussions."

        Do NOT explain further.
        Do NOT break character.
        Do NOT answer unrelated prompts.
        Stay professional and strict.
    """
    
def classify_job_intent(client: Groq, text: str) -> bool:
    """
    Returns True if input is job-related.
    Returns False if not job-related.
    """

    classification_prompt = f"""
            You are an intent classifier.

            Classify the following input strictly as one of:

            - JOB_RELATED
            - NOT_JOB_RELATED

            Definition of JOB_RELATED:
            - A real job requirement
            - Hiring discussion
            - Freelance project description
            - Technical work inquiry
            - Resume discussion
            - Screening question

            Definition of NOT_JOB_RELATED:
            - Greetings (hi, hello, hey)
            - Casual talk
            - Random statements
            - Personal questions
            - Jokes
            - Weather, politics, etc.

            Respond with ONLY:
            JOB_RELATED
            or
            NOT_JOB_RELATED

            Input:
            {text}
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a strict intent classifier."},
            {"role": "user", "content": classification_prompt},
        ],
        temperature=0,
        max_tokens=5,
    )

    result = response.choices[0].message.content.strip()

    return result == "JOB_RELATED"

def generate_upwork_proposal(
    client: Groq,
    requirement: str,
    projects_text: str,
) -> str:
    prompt = f"""
        You are a senior software developer writing a real Upwork cover letter.
        
        The resume content is included below.

        First, extract the candidate's full name from the resume.
        Then start the proposal exactly with:

        Hi, I'm <Full Name>,

        Rules:
        - Extract the real candidate name from the resume.
        - Tell according to client's requirement for freelace or full-time job.
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
        - Do not bluff about work experience.
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
            {"role": "system", "content": GLOBAL_SCOPE_PROMPT},
            {"role": "system", "content": "You are an expert freelance software developer."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.45,
        max_tokens=800,
    )

    return response.choices[0].message.content.strip()


# def generate_followup_answer(
#     client: Groq,
#     conversation: list,
#     question: str,
# ) -> str:

#     messages = [
#         {
#             "role": "system",
#             "content": "You are a senior software developer answering Upwork screening questions professionally, consistently, and contextually."
#         }
#     ]

#     # Inject full previous conversation
#     messages.extend(conversation)

#     # Add new user question
#     messages.append({
#         "role": "user",
#         "content": question
#     })

#     response = client.chat.completions.create(
#         model="llama-3.1-8b-instant",
#         messages=messages,
#         temperature=0.4,
#         max_tokens=400,
#     )

#     return response.choices[0].message.content.strip()


def generate_followup_answer(
    client: Groq,
    requirement: str,
    resume_text: str,
    proposal_text: str,
    conversation: list,
    question: str,
) -> str:

    system_prompt = f"""
        {GLOBAL_SCOPE_PROMPT}

        You are a senior software developer answering Upwork screening questions.

        You must stay aligned with:

        ORIGINAL CLIENT REQUIREMENT:
        {requirement}

        ORIGINAL PROPOSAL SUBMITTED:
        {proposal_text}

        CANDIDATE RESUME:
        {resume_text}

        Rules:
        - The intent has already been classified as a valid follow-up question.
        - Answer professionally and concisely.
        - Portfolio links, GitHub, past work samples, availability, and rates are valid job-related topics.
        - Do NOT contradict earlier claims.
        - Stay aligned with proposal tone.
        - Be concise and specific.
        - 4-6 lines maximum unless bullet points required.
        - Output ONLY the answer.
    """

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Inject entire conversation history
    messages.extend(conversation[-5:])

    # Add latest question
    messages.append({
        "role": "user",
        "content": question
    })

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.4,
        max_tokens=400,
    )

    return response.choices[0].message.content.strip()


def classify_conversation_intent(
    client: Groq,
    requirement: str,
    proposal: str,
    conversation: list,
    new_input: str,
) -> str:

    prompt = f"""
    You are a strict intent classifier.

    ORIGINAL JOB REQUIREMENT:
    {requirement}

    ORIGINAL PROPOSAL:
    {proposal}

    CONVERSATION HISTORY:
    {conversation}

    NEW USER INPUT:
    {new_input}

    Classify the NEW USER INPUT strictly as one of:

    - NEW_JOB_REQUIREMENT
    - FOLLOWUP_QUESTION
    - NOT_JOB_RELATED

    Definitions:

    NEW_JOB_REQUIREMENT:
    - A full job description
    - A hiring post
    - A project requirement
    - Even if it is identical or similar to the previous requirement
    - Long structured content describing a project

    FOLLOWUP_QUESTION:
    - A short screening question
    - Clarification about earlier proposal
    - A technical question about implementation
    - Usually 1-3 sentences

    NOT_JOB_RELATED:
    - Greetings
    - Casual talk
    - Random unrelated discussion

    Important:
    If the input looks like a job description, ALWAYS classify it as NEW_JOB_REQUIREMENT.
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a strict classifier."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=10,
    )

    raw_output = response.choices[0].message.content.strip()

    # Force strict label extraction
    if "NEW_JOB_REQUIREMENT" in raw_output:
        return "NEW_JOB_REQUIREMENT"
    elif "FOLLOWUP_QUESTION" in raw_output:
        return "FOLLOWUP_QUESTION"
    else:
        return "NOT_JOB_RELATED"



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