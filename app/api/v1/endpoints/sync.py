# app/api/v1/endpoints/sync.py
"""
Data synchronization endpoints for Google Sheets.
"""
import pandas as pd
from fastapi import APIRouter, HTTPException

from app.services.vectorstore_service import (
    ProjectStoreService,
    ReviewStoreService,
)
from app.utils.google_sheet import load_google_sheet_dataframe
from app.core.exceptions import InvalidGoogleSheetError, VectorStoreError
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/sync/google-sheet", tags=["sync"])

# Global store instances (initialized on startup)
project_store: ProjectStoreService = None
review_store: ReviewStoreService = None


def set_stores(
    projects: ProjectStoreService,
    reviews: ReviewStoreService,
) -> None:
    """Set global store instances."""
    global project_store, review_store
    project_store = projects
    review_store = reviews


@router.post("/projects")
def sync_projects_from_google_sheet(payload: dict):
    """
    Sync projects from Google Sheet.
    
    Args:
        payload: JSON with sheet_url
        
    Returns:
        JSON with sync status
    """
    try:
        sheet_url = payload.get("sheet_url")
        if not sheet_url:
            raise HTTPException(status_code=400, detail="sheet_url is required")
        
        logger.info(f"Syncing projects from: {sheet_url}")
        
        # Load sheet
        df = load_google_sheet_dataframe(sheet_url)
        logger.info(f"PROJECT CSV HEADERS: {df.columns.tolist()}")
        
        # Reset store
        project_store.index = None
        project_store.texts = []
        project_store.metadata = []
        
        # Process rows
        for _, row in df.iterrows():
            project_name = str(row.get("PROJECT NAME", "")).strip()
            project_type = str(row.get("", "")).strip()
            
            if not project_type:
                project_type = str(row.get("Unnamed: 1", "")).strip()
            
            industry = str(row.get("INDUSTRY", "")).strip()
            tech_stack = str(row.get("Tech Stack", "")).strip()
            description = str(row.get("DESCRIPTION", "")).strip()
            
            # Skip empty rows
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
        
        # Check if we have data
        if not project_store.texts:
            raise HTTPException(
                status_code=400,
                detail="No valid rows found in projects sheet. Check headers/rows."
            )
        
        # Build and save index
        embeddings = project_store.model.encode(
            project_store.texts,
            normalize_embeddings=True,
        ).astype("float32")
        
        project_store._build_index(embeddings)
        project_store.save()
        
        # Reload to ensure RAM matches disk
        project_store.load()
        
        logger.info(f"Successfully synced {len(project_store.texts)} projects")
        
        return {
            "status": "success",
            "rows": len(project_store.texts)
        }
        
    except InvalidGoogleSheetError as e:
        logger.error(f"Google Sheet error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing projects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reviews")
def sync_reviews_from_google_sheet(payload: dict):
    """
    Sync reviews from Google Sheet.
    
    Args:
        payload: JSON with sheet_url
        
    Returns:
        JSON with sync status
    """
    try:
        sheet_url = payload.get("sheet_url")
        if not sheet_url:
            raise HTTPException(status_code=400, detail="sheet_url is required")
        
        logger.info(f"Syncing reviews from: {sheet_url}")
        
        # Load sheet
        df = load_google_sheet_dataframe(sheet_url)
        
        # Reset store
        review_store.index = None
        review_store.texts = []
        review_store.metadata = []
        
        # Process rows
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
        
        # Check if we have data
        if not review_store.texts:
            logger.warning("No review rows found in sheet")
            return {
                "status": "success",
                "rows": 0,
                "message": "No review rows found."
            }
        
        # Build and save index
        embeddings = review_store.model.encode(
            review_store.texts,
            normalize_embeddings=True,
        ).astype("float32")
        
        review_store._build_index(embeddings)
        review_store.save()
        
        # Reload
        review_store.load()
        
        logger.info(f"Successfully synced {len(review_store.texts)} reviews")
        
        return {
            "status": "success",
            "rows": len(review_store.texts)
        }
        
    except InvalidGoogleSheetError as e:
        logger.error(f"Google Sheet error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
