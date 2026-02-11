# app/schemas.py
from pydantic import BaseModel

class UpworkRequest(BaseModel):
    requirement: str
    
    
class UpworkResponse(BaseModel):
    proposal: str
