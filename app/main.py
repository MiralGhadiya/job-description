# app/main.py

import json
import pandas as pd
import faiss
import pdfplumber
from fastapi import FastAPI, Form, UploadFile, File, requests
from app.config import groq_client
# from app.config import gemini_model

from app.vectorstore import FaissProjectStore
from app.review_store import FaissReviewStore
from app.resume_store import FaissResumeStore

# from app.session_store import ApplicationSessionStore

from app.models import ApplicationSession
from app.database import SessionLocal
from app.schemas import UpworkRequest, FollowupRequest
from app.llm_core import generate_upwork_proposal, generate_followup_answer, classify_job_intent, classify_conversation_intent


app = FastAPI(
    title="Job Application Generator API",
    version="0.1.0"
)

review_store = None
project_store = None
resume_store = None

# session_store = ApplicationSessionStore()

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
    
    
@app.post("/classify")
def classify(req: UpworkRequest):
    is_job_related = classify_job_intent(
        client=groq_client,
        text=req.requirement
    )
    return {"is_job_related": is_job_related}


@app.post("/generate/upwork")
def generate_upwork(req: UpworkRequest):
    
    db = SessionLocal()
    
    projects_text = project_store.search(req.requirement, top_k=3)
    print(f"Project search results:\n{projects_text}\n---")
    
    review_text = review_store.search(req.requirement, top_k=2)
    print(f"Review search results:\n{review_text}\n---")
    
    if req.resume_name:
        resume_data = resume_store.get_by_name(req.resume_name)
        print(f"Resume search result for '{req.resume_name}':\n{resume_data}\n---")
        
        if not resume_data:
            return {
                "error": f"Resume with name '{req.resume_name}' not found."
            }
    else:
        resume_data = resume_store.search(req.requirement)
        print(f"Resume search result for semantic search:\n{resume_data}\n---")
        
        similarity_score = resume_data.get("score", 0)

        # 50% threshold check
        if similarity_score < 0.50:
            return {
                "error": "Requirements do not match with your resume list. Do you want to proceed with the most similar resume or do you want to upload a new one?",
                "best_match_resume": resume_data["metadata"]["name"],
                "similarity_score": similarity_score
            }
        
    resume_text = resume_data["text"]
    print(f"Using resume text:\n{resume_text}\n---")
    
    combined_text = f"""
        Candidate Resume:
        {resume_text}

        Structured Project Data:
        {projects_text}

        Client Feedback Data:
        {review_text}
    """

    proposal = generate_upwork_proposal(
        client=groq_client,
        requirement=req.requirement,
        projects_text=combined_text
    )
    print(f"Generated proposal:\n{proposal}\n---")
    
    # session_id = session_store.create({
    #     "requirement": req.requirement,
    #     "resume_text": resume_text,
    #     "proposal_text": proposal
    # })
    # prin.t(f"Created session with ID: {session_id}")
    
    conversation = [
        {"role": "user", "content": req.requirement},
        {"role": "assistant", "content": proposal}
    ]
    
    session_obj = ApplicationSession(
        requirement=req.requirement,
        resume_text=resume_text,
        proposal_text=proposal,
        conversation_json=json.dumps(conversation)
    )
    
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)

    return {
        "session_id": session_obj.id,
        "proposal": proposal
    }


