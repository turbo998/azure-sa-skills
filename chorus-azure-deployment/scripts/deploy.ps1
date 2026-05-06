<#
.SYNOPSIS
  Deploy Chorus to Azure Container Apps (single-instance test environment).

.DESCRIPTION
  - Creates the resource group if it does not exist.
  - Generates a strong NEXTAUTH_SECRET (32 random bytes, base64).
  - Prompts for the bootstrap admin password (or accepts -DefaultPassword).
  - If the Chorus container app already exists, FIRST scales it to 0 replicas
    and waits for the running revision to drain. This is critical because the
    embedded PGlite database does not tolerate two processes touching the
    persistent volume during an ACA rolling deployment.
  - Submits secrets via a temporary deployment-parameters JSON file (deleted
    in `finally`) so values never appear on the az command line.
  - Runs `az deployment group create` against main.bicep.
  - Prints the public app URL and waits for the first response (Prisma
    migrations can take up to ~60 seconds on first launch).

.PARAMETER ResourceGroup
  Resource group name. Created if missing.

.PARAMETER Location
  Azure region. Defaults to southeastasia.

.PARAMETER Subscription
  Optional subscription ID or name. If omitted, uses the current az context.

.PARAMETER DefaultPassword
  Optional. If omitted, the script prompts via Read-Host -AsSecureString.

.PARAMETER AppName
  Container app name. Must match the namePrefix in main.parameters.json (default: chorus).

.EXAMPLE
  .\deploy.ps1 -ResourceGroup rg-chorus-test-sea
#>
[CmdletBinding()]
param(
    [string]$ResourceGroup = 'rg-chorus-test-sea',
    [string]$Location      = 'southeastasia',
    [string]$Subscription,
    [SecureString]$DefaultPassword,
    [string]$AppName       = 'chorus'
)

$ErrorActionPreference = 'Stop'

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found on PATH: $Name"
    }
}

Require-Command az

Write-Host "==> Verifying Azure login" -ForegroundColor Cyan
$accountJson = az account show -o json 2>$null
if (-not $accountJson) {
    Write-Host "Not logged in. Running 'az login'..." -ForegroundColor Yellow
    az login | Out-Null
    $accountJson = az account show -o json
}
if ($Subscription) {
    az account set --subscription $Subscription | Out-Null
}
$account = $accountJson | ConvertFrom-Json
Write-Host ("    Subscription: {0} ({1})" -f $account.name, $account.id)

Write-Host "==> Registering required resource providers (idempotent)" -ForegroundColor Cyan
foreach ($ns in @('Microsoft.App','Microsoft.OperationalInsights','Microsoft.Storage')) {
    az provider register --namespace $ns --wait 2>&1 | Out-Null
}

Write-Host "==> Ensuring resource group $ResourceGroup in $Location" -ForegroundColor Cyan
az group create -n $ResourceGroup -l $Location -o none

# --- Pre-deployment: avoid PGlite revision overlap ---------------------------
$existing = az containerapp show -n $AppName -g $ResourceGroup --query name -o tsv 2>$null
if ($existing) {
    Write-Host "==> Existing container app detected. Scaling to 0 to avoid PGlite revision overlap..." -ForegroundColor Cyan
    az containerapp update -n $AppName -g $ResourceGroup --min-replicas 0 --max-replicas 0 -o none

    Write-Host "    Waiting for running replicas to drain (up to 3 minutes)..."
    $deadline = (Get-Date).AddMinutes(3)
    while ((Get-Date) -lt $deadline) {
        $runningCount = az containerapp replica list -n $AppName -g $ResourceGroup --query "length([?properties.runningState=='Running'])" -o tsv 2>$null
        if (-not $runningCount -or $runningCount -eq '0') {
            Write-Host "    All replicas drained." -ForegroundColor Green
            break
        }
        Write-Host "    Still $runningCount replica(s) running, retrying..."
        Start-Sleep -Seconds 5
    }
}

