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

from datawrapper import Datawrapper
import pandas as pd
from requests.exceptions import ReadTimeout

# %%
# SET CONSTANTS
DATAWRAPPER_API_TOKEN = os.getenv("DATAWRAPPER_API_TOKEN")
BASE_FOLDER_ID = 312749
BASE_PATH = "C:/Users/" + os.getlogin() + "/INSTITUTE FOR GOVERNMENT/Research - Public services/Projects/Performance Tracker/PT2025/6. PT25 charts/9. Prisons"
CHART_NUMBERING_FILE_PATH = "C:/Users/" + os.getlogin() + "/Institute for Government/Research - Public services/Projects/Performance Tracker/PT2025/6. PT25 charts/9. Prisons/Chart numbering - Prisons.xlsx"

# %%
# IMPORT CHART NUMBERING
if CHART_NUMBERING_FILE_PATH:
    df_chart_numbering = pd.read_excel(
        CHART_NUMBERING_FILE_PATH,
        dtype={"Chart ID": str}
    )

# %%
# INITIALISE
dw = Datawrapper(access_token=DATAWRAPPER_API_TOKEN)

base_folder = dw.get_folder(
    folder_id=BASE_FOLDER_ID
)
print(base_folder["name"])


# %%
def export_charts(
    dw: Datawrapper,
    folder_id: int,
    path: str,
    output: str,
    max_retries: int = 5,
    recursive: bool = False,
    **kwargs,
) -> None:
    """"
        Parse folder structure and export all charts.

        Parameters:
            - dw: Datawrapper instance
            - folder_id: The ID of the base folder
            - path: Base path for exporting charts
            - output: Export format (e.g. "png" or "svg")
            - max_retries: Maximum number of retry attempts for chart export (default: 5)
            - recursive: Whether to recursively browse sub-folders (default: False)
            - **kwargs: Additional keyword arguments to pass to the export function

        Returns:
            None

        Notes:
            - height="auto" is not the same as supplying None: the former exports the chart at its height in the Datawrapper UI, minus height required for the header and footer; the latter exports the chart at its full height (even where plain=True is supplied)
    """

    folder = dw.get_folder(
        folder_id=folder_id
    )

    if folder["charts"]:
        for chart in folder["charts"]:

            # Skip charts without a proper title
            # NB: For some reason, there seem to tend to be a few blank charts per folder, not visible in the UI
            chart_title = dw.get_chart(chart_id=chart["id"])["title"]
            if chart_title != "[ Insert title here ]":

                # Look up chart number from df_chart_numbering
                chart_number_row = df_chart_numbering[df_chart_numbering['Chart ID'] == chart["id"]]

                if not chart_number_row.empty:
                    chart_number = chart_number_row.iloc[0]['Chart number']
                    filename = chart_number
                    print(f"Exporting chart {chart["id"]}-{chart_title} as {filename}")

                # Fallback to original naming if chart ID not found in lookup
                else:
                    title_clean = chart_title.replace("/", "").replace(":", "")
                    filename = f"{chart["id"]}-{title_clean}"
                    print(f"Chart ID {chart["id"]} not found in lookup table. Using fallback name: {filename}")

                # Remove characters that break file paths from filename
                filename = filename.replace("/", "").replace(":", "")

                for _ in range(max_retries):

                    try:
                        dw.export_chart(
                            chart_id=chart["id"],
                            width=None,
                            height="auto",
                            border_width=0,
                            output=output,
                            filepath=path + f"/{filename}.{output}",
                            display=False,
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
                max_retries=max_retries,
                recursive=recursive
            )

    return


# %%
export_formats = {
    "svg": {"plain": True},
    "png": {"plain": False},
}

for format, options in export_formats.items():
    export_charts(
        dw=dw,
        folder_id=BASE_FOLDER_ID,
        path=BASE_PATH,
        output=format,
        **options
    )

# %%
