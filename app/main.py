# app/main_new.py
"""
Production-ready FastAPI application.
Refactored with proper separation of concerns: routes, services, and utilities.
"""
from fastapi import FastAPI
from app.core.logging import get_logger
from app.api.v1 import create_api_router
from app.services.vectorstore_service import (
    ProjectStoreService,
    ReviewStoreService,
    ResumeStoreService,
)
from app.api.v1.endpoints import proposals, resumes, sync, debug

logger = get_logger(__name__)

# ============================================================================
# Application Factory
# ============================================================================

def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Job Application Generator API",
        version="1.0.0",
        description="Production-ready API for generating Upwork proposals",
    )
    
    # Initialize vector stores
    project_store = ProjectStoreService()
    review_store = ReviewStoreService()
    resume_store = ResumeStoreService()
    
    # ========================================================================
    # Startup Event
    # ========================================================================
    
    @app.on_event("startup")
    def startup_event():
        """Initialize stores and load data on application startup."""
        logger.info("Starting up application...")
        
        try:
            # Load stores
            project_store.load()
            review_store.load()
            resume_store.load()
            
            logger.info("FAISS stores loaded successfully.")
            logger.info(f"  - Projects: {len(project_store.texts)} items")
            logger.info(f"  - Reviews: {len(review_store.texts)} items")
            logger.info(f"  - Resumes: {len(resume_store.texts)} items")
            
            # Register stores with endpoints
            proposals.set_stores(project_store, review_store, resume_store)
            resumes.set_store(resume_store)
            sync.set_stores(project_store, review_store)
            debug.set_store(project_store)
            
        except Exception as e:
            logger.error(f"Failed to initialize stores: {str(e)}")
            raise
    
    # ========================================================================
    # Shutdown Event
    # ========================================================================
    
    @app.on_event("shutdown")
    def shutdown_event():
        """Cleanup on application shutdown."""
        logger.info("Shutting down application...")
    
    # ========================================================================
    # Health Check
    # ========================================================================
    
    @app.get("/health")
    def health_check():
        """Simple health check endpoint."""
        return {
            "status": "healthy",
            "version": "1.0.0"
        }
    
    # ========================================================================
    # Include Routers
    # ========================================================================
    
    api_router = create_api_router()
    app.include_router(api_router)
    
    logger.info("Application configured and ready")
    
    return app


# ============================================================================
# Application Instance
# ============================================================================

app = create_app()


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main_new:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
