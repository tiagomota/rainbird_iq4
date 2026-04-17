# CLAUDE.md

## Tooling

- Use `uv` for all Python package management (never `pip` directly).
  - Check latest package versions: `uv tool run pip index versions <package>`
  - Install packages: `uv add <package>`

## Project

Home Assistant custom integration for RainBird IQ4, distributed via HACS.

