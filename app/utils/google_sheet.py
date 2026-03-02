# app/utils/google_sheet.py
"""
Google Sheets integration utilities.
"""
import re
import pandas as pd
import requests
from typing import Optional
from app.core.exceptions import InvalidGoogleSheetError
from app.core.logging import get_logger

logger = get_logger(__name__)


def convert_google_sheet_to_csv_url(url: str) -> str:
    """
    Convert Google Sheets sharing URL to CSV export URL.
    
    Args:
        url: Google Sheets sharing URL
        
    Returns:
        CSV export URL
        
    Raises:
        InvalidGoogleSheetError: If URL format is invalid
    """
    # Already export link
    if "export?format=csv" in url:
        return url

    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    if not match:
        raise InvalidGoogleSheetError(
            "Invalid Google Sheets URL. Expected format: "
            "https://docs.google.com/spreadsheets/d/SHEET_ID/..."
        )

    sheet_id = match.group(1)
    gid_match = re.search(r"gid=([0-9]+)", url)
    gid = gid_match.group(1) if gid_match else "0"

    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    logger.info(f"Converted Google Sheet URL to CSV: {csv_url}")
    return csv_url


def load_google_sheet_dataframe(sheet_url: str) -> pd.DataFrame:
    """
    Load Google Sheet into a pandas DataFrame.
    
    Handles:
    - Private sheets (with appropriate error message)
    - Permission errors
    - HTML instead of CSV
    - Empty sheets
    
    Args:
        sheet_url: Google Sheets URL
        
    Returns:
        DataFrame with sheet data
        
    Raises:
        InvalidGoogleSheetError: If sheet cannot be accessed or loaded
    """
    try:
        csv_url = convert_google_sheet_to_csv_url(sheet_url)
        logger.info(f"Loading Google Sheet from CSV URL: {csv_url}")
        
        response = requests.get(csv_url, timeout=10)

        if response.status_code != 200:
            raise InvalidGoogleSheetError(
                f"Unable to access sheet (HTTP {response.status_code}). "
                "Ensure sharing is set to 'Anyone with link → Viewer'."
            )

        content_type = response.headers.get("Content-Type", "")

        # Google returns text/html if not public
        if "text/html" in content_type:
            raise InvalidGoogleSheetError(
                "Sheet is not publicly accessible. "
                "Set sharing permissions to 'Anyone with link → Viewer'."
            )

        df = pd.read_csv(csv_url)
        logger.info(f"Successfully loaded DataFrame with shape: {df.shape}")

        if df.empty:
            raise InvalidGoogleSheetError(
                "Sheet loaded but contains no data. "
                "Please check the sheet content."
            )

        return df

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error accessing Google Sheet: {str(e)}")
        raise InvalidGoogleSheetError(f"Network error: {str(e)}")
    except pd.errors.ParserError as e:
        logger.error(f"Failed to parse CSV: {str(e)}")
        raise InvalidGoogleSheetError(
            "Failed to parse CSV. Ensure sheet contains valid tabular data."
        )
