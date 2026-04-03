# Production-Ready Code Refactoring Guide

## Overview

Your codebase has been refactored from monolithic to a properly structured, production-ready architecture following industry best practices.

## What Changed

### Before (Monolithic)
```
main.py (600+ lines)
├── All routes mixed together
├── LLM logic directly in routes
├── File handling inline
├── Global store variables
└── No error handling

llm_core.py (400+ lines)
├── LLM functions
├── Prompts hardcoded
├── No logging
└── Direct client calls

vectorstore.py, resume_store.py, review_store.py
├── Duplicated logic
├── No consistent interface
└── Tight coupling
```

### After (Layered Architecture)
```
app/
├── core/                    # Configuration & Exceptions
├── api/v1/endpoints/       # HTTP Routes (thin layer)
├── services/               # Business Logic (reusable)
├── utils/                  # Helper Functions
├── config.py               # External Configuration
├── models.py               # Data Models
└── main_new.py            # Application Factory
```

## Architecture Layers

### 1. **Core Layer** (`app/core/`)
**Responsibility**: Configuration, constants, and exception handling

- **constants.py**: Single source of truth for all constants
  - Model names, API temperatures
  - File paths, search parameters
  - Prompts and configuration values
  
- **exceptions.py**: Custom exception hierarchy
  - Type-safe error handling
  - Consistent error responses
  
- **logging.py**: Centralized logging
  - Consistent formatting across application

**Benefits**:
- Easy to change configuration without touching code logic
- Tests can use different configurations
- Clear error semantics

---

### 2. **Service Layer** (`app/services/`)
**Responsibility**: Business logic independent of HTTP

#### LLMService
```python
class LLMService:
    def classify_job_intent(text: str) -> bool
    def generate_proposal(requirement, projects_text) -> str
    def generate_followup_answer(...) -> str
    def classify_conversation_intent(...) -> str
```

**Advantages**:
- Can be used in CLI, scheduled tasks, etc.
- Easy to test in isolation
- Reusable across endpoints

#### VectorStoreService (and subclasses)
```python
class ProjectStoreService(VectorStoreService):
    def load() -> None
    def search(query, top_k) -> str
    def build_from_excel(path) -> int

class ResumeStoreService(VectorStoreService):
    def add_resume(name, text) -> None
    def delete_resume(name) -> bool
    def search(query, top_k) -> Dict
    def list_all() -> List[str]

class ReviewStoreService(VectorStoreService):
    def build_from_dataframe(df) -> int
    def search(query, top_k) -> str
```

**Advantages**:
- Single interface for all vector operations
- Consistent error handling
- Easy to swap FAISS for another library if needed

---

### 3. **API Layer** (`app/api/v1/endpoints/`)
**Responsibility**: HTTP request/response handling

Each endpoint module is simple and focused:

```python
@router.post("/generate/upwork")
def generate_upwork_proposal(req: UpworkRequest):
    llm_service = LLMService(groq_client)
    projects = project_store.search(req.requirement)
    proposal = llm_service.generate_proposal(...)
    return {"session_id": ..., "proposal": ...}
```

**Advantages**:
- Endpoints are thin and easy to understand
- Logic is in services, not routes
- Easy to add authentication, logging, etc.
- Easy to test by mocking services

---

### 4. **Utils Layer** (`app/utils/`)
**Responsibility**: Common operations, third-party integrations

```python
# File handling
async def extract_text_from_file(file: UploadFile) -> str

# Google Sheets
def convert_google_sheet_to_csv_url(url: str) -> str
def load_google_sheet_dataframe(sheet_url: str) -> DataFrame
```

**Advantages**:
- Reusable across multiple endpoints
- Easy to add more utility functions
- Centralized third-party integration logic

---

## Architectural Principles

### 1. **Separation of Concerns**
Each layer has a single responsibility:
- **Core**: Configuration
- **Services**: Business logic
- **API**: HTTP handling
- **Utils**: Common operations

### 2. **Dependency Inversion**
- Endpoints depend on services (abstract)
- Services don't depend on HTTP layer
- Easy to test in isolation

### 3. **DRY (Don't Repeat Yourself)**
- Services encapsulate common logic
- Utils consolidate helper functions
- Constants defined in one place

