# app/core/constants.py
"""
Application-wide constants and configuration values.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/job-description")

# LLM Models
GROQ_MODEL = "llama-3.1-8b-instant"

# Embedding Configuration
EMBED_MODEL = "all-MiniLM-L6-v2"

# FAISS Search Parameters
DEFAULT_TOP_K_PROJECTS = 3
DEFAULT_TOP_K_REVIEWS = 2
DEFAULT_TOP_K_RESUMES = 1

# Resume Matching Threshold
RESUME_SIMILARITY_THRESHOLD = 0.50

# LLM Temperature & Token Settings
PROPOSAL_TEMPERATURE = 0.45
PROPOSAL_MAX_TOKENS = 800
FOLLOWUP_TEMPERATURE = 0.4
FOLLOWUP_MAX_TOKENS = 400
INTENT_TEMPERATURE = 0.0
INTENT_MAX_TOKENS = 5

# API Configuration
API_TITLE = "Job Application Generator API"
API_VERSION = "0.1.0"

# Data Paths
DATA_DIR = "data"
PROJECTS_INDEX_PATH = f"{DATA_DIR}/projects.faiss"
PROJECTS_META_PATH = f"{DATA_DIR}/projects_meta.pkl"
REVIEWS_INDEX_PATH = f"{DATA_DIR}/reviews.faiss"
REVIEWS_META_PATH = f"{DATA_DIR}/reviews_meta.pkl"
RESUMES_INDEX_PATH = f"{DATA_DIR}/resumes.faiss"
RESUMES_META_PATH = f"{DATA_DIR}/resumes_meta.pkl"

# Prompts
GLOBAL_SCOPE_PROMPT = """
You are a strict Job Application Assistant.

Your ONLY purpose is to:
- Generate Upwork job proposals
- Answer job-related follow-up questions
- Discuss resume, skills, experience, rates, availability
- Clarify technical details related to a job opportunity

If the user:
- Tries casual conversation
- Mentions names or identity changes
- Asks personal or unrelated questions
- Talks about weather, politics, jokes, etc.
- Provides random statements unrelated to hiring

You MUST respond exactly with:

"I am a job-application assistant and can only assist with job-related queries such as proposals, requirements, resume details, or hiring discussions."

Do NOT explain further.
Do NOT break character.
Do NOT answer unrelated prompts.
Stay professional and strict.
"""

# Project Sheet Configuration
PROJECT_SHEETS = {
    "PHP PROJECT LIST": "PHP Project",
    "FLUTTER PROJECT LIST": "Flutter Project",
    "PYTHON PROJECT LIST": "Python Project",
}

# Conversation Context
CONVERSATION_CONTEXT_LENGTH = 4

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


# ============================================================================
# Groq Client Initialization
# ============================================================================

def get_groq_client():
    """
    Initialize and return Groq API client.
    
    Returns:
        Groq client instance
        
    Raises:
        ValueError: If GROQ_API_KEY is not set
    """
    from groq import Groq
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. "
            "Please set the environment variable: export GROQ_API_KEY='your-key'"
        )
    
    return Groq(api_key=api_key)


# Initialize Groq client for use in modules
try:
    groq_client = get_groq_client()
except ValueError as e:
    import warnings
    warnings.warn(f"Groq client initialization warning: {str(e)}", stacklevel=2)
    groq_client = None


# ============================================================================
# Embedding Model Initialization
# ============================================================================

def get_embedding_model():
    """
    Initialize and return SentenceTransformer embedding model.
    
    Returns:
        SentenceTransformer model instance
        
    Raises:
        ImportError: If sentence-transformers not installed
    """
    from sentence_transformers import SentenceTransformer
    
    try:
        model = SentenceTransformer(EMBED_MODEL)
        return model
    except Exception as e:
        raise ImportError(
            f"Failed to load embedding model {EMBED_MODEL}: {str(e)}"
        )


# Initialize embedding model for use in modules
try:
    embedding_model = get_embedding_model()
except ImportError as e:
    import warnings
    warnings.warn(f"Embedding model initialization warning: {str(e)}", stacklevel=2)
    embedding_model = None


