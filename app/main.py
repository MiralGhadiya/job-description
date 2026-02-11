# app/main.py
from fastapi import FastAPI
from app.config import groq_client

from app.vectorstore import FaissProjectStore
from app.review_store import FaissReviewStore

from app.llm_core import generate_upwork_proposal
from app.schemas import UpworkRequest, UpworkResponse


app = FastAPI(
    title="Job Application Generator API",
    version="0.1.0"
)

review_store = FaissReviewStore()
project_store = FaissProjectStore()

review_store.load()
project_store.load()

@app.post("/generate/upwork", response_model=UpworkResponse)
def generate_upwork(req: UpworkRequest):
    
    projects_text = project_store.search(req.requirement, top_k=3)
    review_text = review_store.search(req.requirement, top_k=1)
    
    combined_text = f"""
        Relevant projects:
        {projects_text}
        
        Relevant client feedback:
        {review_text}
        """

    proposal = generate_upwork_proposal(
        client=groq_client,
        requirement=req.requirement,
        projects_text=combined_text,
    )
    return {"proposal": proposal}


@app.post("/debug/search")
def debug_search(payload: dict):
    query = payload.get("query")
    top_k = payload.get("top_k", 5)

    if not query:
        return {"error": "query is required"}

    results = project_store.search_debug(query, top_k=top_k)
    return {"results": results}
