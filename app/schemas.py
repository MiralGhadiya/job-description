# app/schemas.py
from pydantic import BaseModel

class UpworkRequest(BaseModel):
    requirement: str
    projects: str  # later this will come from vector DB

class UpworkResponse(BaseModel):
    proposal: str
