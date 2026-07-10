# Always use this to start the app — it stops any already-running copy first,
# so you can never end up with two instances serving different code at once
# (which is what caused several confusing "ImportError"/"TypeError" sessions).
#
# Usage: right-click > Run with PowerShell, or from a terminal:
#   powershell -ExecutionPolicy Bypass -File run.ps1

$ErrorActionPreference = "SilentlyContinue"

$stray = Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'streamlit.exe'" |
    Where-Object { $_.CommandLine -like "*$PSScriptRoot*" }

if ($stray) {
    Write-Host "Stopping $($stray.Count) already-running process(es) for this app..." -ForegroundColor Yellow
    $stray | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
    Start-Sleep -Seconds 1
}

Write-Host "Starting CropDoc..." -ForegroundColor Green
& "$PSScriptRoot\.venv\Scripts\streamlit.exe" run "$PSScriptRoot\streamlit_app\app.py"
