$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$target = Join-Path $repo 'launch_keystone_bid_tracker.cmd'
if (-not (Test-Path $target)) {
    throw "Launcher not found: $target"
}
$desktop = [Environment]::GetFolderPath('Desktop')
$lnk = Join-Path $desktop 'Keystone Bid Tracker.lnk'
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($lnk)
$Shortcut.TargetPath = $target
$Shortcut.WorkingDirectory = $repo
$Shortcut.Description = 'Keystone Bid Tracker (runs from git repo)'
$appIcon = Join-Path $repo 'keystone_bid_tracker\Assets\icons\bidtracker.ico'
$venvPythonw = Join-Path $repo '.venv\Scripts\pythonw.exe'
if (Test-Path $appIcon) {
    $Shortcut.IconLocation = "$appIcon,0"
} elseif (Test-Path $venvPythonw) {
    $Shortcut.IconLocation = "$venvPythonw,0"
} else {
    $py = Get-Command pythonw -ErrorAction SilentlyContinue
    if ($py) { $Shortcut.IconLocation = "$($py.Source),0" }
}
$Shortcut.Save()
Write-Host "Created: $lnk"
