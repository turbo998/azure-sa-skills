<#
.SYNOPSIS
  Tear down the Chorus test deployment by deleting the resource group.

.PARAMETER ResourceGroup
  Resource group to delete. Must contain only the Chorus deployment.

.PARAMETER Subscription
  Optional subscription ID or name.

.EXAMPLE
  .\destroy.ps1 -ResourceGroup rg-chorus-test-sea
#>
[CmdletBinding()]
param(
    [string]$ResourceGroup = 'rg-chorus-test-sea',
    [string]$Subscription
)

$ErrorActionPreference = 'Stop'

if ($Subscription) {
    az account set --subscription $Subscription | Out-Null
}

Write-Host "About to DELETE resource group '$ResourceGroup' and ALL resources inside it." -ForegroundColor Yellow
$confirm = Read-Host "Type the resource group name to confirm"
if ($confirm -ne $ResourceGroup) {
    Write-Host "Aborted." -ForegroundColor Red
    exit 1
}

Write-Host "==> Deleting resource group (running asynchronously)..." -ForegroundColor Cyan
az group delete -n $ResourceGroup --yes --no-wait
Write-Host "    Submitted. Track with: az group show -n $ResourceGroup"
