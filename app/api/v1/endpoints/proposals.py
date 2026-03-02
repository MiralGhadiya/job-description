# app/api/v1/endpoints/proposals.py
"""
Proposal generation endpoints.
"""
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import ApplicationSession
from app.schemas import UpworkRequest, FollowupRequest
from app.services.llm_service import LLMService
from app.services.vectorstore_service import (
    ProjectStoreService,
    ReviewStoreService,
    ResumeStoreService,
)
from app.core.constants import groq_client, RESUME_SIMILARITY_THRESHOLD
from app.core.exceptions import (
    ResumeNotFoundError,
    ResumeSimilarityError,
    InvalidSessionError,
)
from app.utils.file_handler import extract_text_from_file
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/generate/upwork", tags=["proposals"])

# Global store instances (initialized on startup)
project_store: ProjectStoreService = None
review_store: ReviewStoreService = None
resume_store: ResumeStoreService = None


def set_stores(
    projects: ProjectStoreService,
    reviews: ReviewStoreService,
    resumes: ResumeStoreService,
) -> None:
    """Set global store instances."""
    global project_store, review_store, resume_store
    project_store = projects
    review_store = reviews
    resume_store = resumes


@router.post("")
def generate_upwork_proposal(req: UpworkRequest):
    """
    Generate Upwork proposal for a job requirement.
    
    Args:
        req: Proposal request with requirement and optional resume_name
        
    Returns:
        JSON with session_id and generated proposal
    """
    try:
        db: Session = SessionLocal()
        llm_service = LLMService(groq_client)
        
        # Search for relevant projects and reviews
        projects_text = project_store.search(req.requirement)
        logger.info(f"Project search results:\n{projects_text}\n---")
        
        review_text = review_store.search(req.requirement)
        logger.info(f"Review search results:\n{review_text}\n---")
        
        # Get resume
        if req.resume_name:
            resume_data = resume_store.get_by_name(req.resume_name)
            logger.info(f"Resume search result for '{req.resume_name}':\n{resume_data}\n---")
            
            if not resume_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Resume with name '{req.resume_name}' not found."
                )
        else:
            resume_data = resume_store.search(req.requirement)
            logger.info(f"Resume search result for semantic search:\n{resume_data}\n---")
            
            similarity_score = resume_data.get("score", 0)
            
            # Check threshold
            if similarity_score < RESUME_SIMILARITY_THRESHOLD:
                return {
                    "error": "Requirements do not match with your resume list. "
                             "Do you want to proceed with the most similar resume "
                             "or do you want to upload a new one?",
                    "best_match_resume": resume_data["metadata"]["name"],
                    "similarity_score": similarity_score
                }
        
        resume_text = resume_data["text"]
        logger.info(f"Using resume text:\n{resume_text}\n---")
        
        combined_text = f"""
Candidate Resume:
{resume_text}

Structured Project Data:
{projects_text}

Client Feedback Data:
{review_text}
"""
        
        # Generate proposal
        proposal = llm_service.generate_proposal(
            requirement=req.requirement,
            projects_text=combined_text
        )
        logger.info(f"Generated proposal:\n{proposal}\n---")
        
        # Create conversation history
        conversation = [
            {"role": "user", "content": req.requirement},
            {"role": "assistant", "content": proposal}
        ]
        
        # Save session to database
        session_obj = ApplicationSession(
            requirement=req.requirement,
            resume_text=resume_text,
            proposal_text=proposal,
            conversation_json=json.dumps(conversation)
        )
        
        db.add(session_obj)
        db.commit()
        db.refresh(session_obj)
        db.close()
        
        logger.info(f"Created session: {session_obj.id}")
        
        return {
            "session_id": session_obj.id,
            "proposal": proposal
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating proposal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/followup")
def generate_followup(req: FollowupRequest):
    """
    Generate answer to a follow-up question on a proposal.
    
    Args:
        req: Follow-up request with session_id and question
        
    Returns:
        JSON with answer or new proposal (if new job requirement detected)
    """
    try:
        db: Session = SessionLocal()
        llm_service = LLMService(groq_client)
        
        # Get session
        session_obj = db.query(ApplicationSession).filter_by(id=req.session_id).first()
        logger.info(f"Retrieved session for ID {req.session_id}: {session_obj}")
        
        if not session_obj:
            raise HTTPException(status_code=404, detail="Invalid session_id")
        
        conversation = json.loads(session_obj.conversation_json)
        logger.info(f"Current conversation history:\n{conversation}\n---")
        
        # Classify intent
        intent = llm_service.classify_conversation_intent(
            requirement=session_obj.requirement,
            proposal=session_obj.proposal_text,
            conversation=conversation[-4:],  # Keep context short
            new_input=req.question
        )
        
        logger.info(f"Detected intent: {intent}")
        
        # CASE 1: New Job Requirement
        if intent == "NEW_JOB_REQUIREMENT":
            projects_text = project_store.search(req.question)
            review_text = review_store.search(req.question)
            
            combined_text = f"""
Candidate Resume:
{session_obj.resume_text}

Structured Project Data:
{projects_text}

Client Feedback Data:
{review_text}
"""
            
            proposal = llm_service.generate_proposal(
                requirement=req.question,
                projects_text=combined_text
            )
            
            # Reset conversation
            conversation.append({"role": "user", "content": req.question})
            conversation.append({"role": "assistant", "content": proposal})
            
            session_obj.requirement = req.question
            session_obj.proposal_text = proposal
            session_obj.conversation_json = json.dumps(conversation)
            db.commit()
            
            logger.info("Regenerated proposal for new job requirement")
            
            return {"proposal": proposal}
        
        # CASE 2: Follow-up Question
        elif intent == "FOLLOWUP_QUESTION":
            answer = llm_service.generate_followup_answer(
                requirement=session_obj.requirement,
                resume_text=session_obj.resume_text,
                proposal_text=session_obj.proposal_text,
                conversation=conversation,
                question=req.question
            )
            
            conversation.append({"role": "user", "content": req.question})
            conversation.append({"role": "assistant", "content": answer})
            
            session_obj.conversation_json = json.dumps(conversation)
            db.commit()
            
            logger.info("Generated follow-up answer")
            
            return {"answer": answer}
        
        # CASE 3: Not Job Related
        else:
            return {
                "answer": "I am a job-application assistant and can only assist with "
                          "job-related queries such as proposals, requirements, resume "
                          "details, or hiring discussions."
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating follow-up: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/upload")
async def generate_with_upload(
    requirement: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Generate proposal with uploaded resume (one-time use).
    
    Args:
        requirement: Job requirement
        file: Resume file (PDF or TXT)
        
    Returns:
        JSON with session_id and generated proposal
    """
    if not file:
        raise HTTPException(
            status_code=400,
            detail="No resume file uploaded."
        )
    
    try:
        db: Session = SessionLocal()
        llm_service = LLMService(groq_client)
        
        # Extract resume text
        resume_text = await extract_text_from_file(file)
        
        # Search for projects and reviews
        projects_text = project_store.search(requirement)
        review_text = review_store.search(requirement)
        
        combined_text = f"""
Candidate Resume:
{resume_text}

Structured Project Data:
{projects_text}

Client Feedback:
{review_text}
"""
        
        # Generate proposal
        proposal = llm_service.generate_proposal(
            requirement=requirement,
            projects_text=combined_text
        )
        
        # Create conversation history
        conversation = [
            {"role": "user", "content": requirement},
            {"role": "assistant", "content": proposal}
        ]
        
        # Save session
        session_obj = ApplicationSession(
            requirement=requirement,
            resume_text=resume_text,
            proposal_text=proposal,
            conversation_json=json.dumps(conversation)
        )
        
        db.add(session_obj)
        db.commit()
        db.refresh(session_obj)
        db.close()
        
        logger.info(f"Created session with uploaded resume: {session_obj.id}")
        
        return {
            "session_id": session_obj.id,
            "proposal": proposal
        }
        
    except Exception as e:
        logger.error(f"Error generating proposal from upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
