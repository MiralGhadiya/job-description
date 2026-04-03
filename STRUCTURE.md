# Project Structure

## Directory Layout

```
app/
├── core/                          # Core configuration and exceptions
│   ├── __init__.py
│   ├── constants.py              # All application constants
│   ├── exceptions.py             # Custom exception classes
│   └── logging.py                # Logging configuration
│
├── api/                           # API layer with versioning
│   ├── __init__.py
│   └── v1/                        # API v1 endpoints
│       ├── __init__.py
│       └── endpoints/             # Endpoint modules
│           ├── __init__.py
│           ├── classification.py  # Job intent classification
│           ├── proposals.py       # Proposal generation
│           ├── resumes.py         # Resume management
│           ├── sessions.py        # Session management
│           ├── sync.py            # Google Sheets sync
│           └── debug.py           # Debug utilities
│
├── services/                      # Business logic layer
│   ├── __init__.py
│   ├── llm_service.py            # LLM operations (Groq)
│   └── vectorstore_service.py    # Vector store operations (FAISS)
│
├── utils/                         # Utility functions
│   ├── __init__.py
│   ├── file_handler.py           # File upload processing
│   └── google_sheet.py           # Google Sheets utilities
│
├── main_new.py                    # Production application factory
├── config.py                      # API client configuration
├── database.py                    # Database setup
├── models.py                      # SQLAlchemy models
├── schemas.py                     # Pydantic schemas
├── embeddings.py                  # Embedding model setup
│
├── vectorstore.py                 # (Legacy - can be removed)
├── resume_store.py                # (Legacy - refactored to services)
├── review_store.py                # (Legacy - refactored to services)
└── llm_core.py                    # (Legacy - refactored to services)
```

## Layer Explanation

### Core Layer (`app/core/`)
- **constants.py**: Centralized configuration constants
  - LLM model names, temperature settings
  - FAISS search parameters
  - File paths
  - Prompts
  
- **exceptions.py**: Custom exception classes for different error scenarios
  - ResumeNotFoundError
  - InvalidSessionError
  - LLMGenerationError
  - etc.
  
- **logging.py**: Centralized logging setup
  - Consistent logging across application
  - Easy to modify log format in one place

### API Layer (`app/api/v1/endpoints/`)
- **classification.py**: Job intent and content classification
- **proposals.py**: Proposal generation (stored, uploaded, follow-up)
- **resumes.py**: Resume CRUD operations
- **sessions.py**: Application session management
- **sync.py**: Data synchronization from Google Sheets
- **debug.py**: Debugging and inspection tools

Each endpoint module:
- Handles HTTP requests/responses
- Calls service layer methods
- Returns appropriate error responses
- Logs operations

### Services Layer (`app/services/`)
- **llm_service.py**: LLM operations
  - classify_job_intent()
  - generate_proposal()
  - generate_followup_answer()
  - classify_conversation_intent()
  
- **vectorstore_service.py**: FAISS operations
  - ProjectStoreService
  - ReviewStoreService
  - ResumeStoreService

Service classes:
- Encapsulate business logic
- Manage state and persistence
- Abstract away implementation details
- Handle errors gracefully

### Utils Layer (`app/utils/`)
- **file_handler.py**: File upload processing
  - extract_text_from_file() - PDF/TXT extraction
  
- **google_sheet.py**: Google Sheets integration
  - convert_google_sheet_to_csv_url()
  - load_google_sheet_dataframe()

## Key Improvements

### 1. Separation of Concerns
- **API Layer**: Handles HTTP requests/responses
- **Services Layer**: Handles business logic
- **Utils Layer**: Handles common operations
- **Core Layer**: Handles configuration

### 2. Reusability
- Services can be imported and used in multiple endpoints
- Utils can be used across application
- Constants defined in one place

### 3. Testability
- Each layer can be tested independently
- Services don't depend on HTTP layer
- Easy to mock dependencies

### 4. Maintainability
- Clear responsibility for each module
- Easy to find and modify code
- Constants centralized
- Consistent error handling

### 5. Scalability
- Easy to add new endpoints
- Easy to add new services
- API versioning (v1, v2, etc.)
- Database operations isolated

### 6. Error Handling
- Custom exceptions for different scenarios
- Consistent error responses
- Proper HTTP status codes
- Detailed logging

### 7. Logging
- Centralized logging configuration
- Consistent log format
- Easy to change log level

## Migration Path

### Step 1: Keep Old Code as Backup
- Original `main.py`, `llm_core.py`, etc. remain unchanged

### Step 2: Use New Application
- Switch to `main_new.py` which uses refactored code
- Test all endpoints thoroughly

### Step 3: Remove Legacy Code
- Once tested, remove old files:
  - `main.py` → use `main_new.py`
  - `llm_core.py` → removed (now in services)
  - `vectorstore.py`, `resume_store.py`, `review_store.py` → removed
  
### Step 4: Rename
- Rename `main_new.py` to `main.py`
- Update entrypoint in deployment

## Running the Application

```bash
# Development
uvicorn app.main_new:app --reload --host 0.0.0.0 --port 8000

# Production (with main.py)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Structure

All endpoints are prefixed with `/api/v1/`:

```
/api/v1/classify                          POST - Classify intent
/api/v1/generate/upwork                   POST - Generate proposal (stored resume)
/api/v1/generate/upwork/followup          POST - Answer follow-up question
/api/v1/generate/upwork/upload            POST - Generate proposal (uploaded resume)
/api/v1/resumes                           GET  - List resumes
/api/v1/resumes/upload                    POST - Upload resume
/api/v1/resumes/{resume_name}             DELETE - Delete resume
/api/v1/sessions                          GET  - List all sessions
/api/v1/sessions/{session_id}             GET  - Get session details
/api/v1/sync/google-sheet/projects        POST - Sync projects from Google Sheet
/api/v1/sync/google-sheet/reviews         POST - Sync reviews from Google Sheet
/api/v1/debug/search                      POST - Debug FAISS search
/health                                   GET  - Health check
```
