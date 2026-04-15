---
name: azure-hermes-ghcp-wechat
description: "Deploy Hermes Agent on an Azure VM, configure GitHub Copilot as the model provider, and connect Weixin/WeChat. Covers Azure VM sizing, SSH access, Hermes install, Copilot OAuth/device-code login, model switch to copilot/gpt-5.4, Weixin QR login, gateway startup, and validation. WHEN: \"deploy hermes on azure\", \"install hermes agent\", \"hermes ghcp\", \"hermes github copilot\", \"hermes wechat\", \"hermes weixin\", \"azure vm hermes wechat\"."
license: MIT
metadata:
  version: "1.0.0"
---

# Hermes Agent on Azure VM + GitHub Copilot + Weixin/WeChat

> **KNOWN-GOOD EXECUTION PLAYBOOK** — Use this skill to deploy `NousResearch/hermes-agent` on an Azure Linux VM, configure GitHub Copilot as the inference provider, and connect Hermes to personal Weixin/WeChat.

## Overview

This skill covers a practical end-to-end path that has already been exercised on Azure:

- **Compute:** single Ubuntu VM in Azure
- **Agent:** `NousResearch/hermes-agent`
- **Model provider:** GitHub Copilot (`provider: copilot`)
- **Default model:** `gpt-5.4`
- **Messaging:** Weixin / WeChat via Hermes gateway
- **Recommended region:** `southeastasia`

This is the right skill when the goal is:

1. Create or reuse an Azure VM
2. Install Hermes Agent
3. Bind Hermes to GitHub Copilot credentials
4. Log Hermes into Weixin by QR code
5. Run the gateway as a long-lived background process

## Validated Defaults

| Item | Recommended value |
|---|---|
| Region | `southeastasia` |
| OS | Ubuntu Server 22.04 LTS Gen2 |
| VM SKU | `Standard_D2ds_v5` |
| Access | SSH key only |
| Hermes install path | `~/.hermes/hermes-agent` |
| Hermes binary | `~/.local/bin/hermes` |
| Config file | `~/.hermes/config.yaml` |
| Secrets file | `~/.hermes/.env` |
| Model provider | `copilot` |
| Default model | `gpt-5.4` |

## Important Constraints

### 1. GitHub Copilot token types

Hermes supports GitHub Copilot, but **classic PATs (`ghp_*`) are not valid** for the Copilot API.

Supported token types:

- `gho_*` — OAuth token
- `github_pat_*` — fine-grained PAT with **Copilot Requests** permission
- `ghu_*` — GitHub App token

Preferred path:

- use **Hermes/Copilot device login**
- or provide `COPILOT_GITHUB_TOKEN`

### 2. Weixin mode does not require public webhook ingress

Personal Weixin/WeChat login in Hermes uses QR/device binding and long-polling behavior, not an inbound public callback.

That means:

- you can keep the VM mostly closed
- only SSH is required for the base setup
- public reverse proxy / AFD is optional unless you also need other public services

### 3. Hermes uses Linux-first assumptions

Do not target native Windows for Hermes runtime. Use:

- Azure Linux VM
- WSL2
- or another Linux host

## Quick Path

Use this when you want the fastest reproducible deployment.

1. **Create VM**
   - Ubuntu 22.04
   - `Standard_D2ds_v5`
   - SSH public key auth

2. **Install Hermes**
   - `curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash`
   - confirm `~/.local/bin/hermes --version`

3. **Configure Copilot**
   - complete GitHub device-code login
   - set `~/.hermes/config.yaml` to:
     ```yaml
     model:
       default: gpt-5.4
       provider: copilot
     ```
   - store the token in `~/.hermes/.env` as `COPILOT_GITHUB_TOKEN=...`

4. **Configure Weixin**
   - run `hermes gateway setup`
   - choose **Weixin / WeChat**
   - scan QR code immediately
   - ensure `WEIXIN_ACCOUNT_ID` and `WEIXIN_TOKEN` appear in `~/.hermes/.env`

5. **Open DM policy**
   - set:
     ```env
     WEIXIN_DM_POLICY=open
     WEIXIN_GROUP_POLICY=disabled
     GATEWAY_ALLOW_ALL_USERS=true
     ```

6. **Start gateway**
   - `nohup hermes gateway run > ~/.hermes/weixin-gateway.out 2>&1 &`

## Phase 1: Provision Azure VM

Example Azure CLI flow:

```bash
az group create -n rg-hermes-agent-sg -l southeastasia

az vm create \
  --resource-group rg-hermes-agent-sg \
  --name vm-hermes-agent-sg \
  --location southeastasia \
  --image Canonical:ubuntu-22_04-lts:server:latest \
  --size Standard_D2ds_v5 \
  --admin-username azureuser \
  --generate-ssh-keys \
  --public-ip-sku Standard
```

Minimum networking baseline:

- allow `22/tcp`
- preferably restrict source IP for SSH

## Phase 2: Install Hermes Agent

