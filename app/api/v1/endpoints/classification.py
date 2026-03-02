# app/api/v1/endpoints/classification.py
"""
Classification endpoints for intent and job-related classification.
"""
from fastapi import APIRouter, Depends
from app.schemas import UpworkRequest
from app.services.llm_service import LLMService
from app.core.constants import groq_client
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/classify", tags=["classification"])


@router.post("")
def classify_input(req: UpworkRequest):
    """
    Classify if input is job-related.
    
    Args:
        req: Classification request with requirement text
        
    Returns:
        JSON with is_job_related boolean
    """
    llm_service = LLMService(groq_client)
    is_job_related = llm_service.classify_job_intent(req.requirement)
    
    return {"is_job_related": is_job_related}
