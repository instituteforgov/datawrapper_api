# %%
"""
    Purpose
        Get details of all charts in a Datawrapper folder including embed codes and save to Excel
    Inputs
        - API: Datawrapper API
    Outputs
        - xlsx: Chart numbering lookup file
    Notes
        None
"""

import os

import pandas as pd
from pandas.io.formats import excel

from utils import get_chart, get_folder, get_iframe_code, validate_api_token


# %%
# SET CONSTANTS
FOLDER_ID = 340017
OUTPUT_PATH = "C:/Users/" + os.getlogin() + "/Institute for Government/Research - Whitehall Monitor/Projects/2026/Charts"
CHART_NUMBERING_FILE_PATH = OUTPUT_PATH + "/Chart numbering - WM2026.xlsx"


# %%
# DEFINE FUNCTIONS
def get_chart_details(
    folder_id: int,
    dw_folder_path: str = "",
    recursive: bool = False,
    skip_folder_name: str = "Archive",
) -> list[dict]:
    """
    Get details all charts from a folder.

    Parameters:
        folder_id: The ID of the folder to list charts from
        dw_folder_path: Folder path within Datawrapper for tracking hierarchy
        recursive: Whether to include charts from subfolders
        skip_folder_name: Name of folders to skip (default: 'Archive')

    Returns:
        List of dictionaries containing chart information
    """

    charts_data = []

    try:
        folder = get_folder(folder_id=folder_id)
        folder_name = folder["name"]

        # Skip folder if it matches the skip_folder_name
        if folder_name == skip_folder_name:
            print(f"Skipping folder: {folder_name}")
            return charts_data

        # Update folder path
        current_path = os.path.join(dw_folder_path, folder_name) if dw_folder_path else folder_name

        print(f"Processing folder: {current_path}")

        # Process charts in current folder
        if folder.get("charts"):
            for chart in folder["charts"]:
                try:
                    chart_details = get_chart(chart_id=chart["id"])

                    # Skip charts without a proper title
                    # NB: For some reason, there seem to tend to be a few blank charts per folder, not visible in the UI
                    chart_title = chart_details["title"]
                    if chart_title != "[ Insert title here ]":

                        # Get responsive iframe code
                        try:
                            iframe_code = get_iframe_code(chart_id=chart["id"], responsive=True)
                        except Exception as iframe_error:
                            print(f"    Warning: Could not get iframe code for chart {chart['id']}: {iframe_error}")
                            iframe_code = "Error retrieving iframe code"

                        chart_info = {
                            "Folder path": current_path,
                            "Chart title": chart_title,
                            "Chart ID": chart["id"],
                            "Chart number": "",
                            "iframe code": iframe_code,
                        }
                        charts_data.append(chart_info)
                        print(f"  Found chart: {chart['id']} - {chart_info['Chart title']}")

                except Exception as e:
                    chart_info = {
                        "Folder path": current_path,
                        "Chart title": "Error retrieving title",
                        "Chart ID": chart["id"],
                        "Chart number": "",
                        "iframe code": "Error retrieving iframe code",
                    }
                    charts_data.append(chart_info)
                    print(f"  Error getting details for chart {chart['id']}: {e}")
        if recursive and folder.get("children"):
            for child_folder in folder["children"]:
                child_charts = get_chart_details(
                    folder_id=child_folder["id"],
                    recursive=True,
                    dw_folder_path=current_path,
                    skip_folder_name=skip_folder_name
                )
                charts_data.extend(child_charts)

    except Exception as e:
        print(f"Error processing folder {folder_id}: {e}")

    return charts_data


# %%
# EXECUTE
validate_api_token()

print(f"Listing charts from folder ID: {FOLDER_ID}")
print(f"Output file: {OUTPUT_PATH}")
print("-" * 50)

# Get all charts
charts_data = get_chart_details(
    folder_id=FOLDER_ID,
    recursive=True,
    skip_folder_name="Archive"
)

# Save details
excel.ExcelFormatter.header_style = None
if charts_data:
    df = pd.DataFrame(charts_data)
    df = df[["Folder path", "Chart title", "Chart ID", "Chart number", "iframe code"]]
    df.to_excel(OUTPUT_PATH, index=False)

    print("-" * 50)
    print(f"Successfully saved {len(charts_data)} charts to {OUTPUT_PATH}")
else:
    print("No charts found in the specified folder.")
