# Architecture Diagram and Flow

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT (Frontend/API Calls)                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   📡 API LAYER (app/api/v1/endpoints/)              │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ classification│ │ proposals    │  │ resumes      │             │
│  └────┬─────────┘  └────┬─────────┘  └────┬────────┘             │
│  ┌────┴──┐  ┌────────────┴────────────┐  ┌──┴─────────┐           │
│  │sessions│  │sessions              │  │ sync      │           │
│  └────┬──┘  │debug                  │  └──┬─────────┘           │
│       │      └────────────┬──────────┘     │                    │
│       └──────────────┬────┴────────────────┘                    │
└──────────────────────┼──────────────────────────────────────────┘
                       │ (Uses)
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                ⚙️ SERVICES LAYER (app/services/)                    │
│                                                                     │
│  ┌──────────────────────────┐  ┌─────────────────────────────┐    │
│  │   LLMService             │  │ VectorStoreService (Base)   │    │
│  │                          │  │                             │    │
│  │ • classify_job_intent()  │  │ • load()                    │    │
│  │ • generate_proposal()    │  │ • save()                    │    │
│  │ • generate_followup...() │  │ • _add_embeddings()         │    │
│  │ • classify_conv...()     │  │ • _build_index()            │    │
│  └──────────────────────────┘  └──────────┬──────────────────┘    │
│                                            │ (Extends)             │
│                    ┌───────────────────────┼───────────────────┐   │
│                    ▼                       ▼                   ▼   │
│         ┌──────────────────────┐ ┌──────────┐   ┌──────────┐      │
│         │ProjectStoreService   │ │ReviewStore │ResumesStore│      │
│         │• search()            │ │• search()  │• add()    │      │
│         │• search_debug()      │ │• build...()│• delete() │      │
│         │• build_from_excel()  │ │           │• get...() │      │
│         └──────────────────────┘ └──────────┘ └──────────┘      │
└──────────────────────────┬───────────────────────────────────────┘
                           │ (Uses)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  🛠️ UTILS LAYER (app/utils/)                        │
│                                                                     │
│  ┌──────────────────────────┐  ┌─────────────────────────────┐    │
│  │  file_handler.py         │  │  google_sheet.py            │    │
│  │                          │  │                             │    │
│  │ • extract_text_from...() │  │ • convert_google_sheet...() │    │
│  │   (PDF/TXT parsing)      │  │ • load_google_sheet_df()    │    │
│  └──────────────────────────┘  └─────────────────────────────┘    │
└──────────────────────────┬───────────────────────────────────────┘
                           │ (Uses)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│               📋 CORE LAYER (app/core/)                              │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ constants.py │  │exceptions.py │  │  logging.py  │             │
│  │              │  │              │  │              │             │
│  │• All config  │  │• Custom excs │  │• get_logger()│             │
│  │• Prompts     │  │  for every   │  │• Log format  │             │
│  │• Paths       │  │  error type  │  │• Log level   │             │
│  │• Models      │  │              │  │              │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└──────────────────────────┬───────────────────────────────────────┘
                           │ (Configures)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│               🔗 EXTERNAL SERVICES & DATA                            │
│                                                                     │
│  ┌──────────────────────┐  ┌──────────────────────┐                │
│  │    Groq LLM         │  │   PostgreSQL DB      │                │
│  │  (API Client)       │  │ (Sessions & History) │                │
│  └──────────────────────┘  └──────────────────────┘                │
│  ┌──────────────────────┐  ┌──────────────────────┐                │
│  │   FAISS Indexes     │  │  Google Sheets       │                │
│  │ (Embeddings)        │  │ (Project/Review Data)│                │
│  └──────────────────────┘  └──────────────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Generate Proposal

```
User/Frontend
    │
    │ POST /api/v1/generate/upwork
    │ { "requirement": "...", "resume_name": "..." }
    │
    ▼
proposals.generate_upwork_proposal()
    │
    ├─→ ProjectStoreService.search(requirement)
    │     └─→ Embed requirement
    │     └─→ Search FAISS index
    │     └─→ Return top 3 projects
    │
    ├─→ ReviewStoreService.search(requirement)
    │     └─→ Embed requirement
    │     └─→ Search FAISS index
    │     └─→ Return top 2 reviews
    │
    ├─→ ResumeStoreService.get_by_name() OR .search()
    │     ├─→ If by name: Return exact match
    │     └─→ If search: Return most similar
    │
    ├─→ Combine all text (resume + projects + reviews)
    │
    ├─→ LLMService.generate_proposal()
    │     ├─→ Build system prompts
    │     ├─→ Call Groq API
    │     └─→ Return generated proposal
    │
    ├─→ Create ApplicationSession record
    │     └─→ Store in PostgreSQL
    │
    └─→ Return JSON
        {
            "session_id": "...",
            "proposal": "..."
        }
    │
    ▼
Frontend Display
```

