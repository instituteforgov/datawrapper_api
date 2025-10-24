"""
Utility functions for interacting with the Datawrapper API.

This module provides common functions for making API requests to Datawrapper
and handling responses.
"""

import os

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

    # Handle case where response might be a list or dict
    if isinstance(embed_data, list) and len(embed_data) > 0:
        embed_data = embed_data[0]

    if responsive:
        return embed_data.get("responsive", "")
    else:
        return embed_data.get("static", "")
