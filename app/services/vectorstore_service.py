# app/services/vectorstore_service.py
"""
Service layer for vector store operations.
Manages FAISS indices for projects, reviews, and resumes.
"""
import faiss
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any

from app.core.constants import (
    embedding_model,
    PROJECTS_INDEX_PATH,
    PROJECTS_META_PATH,
    REVIEWS_INDEX_PATH,
    REVIEWS_META_PATH,
    RESUMES_INDEX_PATH,
    RESUMES_META_PATH,
    DEFAULT_TOP_K_PROJECTS,
    DEFAULT_TOP_K_REVIEWS,
    DEFAULT_TOP_K_RESUMES,
    PROJECT_SHEETS,
)
from app.core.exceptions import VectorStoreError, ResumeNotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)


class VectorStoreService:
    """Base service for FAISS vector store operations."""
    
    def __init__(self, index_path: str, meta_path: str):
        """
        Initialize vector store service.
        
        Args:
            index_path: Path to FAISS index file
            meta_path: Path to metadata pickle file
        """
        self.index_path = index_path
        self.meta_path = meta_path
        self.model = embedding_model
        self.index: Optional[faiss.IndexFlatIP] = None
        self.texts: List[str] = []
        self.metadata: List[Dict[str, Any]] = []
    
    def load(self) -> None:
        """Load vector store from disk."""
        try:
            index_exists = Path(self.index_path).exists()
            meta_exists = Path(self.meta_path).exists()
            
            if not index_exists or not meta_exists:
                logger.info(f"Store not found at {self.index_path}. Creating empty store.")
                self.index = None
                self.texts = []
                self.metadata = []
                return
            
            self.index = faiss.read_index(str(self.index_path))
            with open(self.meta_path, "rb") as f:
                self.texts, self.metadata = pickle.load(f)
            
            logger.info(f"Loaded {len(self.texts)} items from vector store")
            
        except Exception as e:
            logger.error(f"Failed to load vector store: {str(e)}")
            raise VectorStoreError(f"Failed to load vector store: {str(e)}")
    
    def save(self) -> None:
        """Save vector store to disk."""
        try:
            Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)
            
            if self.index is not None:
                faiss.write_index(self.index, str(self.index_path))
            
            with open(self.meta_path, "wb") as f:
                pickle.dump((self.texts, self.metadata), f)
            
            logger.info(f"Saved vector store with {len(self.texts)} items")
            
        except Exception as e:
            logger.error(f"Failed to save vector store: {str(e)}")
            raise VectorStoreError(f"Failed to save vector store: {str(e)}")
    
    def _add_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            Numpy array of embeddings
        """
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
        ).astype("float32")
        return np.array(embeddings)
    
    def _build_index(self, embeddings: np.ndarray) -> None:
        """
        Build FAISS index from embeddings.
        
        Args:
            embeddings: Numpy array of embeddings
        """
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)


class ProjectStoreService(VectorStoreService):
    """Service for managing project vector store."""
    
    def __init__(self):
        """Initialize project store service."""
        super().__init__(PROJECTS_INDEX_PATH, PROJECTS_META_PATH)
    
    def build_from_excel(self, excel_path: str) -> int:
        """
        Build vector store from Excel file.
        
        Args:
            excel_path: Path to Excel file
            
        Returns:
            Number of projects added
        """
        try:
            xls = pd.ExcelFile(excel_path)
            
            for sheet, category in PROJECT_SHEETS.items():
                df = xls.parse(sheet)
                
                for _, row in df.iterrows():
                    text = self._row_to_text(row, category)
                    if not text.strip():
                        continue
                    
                    self.texts.append(text)
                    self.metadata.append({
                        "project_name": str(row.get("PROJECT NAME", "")).strip(),
                        "category": category,
                        "industry": str(row.get("INDUSTRY", "")).strip(),
                    })
            
            embeddings = self._add_embeddings(self.texts)
            embeddings = np.array(embeddings).astype("float32")
            self._build_index(embeddings)
            self.save()
            
            logger.info(f"Built project store with {len(self.texts)} items")
            return len(self.texts)
            
        except Exception as e:
            logger.error(f"Failed to build project store from Excel: {str(e)}")
            raise VectorStoreError(f"Failed to build project store: {str(e)}")
    
    def search(self, query: str, top_k: int = DEFAULT_TOP_K_PROJECTS) -> str:
        """
        Search for relevant projects.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            Formatted project results
        """
        if self.index is None:
            return "No projects found in store."
        
        query_emb = self.model.encode(
            [query],
            normalize_embeddings=True,
        ).astype("float32")
        
        scores, indices = self.index.search(query_emb, top_k)
        results = [self.texts[i] for i in indices[0]]
        
        return "\n\n".join(results)
    
    def search_debug(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Debug search with scores and metadata.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of results with scores and metadata
        """
        if self.index is None:
            return []
        
        query_emb = self.model.encode(
            [query],
            normalize_embeddings=True,
        ).astype("float32")
        
        scores, indices = self.index.search(query_emb, top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            results.append({
                "score": float(score),
                "text": self.texts[idx],
                "metadata": self.metadata[idx],
            })
        
        return results
    
    @staticmethod
    def _row_to_text(row: pd.Series, category: str) -> str:
        """Format project row as text."""
        return f"""
Project: {row.get('PROJECT NAME', '')}
Project Type: {row.get('Unnamed: 1', '')}
Category: {category}
Industry: {row.get('INDUSTRY', '')}
Tech Stack: {row.get('Tech Stack', '')}
Description: {row.get('DESCRIPTION', '')}
""".strip()


class ReviewStoreService(VectorStoreService):
    """Service for managing review vector store."""
    
    def __init__(self):
        """Initialize review store service."""
        super().__init__(REVIEWS_INDEX_PATH, REVIEWS_META_PATH)
    
    def build_from_dataframe(self, df: pd.DataFrame) -> int:
        """
        Build vector store from DataFrame.
        
        Args:
            df: DataFrame with review data
            
        Returns:
            Number of reviews added
        """
        try:
            for _, row in df.iterrows():
                text = self._row_to_text(row)
                if not text.strip():
                    continue
                
                self.texts.append(text)
                self.metadata.append({
                    "product": str(row.get("Product Name", "")).strip(),
                    "rating": row.get("Rating"),
                    "country": str(row.get("Country", "")).strip(),
                })
            
            embeddings = self._add_embeddings(self.texts)
            embeddings = np.array(embeddings).astype("float32")
            self._build_index(embeddings)
            self.save()
            
            logger.info(f"Built review store with {len(self.texts)} items")
            return len(self.texts)
            
        except Exception as e:
            logger.error(f"Failed to build review store from DataFrame: {str(e)}")
            raise VectorStoreError(f"Failed to build review store: {str(e)}")
    
    def search(self, query: str, top_k: int = DEFAULT_TOP_K_REVIEWS) -> str:
        """
        Search for relevant reviews.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            Formatted review results
        """
        if self.index is None:
            return "No reviews found in store."
        
        query_emb = self.model.encode(
            [query],
            normalize_embeddings=True,
        ).astype("float32")
        
        scores, indices = self.index.search(query_emb, top_k)
        return "\n".join(self.texts[i] for i in indices[0])
    
    @staticmethod
    def _row_to_text(row: pd.Series) -> str:
        """Format review row as text."""
        return f"""
Review for: {row.get('Product Name', '')}
Rating: {row.get('Rating')} stars
Client Location: {row.get('Country', '')}
Feedback: {row.get('Review / Comment', '')}
""".strip()


class ResumeStoreService(VectorStoreService):
    """Service for managing resume vector store."""
    
    def __init__(self):
        """Initialize resume store service."""
        super().__init__(RESUMES_INDEX_PATH, RESUMES_META_PATH)
    
    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get resume by name.
        
        Args:
            name: Resume name
            
        Returns:
            Resume data or None
        """
        for text, meta in zip(self.texts, self.metadata):
            if meta["name"].lower() == name.lower():
                return {
                    "text": text,
                    "metadata": meta,
                }
        return None
    
    def add_resume(self, name: str, text: str) -> None:
        """
        Add new resume to store.
        
        Args:
            name: Resume name
            text: Resume content
            
        Raises:
            ResumeNotFoundError: If resume name already exists
        """
        try:
            # Prevent duplicate names
            for meta in self.metadata:
                if meta["name"].lower() == name.lower():
                    raise ResumeNotFoundError(
                        f"Resume with name '{name}' already exists."
                    )
            
            embedding = self.model.encode(
                [text],
                normalize_embeddings=True
            ).astype("float32")
            
            if self.index is None:
                dim = embedding.shape[1]
                self.index = faiss.IndexFlatIP(dim)
            
            self.index.add(embedding)
            self.texts.append(text)
            self.metadata.append({"name": name})
            self.save()
            
            logger.info(f"Added resume: {name}")
            
        except Exception as e:
            logger.error(f"Failed to add resume: {str(e)}")
            raise
    
    def delete_resume(self, name: str) -> bool:
        """
        Delete resume from store.
        
        Args:
            name: Resume name
            
        Returns:
            True if deleted, False if not found
        """
        try:
            new_texts = []
            new_metadata = []
            
            for text, meta in zip(self.texts, self.metadata):
                if meta["name"].lower() != name.lower():
                    new_texts.append(text)
                    new_metadata.append(meta)
            
            if len(new_texts) == len(self.texts):
                return False  # Not found
            
            self.texts = new_texts
            self.metadata = new_metadata
            
            if not self.texts:
                self.index = None
            else:
                embeddings = self.model.encode(
                    self.texts,
                    normalize_embeddings=True
                ).astype("float32")
                
                dim = embeddings.shape[1]
                self.index = faiss.IndexFlatIP(dim)
                self.index.add(embeddings)
            
            self.save()
            logger.info(f"Deleted resume: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete resume: {str(e)}")
            raise VectorStoreError(f"Failed to delete resume: {str(e)}")
    
    def search(self, query: str, top_k: int = DEFAULT_TOP_K_RESUMES) -> Dict[str, Any]:
        """
        Search for most similar resume.
        
        Args:
            query: Search query
            top_k: Number of results (typically 1)
            
        Returns:
            Best matching resume with metadata and score
        """
        if self.index is None:
            raise VectorStoreError("No resumes found in store.")
        
        query_emb = self.model.encode(
            [query],
            normalize_embeddings=True,
        ).astype("float32")
        
        scores, indices = self.index.search(query_emb, top_k)
        
        idx = indices[0][0]
        score = float(scores[0][0])
        
        return {
            "text": self.texts[idx],
            "metadata": self.metadata[idx],
            "score": score
        }
    
    def list_all(self) -> List[str]:
        """
        List all resume names.
        
        Returns:
            List of resume names
        """
        return [meta["name"] for meta in self.metadata]
