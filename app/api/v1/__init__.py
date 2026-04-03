# app/api/v1/__init__.py
"""API v1 module."""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    classification,
    proposals,
    resumes,
    sessions,
    sync,
    debug,
)


def create_api_router() -> APIRouter:
    """
    Create and configure API v1 router with all endpoints.
    
    Returns:
        APIRouter with all v1 endpoints
    """
    router = APIRouter(prefix="/api/v1")
    
    router.include_router(classification.router)
    router.include_router(proposals.router)
    router.include_router(resumes.router)
    router.include_router(sessions.router)
    router.include_router(sync.router)
    router.include_router(debug.router)
    
    return router
