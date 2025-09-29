# %%
"""
    Purpose
        Get details of all charts in a Datawrapper folder including embed codes and save to Excel
    Inputs
        - API: Datawrapper API
    Outputs
        - xlsx:
    Notes
        None
"""

import os

from datawrapper import Datawrapper
import pandas as pd


# %%
# SET CONSTANTS
DATAWRAPPER_API_TOKEN = os.getenv("DATAWRAPPER_API_TOKEN")
FOLDER_ID = 325652
OUTPUT_PATH = "chart_numbering_homelessness.xlsx"


# %%
def get_charts(
    dw: Datawrapper,
    folder_id: int,
    dw_folder_path: str = "",
    recursive: bool = False,
) -> list[dict]:
    """
    Get details all charts from a folder.

    Parameters:
        - dw: Datawrapper instance
        - folder_id: The ID of the folder to list charts from
        - dw_folder_path: Folder path within Datawrapper for tracking hierarchy
        - recursive: Whether to include charts from subfolders

    Returns:
        List of dictionaries containing chart information
    """

    charts_data = []

    try:
        folder = dw.get_folder(folder_id=folder_id)
        folder_name = folder["name"]

        # Update folder path
        current_path = os.path.join(dw_folder_path, folder_name) if dw_folder_path else folder_name

        print(f"Processing folder: {current_path}")

        # Process charts in current folder
        if folder.get("charts"):
            for chart in folder["charts"]:
                try:
                    chart_details = dw.get_chart(chart_id=chart["id"])

                    # Get responsive iframe code
                    try:
                        iframe_code = dw.get_iframe_code(chart_id=chart["id"], responsive=True)
                    except Exception as iframe_error:
                        print(f"    Warning: Could not get iframe code for chart {chart['id']}: {iframe_error}")
                        iframe_code = "Error retrieving iframe code"

                    chart_info = {
                        "Chart number": "",
                        "Chart ID": chart["id"],
                        "Chart title": chart_details.get("title", "Untitled"),
                        "iframe code": iframe_code,
                        "Folder path": current_path
                    }
                    charts_data.append(chart_info)
                    print(f"  Found chart: {chart['id']} - {chart_info['Chart title']}")

                except Exception as e:
                    chart_info = {
                        "Chart number": "",
                        "Chart ID": chart["id"],
                        "Chart title": "Error retrieving title",
                        "iframe code": "Error retrieving iframe code",
                        "Folder path": current_path
                    }
                    charts_data.append(chart_info)
                    print(f"  Error getting details for chart {chart['id']}: {e}")
        if recursive and folder.get("children"):
            for child_folder in folder["children"]:
                child_charts = get_charts(
                    dw=dw,
                    folder_id=child_folder["id"],
                    recursive=True,
                    dw_folder_path=current_path
                )
                charts_data.extend(child_charts)

    except Exception as e:
        print(f"Error processing folder {folder_id}: {e}")

    return charts_data


# %%
if not DATAWRAPPER_API_TOKEN:
    raise ValueError("DATAWRAPPER_API_TOKEN environment variable not set")

# Initialise Datawrapper
dw = Datawrapper(access_token=DATAWRAPPER_API_TOKEN)

print(f"Listing charts from folder ID: {FOLDER_ID}")
print(f"Output file: {OUTPUT_PATH}")
print("-" * 50)

# Get all charts
charts_data = get_charts(
    dw=dw,
    folder_id=FOLDER_ID,
)

# Save details
if charts_data:
    df = pd.DataFrame(charts_data)
    df = df[["Chart number", "Chart ID", "Chart title", "iframe code", "Folder path"]]
    df.to_excel(OUTPUT_PATH, index=False)

    print("-" * 50)
    print(f"Successfully saved {len(charts_data)} charts to {OUTPUT_PATH}")
else:
    print("No charts found in the specified folder.")

# %%
