# app/core/exceptions.py
"""
Custom exception classes for the application.
"""


class JobApplicationException(Exception):
    """Base exception for all job application errors."""
    pass


class ResumeNotFoundError(JobApplicationException):
    """Raised when a resume with the specified name is not found."""
    pass


class InvalidSessionError(JobApplicationException):
    """Raised when a session_id is invalid or not found."""
    pass


class ResumeSimilarityError(JobApplicationException):
    """Raised when resume similarity falls below threshold."""
    def __init__(self, message: str, best_match_resume: str, similarity_score: float):
        self.message = message
        self.best_match_resume = best_match_resume
        self.similarity_score = similarity_score
        super().__init__(message)


class InvalidGoogleSheetError(JobApplicationException):
    """Raised when Google Sheet URL or content is invalid."""
    pass


class FileProcessingError(JobApplicationException):
    """Raised when file upload/processing fails."""
    pass


class LLMGenerationError(JobApplicationException):
    """Raised when LLM fails to generate content."""
    pass


class VectorStoreError(JobApplicationException):
    """Raised when FAISS vector store operations fail."""
    pass
