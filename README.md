# Keystone Bid Tracker

Desktop app for bid tracking and PM workflow support, with Moraware integration and a shared SQLite database workflow.

## Development Status

This project is under active development and is not feature-complete.

### Portal maturity
- **Estimator Portal:** most stable area for daily use/testing.
- **PM Portal:** in-progress and evolving rapidly.
  - **Active Jobs:** primary PM workflow currently being refined.
  - **Pending Award:** **unfinished / partial implementation**.
  - **Completed History:** **unfinished / partial implementation**.

Please treat PM outcomes as provisional, especially in **Pending Award** and **Completed History**.

## What It Does

- Tracks bids, revisions, statuses, and customers.
- Supports bid-to-Moraware job linking workflows.
- Provides PM-oriented views for active/pending/history operations.
- Uses a shared SQLite database (commonly hosted in Dropbox).

## Tech Stack

- Python
- PyQt5
- SQLite

## Quick Start (Windows)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python keystone_bid_tracker/main.py
```

## Required Local Configuration (Per User)

This project requires local credentials and local path configuration that are **not committed to Git**.

Each user must configure:
- `moraware_url`
- `moraware_username`
- `moraware_password` (API-enabled account)
- `dropbox_bids_path`
- `database_path`

These values are stored locally in `keystone_bid_tracker/config.json` (or beside the packaged `.exe`) and are intentionally ignored by Git.

## Example Path Patterns (Windows)

- `dropbox_bids_path`  
  `C:\Users\<your-user>\Dropbox\<Company Shared Folder>\Bids`

- `database_path`  
  `C:\Users\<your-user>\Dropbox\<Company Shared Folder>\Bids\keystone_bid_tracker.db`

## Repository Structure (High Level)

- `keystone_bid_tracker/` - application source
- `docs/` - project/setup/reference docs
- `reference/` - legacy/reference source materials
- `tools/release/` - packaging scripts/spec files
- `_archive/` - archived generated build outputs

## Reviewer Notes

If reviewing this codebase, prioritize:
1. Estimator portal workflows
2. PM `Active Jobs` linking/review workflows

Treat PM `Pending Award` and `Completed History` as in-progress.

## Security / Secrets

- No production credentials are included in source control.
- Do not commit local config files with credentials.
- Build outputs are archived/ignored and are not required for source-based development.
