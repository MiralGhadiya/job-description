# app/utils/file_handler.py
"""
File processing utilities for PDF and text files.
"""
import pdfplumber
from typing import Union
from fastapi import UploadFile
from app.core.exceptions import FileProcessingError
from app.core.logging import get_logger

logger = get_logger(__name__)


async def extract_text_from_file(file: UploadFile) -> str:
    """
    Extract text from PDF or TXT file.
    
    Args:
        file: UploadFile instance
        
    Returns:
        Extracted text content
        
    Raises:
        FileProcessingError: If file processing fails
    """
    try:
        if file.filename.endswith(".pdf"):
            with pdfplumber.open(file.file) as pdf:
                text = "\n".join(
                    page.extract_text() or "" for page in pdf.pages
                )
        elif file.filename.endswith(".txt"):
            content = await file.read()
            text = content.decode("utf-8")
        else:
            raise FileProcessingError(
                f"Unsupported file type: {file.filename}. "
                "Please upload PDF or TXT files only."
            )
        
        logger.info(f"Successfully extracted text from {file.filename}")
        return text
        
    except Exception as e:
        logger.error(f"Failed to process file {file.filename}: {str(e)}")
        raise FileProcessingError(f"Failed to process file: {str(e)}")
