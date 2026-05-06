---
name: chorus-azure-deployment
description: "Deploy Chorus (Chorus-AIDLC/Chorus, Next.js 15 agent harness) to Azure Container Apps for testing at minimum cost. Covers Bicep IaC (Log Analytics + Storage + ACA env + Container App), embedded PGlite database, Azure Files SMB volume vs node-local emptyDir tradeoff, the MCAPS-style `StorageAccount_DisableLocalAuth_Modify` policy gotcha that blocks SMB account-key mounts, image tag `v` prefix convention, ACA single-replica + PGlite invariant, deploy/destroy PowerShell scripts, smoke tests. WHEN: \"deploy chorus\", \"deploy chorus to azure\", \"chorus on azure\", \"chorus container apps\", \"chorus aca\", \"chorus pglite azure\", \"chorus testing deployment\", \"chorus aidlc azure\", \"chorus bicep\", \"agent harness on azure\", \"chorus mount error 13\", \"allowSharedKeyAccess policy\", \"chorus image tag\", \"chorus emptydir\"."
license: MIT
metadata:
  version: "1.0.0"
---

# Deploy Chorus on Azure (Test/Min-Cost)

> **COMPLETE DEPLOYMENT GUIDE** — Stand up [Chorus-AIDLC/Chorus](https://github.com/Chorus-AIDLC/Chorus) on Azure Container Apps with embedded PGlite, single replica, and minimum monthly cost. Battle-tested on a subscription with the `StorageAccount_DisableLocalAuth_Modify` policy enforced (very common in enterprise / MCAPS / landing-zone subscriptions).

## Overview

This skill produces a working Chorus instance reachable over HTTPS in ~5 minutes:

- **Compute:** Azure Container Apps, Consumption profile, **min=max=1 replica** (PGlite is single-process; multiple replicas WILL corrupt the database).
- **Image:** `chorusaidlc/chorus-app:v0.7.1` (public Docker Hub, no ACR needed).
- **Database:** Embedded **PGlite** at `/app/data/pglite` (set automatically when `DATABASE_URL` is unset). No external Postgres.
- **Cache:** None. Chorus auto-falls back to in-memory EventBus when `REDIS_URL` is unset and replicaCount=1.
- **Storage:** Two volume modes — pick based on subscription policy:
  - `azureFile` — Azure Files SMB share. **Requires** storage account `allowSharedKeyAccess=true`. Survives revision rollover.
  - `emptyDir` — node-local ephemeral disk. Survives container restarts but **lost on every revision rebuild**. Use this when the subscription enforces the shared-key-disable policy.
- **Logs:** Log Analytics (PerGB2018, 30-day retention).
- **TLS / FQDN:** ACA-managed, no custom domain needed.

Estimated cost: **USD 22-35 / month** for 24/7 single-replica.

## When to Use This Skill

Invoke when a user wants to:
- "Deploy Chorus to Azure for testing / a demo"
- Stand up an agent-harness for evaluation without paying for managed Postgres
- Reproduce the deployment in a new region or subscription
- Diagnose `mount error(13): Permission denied` on ACA after deploy
- Understand why their Bicep `allowSharedKeyAccess: true` keeps reverting to `false`

Do NOT use this skill for production multi-tenant deployments. PGlite + emptyDir is acceptable only for single-user testing.

---

## Quick Reference

| Property | Value |
|---|---|
| Image | `chorusaidlc/chorus-app:v0.7.1` (tags use **`v` prefix** — `0.7.1` does NOT exist) |
| App listen port | `8637` |
| Default region (this skill) | `southeastasia` |
| Resource group convention | `rg-chorus-<env>-<region-short>` |
| Bicep target scope | `resourceGroup` |
| ACA api version | `2024-03-01` |
| ACA workload profile | `Consumption` (no dedicated nodes) |
| Volume mount | `/app/data` |
| Default admin env vars | `DEFAULT_USER`, `DEFAULT_PASSWORD` (created by entrypoint at first boot) |
| Auth secret env var | `NEXTAUTH_SECRET` (32-byte random base64) |
| Health endpoint | `GET /api/health` → `{"status":"ok","database":"connected"}` |

---

## Critical Gotchas (Read First)

### 1. Image tag prefix

```bash
# ❌ WRONG (image not found)
chorusaidlc/chorus-app:0.7.1
# ✅ RIGHT
chorusaidlc/chorus-app:v0.7.1
```

Verify tags via:
```bash
curl -s https://hub.docker.com/v2/repositories/chorusaidlc/chorus-app/tags | jq -r ".results[].name"
```

### 2. The `StorageAccount_DisableLocalAuth_Modify` policy

Many enterprise subscriptions (MCAPS, ALZ, CAF baselines) enforce a **`Modify`** Azure Policy that automatically resets `allowSharedKeyAccess` to `false` immediately after any storage account is created. Symptoms:

- Bicep deploy succeeds; `allowSharedKeyAccess: true` in template.
- After deploy, `az storage account show ... --query allowSharedKeyAccess` returns `false`.
- Manual `az storage account update --allow-shared-key-access true` "succeeds" but the value silently stays `false` (Azure Policy modifies it back).
- ACA `azureFile` volume binding fails with: `mount error(13): Permission denied` — visible in `ContainerAppSystemLogs_CL`, NOT in `ContainerAppConsoleLogs_CL` (container never produces stdout when mount fails).
- Container goes into `CrashLoopBackOff` with `runningState: Failed`.

**Detect** with:
```bash
az policy state list --resource <storage-account-resource-id> \
  --query "[?contains(policyDefinitionName,'DisableLocalAuth')]"
```
If the policy shows up with `state: Compliant` and `action: modify`, you cannot use `azureFile` mounts without an exemption.

**Workarounds, ranked by simplicity:**
1. **Switch to `volumeMode=emptyDir`** (this skill's recommended path for a test deployment). Trade-off: PGlite data is lost when the revision is rebuilt (every Bicep deploy with template changes). Container restarts within the same revision retain data.
2. **Request a policy exemption** at the RG scope. Slow (admin approval) but preserves data.
3. **Pivot to Azure Database for PostgreSQL Flexible Server.** Add ~USD 15/mo, drop the volume entirely, set `DATABASE_URL` env var.
4. **Switch to NFS Premium FileStorage + VNet + private endpoint.** Highest complexity and ~USD 15/mo extra. Only if the original SMB persistence model is required.

### 3. Bicep secure-output limitation (BCP426)

You cannot dereference a `@secure()` module output through a ternary expression:

```bicep
// ❌ Compile error BCP426
storageAccountKey: volumeMode == 'azureFile' ? storage.outputs.accountKey : ''

// ✅ Always pass the secret; let downstream module conditionally use it
storageAccountKey: storage.outputs.accountKey
```

Therefore the storage module is **always created**, even in `emptyDir` mode. The empty file share costs effectively zero (no transactions, no data, no provisioning fee on Standard_LRS).

### 4. ACA single-replica invariant for PGlite

PGlite is an embedded single-process Postgres. Two concurrent replicas writing to the same volume → **immediate data corruption**. ACA's default rolling deployment briefly runs `old + new` revision concurrently against the same Azure Files mount even with `activeRevisionsMode: 'Single'`. Mitigations baked into this skill:

- `replicaCount` is `@allowed([1])` — Bicep refuses any other value.
- `deploy.ps1` scales the existing app to `min=max=0` and waits before redeploying.
- Use `volumeMode=emptyDir` to make per-revision volumes fully isolated (each new revision gets a fresh empty disk).

### 5. ACA log type filter

`az containerapp logs show --type system` does **NOT** accept `--revision`, `--replica`, `--container`. Those flags are `--type console` only. To find mount errors, query `ContainerAppSystemLogs_CL` directly via Log Analytics:

```kusto
ContainerAppSystemLogs_CL
| where ContainerAppName_s == "chorus"
| where TimeGenerated > ago(15m)
| project TimeGenerated, Reason_s, Log_s
| order by TimeGenerated desc
```

---

## Architecture

```
Internet ──HTTPS──▶ Azure Container Apps Env (Consumption)
                    └─▶ Container App "chorus"  (1 replica, 1 vCPU / 2 GiB)
                          ├── chorusaidlc/chorus-app:v0.7.1 (port 8637)
                          ├── PGlite at /app/data/pglite
                          └── Volume /app/data ──┬─ AzureFile (SMB share)   [if shared-key allowed]
                                                 └─ EmptyDir (node local)   [if policy-blocked]
                          stdout/stderr ─▶ Log Analytics workspace
```

Resources created:

| Resource | Name pattern | Notes |
|---|---|---|
| Resource Group | `rg-chorus-test-<region>` | Cleanup boundary |
| Log Analytics | `chorus-logs` | PerGB2018, 30-day retention |
| Storage Account | `chorus<14-char-uniqueString>` | StorageV2, Standard_LRS — created even in emptyDir mode (BCP426) |
| File Share | `chorus-data` | SMB, TransactionOptimized, 100 GiB quota; unmounted in emptyDir mode |
| ACA Managed Env | `chorus-env` | Consumption profile only |
| Env Storage Binding | `chorusdata` | `azureFile{accountName, accountKey, shareName, ReadWrite}` — only created when `bindAzureFileStorage=true` |
| Container App | `chorus` | External HTTPS ingress on 8637 |

---

## Step-by-Step Deployment

### Prerequisites

- Azure CLI ≥ 2.60 (`az --version`)
- Bicep CLI (`az bicep version`; auto-installed on first use)
- PowerShell 7+
- Subscription with `Contributor` on the target RG
- Auto-registered providers (CLI handles): `Microsoft.App`, `Microsoft.OperationalInsights`, `Microsoft.Storage`

### 1. Login and select subscription

```powershell
az login
az account set --subscription "<subscription-name-or-id>"
az account show --query "{id:id, name:name, tenantId:tenantId}" -o table
```

### 2. Create resource group

```powershell
$RG = "rg-chorus-test-sea"
$LOC = "southeastasia"
az group create -n $RG -l $LOC
```

### 3. Decide on volume mode

Run the policy probe FIRST so you don't deploy with the wrong setting:

```powershell
# Quick, indirect probe: try to set a known-good value on a throwaway storage account
# OR skip the probe and just default to emptyDir for safety on enterprise subscriptions.
```

**Default recommendation for unknown enterprise subscriptions:** `emptyDir`. You can always redeploy with `azureFile` later if persistence becomes a priority and the policy permits.

### 4. Drop in the IaC

Copy the contents of this skill's `iac/` folder to a working dir, e.g. `C:\Users\<you>\azure-deploy\`. The skill ships:

- `iac/main.bicep` — RG-scope orchestrator
- `iac/modules/logs.bicep`
- `iac/modules/storage.bicep`
- `iac/modules/aca-env.bicep`
- `iac/modules/aca-app.bicep`
- `iac/main.parameters.json`
- `scripts/deploy.ps1`, `scripts/destroy.ps1`

Edit `main.parameters.json`:
```json
{
  "volumeMode":      { "value": "emptyDir" },
  "imageTag":        { "value": "v0.7.1" },
  "defaultUser":     { "value": "admin@example.com" },
  "allowedSourceIps":{ "value": [] },
  "tags":            { "value": { "app": "chorus", "env": "test", "managedBy": "bicep" } }
}
```

`allowedSourceIps` accepts an array of CIDRs (e.g. `["1.2.3.4/32"]`) for ingress IP allowlisting. Empty = open to internet.

### 5. Deploy

`scripts/deploy.ps1` does the safe thing: scales any existing app to 0, prompts for a SecureString password, generates a 32-byte `NEXTAUTH_SECRET`, writes a temp parameters file (deleted in `finally`), runs the deployment, and polls the FQDN until it answers HTTP.

```powershell
cd <working-dir>
.\scripts\deploy.ps1 -ResourceGroup rg-chorus-test-sea -Location southeastasia
```

**Save the printed `DEFAULT_PASSWORD` and `NEXTAUTH_SECRET`** to a local file you DO NOT check into git, e.g. `C:\Users\<you>\chorus-azure-credentials.txt`. Reuse them on every redeploy to keep the same admin account.

The deploy emits the public URL: `https://chorus.<random>.<region>.azurecontainerapps.io`.

### 6. Smoke-test

```powershell
$URL = "https://chorus.<random>.southeastasia.azurecontainerapps.io"
Invoke-WebRequest "$URL/api/health" | Select -Expand Content
# expect: {"status":"ok","timestamp":"...","database":"connected"}

az containerapp revision list -n chorus -g rg-chorus-test-sea `
  --query "[].{n:name, h:properties.healthState, r:properties.runningState}" -o table
# expect: HealthState=Healthy, RunningState=RunningAtMaxScale
```

If `database:connected` returns ok, login at the root URL with the saved `DEFAULT_USER` / `DEFAULT_PASSWORD`.

### 7. (Optional) Tighten ingress

```powershell
# Get your egress IP
$myIp = (Invoke-RestMethod -Uri "https://api.ipify.org?format=json").ip

# Patch the IaC parameter and redeploy
# main.parameters.json: "allowedSourceIps": { "value": ["$myIp/32"] }
.\scripts\deploy.ps1 ...
```

---

## Operations

### View logs

```powershell
# Live tail (console = stdout/stderr)
az containerapp logs show -n chorus -g rg-chorus-test-sea --type console --follow

# System events (mount errors, scale events)
az containerapp logs show -n chorus -g rg-chorus-test-sea --type system

# KQL on Log Analytics (when policy lag means container never wrote stdout):
# table: ContainerAppSystemLogs_CL
```

### Pause to save money (cold-start ~30s)

```powershell
az containerapp update -n chorus -g rg-chorus-test-sea --min-replicas 0 --max-replicas 1
```

### Resume

```powershell
az containerapp update -n chorus -g rg-chorus-test-sea --min-replicas 1 --max-replicas 1
```

### Upgrade image

1. Edit `main.parameters.json` → bump `imageTag` (remember the `v` prefix).
2. `.\scripts\deploy.ps1 ...`

### Backup PGlite data (azureFile mode only)

PGlite stores SQLite-style files at `/app/data/pglite`. Snapshot via Azure Files snapshots:

```powershell
$STG = "<storage-account-name>"
az storage share snapshot --account-name $STG --name chorus-data --auth-mode login
# OR on Standard share if shared-key allowed:
az storage share snapshot --account-name $STG --name chorus-data --account-key "<key>"
```

For `emptyDir` mode there is no backup — re-create test data after revision rebuilds.

### Cleanup

```powershell
.\scripts\destroy.ps1 -ResourceGroup rg-chorus-test-sea
# OR
az group delete -n rg-chorus-test-sea --yes --no-wait
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Image not found: chorusaidlc/chorus-app:0.7.1` | Missing `v` prefix | Use `v0.7.1` |
| Container `CrashLoopBackOff`, no console logs | Volume mount failed before stdout | Check `ContainerAppSystemLogs_CL` for `mount error(13)` |
| `mount error(13): Permission denied` | Subscription policy disabled shared-key | Switch `volumeMode` to `emptyDir` |
| `KeyBasedAuthenticationNotPermitted` from `az storage` | Same policy | Use AAD: `--auth-mode login` (limited operations) |
| Bicep error `BCP426 Secure outputs may only be accessed via a direct module reference` | Ternary on `@secure()` output | Pass the secret unconditionally; gate consumer with a separate boolean |
| App URL returns 502/503 for >5 min | Probe failure or DB migration loop | `prisma migrate deploy` retries for 5 min; check console logs after that |
| HTTP 200 but page is "Welcome to ACA" not Chorus | Default ingress hit, app didn't start | Container is failing — check revision health |
| `--revision` rejected on `logs show --type system` | API limitation | System logs are env-wide; use Log Analytics KQL |
| ACA rolling deploy corrupts PGlite | Two revisions ran concurrently against same volume | Always use `deploy.ps1` (scales to 0 first) |

---

## Cost Notes

Approx monthly steady-state for 1 vCPU / 2 GiB / 24-7:

| Item | USD/mo (rough) |
|---|---|
| ACA Consumption (1 vCPU, 2 GiB always-on) | 18 - 28 |
| Log Analytics ingestion (light) | 1 - 3 |
| Storage Account (Standard_LRS, ~empty) | 0 - 1 |
| Azure Files SMB (100 GiB quota, ~0 GiB used) | 0 (only used capacity bills) |
| **Total** | **~22 - 35** |

Reduce further by setting `min-replicas 0` when not testing → drops to ~Log Analytics + storage minimums (~USD 1-3/mo).

---

## Files Shipped With This Skill

```
chorus-azure-deployment/
├── SKILL.md                            (this file)
├── iac/
│   ├── main.bicep
│   ├── main.parameters.json
│   └── modules/
│       ├── logs.bicep
│       ├── storage.bicep
│       ├── aca-env.bicep
│       └── aca-app.bicep
└── scripts/
    ├── deploy.ps1
    └── destroy.ps1
```

The Bicep templates are linter-clean against `az bicep build` v0.42.1 and tagged for cost attribution. The `volumeMode` parameter switches between `azureFile` and `emptyDir` without code changes.

---

## Reference

- Chorus repo: https://github.com/Chorus-AIDLC/Chorus
- Chorus Docker docs: https://github.com/Chorus-AIDLC/Chorus/blob/main/docs/DOCKER.md
- ACA storage types: https://learn.microsoft.com/azure/container-apps/storage-mounts
- Azure Policy `Modify` effect (root cause of the SMB blocker): https://learn.microsoft.com/azure/governance/policy/concepts/effect-modify
- Bicep BCP426 secure-output rule: https://aka.ms/bicep/core-diagnostics#BCP426

---

**Last verified:** 2026-05-06, deployed successfully to `MCAPS-Hybrid-REQ-136326-2025-qichen2` / `southeastasia` with `volumeMode=emptyDir` after hitting the shared-key policy blocker. Health endpoint confirmed `database:connected`.
