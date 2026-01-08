"""
Utility functions for interacting with the Datawrapper API.

This module provides common functions for making API requests to Datawrapper
and handling responses.
"""

import logging
import os
import re
import time
from functools import wraps
from typing import Callable, TypeVar, ParamSpec

import pandas as pd
import requests
from requests.exceptions import HTTPError, ReadTimeout, ConnectionError, Timeout

P = ParamSpec("P")
T = TypeVar("T")

logger = logging.getLogger(__name__)


def retry_on_api_error(max_retries: int = 5, base_wait_time: float = 1.0) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to retry API calls on transient failures.

    Parameters:
        max_retries: Maximum number of retry attempts (default: 5)
        base_wait_time: Base wait time in seconds for exponential backoff (default: 1.0)

    Returns:
        Decorated function with retry logic

    Raises:
        The last exception encountered after all retries are exhausted
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (HTTPError, ReadTimeout, ConnectionError, Timeout) as e:
                    if attempt < max_retries - 1:
                        wait_time = base_wait_time * (2 ** attempt)
                        logger.warning(f"API error in {func.__name__}: {e}. Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"API error in {func.__name__}: {e}. Max retries ({max_retries}) exceeded.")
                        raise

            # This should never be reached, but included for type safety
            return func(*args, **kwargs)
        return wrapper
    return decorator


# API Configuration
DATAWRAPPER_API_BASE = "https://api.datawrapper.de/v3"
DATAWRAPPER_API_TOKEN = os.getenv("DATAWRAPPER_API_TOKEN")


@retry_on_api_error()
def publish_chart(chart_id: str) -> dict:
    """
    Publish a chart on Datawrapper.

    Parameters:
        chart_id: The ID of the chart to publish

    Returns:
        JSON response as dictionary

    Raises:
        requests.exceptions.HTTPError: If the API request fails
    """
    headers = {
        "Authorization": f"Bearer {DATAWRAPPER_API_TOKEN}",
        "Content-Type": "application/json"
    }

    endpoint = f"{DATAWRAPPER_API_BASE}/charts/{chart_id}/publish"
    response = requests.post(endpoint, headers=headers)
    response.raise_for_status()
    return response.json()


def validate_api_token() -> None:
    """
    Validate that the Datawrapper API token is available.

    Raises:
        ValueError: If DATAWRAPPER_API_TOKEN environment variable is not set
    """
    if not DATAWRAPPER_API_TOKEN:
        raise ValueError("DATAWRAPPER_API_TOKEN environment variable not set")


@retry_on_api_error()
def _make_api_request(endpoint: str) -> dict:
    """
    Make a GET request to the Datawrapper API.

    Parameters:
        endpoint: API endpoint path

    Returns:
        JSON response as dictionary

    Raises:
        requests.exceptions.HTTPError: If the API request fails
    """
    headers = {
        "Authorization": f"Bearer {DATAWRAPPER_API_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.get(f"{DATAWRAPPER_API_BASE}{endpoint}", headers=headers)
    response.raise_for_status()
    return response.json()


@retry_on_api_error()
def export_chart(chart_id: str, output_format: str, filepath: str, width: int | None = None, height: str | None = "auto", border_width: int = 0, plain: bool = False) -> None:
    """
    Export chart from Datawrapper API and save to file.

    Parameters:
        chart_id: The ID of the chart to export
        output_format: Export format (e.g., "png", "svg")
        filepath: Local file path to save the export
        width: Width in pixels (None for auto)
        height: Height in pixels or "auto" for automatic
        border_width: Border width in pixels
        plain: Whether to export without header/footer

    Raises:
        requests.exceptions.HTTPError: If the API request fails
    """
    params = {}

    if width is not None:
        params["width"] = width
    if height is not None:
        params["height"] = height
    if border_width != 0:
        params["borderWidth"] = border_width
    if plain:
        params["plain"] = "true"

    headers = {
        "Authorization": f"Bearer {DATAWRAPPER_API_TOKEN}"
    }

    endpoint = f"{DATAWRAPPER_API_BASE}/charts/{chart_id}/export/{output_format}"
    response = requests.get(endpoint, headers=headers, params=params)
    response.raise_for_status()

    with open(filepath, "wb") as f:
        f.write(response.content)


def get_folder(folder_id: int) -> dict:
    """
    Get folder details from Datawrapper API.

    Parameters:
        folder_id: The ID of the folder

    Returns:
        Folder data dictionary
    """
    return _make_api_request(f"/folders/{folder_id}")


def get_chart(chart_id: str) -> dict:
    """
    Get chart details from Datawrapper API.

    Parameters:
        chart_id: The ID of the chart

    Returns:
        Chart data dictionary
    """
    return _make_api_request(f"/charts/{chart_id}")


def get_iframe_code(chart_id: str, responsive: bool = True) -> str:
    """
    Get iframe embed code for a chart from Datawrapper API.

    Parameters:
        chart_id: The ID of the chart
        responsive: Whether to get responsive embed code

    Returns:
        Iframe embed code as string
    """
    embed_data = _make_api_request(f"/charts/{chart_id}/embed-codes")

    # Ensure embed_data is a list
    if isinstance(embed_data, list):
        # Find the appropriate embed code based on the id
        for item in embed_data:
            if (responsive and item.get("id") == "responsive") or (not responsive and item.get("id") == "iframe"):
                return item.get("code", "")

    # Return an empty string if no matching embed code is found
    return ""


def sanitise_string(input_string: str) -> str:
    """
    Clean a string to make it safe for use in a Windows file or folder path.

    Parameters:
        input_string: The original string

    Returns:
        A cleaned string
    """
    # Remove invalid characters for Windows file names
    cleaned = re.sub(r'[\\/:*?"<>|\n\r\t]', "", input_string)

    # Remove control characters (ASCII 0–31)
    cleaned = "".join(ch for ch in cleaned if ord(ch) >= 32)

    # Truncate to a safe length
    cleaned = cleaned[:255]

    # Strip leading/trailing whitespace and dots
    cleaned = cleaned.strip().strip(".")

    return cleaned


def normalise_export_formats(export_formats: str | list[str] | dict[str, dict]) -> dict[str, dict]:
    """
    Normalise export_formats input to dict format.

    Parameters:
        export_formats: Format(s) as string, list, or dict

    Returns:
        Dictionary mapping format names to their export options
    """
    if isinstance(export_formats, str):
        return {export_formats: {}}
    elif isinstance(export_formats, list):
        return {fmt: {} for fmt in export_formats}
    elif isinstance(export_formats, dict):
        return export_formats
    else:
        raise TypeError(f"export_formats must be str, list, or dict, not {type(export_formats)}")


def set_chart_filename(
    chart_id: str,
    title: str,
    chart_numbering_df: pd.DataFrame | None
) -> str:
    """
    Set filename for a chart either based on numbering lookup or fallback.

    Parameters:
        chart_id: The ID of the chart
        title: The title of the chart
        chart_numbering_df: DataFrame containing chart numbering lookup

    Returns:
        Sanitised filename string
    """
    if chart_numbering_df is not None:
        chart_numbering_row = chart_numbering_df[chart_numbering_df["Chart ID"] == chart_id]

        if not chart_numbering_row.empty:
            chart_number = chart_numbering_row.iloc[0]["Chart number"]
            if pd.notna(chart_number):
                logger.info(f"Exporting chart {chart_id}-{title} as {chart_number}-{title}")
                return sanitise_string(f"{str(chart_number)}-{title}")
            else:
                logger.info(f"Chart ID {chart_id} has blank chart number. Using fallback name")
        else:
            logger.warning(f"Chart ID {chart_id} not found in lookup table. Using fallback name")

    return sanitise_string(f"{chart_id}-{title}")