# --- Generate secrets --------------------------------------------------------
Write-Host "==> Generating NEXTAUTH_SECRET" -ForegroundColor Cyan
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$nextAuthSecret = [Convert]::ToBase64String($bytes)

if (-not $DefaultPassword) {
    Write-Host "==> Enter the bootstrap admin password (DEFAULT_PASSWORD)" -ForegroundColor Cyan
    $DefaultPassword = Read-Host -Prompt "Password" -AsSecureString
}
$bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($DefaultPassword)
try {
    $plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
} finally {
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}
if ([string]::IsNullOrWhiteSpace($plainPassword)) {
    throw "DEFAULT_PASSWORD must not be empty."
}

# --- Build a transient parameters file (avoid secrets on the az cmdline) -----
$bicepPath        = Join-Path $PSScriptRoot 'main.bicep'
$paramsPath       = Join-Path $PSScriptRoot 'main.parameters.json'
$secretsParamsFs  = New-TemporaryFile
$secretsParamsPath = "$($secretsParamsFs.FullName).json"
Move-Item -LiteralPath $secretsParamsFs.FullName -Destination $secretsParamsPath -Force

$secretsObj = @{
    '$schema'      = 'https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#'
    contentVersion = '1.0.0.0'
    parameters     = @{
        nextAuthSecret  = @{ value = $nextAuthSecret }
        defaultPassword = @{ value = $plainPassword }
    }
}
$secretsObj | ConvertTo-Json -Depth 5 | Set-Content -Path $secretsParamsPath -Encoding utf8

$deploymentName = "chorus-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

try {
    Write-Host "==> Submitting deployment $deploymentName" -ForegroundColor Cyan
    $deploymentJson = az deployment group create `
        -g $ResourceGroup `
        -n $deploymentName `
        -f $bicepPath `
        -p "@$paramsPath" `
        -p "@$secretsParamsPath" `
        -o json
    if ($LASTEXITCODE -ne 0 -or -not $deploymentJson) {
        throw "Deployment failed."
    }
    $deployment = $deploymentJson | ConvertFrom-Json
} finally {
    # Always purge the secrets parameters file.
    Remove-Item -LiteralPath $secretsParamsPath -Force -ErrorAction SilentlyContinue
    # Also overwrite the password copy in memory.
    $plainPassword = $null
}

$appUrl = $deployment.properties.outputs.appUrl.value
Write-Host ""
Write-Host "==> Deployment complete" -ForegroundColor Green
Write-Host "    App URL : $appUrl"
Write-Host "    Storage : $($deployment.properties.outputs.storageAccount.value)"
Write-Host "    Env     : $($deployment.properties.outputs.environment.value)"

Write-Host ""
Write-Host "==> Waiting for first response (Prisma migrate may take ~60s)..." -ForegroundColor Cyan
$deadline = (Get-Date).AddMinutes(5)
$ok = $false
while ((Get-Date) -lt $deadline) {
    try {
        $resp = Invoke-WebRequest -Uri $appUrl -Method Head -TimeoutSec 10 -SkipHttpErrorCheck
        if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
            Write-Host "    HTTP $($resp.StatusCode) — service is up." -ForegroundColor Green
            $ok = $true
            break
        }
        Write-Host "    HTTP $($resp.StatusCode), retrying..."
    } catch {
        Write-Host "    Not ready yet ($($_.Exception.Message)), retrying..."
    }
    Start-Sleep -Seconds 10
}

if (-not $ok) {
    Write-Warning "Service did not respond within 5 minutes. Check logs:"
    Write-Warning "  az containerapp logs show -n $AppName -g $ResourceGroup --follow"
    exit 1
}

Write-Host ""
Write-Host "Login at $appUrl" -ForegroundColor Green
Write-Host "  Username: (DEFAULT_USER from main.parameters.json — default admin@example.com)" -ForegroundColor Green
Write-Host "  Password: (the one you just entered)" -ForegroundColor Green
