$ErrorActionPreference = "Stop"

Write-Host "Running IPM tests (-m 'ipm_setup or ipm')..." -ForegroundColor Cyan
python -m pytest -m "ipm_setup or ipm" -v
