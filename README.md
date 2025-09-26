# datawrapper_api
This repository contains scripts for interacting with the Datawrapper API and related image processing tasks.

## Structure
- `query_api.py`: Script for exporting charts.
- `get chart details.py`: Script for getting chart details and exporting to Excel.

## Usage
- Requires a Datawrapper API token with read access to be stored in a `DATAWRAPPER_API_TOKEN` environment variable.

## Dependencies
The `datawrapper` dependency is for [a forked version of the Datawrappy Python package, with `height` parameter added to the `export_chart()` method](https://github.com/philipnye/Datawrapper)
    - Install using `pip install git+https://github.com/philipnye/Datawrapper`
