"""
Entry point for launch_keystone_bid_tracker.cmd.

Ensures the process working directory is the repo root (fixes odd Explorer/shortcut
cases) and writes Python tracebacks to %%TEMP%%\\KeystoneBidTracker_last_error.txt
when startup fails — pythonw would otherwise hide all output.
"""

from __future__ import annotations

import os
import sys
import traceback


def _repo_root() -> str:
    # This file lives in <repo>/scripts/launch_app.py
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _error_log_path() -> str:
    return os.path.join(os.environ.get("TEMP", "."), "KeystoneBidTracker_last_error.txt")


def _write_error(msg: str) -> None:
    try:
        with open(_error_log_path(), "w", encoding="utf-8") as f:
            f.write(msg)
    except OSError:
        pass


def main() -> None:
    root = _repo_root()
    try:
        os.chdir(root)
    except OSError as e:
        _write_error(f"Could not set working directory to repo root:\n{root}\n\n{e!r}\n")
        sys.exit(1)

    kbt_pkg = os.path.join(root, "keystone_bid_tracker")
    if kbt_pkg not in sys.path:
        sys.path.insert(0, kbt_pkg)

    try:
        import main as app_main

        app_main.main()
    except SystemExit:
        raise
    except Exception:
        try:
            with open(_error_log_path(), "w", encoding="utf-8") as f:
                traceback.print_exc(file=f)
        except OSError:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
