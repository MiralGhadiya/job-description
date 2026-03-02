# app/services/llm_service.py
"""
Service layer for LLM operations using Groq API.
Handles proposal generation, intent classification, and follow-up answers.
"""
from groq import Groq
from app.core.constants import (
    GROQ_MODEL,
    PROPOSAL_TEMPERATURE,
    PROPOSAL_MAX_TOKENS,
    FOLLOWUP_TEMPERATURE,
    FOLLOWUP_MAX_TOKENS,
    INTENT_TEMPERATURE,
    INTENT_MAX_TOKENS,
    GLOBAL_SCOPE_PROMPT,
    CONVERSATION_CONTEXT_LENGTH,
)
from app.core.exceptions import LLMGenerationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMService:
    """Service for LLM-based operations."""
    
    def __init__(self, client: Groq):
        """
        Initialize LLM service.
        
        Args:
            client: Groq API client
        """
        self.client = client
    
    def classify_job_intent(self, text: str) -> bool:
        """
        Classify whether input is job-related.
        
        Args:
            text: User input text
            
        Returns:
            True if job-related, False otherwise
            
        Raises:
            LLMGenerationError: If classification fails
        """
        try:
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
                - Jokes
                - Weather, politics, etc.

                Respond with ONLY:
                JOB_RELATED
                or
                NOT_JOB_RELATED

                Input:
                {text}
            """

            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are a strict intent classifier."},
                    {"role": "user", "content": classification_prompt},
                ],
                temperature=INTENT_TEMPERATURE,
                max_tokens=INTENT_MAX_TOKENS,
            )
            
            result = response.choices[0].message.content.strip()
            logger.info(f"Job intent classification result: {result}")
            return result == "JOB_RELATED"
            
        except Exception as e:
            logger.error(f"Failed to classify job intent: {str(e)}")
            raise LLMGenerationError(f"Intent classification failed: {str(e)}")
    
    def generate_proposal(
        self,
        requirement: str,
        projects_text: str,
    ) -> str:
        """
        Generate Upwork proposal for a job requirement.
        
        Args:
            requirement: Job requirement text
            projects_text: Formatted project information
            
        Returns:
            Generated proposal text
            
        Raises:
            LLMGenerationError: If proposal generation fails
        """
        try:
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
                - Write in 5-7 clearly separated paragraphs and also include bullet points.
                - Maintain natural spacing between paragraphs.
                - The proposal must feel thoughtful, specific, and written for this exact job.

                Client Requirement:
                {requirement}

                Past Projects:
                {projects_text}

                Use the above structured project information to extract:
                - Title
                - Industry
                - Tech Stack in bullet points
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
                - Highlight real-world production experience in bullet points.
                - Make the client feel you've solved this exact problem before.

                Guidelines:
                - Avoid fluff, but allow natural elaboration where helpful.
                - Select ONLY 1-2 most relevant projects from the provided list in strictly bullet points.
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

            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": GLOBAL_SCOPE_PROMPT},
                    {"role": "system", "content": "You are an expert freelance software developer."},
                    {"role": "user", "content": prompt},
                ],
                temperature=PROPOSAL_TEMPERATURE,
                max_tokens=PROPOSAL_MAX_TOKENS,
            )
            
            proposal = response.choices[0].message.content.strip()
            logger.info("Proposal generated successfully")
            return proposal
            
        except Exception as e:
            logger.error(f"Failed to generate proposal: {str(e)}")
            raise LLMGenerationError(f"Proposal generation failed: {str(e)}")
    
    def generate_followup_answer(
        self,
        requirement: str,
        resume_text: str,
        proposal_text: str,
        conversation: list,
        question: str,
    ) -> str:
        """
        Generate answer to a follow-up question about the proposal.
        
        Args:
            requirement: Original job requirement
            resume_text: Candidate's resume
            proposal_text: Original proposal submitted
            conversation: Conversation history
            question: Follow-up question
            
        Returns:
            Answer to the question
            
        Raises:
            LLMGenerationError: If answer generation fails
        """
        try:
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
                - If required then show content with bullet points.
                - 4-6 lines maximum unless bullet points required.
                - Output ONLY the answer.
            """

            messages = [
                {"role": "system", "content": system_prompt}
            ]

            # Inject entire conversation history (limited to reduce tokens)
            messages.extend(conversation[-CONVERSATION_CONTEXT_LENGTH:])

            # Add latest question
            messages.append({
                "role": "user",
                "content": question
            })

            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=FOLLOWUP_TEMPERATURE,
                max_tokens=FOLLOWUP_MAX_TOKENS,
            )

            answer = response.choices[0].message.content.strip()
            logger.info("Follow-up answer generated successfully")
            return answer
            
        except Exception as e:
            logger.error(f"Failed to generate follow-up answer: {str(e)}")
            raise LLMGenerationError(f"Follow-up answer generation failed: {str(e)}")
    
    def classify_conversation_intent(
        self,
        requirement: str,
        proposal: str,
        conversation: list,
        new_input: str,
    ) -> str:
        """
        Classify the intent of new user input in ongoing conversation.
        
        Args:
            requirement: Original job requirement
            proposal: Original proposal
            conversation: Conversation history
            new_input: New user input
            
        Returns:
            One of: "NEW_JOB_REQUIREMENT", "FOLLOWUP_QUESTION", "NOT_JOB_RELATED"
            
        Raises:
            LLMGenerationError: If classification fails
        """
        try:
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

            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are a strict classifier."},
                    {"role": "user", "content": prompt},
                ],
                temperature=INTENT_TEMPERATURE,
                max_tokens=INTENT_MAX_TOKENS,
            )

            raw_output = response.choices[0].message.content.strip()
            logger.info(f"Conversation intent classification: {raw_output}")

            # Force strict label extraction
            if "NEW_JOB_REQUIREMENT" in raw_output:
                return "NEW_JOB_REQUIREMENT"
            elif "FOLLOWUP_QUESTION" in raw_output:
                return "FOLLOWUP_QUESTION"
            else:
                return "NOT_JOB_RELATED"
                
        except Exception as e:
            logger.error(f"Failed to classify conversation intent: {str(e)}")
            raise LLMGenerationError(f"Conversation intent classification failed: {str(e)}")
