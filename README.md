# datawrapper_api
This repository contains scripts for interacting with the Datawrapper API and related image processing tasks.

## Structure
- `images/`: Directory for storing image files.
- `temp/`: Temporary files and scripts.
- `query_api.py`: Main script for querying the Datawrapper API.

## Usage
1. Clone the repository.
2. Install dependencies.
3. Run `query_api.py` to interact with the Datawrapper API.

## Dependencies
- **datawrapper**: [A forked version of the Datawrappy Python package, with `height` parameter added to the `export_chart()` method](https://github.com/philipnye/Datawrapper)
    - Install using `pip install git+https://github.com/philipnye/Datawrapper`
- **requests**
