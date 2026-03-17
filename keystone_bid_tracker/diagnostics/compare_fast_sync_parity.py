"""
Quick parity checker for Moraware fast sync vs legacy per-job sync.

Usage:
  python keystone_bid_tracker/diagnostics/compare_fast_sync_parity.py ^
    --base-url "https://keystonesolidsurfaces.moraware.net" ^
    --username "your_user" ^
    --job-id 12345 --job-id 23456

Optional:
  --password "your_password"    (or omit and the script prompts securely)
  --start-date YYYY-MM-DD
  --end-date YYYY-MM-DD
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from typing import Any


THIS_FILE = os.path.abspath(__file__)
DIAGNOSTICS_DIR = os.path.dirname(THIS_FILE)
PACKAGE_DIR = os.path.dirname(DIAGNOSTICS_DIR)
REPO_ROOT = os.path.dirname(PACKAGE_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from keystone_bid_tracker.utils.moraware_client import MorewareClient  # noqa: E402


def _fmt_tp(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        return f"{float(value):.2f}"
    except Exception:
        return str(value).strip()


def _phase_tp_map(rows: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in rows or []:
        phase = str(row.get("phase") or "").strip()
        if not phase:
            continue
        out[phase] = _fmt_tp(row.get("tp_code"))
    return out


def _print_phase_table(job_label: str, fast_rows: list[dict], legacy_rows: list[dict]) -> tuple[int, int]:
    fast_map = _phase_tp_map(fast_rows)
    legacy_map = _phase_tp_map(legacy_rows)
    phases = sorted(set(fast_map.keys()) | set(legacy_map.keys()))

    print(f"\n{job_label} - phase/TP comparison")
    print("-" * 92)
    print(f"{'Phase':<32} {'Fast TP':<16} {'Legacy TP':<16} {'Match':<8}")
    print("-" * 92)

    matched = 0
    total = len(phases)
    for phase in phases:
        f = fast_map.get(phase, "")
        l = legacy_map.get(phase, "")
        is_match = f == l
        if is_match:
            matched += 1
        print(f"{phase:<32} {f:<16} {l:<16} {('yes' if is_match else 'no'):<8}")
    if not phases:
        print("(no phases returned by either method)")
    return matched, total


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare Moraware fast sync output against legacy per-job sync.")
    parser.add_argument("--base-url", required=True, help="Moraware base URL, e.g. https://keystonesolidsurfaces.moraware.net")
    parser.add_argument("--username", required=True, help="Moraware username")
    parser.add_argument("--password", default="", help="Moraware password (omit to prompt)")
    parser.add_argument("--job-id", action="append", default=[], help="Moraware job id to test (repeat flag for multiple)")
    parser.add_argument("--start-date", default="", help="Optional YYYY-MM-DD fast sync filter start date")
    parser.add_argument("--end-date", default="", help="Optional YYYY-MM-DD fast sync filter end date")
    args = parser.parse_args()

    job_ids = [str(j).strip() for j in args.job_id if str(j).strip()]
    if not job_ids:
        print("No job IDs provided. Use one or more --job-id values.")
        return 2

    password = args.password or getpass.getpass("Moraware password: ")
    client = MorewareClient(
        username=args.username,
        password=password,
        base_url=args.base_url,
        use_fast_sync=True,
    )

    print("Logging in to Moraware...")
    client.login()
    print("Login successful.")

    linked_jobs = [{"moraware_job_id": j} for j in job_ids]
    print(f"Running fast bulk sync for {len(job_ids)} job(s)...")

    fast_result = client.sync_invoice_data_fast(
        linked_jobs=linked_jobs,
        start_date=args.start_date or None,
        end_date=args.end_date or None,
        progress_cb=lambda i, total: print(f"  fast progress {i}/{total}"),
    )

    fast_rows_by_job = fast_result.get("rows_by_job_id", {}) or {}
    fast_meta_by_job = fast_result.get("meta_by_job_id", {}) or {}

    print("\nRunning legacy per-job calls...")
    legacy_rows_by_job: dict[str, list[dict]] = {}
    legacy_details_by_job: dict[str, dict] = {}
    for idx, job_id in enumerate(job_ids, start=1):
        print(f"  legacy progress {idx}/{len(job_ids)}")
        legacy_rows_by_job[job_id] = client.get_invoice_data(job_id)
        legacy_details_by_job[job_id] = client.get_job_details(job_id)

    print("\n========== Parity Report ==========")
    total_phase_matches = 0
    total_phase_count = 0

    for job_id in job_ids:
        fast_job_number = str((fast_meta_by_job.get(job_id) or {}).get("job_number") or "").strip()
        legacy_job_number = str((legacy_details_by_job.get(job_id) or {}).get("job_number") or "").strip()
        job_number_match = fast_job_number == legacy_job_number
        display_job_number = fast_job_number or legacy_job_number
        job_label = f"Job # {display_job_number}" if display_job_number else "Job # (unknown)"

        print(f"\n{job_label} - job number comparison")
        print(f"  fast   : {fast_job_number or '(blank)'}")
        print(f"  legacy : {legacy_job_number or '(blank)'}")
        print(f"  match  : {'yes' if job_number_match else 'no'}")

        matched, total = _print_phase_table(
            job_label=job_label,
            fast_rows=fast_rows_by_job.get(job_id, []) or [],
            legacy_rows=legacy_rows_by_job.get(job_id, []) or [],
        )
        total_phase_matches += matched
        total_phase_count += total

    stats = fast_result.get("stats", {}) or {}
    print("\n========== Summary ==========")
    print(f"Phase TP matches: {total_phase_matches}/{total_phase_count}")
    print(f"Fast stats: {stats}")
    issues = fast_result.get("issues", []) or []
    if issues:
        print(f"Fast issues ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Fast issues: none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