SSH to the VM and install Hermes:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc
hermes --version
```

Useful validation:

```bash
hermes doctor
hermes config
```

Expected file layout:

```text
~/.local/bin/hermes
~/.hermes/config.yaml
~/.hermes/.env
~/.hermes/hermes-agent/
```

## Phase 3: Configure GitHub Copilot as Model Provider

### Option A — recommended: interactive/device login

If running interactively:

```bash
hermes model
```

Choose:

- **GitHub Copilot**
- complete the GitHub device authorization in browser

### Option B — manual token injection

If you already have a valid supported token:

```bash
printf '\nCOPILOT_GITHUB_TOKEN=%s\n' "$TOKEN" >> ~/.hermes/.env
```

Then set model config:

```yaml
model:
  default: gpt-5.4
  provider: copilot
```

Or:

```bash
hermes config set model.provider copilot
hermes config set model.default gpt-5.4
```

### Verification

Run a direct inference test:

```bash
hermes chat --provider copilot --model gpt-5.4 -q "Reply with OK only." -Q
```

Expected result:

- response returns `OK`

If you see `Authorization header is badly formatted`, check whether the token is an unsupported `ghp_*` token.

## Phase 4: Configure Weixin / WeChat

Run:

```bash
hermes gateway setup
```

In the setup flow:

1. choose **Weixin / WeChat**
2. scan the QR code immediately
3. complete the login confirmation in mobile WeChat

After successful login, Hermes should write:

```env
WEIXIN_ACCOUNT_ID=...
WEIXIN_TOKEN=...
```

Recommended policy settings:

```env
WEIXIN_DM_POLICY=open
WEIXIN_GROUP_POLICY=disabled
GATEWAY_ALLOW_ALL_USERS=true
```

Explanation:

- `WEIXIN_DM_POLICY=open` avoids DM authorization friction
- `WEIXIN_GROUP_POLICY=disabled` keeps the first rollout simple
- `GATEWAY_ALLOW_ALL_USERS=true` avoids the common “connected but unauthorized sender” issue during initial testing

## Phase 5: Start Hermes Weixin Gateway

Start the gateway:

```bash
nohup hermes gateway run > ~/.hermes/weixin-gateway.out 2>&1 &
echo $! > ~/.hermes/weixin-gateway.pid
```

Check that it is alive:

```bash
ps -p "$(cat ~/.hermes/weixin-gateway.pid)" -o pid=,args=
tail -n 50 ~/.hermes/weixin-gateway.out
```

If you change the provider or model later, restart the gateway:

```bash
kill "$(cat ~/.hermes/weixin-gateway.pid)"
nohup hermes gateway run > ~/.hermes/weixin-gateway.out 2>&1 &
echo $! > ~/.hermes/weixin-gateway.pid
```

## Validation Checklist

### Azure

- VM is running
- SSH succeeds
- NSG rules are intentional and minimal

### Hermes

- `hermes --version` works
- `hermes config` shows `provider: copilot`
- direct prompt test returns a valid response

### Weixin

- `WEIXIN_ACCOUNT_ID` exists in `~/.hermes/.env`
- `WEIXIN_TOKEN` exists in `~/.hermes/.env`
- gateway process is running
- sending a direct WeChat message to Hermes gets a reply

## Common Failure Modes

### 1. QR code expires too fast

Symptoms:

- QR code is already invalid by the time you scan it

Actions:

- rerun the login flow
- keep the terminal active
- scan immediately after the QR is generated

### 2. Weixin shows connected but messages get no reply

Symptoms:

- account login succeeded
- no response after sending a DM

Usually caused by authorization policy, not transport.

Fix:

```env
WEIXIN_DM_POLICY=open
GATEWAY_ALLOW_ALL_USERS=true
```

Then restart the gateway.

### 3. Copilot provider returns 400

Symptoms:

- `Authorization header is badly formatted`

Likely causes:

- invalid token type
- classic PAT `ghp_*`
- malformed env value

Fix:

- use device-code OAuth again
- replace with `gho_*` or fine-grained `github_pat_*`

### 4. Hermes command not found

Fix:

```bash
export PATH="$HOME/.local/bin:$PATH"
source ~/.bashrc
```

## Security Notes

- keep `~/.hermes/.env` permission-tight:
  ```bash
  chmod 600 ~/.hermes/.env
  ```
- delete temporary device-login token files after setup
- prefer SSH key auth over password auth
- only expose public ports you actually need

## Optional Enhancements

You can layer these on after the base deployment works:

- Azure Key Vault for secret retrieval
- systemd user service for `hermes gateway run`
- Azure Monitor alerts
- Application Gateway WAF or Front Door in front of any public-facing callback service

## Recommended Output Shape When Using This Skill

When executing this skill for a user, aim to leave behind:

1. a running Azure VM
2. Hermes installed and callable as `hermes`
3. Copilot provider working with `gpt-5.4`
4. Weixin account bound
5. gateway process running
6. one successful WeChat reply as end-to-end proof
