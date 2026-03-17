# Build Notes

## Windows app icon

- Runtime icon path: `keystone_bid_tracker/Assets/icons/bidtracker.ico`
- Source SVGs:
  - `keystone_bid_tracker/Assets/icons/bidtracker-full.svg` (48+ sizes)
  - `keystone_bid_tracker/Assets/icons/bidtracker-small.svg` (16/24/32)
- Generated raster/icon assets are stored in `keystone_bid_tracker/Assets/icons/`.

## PyInstaller usage

When building on Windows, pass the icon file explicitly:

```bash
pyinstaller --noconfirm --windowed --name "Keystone Bid Tracker" --icon "keystone_bid_tracker/Assets/icons/bidtracker.ico" "keystone_bid_tracker/main.py"
```

If your build command is scripted elsewhere, keep this same `.ico` path in that script so taskbar and shortcut icons match the runtime icon.

## One-click scripts (repo root)

- `build_windows_exe.bat`
  - Builds a windowed executable with icon and bundled `Assets`.
  - Output: `dist/Keystone Bid Tracker/Keystone Bid Tracker.exe`
- `run_keystone_bid_tracker.bat`
  - Launches the built executable with no terminal window.
  - If the executable does not exist yet, run `build_windows_exe.bat` first.
