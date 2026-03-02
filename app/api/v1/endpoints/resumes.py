# app/api/v1/endpoints/resumes.py
"""
Resume management endpoints.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.vectorstore_service import ResumeStoreService
from app.utils.file_handler import extract_text_from_file
from app.core.exceptions import ResumeNotFoundError, FileProcessingError
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/resumes", tags=["resumes"])

# Global store instance (initialized on startup)
resume_store: ResumeStoreService = None


def set_store(store: ResumeStoreService) -> None:
    """Set global store instance."""
    global resume_store
    resume_store = store


@router.get("")
def list_resumes():
    """
    List all stored resumes.
    
    Returns:
        JSON with list of resume names
    """
    try:
        resumes = resume_store.list_all()
        logger.info(f"Listed {len(resumes)} resumes")
        return {"resumes": resumes}
    except Exception as e:
        logger.error(f"Error listing resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_resume(
    resume_name: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Upload and save resume to store.
    
    Args:
        resume_name: Name for the resume
        file: Resume file (PDF or TXT)
        
    Returns:
        JSON with success status
    """
    try:
        # Extract text from file
        resume_text = await extract_text_from_file(file)
        
        # Add to store
        resume_store.add_resume(resume_name, resume_text)
        
        logger.info(f"Successfully uploaded resume: {resume_name}")
        
        return {
            "status": "success",
            "resume_name": resume_name
        }
        
    except ResumeNotFoundError as e:
        logger.warning(f"Resume upload failed: {str(e)}")
        raise HTTPException(status_code=409, detail=str(e))
    except FileProcessingError as e:
        logger.error(f"File processing error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{resume_name}")
def delete_resume(resume_name: str):
    """
    Delete resume from store.
    
    Args:
        resume_name: Name of resume to delete
        
    Returns:
        JSON with deletion status
    """
    try:
        success = resume_store.delete_resume(resume_name)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Resume '{resume_name}' not found."
            )
        
        logger.info(f"Deleted resume: {resume_name}")
        
        return {
            "status": "deleted",
            "resume_name": resume_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
