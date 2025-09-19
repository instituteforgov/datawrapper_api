# %%
"""
    Purpose
        Use Datawrapper API to export charts to SVG
    Inputs
        - API: Datawrapper API
    Outputs
        - svg: Various
    Parameters
        - DATAWRAPPER_API_TOKEN: Datawrapper API token
        - BASE_FOLDER_ID: ID of the base folder
        - BASE_PATH: Base path for exporting charts
    Notes
        - Sometimes files need to be saved to e.g. Downloads, as long file names mean they
        cannot always be saved in the intended location
        - When tested on WM2025
            - Tables generally came in with excess whitespace at the bottom (e.g.
            https://app.datawrapper.de/edit/kgU97/edit)
            - Some charts also had excess whitespace at the bottom (e.g.
            https://app.datawrapper.de/edit/4y8jS/publish#export-svg)
            - In some cases there were additional gridlines and axis labels were added (e.g.
            https://app.datawrapper.de/edit/31VXr/publish#export-svg)
        These all probably stem from the fact that, using the front end, we export SVGs with the
        'Auto' option selected when exporting just the chart body. This means the height is set
        to just the chart body height, rather than the chart body being stretched to the full
        height of the chart before the header and footer are removed. Using the API, as of
        December 2024, it doesn't seem to be possible to use such an 'Auto' option
"""

import os

from datawrapper import Datawrapper
from requests.exceptions import ReadTimeout

# %%
# SET PARAMETERS
DATAWRAPPER_API_TOKEN = os.getenv("DATAWRAPPER_API_TOKEN")
BASE_FOLDER_ID = 315975
BASE_PATH = "C:/Users/nyep/Downloads"

# %%
# INITIALISE
dw = Datawrapper(access_token=DATAWRAPPER_API_TOKEN)

base_folder = dw.get_folder(
    folder_id=BASE_FOLDER_ID
)
print(base_folder["name"])


# %%
def export_charts(
    BASE_FOLDER_ID: int,
    BASE_PATH: str,
    max_retries: int = 5
) -> None:
    """"
        Recursively parse folder structure and export all charts to SVG

        Parameters:
            - BASE_FOLDER_ID: The ID of the base folder

        Returns:
            None

        Notes:
            None
    """

    folder = dw.get_folder(
        folder_id=BASE_FOLDER_ID
    )

    path_folder = os.path.join(
        BASE_PATH,
        folder["name"]
    )

    if not os.path.exists(path_folder):
        os.makedirs(path_folder)

    if folder["charts"]:
        for chart in folder["charts"]:
            title = dw.get_chart(
                chart_id=chart["id"]
            )["title"]

            print(f"Exporting chart {chart["id"]}-{title}")

            # Remove characters that break file paths
            title = title.replace("/", "")
            title = title.replace(":", "")

            for _ in range(max_retries):

                try:
                    dw.export_chart(
                        chart_id=chart["id"],
                        width=853,
                        height="auto",
                        border_width=0,
                        output="svg",
                        plain=True,
                        filepath=path_folder + f"/{chart["id"]}-{title}.svg",
                        display=False
                    )
                    break

                except ReadTimeout:
                    pass

                except ValueError:
                    print(f"Error exporting chart {chart["id"]}-{title}")

    for child_folder in folder["children"]:

        export_charts(
            BASE_FOLDER_ID=child_folder["id"],
            BASE_PATH=path_folder
        )

    return


# %%
export_charts(
    BASE_FOLDER_ID,
    BASE_PATH
)

# %%
