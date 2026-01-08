# %%
"""
    Purpose
        Export charts
    Inputs
        - API: Datawrapper API
        - xlsx: Chart numbering lookup file
    Outputs
        - svg/png: Various
    Notes
        - Sometimes files need to be saved to e.g. Downloads, as long file names mean they cannot always be saved in the intended location
    Future enhancements
        - Add arg to skip charts without a chart number in the lookup file
"""

import os
import time

import pandas as pd
from requests.exceptions import HTTPError, ReadTimeout

from utils import sanitise_string, export_chart, get_chart, get_folder, validate_api_token, publish_chart

# %%
# SET CONSTANTS
FOLDER_ID = 340017
OUTPUT_PATH = "C:/Users/" + os.getlogin() + "/Institute for Government/Research - Whitehall Monitor/Projects/2026/Charts"
CHART_NUMBERING_FILE_PATH = OUTPUT_PATH + "/Datawrapper chart numbering - WM2026.xlsx"


# %%
# DEFINE FUNCTIONS
def export_charts(
    folder_id: int,
    path: str,
    output: str,
    max_retries: int = 5,
    recursive: bool = False,
    skip_folder_name: str = "Archive",
    flatten_path: bool = False,
    publish: bool = True,
    chart_numbering_df: pd.DataFrame | None = None,
    **kwargs,
) -> None:
    """"
        Export charts in a folder, optionally operating recursively.

        Parameters:
            folder_id: The ID of the base folder
            path: Base path for exporting charts
            output: Export format (e.g. "png" or "svg")
            max_retries: Maximum number of retry attempts for chart export (default: 5)
            recursive: Whether to recursively browse sub-folders (default: False)
            skip_folder_name: Name of folders to skip (default: "Archive")
            flatten_path: Whether to flatten the folder structure in the export path (default: False)
            publish: Whether to publish unpublished charts (default: True)
            chart_numbering_df: DataFrame containing chart numbering lookup
            **kwargs: Additional keyword arguments to pass to the export_chart() function

        Returns:
            None
    """

    folder = get_folder(
        folder_id=folder_id
    )

    # Skip folder if it matches the skip_folder_name
    if folder["name"] == skip_folder_name:
        print(f"Skipping folder: {folder['name']}")
        return

    # Create subdirectory for this folder (unless it's the root or flattened)
    if folder_id != FOLDER_ID and not flatten_path:
        folder_name = sanitise_string(folder["name"])
        path = os.path.join(path, folder_name)
        if not os.path.exists(path):
            os.makedirs(path)

    if folder["charts"]:
        for chart in folder["charts"]:

            # Skip charts without a proper title
            # NB: For some reason, there seem to tend to be a few blank charts per folder, not visible in the UI
            chart_details = get_chart(chart_id=chart["id"])
            title = chart_details["title"]
            if title != "[ Insert title here ]":

                # Publish chart if it's not already published and publish flag is True
                if publish and not chart_details.get("publicVersion"):
                    try:
                        publish_chart(chart_id=chart["id"])
                        print(f"Published chart {chart['id']}-{title}")
                    except HTTPError as e:
                        print(f"Failed to publish chart {chart['id']}-{title}: {e}")

                # Look up chart number from chart_numbering_df if provided
                if chart_numbering_df is not None:
                    chart_numbering_row = chart_numbering_df[chart_numbering_df["Chart ID"] == chart["id"]]

                    if not chart_numbering_row.empty:
                        chart_number = chart_numbering_row.iloc[0]["Chart number"]
                        # Handle case where chart_number might be NaN
                        if pd.notna(chart_number):
                            filename = f"{str(chart_number)}-{title}"
                            print(f"Exporting chart {chart["id"]}-{title} as {filename}")
                        else:
                            filename = f"{chart["id"]}-{title}"
                            print(f"Chart ID {chart["id"]} has blank chart number. Using fallback name: {filename}")

                    # Fallback to original naming if chart ID not found in lookup
                    else:
                        filename = f"{chart["id"]}-{title}"
                        print(f"Chart ID {chart["id"]} not found in lookup table. Using fallback name: {filename}")
                else:
                    # No chart numbering provided, use chart ID and title
                    filename = f"{chart["id"]}-{title}"
                    print(f"Exporting chart {chart["id"]}-{title} as {filename}")

                # Remove characters that break file paths from filename
                filename = sanitise_string(filename)

                for attempt in range(max_retries):

                    try:
                        export_chart(
                            chart_id=chart["id"],
                            output_format=output,
                            filepath=path + f"/{filename}.{output}",
                            width=None,
                            height="auto",
                            border_width=0,
                            **kwargs
                        )
                        break

                    except ReadTimeout:
                        wait_time = 2 ** attempt
                        print(f"Timeout occurred while exporting chart {filename}. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)

                    except HTTPError as http_err:
                        wait_time = 2 ** attempt
                        print(f"HTTP error occurred while exporting chart {filename}: {http_err}. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)

                    except ValueError:
                        print(f"ValueError occurred while exporting chart {filename}")
                        break

    # Recursively process child folders if recursive flag is True
    if recursive:
        for child_folder in folder["children"]:
            export_charts(
                folder_id=child_folder["id"],
                path=path,
                output=output,
                max_retries=max_retries,
                recursive=recursive,
                skip_folder_name=skip_folder_name,
                flatten_path=flatten_path,
                publish=publish,
                chart_numbering_df=chart_numbering_df,
                **kwargs,
            )

    return


# %%
# EXECUTE
validate_api_token()

# Import chart numbering
if CHART_NUMBERING_FILE_PATH:
    df_chart_numbering = pd.read_excel(
        CHART_NUMBERING_FILE_PATH,
        dtype={"Chart number": str}
    )

# Initialise
base_folder = get_folder(
    folder_id=FOLDER_ID
)
print(base_folder["name"])

export_formats = {
    "svg": {"plain": True},
    "png": {"plain": False},
}

# Export charts
for format, options in export_formats.items():
    export_charts(
        folder_id=FOLDER_ID,
        path=OUTPUT_PATH,
        output=format,
        recursive=True,
        skip_folder_name="Archive",
        flatten_path=True,
        chart_numbering_df=df_chart_numbering,
        **options
    )

# %%
