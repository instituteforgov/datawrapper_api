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
"""

import logging
import os

import pandas as pd
from requests.exceptions import HTTPError

from utils import sanitise_string, export_chart, get_chart, get_folder, validate_api_token, publish_chart, normalise_export_formats, set_chart_filename

logger = logging.getLogger(__name__)

# %%
# SET CONSTANTS
FOLDER_ID = 340017
OUTPUT_PATH = "C:/Users/" + os.getlogin() + "/Downloads"
CHART_NUMBERING_FILE_PATH = OUTPUT_PATH + "/Datawrapper chart numbering - WM2026.xlsx"

EXPORT_FORMATS = {
    "svg": {"plain": True},
    "png": {"plain": False},
}

# %%
# Import chart numbering
if CHART_NUMBERING_FILE_PATH:
    df_chart_numbering = pd.read_excel(
        CHART_NUMBERING_FILE_PATH,
        dtype={"Chart number": str}
    )


# %%
# DEFINE FUNCTIONS
def collect_charts_for_export(
    folder_id: int,
    export_formats: str | list[str] | dict[str, dict],
    recursive: bool = False,
    skip_folder_name: str = "Archive",
    publish: bool = True,
    chart_numbering_df: pd.DataFrame | None = None,
    folder_path: list[str] | None = None,
    is_root: bool = True,
) -> list[dict]:
    """
    Collect all charts that need to be exported, publishing unpublished charts if requested.

    Parameters:
        folder_id: The ID of the base folder
        export_formats: Format(s) to export, optionally with export options. Can be:
            - String: "svg" or "png"
            - List: ["svg", "png"]
            - Dict: {"svg": {"plain": True}, "png": {"plain": False}}
        recursive: Whether to recursively browse sub-folders (default: False)
        skip_folder_name: Name of folders to skip (default: "Archive")
        publish: Whether to publish unpublished charts (default: True)
        chart_numbering_df: DataFrame containing chart numbering lookup
        folder_path: Internal parameter for tracking folder path during recursion
        is_root: Internal parameter indicating if this is the root folder (default: True)

    Returns:
        List of dictionaries containing chart export information:
        [{
            "chart_id": str,
            "title": str,
            "filename": str,
            "folder_path": list[str],
            "output_format": str,
            "export_params": dict
        }, ...]
    """
    if folder_path is None:
        folder_path = []

    # Normalise export_formats to dict format
    export_formats = normalise_export_formats(export_formats)

    folder = get_folder(folder_id=folder_id)
    charts_to_export = []

    # Skip folder if it matches skip_folder_name
    if folder["name"] == skip_folder_name:
        logger.info(f"Skipping folder: {folder['name']}")
        return charts_to_export

    # Process charts in this folder
    if folder["charts"]:
        for chart in folder["charts"]:
            chart_details = get_chart(chart_id=chart["id"])
            title = chart_details["title"]

            # Skip charts without proper title
            if title == "[ Insert title here ]":
                continue

            # Set filename
            filename = set_chart_filename(
                chart_id=chart["id"],
                title=title,
                chart_numbering_df=chart_numbering_df
            )

            # Publish if needed (once per chart, not per format)
            if publish and not chart_details.get("publicVersion"):
                try:
                    publish_chart(chart_id=chart["id"])
                    logger.info(f"Published chart {chart['id']}-{title}")
                except HTTPError as e:
                    logger.error(f"Failed to publish chart {chart['id']}-{title}: {e}")

            # Create entry for each export format
            for output_format, format_options in export_formats.items():
                charts_to_export.append({
                    "chart_id": chart["id"],
                    "title": title,
                    "filename": filename,
                    "folder_path": folder_path.copy(),
                    "output_format": output_format,
                    "export_params": format_options.copy(),
                })

    # Recursively process child folders
    if recursive:
        for child_folder in folder["children"]:

            # Don't include root folder name in path
            if is_root:
                child_path = folder_path
            else:
                child_path = folder_path + [sanitise_string(folder["name"])]

            child_charts = collect_charts_for_export(
                folder_id=child_folder["id"],
                export_formats=export_formats,
                recursive=recursive,
                skip_folder_name=skip_folder_name,
                publish=publish,
                chart_numbering_df=chart_numbering_df,
                folder_path=child_path,
                is_root=False,
            )
            charts_to_export.extend(child_charts)

    return charts_to_export


def save_charts_locally(
    charts: list[dict],
    base_path: str,
    flatten_path: bool = False,
) -> None:
    """
    Save collected charts to local filesystem.

    Parameters:
        charts: List of chart metadata from collect_charts_for_export()
        base_path: Base directory path for saving charts
        flatten_path: Whether to flatten folder structure (default: False)

    Returns:
        None
    """
    for chart in charts:

        # Determine save path
        if flatten_path:
            save_dir = base_path
        else:
            save_dir = os.path.join(base_path, *chart["folder_path"])
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

        filename = chart["filename"]
        output_format = chart["output_format"]
        filepath = os.path.join(save_dir, f"{filename}.{output_format}")

        # Export
        try:
            export_chart(
                chart_id=chart["chart_id"],
                output_format=output_format,
                filepath=filepath,
                width=None,
                height="auto",
                border_width=0,
                **chart["export_params"]
            )
            logger.info(f"Saved {filepath}")
        except ValueError:
            logger.error(f"ValueError occurred while exporting chart {filename}")


# %%
# EXECUTE
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

validate_api_token()

charts = collect_charts_for_export(
    folder_id=FOLDER_ID,
    export_formats=EXPORT_FORMATS,
    recursive=True,
    skip_folder_name="Archive",
    publish=True,
    chart_numbering_df=df_chart_numbering,
)

# Save them locally
save_charts_locally(
    charts=charts,
    base_path=OUTPUT_PATH,
    flatten_path=False,
)

# %%
