# app/api/v1/endpoints/sessions.py
"""
Session management endpoints.
"""
import json
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import SessionLocal
from app.models import ApplicationSession
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("")
def list_sessions():
    """
    List all application sessions.
    
    Returns:
        JSON with list of sessions
    """
    try:
        db: Session = SessionLocal()
        sessions = db.query(ApplicationSession).order_by(
            desc(ApplicationSession.created_at)
        ).all()
        
        result = [
            {
                "id": s.id,
                "title": s.requirement[:60],
                "created_at": s.created_at.isoformat() if s.created_at else None
            }
            for s in sessions
        ]
        
        logger.info(f"Listed {len(result)} sessions")
        db.close()
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}")
def get_session(session_id: str):
    """
    Get session details.
    
    Args:
        session_id: Session ID
        
    Returns:
        JSON with session details
    """
    try:
        db: Session = SessionLocal()
        session_obj = db.query(ApplicationSession).filter_by(id=session_id).first()
        
        if not session_obj:
            raise HTTPException(status_code=404, detail="Session not found")
        
        result = {
            "id": session_obj.id,
            "requirement": session_obj.requirement,
            "proposal_text": session_obj.proposal_text,
            "conversation": json.loads(session_obj.conversation_json),
            "created_at": session_obj.created_at.isoformat() if session_obj.created_at else None
        }
        
        logger.info(f"Retrieved session: {session_id}")
        db.close()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
