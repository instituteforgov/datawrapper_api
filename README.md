# datawrapper_api
This repository contains scripts for interacting with the Datawrapper API.

Scripts do not currently make edits to charts within Datawrapper. The only active change possible in Datawrapper is publishing unpublished charts in `collect_charts_for_export()`.

## Structure
- `get_chart_details.py`: Gets chart details and exports them to Excel.
- `export_charts.py`: Exports charts as PNGs and/or SVGs.

## Usage
Requires a Datawrapper API token to be stored in a `DATAWRAPPER_API_TOKEN` environment variable. To use `collect_charts_for_export()` with default arguments, this needs to have the following scopes:
- `chart:read, write`
- `folder:read`
- `theme:read`
- `visualization:read`

To use `export_charts()` with `publish=False`, the required scopes are only:
- `chart:read`
- `folder:read`

Note that in Datawrapper, API tokens are all associated with a user account (verifiable by creating a token with the `user:read` scope and calling the [`me` endpoint](https://developer.datawrapper.de/reference/getme)).