---

## Data Flow: Answer Follow-up Question

```
User/Frontend
    │
    │ POST /api/v1/generate/upwork/followup
    │ { "session_id": "...", "question": "..." }
    │
    ▼
proposals.generate_followup()
    │
    ├─→ Load session from DB
    │     └─→ Get requirement, resume, proposal, conversation
    │
    ├─→ LLMService.classify_conversation_intent()
    │     ├─→ Classify as: NEW_JOB, FOLLOWUP_Q, NOT_JOB
    │     └─→ Return intent type
    │
    ├─→ IF NEW_JOB_REQUIREMENT:
    │     ├─→ ProjectStoreService.search(new_requirement)
    │     ├─→ ReviewStoreService.search(new_requirement)
    │     ├─→ LLMService.generate_proposal(new_requirement)
    │     ├─→ Update session with new proposal
    │     └─→ Return {"proposal": "..."}
    │
    ├─→ ELIF FOLLOWUP_QUESTION:
    │     ├─→ LLMService.generate_followup_answer()
    │     ├─→ Append to conversation history
    │     ├─→ Update session in DB
    │     └─→ Return {"answer": "..."}
    │
    └─→ ELSE NOT_JOB_RELATED:
        └─→ Return standard rejection message
    │
    ▼
Frontend Display
```

---

## Data Flow: Upload Resume

```
User/Frontend
    │
    │ POST /api/v1/resumes/upload
    │ Form: resume_name="My Resume", file=<PDF/TXT>
    │
    ▼
resumes.upload_resume()
    │
    ├─→ file_handler.extract_text_from_file(file)
    │     ├─→ IF PDF: pdfplumber.open() → extract text
    │     ├─→ IF TXT: read and decode
    │     └─→ Return extracted text
    │
    ├─→ ResumeStoreService.add_resume(name, text)
    │     ├─→ Embed text
    │     ├─→ Add to FAISS index
    │     ├─→ Update metadata
    │     └─→ Save to disk
    │
    └─→ Return {"status": "success", "resume_name": "..."}
    │
    ▼
Frontend Confirmation
```

---

## Data Flow: Sync Google Sheet Projects

```
User/Frontend
    │
    │ POST /api/v1/sync/google-sheet/projects
    │ { "sheet_url": "https://docs.google.com/spreadsheets/..." }
    │
    ▼
sync.sync_projects_from_google_sheet()
    │
    ├─→ google_sheet.convert_google_sheet_to_csv_url(url)
    │     └─→ Extract sheet ID and convert to CSV export URL
    │
    ├─→ google_sheet.load_google_sheet_dataframe(csv_url)
    │     ├─→ Fetch CSV from Google
    │     ├─→ Check permissions (public/private)
    │     └─→ Parse into DataFrame
    │
    ├─→ ProjectStoreService reset (clear old data)
    │
    ├─→ Iterate DataFrame rows:
    │     ├─→ Extract fields (PROJECT NAME, INDUSTRY, etc.)
    │     ├─→ Format as text
    │     ├─→ Append to texts list
    │
    ├─→ Embed all texts
    │
    ├─→ Build FAISS index
    │
    ├─→ Save to disk
    │
    └─→ Return {"status": "success", "rows": N}
    │
    ▼
Frontend Confirmation
```

---

## Class Hierarchy: Vector Stores

```
VectorStoreService (Base Class)
├── index: Optional[FAISS]
├── texts: List[str]
├── metadata: List[Dict]
├── model: SentenceTransformer
│
├── Methods:
│  ├── load()
│  ├── save()
│  ├── _add_embeddings()
│  └── _build_index()
│
├─── ProjectStoreService
│    ├── build_from_excel()
│    ├── search(query, top_k) -> str
│    ├── search_debug(query, top_k) -> List[Dict]
│    └── _row_to_text()
│
├─── ReviewStoreService
│    ├── build_from_dataframe()
│    ├── search(query, top_k) -> str
│    └── _row_to_text()
│
└─── ResumeStoreService
     ├── get_by_name(name) -> Dict
     ├── add_resume(name, text)
     ├── delete_resume(name) -> bool
     ├── search(query, top_k) -> Dict
     └── list_all() -> List[str]
```

---

## Exception Hierarchy

```
Exception
│
└── JobApplicationException (Base)
    │
    ├── ResumeNotFoundError
    │   └── Raised when resume not found or already exists
    │
    ├── InvalidSessionError
    │   └── Raised when session_id invalid
    │
    ├── ResumeSimilarityError
    │   └── Raised when resume similarity < threshold
    │
    ├── InvalidGoogleSheetError
    │   └── Raised for Google Sheet issues (permissions, format, etc.)
    │
    ├── FileProcessingError
    │   └── Raised when file upload/parsing fails
    │
    ├── LLMGenerationError
    │   └── Raised when LLM API fails
    │
    └── VectorStoreError
        └── Raised when FAISS operations fail
```

