## Project purpose

This repository adapts H2Integrate for techno-economic and geospatial
energy-system analysis in Chile.

## Development rules

- Never commit directly to main or develop.
- Preserve compatibility with upstream H2Integrate whenever possible.
- Do not modify public interfaces without documenting the reason.
- Keep Chile-specific assumptions configurable.
- Do not hard-code local file paths.
- Do not commit credentials, downloaded meteorological datasets, or large outputs.
- Add or update tests for every behavioral change.
- Run the relevant tests before considering a task complete.
- Prefer small, reviewable changes.
- Explain any assumptions related to Chilean regulation, costs, coordinates,
  units, or meteorological data.

## Python conventions

- Use explicit and descriptive variable names.
- Add type hints to new public functions.
- Add docstrings to new modules, classes, and public functions.
- Use SI units internally unless the existing package specifies otherwise.
- State temporal resolution and timezone explicitly for time-series data.

## Git conventions

- Do not switch branches unless explicitly requested.
- Do not commit or push unless explicitly requested.
- Do not use force push.
- Show the diff and test results after making changes.