@app.post("/generate/upwork/followup")
def generate_followup(req: FollowupRequest):
    
    db = SessionLocal()

    session_obj = db.query(ApplicationSession).filter_by(id=req.session_id).first()
    print(f"Retrieved session object from DB for ID {req.session_id}: {session_obj}")
    
    if not session_obj:
        return {"error": "Invalid session_id"}
    
    conversation = json.loads(session_obj.conversation_json)
    print(f"Current conversation history:\n{conversation}\n---")

    # answer = generate_followup_answer(
    #     client=groq_client,
    #     requirement=session_obj.requirement,
    #     resume_text=session_obj.resume_text,
    #     proposal_text=session_obj.proposal_text,
    #     conversation=conversation,
    #     question=req.question
    # )

    # print(f"Generated follow-up answer:\n{answer}\n---")
    
    # conversation.append({"role": "user", "content": req.question})
    # conversation.append({"role": "assistant", "content": answer})

    # session_obj.conversation_json = json.dumps(conversation)

    # db.commit()
    
    # return {"answer": answer}
    
        # 🔎 Step 1: Let LLM decide intent
    intent = classify_conversation_intent(
        client=groq_client,
        requirement=session_obj.requirement,
        proposal=session_obj.proposal_text,
        conversation=conversation[-4:],  # keep context short
        new_input=req.question
    )

    print(f"!!!!!!!!!!!!!!!!!Detected intent: {intent}")

    # 🟢 CASE 1: New Job Requirement → Regenerate Proposal
    if intent == "NEW_JOB_REQUIREMENT":

        projects_text = project_store.search(req.question, top_k=3)
        review_text = review_store.search(req.question, top_k=2)

        combined_text = f"""
            Candidate Resume:
            {session_obj.resume_text}

            Structured Project Data:
            {projects_text}

            Client Feedback Data:
            {review_text}
        """

        proposal = generate_upwork_proposal(
            client=groq_client,
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

        return {"proposal": proposal}


    # 🟢 CASE 2: Follow-up Question
    elif intent == "FOLLOWUP_QUESTION":

        answer = generate_followup_answer(
            client=groq_client,
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

        return {"answer": answer}

    # 🔴 CASE 3: Not Job Related
    else:
        return {
            "answer": "I am a job-application assistant and can only assist with job-related queries such as proposals, requirements, resume details, or hiring discussions."
        }


     
@app.post("/debug/search")
def debug_search(payload: dict):
    query = payload.get("query")
    top_k = payload.get("top_k", 5)

    if not query:
        return {"error": "query is required"}

    results = project_store.search_debug(query, top_k=top_k)
    return {"results": results}


@app.get("/resumes")
def get_resumes():
    return {
        "resumes" : [meta["name"] for meta in resume_store.metadata]
    }
    
    
@app.post("/resumes/upload")
async def upload_resume(
    resume_name: str = Form(...),
    file: UploadFile = File(...)
):
    if file.filename.endswith(".pdf"):
        with pdfplumber.open(file.file) as pdf:
            resume_text = "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )
    else:
        resume_text = (await file.read()).decode("utf-8")

    try:
        resume_store.add_resume(resume_name, resume_text)
        resume_store.save()
    except ValueError as e:
        return {"error": str(e)}

    return {
        "status": "success",
        "resume_name": resume_name
    }
    
    
@app.delete("/resumes/{resume_name}")
def delete_resume(resume_name: str):

    success = resume_store.delete_resume(resume_name)

    if not success:
        return {"error": "Resume not found."}

    resume_store.save()

    return {
        "status": "deleted",
        "resume_name": resume_name
    }
    

@app.get("/sessions")
def list_sessions():
    db = SessionLocal()
    sessions = db.query(ApplicationSession).order_by(
        ApplicationSession.created_at.desc()
    ).all()

    return [
        {
            "id": s.id,
            "title": s.requirement[:60],
            "created_at": s.created_at
        }
        for s in sessions
    ]
    
    
@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    db = SessionLocal()

    session_obj = db.query(ApplicationSession).filter_by(id=session_id).first()

    if not session_obj:
        return {"error": "Session not found"}

    return {
        "id": session_obj.id,
        "requirement": session_obj.requirement,
        "proposal_text": session_obj.proposal_text,
        "conversation": json.loads(session_obj.conversation_json),
        "created_at": session_obj.created_at
    }
    
    
@app.post("/generate/upwork/upload")
async def generate_with_upload(
    requirement: str = Form(...),
    file: UploadFile = File(...)
):
    db = SessionLocal()

    # Extract text
    if file.filename.endswith(".pdf"):
        with pdfplumber.open(file.file) as pdf:
            resume_text = "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )
    else:
        resume_text = (await file.read()).decode("utf-8")

    # Do NOT use resume_store here
    projects_text = project_store.search(requirement, top_k=3)
    review_text = review_store.search(requirement, top_k=2)

    combined_text = f"""
    Candidate Resume:
    {resume_text}

    Structured Project Data:
    {projects_text}

    Client Feedback:
    {review_text}
    """

    proposal = generate_upwork_proposal(
        client=groq_client,
        requirement=requirement,
        projects_text=combined_text
    )

    conversation = [
        {"role": "user", "content": requirement},
        {"role": "assistant", "content": proposal}
    ]

    session_obj = ApplicationSession(
        requirement=requirement,
        resume_text=resume_text,
        proposal_text=proposal,
        conversation_json=json.dumps(conversation)
    )

    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)

    return {
        "session_id": session_obj.id,
        "proposal": proposal
    }
    
import re   
def convert_google_sheet_to_csv_url(url: str) -> str:
    """
    Converts Google Sheets sharing URL into CSV export URL.
    """

    # Already export link
    if "export?format=csv" in url:
        return url

    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    if not match:
        raise ValueError("Invalid Google Sheets URL format.")

    sheet_id = match.group(1)

    gid_match = re.search(r"gid=([0-9]+)", url)
    gid = gid_match.group(1) if gid_match else "0"

    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


def load_google_sheet_dataframe(sheet_url: str) -> pd.DataFrame:
    """
    Safely loads a Google Sheet into a DataFrame.
    Handles:
    - Private sheets
    - Permission errors
    - HTML instead of CSV
    - Empty sheets
    """

    csv_url = convert_google_sheet_to_csv_url(sheet_url)
    print(f"Converted Google Sheet URL to CSV URL: {csv_url}")

    try:
        response = requests.get(csv_url, timeout=10)

        if response.status_code != 200:
            raise ValueError("Unable to access sheet. Check sharing permissions.")

        content_type = response.headers.get("Content-Type", "")

        # Google returns text/html if not public
        if "text/html" in content_type:
            raise ValueError(
                "Sheet is not publicly accessible. "
                "Set sharing to 'Anyone with link → Viewer'."
            )

        df = pd.read_csv(csv_url)
        print(f"Loaded DataFrame with shape: {df.shape}")

        if df.empty:
            raise ValueError("Sheet loaded but contains no data.")

        return df

    except requests.exceptions.RequestException:
        raise ValueError("Network error while accessing Google Sheet.")

    except pd.errors.ParserError:
        raise ValueError("Failed to parse CSV. Ensure sheet contains valid tabular data.")


@app.post("/sync/google-sheet/projects")
def sync_projects_google_sheet(payload: dict):

    sheet_url = payload.get("sheet_url")
    if not sheet_url:
        return {"error": "sheet_url is required"}

    try:
        df = load_google_sheet_dataframe(sheet_url)
        print("PROJECT CSV HEADERS:", df.columns.tolist())

        # 🔥 FULL RESET
        project_store.index = None
        project_store.texts = []
        project_store.metadata = []

        for _, row in df.iterrows():
            project_name = str(row.get("PROJECT NAME", "")).strip()

            # Column B is blank header in your sheet
            # pandas may call it "" or "Unnamed: 1"
            project_type = str(row.get("", "")).strip()
            if not project_type:
                project_type = str(row.get("Unnamed: 1", "")).strip()

            industry = str(row.get("INDUSTRY", "")).strip()
            tech_stack = str(row.get("Tech Stack", "")).strip()
            description = str(row.get("DESCRIPTION", "")).strip()

            # Skip truly empty rows
            if not (project_name or industry or tech_stack or description):
                continue

            text = f"""
                Project: {project_name}
                Project Type: {project_type}
                Industry: {industry}
                Tech Stack: {tech_stack}
                Description: {description}
            """.strip()

            project_store.texts.append(text)
            project_store.metadata.append({
                "project_name": project_name,
                "project_type": project_type,
                "industry": industry,
            })

        # If nothing loaded, stop early (prevents empty faiss write)
        if not project_store.texts:
            return {"error": "No valid rows found in projects sheet. Check headers/rows."}

        embeddings = project_store.model.encode(
            project_store.texts,
            normalize_embeddings=True,
        ).astype("float32")

        dim = embeddings.shape[1]
        project_store.index = faiss.IndexFlatIP(dim)
        project_store.index.add(embeddings)

        # ✅ SAVE TO DISK
        from pathlib import Path
        import pickle

        DATA_DIR = Path("data")
        DATA_DIR.mkdir(exist_ok=True)

        faiss.write_index(project_store.index, str(DATA_DIR / "projects.faiss"))

        with open(DATA_DIR / "projects_meta.pkl", "wb") as f:
            pickle.dump((project_store.texts, project_store.metadata), f)

        # 🔥 reload so RAM matches disk immediately
        project_store.load()

        return {"status": "success", "rows": len(project_store.texts)}

    except Exception as e:
        return {"error": str(e)}
    
    
@app.post("/sync/google-sheet/reviews")
def sync_reviews_google_sheet(payload: dict):

    sheet_url = payload.get("sheet_url")
    if not sheet_url:
        return {"error": "sheet_url is required"}

    try:
        df = load_google_sheet_dataframe(sheet_url)

        # 🔥 FULL RESET
        review_store.index = None
        review_store.texts = []
        review_store.metadata = []

        for _, row in df.iterrows():
            text = review_store._row_to_text(row)
            if not text.strip():
                continue

            review_store.texts.append(text)
            review_store.metadata.append({
                "product": str(row.get("Product Name", "")).strip(),
                "rating": row.get("Rating"),
                "country": str(row.get("Country", "")).strip(),
            })

        # If no reviews exist, return success but with 0 rows (don’t crash)
        if not review_store.texts:
            return {"status": "success", "rows": 0, "message": "No review rows found."}

        embeddings = review_store.model.encode(
            review_store.texts,
            normalize_embeddings=True,
        ).astype("float32")

        dim = embeddings.shape[1]
        review_store.index = faiss.IndexFlatIP(dim)
        review_store.index.add(embeddings)

        from pathlib import Path
        import pickle

        DATA_DIR = Path("data")
        DATA_DIR.mkdir(exist_ok=True)

        faiss.write_index(review_store.index, str(DATA_DIR / "reviews.faiss"))

        with open(DATA_DIR / "reviews_meta.pkl", "wb") as f:
            pickle.dump((review_store.texts, review_store.metadata), f)

        review_store.load()

        return {"status": "success", "rows": len(review_store.texts)}

    except Exception as e:
        return {"error": str(e)}