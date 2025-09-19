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
"""

import os

from datawrapper import Datawrapper
from requests.exceptions import ReadTimeout

# %%
# SET PARAMETERS
DATAWRAPPER_API_TOKEN = os.getenv("DATAWRAPPER_API_TOKEN")
BASE_FOLDER_ID = 350839
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
            - height="auto" is not the same as supplying None: the former exports the
            chart at its height in the Datawrapper UI, minus height required for the
            header and footer; the latter exports the chart at its full height (even
            where plain=True is supplied)
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
                        width=None,
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
