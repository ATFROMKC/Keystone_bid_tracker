"""
Entry point for launch_keystone_bid_tracker.cmd.

Ensures the process working directory is the repo root (fixes odd Explorer/shortcut
cases) and writes Python tracebacks to %%TEMP%%\\KeystoneBidTracker_last_error.txt
when startup fails — pythonw would otherwise hide all output.

Also appends %%TEMP%%\\KeystoneBidTracker_launch_trace.txt so you can tell whether
the process started at all (useful when pythonw fails silently).
"""

from __future__ import annotations

import datetime
import os
import sys
import traceback


def _repo_root() -> str:
    # This file lives in <repo>/scripts/launch_app.py
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _temp_path(name: str) -> str:
    return os.path.join(os.environ.get("TEMP", "."), name)


_TRACE_FIRST = True


def _trace(msg: str) -> None:
    global _TRACE_FIRST

    line = f"{datetime.datetime.now().isoformat()} {msg}\n"
    try:
        mode = "w" if _TRACE_FIRST else "a"
        _TRACE_FIRST = False
        with open(_temp_path("KeystoneBidTracker_launch_trace.txt"), mode, encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass


def _error_log_path() -> str:
    return _temp_path("KeystoneBidTracker_last_error.txt")


def _write_error(msg: str) -> None:
    try:
        with open(_error_log_path(), "w", encoding="utf-8") as f:
            f.write(msg)
    except OSError:
        pass


def _enable_faulthandler() -> None:
    try:
        import faulthandler

        path = _temp_path("KeystoneBidTracker_faulthandler.log")
        f = open(path, "w", encoding="utf-8")  # noqa: SIM115 — kept for process lifetime
        faulthandler.enable(file=f, all_threads=True)
    except OSError:
        pass


def main() -> None:
    _trace("launch_app.py: entered main()")
    _enable_faulthandler()

    root = _repo_root()
    try:
        os.chdir(root)
        _trace(f"chdir ok: {root}")
    except OSError as e:
        _write_error(f"Could not set working directory to repo root:\n{root}\n\n{e!r}\n")
        _trace("chdir FAILED")
        sys.exit(1)

    kbt_pkg = os.path.join(root, "keystone_bid_tracker")
    if kbt_pkg not in sys.path:
        sys.path.insert(0, kbt_pkg)

    try:
        _trace("importing main...")
        import main as app_main

        _trace("calling app_main.main()...")
        app_main.main()
    except SystemExit as e:
        _trace(f"SystemExit code={e.code!r}")
        raise
    except Exception:
        _trace("uncaught Exception (writing last_error log)")
        try:
            with open(_error_log_path(), "w", encoding="utf-8") as f:
                traceback.print_exc(file=f)
        except OSError:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
