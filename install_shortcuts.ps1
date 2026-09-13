$ErrorActionPreference = 'Stop'
$launcherRoot = $PSScriptRoot
$launcherPython = Join-Path $launcherRoot '.venv\Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $launcherPython)) {
    throw "Launcher environment not found: $launcherPython"
}
$shortcutFolders = @(
    [Environment]::GetFolderPath('Desktop'),
    [Environment]::GetFolderPath('Programs'),
    'C:\IsaacLab-3.0'
)
$shortcutShell = New-Object -ComObject WScript.Shell
foreach ($shortcutFolder in $shortcutFolders) {
    if (-not (Test-Path -LiteralPath $shortcutFolder)) { continue }
    $shortcutPath = Join-Path $shortcutFolder 'Isaac Launcher.lnk'
    if (Test-Path -LiteralPath $shortcutPath) {
        $oldShortcut = $shortcutShell.CreateShortcut($shortcutPath)
        if ($oldShortcut.TargetPath -ne $launcherPython) {
            throw "An unrelated shortcut already exists: $shortcutPath"
        }
    }
    $shortcut = $shortcutShell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $launcherPython
    $shortcut.Arguments = '-B "' + (Join-Path $launcherRoot 'main.py') + '"'
    $shortcut.WorkingDirectory = $launcherRoot
    $shortcut.IconLocation = (Join-Path $launcherRoot 'ui\icon.ico') + ',0'
    $shortcut.Description = 'Launch Isaac Sim or Isaac Lab with template and GPU selection'
    $shortcut.Save()
    Write-Output $shortcutPath
}