---

## Configuration Organization

```
app/core/constants.py
│
├── LLM Configuration
│   ├── GROQ_MODEL
│   ├── PROPOSAL_TEMPERATURE
│   ├── PROPOSAL_MAX_TOKENS
│   ├── FOLLOWUP_TEMPERATURE
│   ├── FOLLOWUP_MAX_TOKENS
│   ├── INTENT_TEMPERATURE
│   └── INTENT_MAX_TOKENS
│
├── Vector Store Parameters
│   ├── DEFAULT_TOP_K_PROJECTS
│   ├── DEFAULT_TOP_K_REVIEWS
│   ├── DEFAULT_TOP_K_RESUMES
│   ├── RESUME_SIMILARITY_THRESHOLD
│   └── EMBED_MODEL
│
├── File Paths
│   ├── DATA_DIR
│   ├── PROJECTS_INDEX_PATH
│   ├── PROJECTS_META_PATH
│   ├── REVIEWS_INDEX_PATH
│   ├── REVIEWS_META_PATH
│   ├── RESUMES_INDEX_PATH
│   └── RESUMES_META_PATH
│
├── Prompts
│   ├── GLOBAL_SCOPE_PROMPT
│   └── PROJECT_SHEETS
│
└── Other
    ├── API_TITLE
    ├── API_VERSION
    ├── LOG_LEVEL
    └── LOG_FORMAT
```

---

## Request/Response Examples

### 1. Generate Proposal
**Request:**
```json
POST /api/v1/generate/upwork
{
  "requirement": "Need a Python REST API developer for microservices project",
  "resume_name": "My Resume"
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "proposal": "Hi, I'm [Name],\n\nI've reviewed your requirement..."
}
```

### 2. Answer Follow-up
**Request:**
```json
POST /api/v1/generate/upwork/followup
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "question": "What's your availability?"
}
```

**Response:**
```json
{
  "answer": "I'm available to start immediately with full-time commitment..."
}
```

### 3. Upload Resume
**Request:**
```
POST /api/v1/resumes/upload
Form Data:
  resume_name: "My Resume"
  file: <PDF/TXT file>
```

**Response:**
```json
{
  "status": "success",
  "resume_name": "My Resume"
}
```

### 4. List Resumes
**Request:**
```
GET /api/v1/resumes
```

**Response:**
```json
{
  "resumes": ["My Resume", "Latest Resume", "Backup Resume"]
}
```

### 5. List Sessions
**Request:**
```
GET /api/v1/sessions
```

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Need a Python REST API developer for microservices...",
    "created_at": "2025-02-25T10:30:00"
  },
  ...
]
```

---

## Dependency Graph

```
main_new.py
    ├── app/api/v1/__init__.py
    │   └── app/api/v1/endpoints/*.py
    │       ├── app/services/*.py
    │       │   ├── app/config.py (groq_client)
    │       │   ├── app/database.py (SessionLocal)
    │       │   ├── app/embeddings.py (embedding_model)
    │       │   └── app/models.py (ApplicationSession)
    │       └── app/utils/*.py
    │           └── third-party libraries (requests, pandas, pdfplumber)
    │
    ├── app/core/*.py
    │   ├── app/core/constants.py (imported by all)
    │   ├── app/core/exceptions.py (raised by services)
    │   └── app/core/logging.py (used everywhere)
    │
    └── FastAPI
        ├── SQLAlchemy (database)
        └── Groq (LLM)
```

---

## Deployment Checklist

```
Pre-deployment
  ☐ Test all endpoints with main_new.py
  ☐ Verify all responses match old code
  ☐ Check logging output
  ☐ Verify error handling for edge cases

Environment Setup
  ☐ Set GROQ_API_KEY environment variable
  ☐ Set DATABASE_URL environment variable
  ☐ Load FAISS indices (runs automatically on startup)

Code Changes
  ☐ Update Docker ENTRYPOINT (if using Docker)
  ☐ Update CI/CD pipeline (if applicable)
  ☐ Update frontend API calls (add /api/v1 prefix or keep as-is)

Deployment
  ☐ Deploy app/main_new.py (or renamed to main.py)
  ☐ Verify health endpoint (/health)
  ☐ Test critical user flows
  ☐ Monitor logs for errors

Post-deployment
  ☐ Keep old main.py as backup for rollback
  ☐ Monitor performance metrics
  ☐ Collect user feedback
```

---

This architecture ensures your application is **production-ready, maintainable, and scalable**! 🚀
