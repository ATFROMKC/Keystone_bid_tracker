# Setup Guide - Keystone Bid Tracker

## 1) Prerequisites

- Windows environment
- Python 3.10+ (recommended)
- Access to:
  - Moraware account with API permissions
  - Shared Dropbox bids folder
  - Shared SQLite DB location (or permission to create one)

## 2) Clone and Install

```bash
git clone <repo-url>
cd Keystone_bid_tracker
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 3) First Run

```bash
python keystone_bid_tracker/main.py
```

On first run, if no DB path is set, the app prompts for a `.db` file location.

## 4) Configure Local Settings (Per User)

Open app Settings and configure:

- Moraware URL
- Moraware Username
- Moraware Password (API-enabled)
- Dropbox Bids Root Path
- Database Path

Expected keys in local config:
- `moraware_url`
- `moraware_username`
- `moraware_password`
- `dropbox_bids_path`
- `database_path`

## 5) Example Path Patterns (Windows)

- Dropbox bids root:  
  `C:\Users\<your-user>\Dropbox\<Company Shared Folder>\Bids`

- SQLite DB file:  
  `C:\Users\<your-user>\Dropbox\<Company Shared Folder>\Bids\keystone_bid_tracker.db`

## 6) Notes on Local Config + Security

- Config is local-only and intentionally not tracked in Git.
- Do not commit credentials.
- Each reviewer/dev must set their own Moraware + Dropbox paths.

## 7) Current Functional Maturity

- Estimator portal is most stable.
- PM portal is actively evolving.
  - `Active Jobs`: primary PM workflow currently used.
  - `Pending Award`: incomplete.
  - `Completed History`: incomplete.

## 8) Troubleshooting

### App cannot connect to DB
- Verify `database_path` points to an existing `.db` (or choose a valid writable location).

### Moraware sync/auth fails
- Verify URL/username/password are correct.
- Confirm account has required API access.

### Dropbox folder actions fail
- Verify `dropbox_bids_path` is correct and accessible on your machine.
- Confirm expected year/month folder structure exists.
