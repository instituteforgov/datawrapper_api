# datawrapper_api

Scripts for interacting with the Datawrapper API.

Scripts do not currently make edits to charts within Datawrapper. The only active change possible in Datawrapper is publishing unpublished charts in `collect_charts_for_export()`.

## Project structure

```
├── temp/
├── .gitignore
├── .pre-commit-config.yaml
├── export_charts.py
├── get_chart_details.py
├── README.md
└── utils.py
```

## Scripts

| File | Description |
| ---- | ----------- |
| `get_chart_details.py` | Gets details of all charts in a Datawrapper folder, including embed codes, and saves them to Excel. |
| `export_charts.py` | Exports charts as PNGs and/or SVGs, optionally publishing unpublished charts first. |
| `utils.py` | Shared utility functions used by the scripts above. |

## Environment variables

The scripts require a Datawrapper API token to be stored in a `DATAWRAPPER_API_TOKEN` environment variable.

| Variable | Description |
| -------- | ----------- |
| `DATAWRAPPER_API_TOKEN` | Datawrapper API token |

To use `collect_charts_for_export()` with default arguments, this needs to have the following scopes:
- `chart:read, write`
- `folder:read`
- `theme:read`
- `visualization:read`

To use `export_charts()` with `publish=False`, the required scopes are only:
- `chart:read`
- `folder:read`

Note that in Datawrapper, API tokens are all associated with a user account (verifiable by creating a token with the `user:read` scope and calling the [`me` endpoint](https://developer.datawrapper.de/reference/getme)).

## Contributing

This project uses `pre-commit` hooks to ensure code quality. To set up:

1. Install `pre-commit` on your system if you don't already have it:
    ```bash
    pip install pre-commit
    ```
2. Set up `pre-commit` in your copy of this project. In the project directory, run:
    ```bash
    pre-commit install
    ```

Rules that are applied can be found in [`.pre-commit-config.yaml`](.pre-commit-config.yaml).

The hooks run automatically on commit, or manually with `pre-commit run --all-files`.
