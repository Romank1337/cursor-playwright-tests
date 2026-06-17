$ErrorActionPreference = "Stop"

Write-Host "Running UI tests without IPM (e2e and not ipm_setup)..." -ForegroundColor Cyan
python -m pytest -m "e2e and not ipm_setup and not ipm" -v
