# app/api/v1/endpoints/debug.py
"""
Debug and utility endpoints.
"""
from fastapi import APIRouter, HTTPException
from app.services.vectorstore_service import ProjectStoreService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/debug", tags=["debug"])

# Global store instance (initialized on startup)
project_store: ProjectStoreService = None


def set_store(store: ProjectStoreService) -> None:
    """Set global store instance."""
    global project_store
    project_store = store


@router.post("/search")
def debug_search(payload: dict):
    """
    Debug search with detailed results including scores.
    
    Args:
        payload: JSON with query and optional top_k
        
    Returns:
        JSON with detailed search results
    """
    try:
        query = payload.get("query")
        top_k = payload.get("top_k", 5)
        
        if not query:
            raise HTTPException(status_code=400, detail="query is required")
        
        results = project_store.search_debug(query, top_k=top_k)
        
        logger.info(f"Debug search for '{query}': {len(results)} results")
        
        return {"results": results}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in debug search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
