<#
.SYNOPSIS
  Creates UI/Smoke namespace in Test IT MDC project by publishing one placeholder autotest.

.DESCRIPTION
  After this script runs, the URL
  https://testit.zyfra.com/projects/3117/autotests?type=Namespace&namespace=UI/Smoke
  will show a "UI / Smoke" node with one placeholder autotest.

  Then run `pytest --testit` to push all 22 real UI autotests into the same namespace.
  The placeholder can be deleted in TMS UI afterwards.

.PARAMETER Token
  Private Token from testit.zyfra.com profile (Profile -> API Keys).

.PARAMETER PlaceholderExternalId
  externalId of the placeholder autotest. Defaults to "ui.smoke.namespace_marker".

.PARAMETER ProjectId
  Project GUID in Test IT. Default = MDC (globalId 3117).

.PARAMETER TmsUrl
  Base URL of Test IT. Default = https://testit.zyfra.com.

.EXAMPLE
  .\tools\testit_create_ui_smoke.ps1 -Token "<your_token>"
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$Token,

  [string]$PlaceholderExternalId = "ui.smoke.namespace_marker",

  [string]$ProjectId = "4974a48f-041b-44ac-a42e-ebab5bb3a74b",

  [string]$TmsUrl = "https://testit.zyfra.com"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

add-type @"
using System.Net;
using System.Security.Cryptography.X509Certificates;
public class TrustAllCertsPolicyTMS : ICertificatePolicy {
  public bool CheckValidationResult(ServicePoint sp, X509Certificate c, WebRequest r, int p) { return true; }
}
"@ -ErrorAction SilentlyContinue
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicyTMS
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12

$headers = @{
  Authorization  = "PrivateToken $Token"
  "Content-Type" = "application/json"
}

Write-Host "[1/3] Verify project access..." -ForegroundColor Cyan
$project = Invoke-RestMethod -Uri "$TmsUrl/api/v2/projects/$ProjectId" -Headers $headers -Method GET
Write-Host ("       OK: project '{0}' (globalId={1})" -f $project.name, $project.globalId) -ForegroundColor Green

Write-Host "[2/3] Check existing autotest with externalId '$PlaceholderExternalId'..." -ForegroundColor Cyan
$searchBody = @{
  filter = @{
    projectIds  = @($ProjectId)
    externalIds = @($PlaceholderExternalId)
  }
} | ConvertTo-Json -Depth 6
try {
  $existing = Invoke-RestMethod -Uri "$TmsUrl/api/v2/autoTests/search" -Headers $headers -Method POST -Body $searchBody
} catch {
  $existing = @()
}
if ($existing -and $existing.Count -gt 0) {
  Write-Host ("       Already exists. Autotest id={0}" -f $existing[0].id) -ForegroundColor Yellow
  Write-Host "       Skipping creation - namespace UI/Smoke is already present." -ForegroundColor Yellow
  Write-Host ""
  Write-Host ("Open: $TmsUrl/projects/{0}/autotests?type=Namespace&namespace=UI/Smoke" -f $project.globalId) -ForegroundColor Cyan
  return
}

Write-Host "[3/3] Create namespace marker autotest..." -ForegroundColor Cyan
$body = @{
  projectId   = $ProjectId
  externalId  = $PlaceholderExternalId
  name        = "UI/Smoke namespace marker (placeholder)"
  namespace   = "UI/Smoke"
  classname   = "Marker"
  title       = "UI/Smoke namespace marker"
  description = "Auto-created so that UI/Smoke namespace appears in the tree. After first 'pytest --testit' run, all real UI tests show up here. This placeholder can be deleted manually."
  steps       = @()
  setup       = @()
  teardown    = @()
  links       = @()
  labels      = @(@{ name = "placeholder" })
  isFlaky     = $false
} | ConvertTo-Json -Depth 6

$created = Invoke-RestMethod -Uri "$TmsUrl/api/v2/autoTests" -Headers $headers -Method POST -Body $body
Write-Host ("       OK: created autotest id={0}" -f $created.id) -ForegroundColor Green
Write-Host ""
Write-Host "Done. Open:" -ForegroundColor Cyan
Write-Host ("  $TmsUrl/projects/{0}/autotests?type=Namespace&namespace=UI/Smoke" -f $project.globalId) -ForegroundColor White
Write-Host ""
Write-Host "Next: run 'pytest --testit' to publish all 22 real UI autotests into the same namespace." -ForegroundColor Cyan