### 4. **Scalability**
- Easy to add new endpoints (just import services)
- Easy to add new services (doesn't affect endpoints)
- API versioning ready (v1, v2, etc.)

---

## Code Maps

### Flow: Generate Proposal
```
POST /api/v1/generate/upwork
    ↓
proposals.py :: generate_upwork_proposal()
    ├─→ ProjectStoreService.search()
    ├─→ ReviewStoreService.search()
    ├─→ ResumeStoreService.search()
    └─→ LLMService.generate_proposal()
    ↓
ApplicationSession saved to DB
    ↓
JSON response with proposal
```

### Flow: Answer Follow-up
```
POST /api/v1/generate/upwork/followup
    ↓
proposals.py :: generate_followup()
    ├─→ Load session from DB
    ├─→ LLMService.classify_conversation_intent()
    ├─→ (NEW_JOB) → regenerate proposal
    ├─→ (FOLLOWUP) → LLMService.generate_followup_answer()
    └─→ (NOT_JOB) → return standard response
    ↓
Update conversation history
    ↓
JSON response
```

---

## Module Responsibilities Quick Reference

| Module | Purpose | Key Classes/Functions |
|--------|---------|----------------------|
| `constants.py` | Configuration | All constants |
| `exceptions.py` | Error types | Custom exceptions |
| `logging.py` | Logging setup | get_logger() |
| `llm_service.py` | LLM operations | LLMService |
| `vectorstore_service.py` | Vector operations | ProjectStoreService, ReviewStoreService, ResumeStoreService |
| `file_handler.py` | File processing | extract_text_from_file() |
| `google_sheet.py` | Google Sheets | load_google_sheet_dataframe() |
| `classification.py` | Classification routes | classify_input() |
| `proposals.py` | Proposal routes | generate_upwork_proposal(), generate_followup() |
| `resumes.py` | Resume routes | list_resumes(), upload_resume(), delete_resume() |
| `sessions.py` | Session routes | list_sessions(), get_session() |
| `sync.py` | Sync routes | sync_projects_from_google_sheet(), sync_reviews_from_google_sheet() |
| `debug.py` | Debug routes | debug_search() |

---

## Error Handling Strategy

**Custom Exceptions** (in `core/exceptions.py`):
```python
class JobApplicationException(Exception)  # Base
    ├── ResumeNotFoundError
    ├── InvalidSessionError
    ├── ResumeSimilarityError
    ├── InvalidGoogleSheetError
    ├── FileProcessingError
    ├── LLMGenerationError
    └── VectorStoreError
```

**HTTP Response Mapping**:
- 200: Success
- 400: Bad request (validation, invalid sheets)
- 404: Not found (resume, session)
- 409: Conflict (duplicate resume)
- 500: Server error (LLM, vectorstore failures)

**Logging**:
- INFO: Normal operations
- WARNING: Expected errors (resume not found, low similarity)
- ERROR: Unexpected errors (LLM failure, file processing)

---

## Testing Strategy

Each layer can be tested independently:

### Unit Tests (Services)
```python
def test_classify_job_intent():
    service = LLMService(mock_groq_client)
    result = service.classify_job_intent("job description")
    assert result == True

def test_add_resume():
    store = ResumeStoreService()
    store.add_resume("test", "resume content")
    assert store.get_by_name("test") is not None
```

### Integration Tests (Endpoints)
```python
def test_generate_proposal_endpoint():
    response = client.post("/api/v1/generate/upwork", json={
        "requirement": "...",
        "resume_name": "..."
    })
    assert response.status_code == 200
    assert "session_id" in response.json()
```

---

## Migration Checklist

- [ ] Test all endpoints with `main_new.py`
- [ ] Verify all responses match original endpoints
- [ ] Update any CI/CD pipelines to use new entry point
- [ ] Backup original `main.py`
- [ ] Rename `main_new.py` to `main.py`
- [ ] Remove legacy files:
  - [ ] Old `main.py` (backup first)
  - [ ] `llm_core.py`
  - [ ] `vectorstore.py`
  - [ ] `resume_store.py`
  - [ ] `review_store.py`
- [ ] Update documentation
- [ ] Deploy to production

---

## Next Steps for Enhancement

1. **Database**: Migrate from JSON to proper schemas
   - Store summaries, ratings, timestamps
   - Add indexes for performance
   
2. **Caching**: Add Redis for frequently accessed data
   - Cache embedding model
   - Cache search results
   
3. **Authentication**: Add API key/JWT authentication
   - Middleware in app factory
   - Rate limiting
   
4. **Monitoring**: Add metrics and tracing
   - Prometheus metrics
   - OpenTelemetry tracing
   
5. **Testing**: Full test suite
   - Unit tests for services
   - Integration tests for endpoints
   - Load testing
   
6. **Documentation**: API specs
   - OpenAPI/Swagger configuration
   - Detailed endpoint documentation
   
7. **Async**: Make database calls async
   - Use SQLAlchemy async ORM
   - Async file operations

---

## Questions?

Refer to specific files:
- Architecture questions → STRUCTURE.md
- Configuration → app/core/constants.py
- Error handling → app/core/exceptions.py
- Service implementation → app/services/
- Endpoint implementation → app/api/v1/endpoints/
