"""
Utility functions for interacting with the Datawrapper API.

This module provides common functions for making API requests to Datawrapper
and handling responses.
"""

import os
import re

import requests


# API Configuration
DATAWRAPPER_API_BASE = "https://api.datawrapper.de/v3"
DATAWRAPPER_API_TOKEN = os.getenv("DATAWRAPPER_API_TOKEN")


def validate_api_token() -> None:
    """
    Validate that the Datawrapper API token is available.

    Raises:
        ValueError: If DATAWRAPPER_API_TOKEN environment variable is not set
    """
    if not DATAWRAPPER_API_TOKEN:
        raise ValueError("DATAWRAPPER_API_TOKEN environment variable not set")


def make_api_request(endpoint: str) -> dict:
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
    return make_api_request(f"/folders/{folder_id}")


def get_chart(chart_id: str) -> dict:
    """
    Get chart details from Datawrapper API.

    Parameters:
        chart_id: The ID of the chart

    Returns:
        Chart data dictionary
    """
    return make_api_request(f"/charts/{chart_id}")


def get_iframe_code(chart_id: str, responsive: bool = True) -> str:
    """
    Get iframe embed code for a chart from Datawrapper API.

    Parameters:
        chart_id: The ID of the chart
        responsive: Whether to get responsive embed code

    Returns:
        Iframe embed code as string
    """
    embed_data = make_api_request(f"/charts/{chart_id}/embed-codes")

    # Ensure embed_data is a list
    if isinstance(embed_data, list):
        # Find the appropriate embed code based on the id
        for item in embed_data:
            if (responsive and item.get("id") == "responsive") or (not responsive and item.get("id") == "iframe"):
                return item.get("code", "")

    # Return an empty string if no matching embed code is found
    return ""


def clean_filename(title: str) -> str:
    """
    Clean a title to make it safe for use as a Windows file name.

    Parameters:
        title: The original title string

    Returns:
        A cleaned title string
    """
    # Remove invalid characters for Windows file names
    cleaned = re.sub(r'[\\/:*?"<>|\n\r\t]', "", title)

    # Remove control characters (ASCII 0–31)
    cleaned = "".join(ch for ch in cleaned if ord(ch) >= 32)

    # Truncate to a safe length
    cleaned = cleaned[:255]

    # Strip leading/trailing whitespace and dots
    cleaned = cleaned.strip().strip(".")

    return cleaned
