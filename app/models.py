# app/models.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from app.database import Base


class ApplicationSession(Base):
    __tablename__ = "application_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement = Column(Text, nullable=False)
    resume_text = Column(Text, nullable=False)
    proposal_text = Column(Text, nullable=False)
    
    resume_summary = Column(Text, nullable=True)
    proposal_summary = Column(Text, nullable=True)
    
    conversation_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
