# app/main.py
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from app.config import groq_client
# from app.config import gemini_model

from app.vectorstore import FaissProjectStore
from app.review_store import FaissReviewStore
from app.resume_store import FaissResumeStore

from app.llm_core import generate_upwork_proposal
from app.schemas import UpworkRequest, UpworkResponse



app = FastAPI(
    title="Job Application Generator API",
    version="0.1.0"
)

review_store = None
project_store = None
resume_store = None

@app.on_event("startup")
def startup_event():
    global review_store, project_store, resume_store

    review_store = FaissReviewStore()
    project_store = FaissProjectStore()
    resume_store = FaissResumeStore()

    review_store.load()
    project_store.load()
    resume_store.load()

    print("FAISS stores loaded successfully.")


@app.post("/generate/upwork", response_class=PlainTextResponse)
def generate_upwork(req: UpworkRequest):
    
    projects_text = project_store.search(req.requirement, top_k=3)
    review_text = review_store.search(req.requirement, top_k=2)
    resume_data = resume_store.search(req.requirement) 
    
    resume_text = resume_data["text"]
    
    combined_text = f"""
        Candidate Resume:
        {resume_text}

        Relevant Projects:
        {projects_text}

        Relevant Client Feedback:
        {review_text}
    """

    proposal = generate_upwork_proposal(
        client=groq_client,
        requirement=req.requirement,
        projects_text=combined_text
    )
    
    # proposal = generate_upwork_proposal(
    #     model=gemini_model,
    #     requirement=req.requirement,
    #     projects_text=combined_text
    # )
    
    return proposal
 
     
@app.post("/debug/search")
def debug_search(payload: dict):
    query = payload.get("query")
    top_k = payload.get("top_k", 5)

    if not query:
        return {"error": "query is required"}

    results = project_store.search_debug(query, top_k=top_k)
    return {"results": results}
