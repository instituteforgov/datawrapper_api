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

import pandas as pd
from requests.exceptions import ReadTimeout

from utils import export_chart, get_chart, get_folder, validate_api_token

# %%
# SET CONSTANTS
FOLDER_ID = 340017
OUTPUT_PATH = "C:/Users/" + os.getlogin() + "/Institute for Government/Research - Whitehall Monitor/Projects/2026/Charts"
CHART_NUMBERING_FILE_PATH = OUTPUT_PATH + "/Chart numbering - WM2026.xlsx"


# %%
# DEFINE FUNCTIONS
def export_charts(
    folder_id: int,
    path: str,
    output: str,
    max_retries: int = 5,
    recursive: bool = False,
    skip_folder_name: str = "Archive",
    chart_numbering_df: pd.DataFrame | None = None,
    **kwargs,
) -> None:
    """"
        Parse folder structure and export all charts.

        Parameters:
            folder_id: The ID of the base folder
            path: Base path for exporting charts
            output: Export format (e.g. "png" or "svg")
            max_retries: Maximum number of retry attempts for chart export (default: 5)
            recursive: Whether to recursively browse sub-folders (default: False)
            skip_folder_name: Name of folders to skip (default: 'Archive')
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

    if folder["charts"]:
        for chart in folder["charts"]:

            # Skip charts without a proper title
            # NB: For some reason, there seem to tend to be a few blank charts per folder, not visible in the UI
            chart_title = get_chart(chart_id=chart["id"])["title"]
            if chart_title != "[ Insert title here ]":

                # Look up chart number from chart_numbering_df if provided
                if chart_numbering_df is not None:
                    chart_number_row = chart_numbering_df[chart_numbering_df['Chart ID'] == chart["id"]]

                    if not chart_number_row.empty:
                        chart_number = chart_number_row.iloc[0]['Chart number']
                        # Handle case where chart_number might be NaN
                        if pd.isna(chart_number):
                            filename = f"{chart["id"]}-{chart_title.replace("/", "").replace(":", "")}"
                            print(f"Chart ID {chart["id"]} has blank chart number. Using fallback name: {filename}")
                        else:
                            filename = str(chart_number)
                            print(f"Exporting chart {chart["id"]}-{chart_title} as {filename}")

                    # Fallback to original naming if chart ID not found in lookup
                    else:
                        title_clean = chart_title.replace("/", "").replace(":", "")
                        filename = f"{chart["id"]}-{title_clean}"
                        print(f"Chart ID {chart["id"]} not found in lookup table. Using fallback name: {filename}")
                else:
                    # No chart numbering provided, use chart ID and title
                    title_clean = chart_title.replace("/", "").replace(":", "")
                    filename = f"{chart["id"]}-{title_clean}"
                    print(f"Exporting chart {chart["id"]}-{chart_title} as {filename}")

                # Remove characters that break file paths from filename
                filename = str(filename).replace("/", "").replace(":", "")

                for _ in range(max_retries):

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
                        pass

                    except ValueError:
                        print(f"Error exporting chart {filename}")

    # Recursively process child folders if recursive flag is True
    if recursive:
        for child_folder in folder["children"]:
            path = path + f"/{folder['name']}"

            if not os.path.exists(path):
                os.makedirs(path)

            export_charts(
                folder_id=child_folder["id"],
                path=path,
                output=output,
                max_retries=max_retries,
                recursive=recursive,
                skip_folder_name=skip_folder_name,
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
        dtype={"Chart ID": str}
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
        chart_numbering_df=df_chart_numbering,
        **options
    )

# %%
