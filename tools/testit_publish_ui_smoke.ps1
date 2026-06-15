<#
.SYNOPSIS
  Publishes UI/Smoke autotests into Test IT MDC project via REST API v2.
  Idempotent: existing autotests are updated by externalId; new ones are created.

.DESCRIPTION
  Bypasses testit-adapter-pytest (incompatible with this server: schema fields
  isFlakyAuto / workItemsCount mismatch). Reads tests definition from
  tools/testit_ui_smoke_autotests.json (UTF-8 with Cyrillic display names).

.PARAMETER Token
  Private Token (testit.zyfra.com -> Profile -> API Keys).

.PARAMETER DefinitionFile
  Path to JSON with autotest definitions. Default = tools/testit_ui_smoke_autotests.json.

.PARAMETER ProjectId
  GUID of the target project. Default = MDC (globalId 3117).

.PARAMETER TmsUrl
  Base URL of Test IT.

.EXAMPLE
  .\tools\testit_publish_ui_smoke.ps1 -Token "<your_token>"
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)] [string]$Token,
  [string]$DefinitionFile = "",
  [string]$ProjectId = "4974a48f-041b-44ac-a42e-ebab5bb3a74b",
  [string]$TmsUrl = "https://testit.zyfra.com"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

if ([string]::IsNullOrEmpty($DefinitionFile)) {
  $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
  $DefinitionFile = Join-Path $scriptDir "testit_ui_smoke_autotests.json"
}

add-type @"
using System.Net;
using System.Security.Cryptography.X509Certificates;
public class TrustAllCertsPolicyPublish : ICertificatePolicy {
  public bool CheckValidationResult(ServicePoint sp, X509Certificate c, WebRequest r, int p) { return true; }
}
"@ -ErrorAction SilentlyContinue
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicyPublish
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12

$headers = @{
  Authorization  = "PrivateToken $Token"
  "Content-Type" = "application/json; charset=utf-8"
}

if (-not (Test-Path $DefinitionFile)) {
  throw "Definition file not found: $DefinitionFile"
}

# Recursively convert JSON steps (PSCustomObject) into ordered hashtables
# so ConvertTo-Json serializes them as Test IT AutoTestStepModel:
# { title, description?, steps?[] }
function Convert-Steps {
  param($items)
  if ($null -eq $items) { return @() }
  $out = New-Object System.Collections.ArrayList
  foreach ($s in $items) {
    if ($null -eq $s) { continue }
    $node = [ordered]@{ title = [string]$s.title }
    if ($s.PSObject.Properties.Match('description').Count -gt 0 -and $s.description) {
      $node.description = [string]$s.description
    }
    if ($s.PSObject.Properties.Match('steps').Count -gt 0 -and $s.steps) {
      $node.steps = (Convert-Steps $s.steps)
    }
    [void]$out.Add($node)
  }
  return , $out.ToArray()
}

# Read JSON in UTF-8 to keep Cyrillic display names intact.
$raw = [System.IO.File]::ReadAllText($DefinitionFile, [System.Text.Encoding]::UTF8)
$autotests = $raw | ConvertFrom-Json

Write-Host ("Total autotests to publish: {0}" -f $autotests.Count) -ForegroundColor Cyan
Write-Host ("Project: {0}  Namespace: UI/Smoke" -f $ProjectId) -ForegroundColor Cyan
Write-Host ""

$created = 0
$updated = 0
foreach ($t in $autotests) {
  $searchBody = @{
    filter = @{
      projectIds  = @($ProjectId)
      externalIds = @($t.externalId)
    }
  } | ConvertTo-Json -Depth 5

  try {
    $existing = Invoke-RestMethod -Uri "$TmsUrl/api/v2/autoTests/search" -Headers $headers -Method POST -Body $searchBody
  } catch {
    $existing = @()
  }

  $desc = if ($t.description) { [string]$t.description } else { "UI autotest. Source: pytest + Playwright. See decorators in tests/test_*.py" }

  $stepsArr    = Convert-Steps $t.steps
  $setupArr    = Convert-Steps $t.setup
  $teardownArr = Convert-Steps $t.teardown

  $payload = [ordered]@{
    projectId   = $ProjectId
    externalId  = $t.externalId
    name        = $t.displayName
    namespace   = "UI/Smoke"
    classname   = $t.classname
    title       = $t.displayName
    description = $desc
    steps       = $stepsArr
    setup       = $setupArr
    teardown    = $teardownArr
    links       = @()
    labels      = @(
      @{ name = "ui" },
      @{ name = "pytest" },
      @{ name = "playwright" }
    )
    isFlaky     = $false
  }

  # Use UTF-8 JSON body so server stores Cyrillic correctly.
  $bodyJson = $payload | ConvertTo-Json -Depth 10
  $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($bodyJson)

  $stepCounts = "setup={0}, steps={1}, teardown={2}" -f $setupArr.Count, $stepsArr.Count, $teardownArr.Count

  if ($existing -and $existing.Count -gt 0) {
    $payload.id = $existing[0].id
    $bodyJson = $payload | ConvertTo-Json -Depth 10
    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($bodyJson)
    Invoke-RestMethod -Uri "$TmsUrl/api/v2/autoTests" -Headers $headers -Method PUT -Body $bodyBytes | Out-Null
    Write-Host ("  UPDATED  {0}  ->  classname={1}  [{2}]" -f $t.externalId, $t.classname, $stepCounts) -ForegroundColor Yellow
    $updated++
  } else {
    $res = Invoke-RestMethod -Uri "$TmsUrl/api/v2/autoTests" -Headers $headers -Method POST -Body $bodyBytes
    Write-Host ("  CREATED  {0}  (id={1}, classname={2})  [{3}]" -f $t.externalId, $res.id, $t.classname, $stepCounts) -ForegroundColor Green
    $created++
  }
}

Write-Host ""
Write-Host ("Done. Created: {0}, Updated: {1}" -f $created, $updated) -ForegroundColor Cyan
Write-Host ("Open: $TmsUrl/projects/3117/autotests?type=Namespace&namespace=UI/Smoke") -ForegroundColor White
