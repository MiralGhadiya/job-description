# app/schemas.py
from pydantic import BaseModel
from typing import Optional

class UpworkRequest(BaseModel):
    requirement: str
    resume_name: Optional[str] = None
    
class UpworkResponse(BaseModel):
    proposal: str
