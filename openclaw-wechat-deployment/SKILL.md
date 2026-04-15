---
name: openclaw-wechat-deployment
description: "Deploy OpenClaw with GitHub Copilot LLM and WeChat integration on Azure VM. Covers VM creation, SKU selection, SSH hardening, Azure CLI setup, OpenClaw install/config, HTTPS via Caddy or Azure Front Door (AFD), WAF, WeChat ClawBot plugin, device approval, assistant personality, post-reboot resilience, and anti-auto-shutdown. WHEN: \"deploy openclaw\", \"install openclaw\", \"openclaw wechat\", \"openclaw azure vm\", \"openclaw copilot setup\", \"wechat bot\", \"openclaw https\", \"caddy reverse proxy openclaw\", \"openclaw AFD\", \"openclaw front door\", \"openclaw security\"."
license: MIT
metadata:
  version: "1.3.0"
---

# OpenClaw + WeChat Deployment on Azure VM with GitHub Copilot

> **COMPLETE DEPLOYMENT GUIDE** — Follow these steps to deploy OpenClaw with GitHub Copilot LLM, HTTPS access, WeChat integration, device approval, and assistant personalization on an Azure VM.

## Overview

This skill covers end-to-end deployment of OpenClaw on an Azure VM (Ubuntu 24.04) with:
- **LLM Provider:** GitHub Copilot (supports gpt-4o, gpt-5.4, etc.)
- **Messaging Channel:** WeChat via `@tencent-weixin/openclaw-weixin` plugin
- **HTTPS:** Caddy reverse proxy with self-signed certificate **OR** Azure Front Door (AFD) Standard (recommended)
- **WAF:** Azure Front Door WAF with rate limiting (when using AFD path)
- **Security:** SSH port hardening, NSG rules, device approval, token auth, AFD origin isolation
- **Optional GitHub Ops:** Bundled `github` / `gh-issues` skills become ready after installing `gh` CLI

## When to Use This Skill

Invoke this skill when:
- **Deploying OpenClaw** on a new Azure VM
- **Configuring WeChat** integration with OpenClaw
- **Setting up HTTPS** for OpenClaw Control UI
- **Hardening SSH** on Ubuntu 24.04 (socket activation)
- **Troubleshooting** OpenClaw post-reboot issues

## Quick Reference

| **Property** | **Details** |
|---|---|
| **OS** | Ubuntu 24.04 LTS (Azure VM) |
| **OpenClaw Version** | v2026.3.24+ |
| **LLM Provider** | GitHub Copilot (enterprise) |
| **WeChat Plugin** | `@tencent-weixin/openclaw-weixin` v2.0.1+ |
| **HTTPS Proxy** | Caddy v2 with self-signed TLS cert |
| **Config File** | `~/.openclaw/openclaw.json` |
| **Gateway Port** | 18789 (default) |
| **Daemon Service** | `~/.config/systemd/user/openclaw-gateway.service` (user-level systemd) |

---

## Teammate Copy/Paste Quick Path

Use this when you want a colleague to reproduce a known-good deployment with the fewest choices:

1. **Azure VM**
   - Region: `southeastasia`
   - OS: Ubuntu 24.04 LTS
   - Size: `Standard_B4ms` first, fallback to `Standard_B4s_v2`
   - Public IP + Standard SKU

2. **Network**
   - Open `3232` for SSH
   - Open `443` for HTTPS
   - Check **both** NIC NSG and subnet NSG

3. **OpenClaw**
   - Install with `curl -fsSL https://openclaw.ai/install.sh | bash`
   - Set `gateway.mode=local`
   - Authenticate GitHub Copilot with `openclaw models auth login-github-copilot`
   - Set model to `github-copilot/gpt-5.4`
   - Install/start daemon

4. **Portal**
   - Install Caddy
   - Reverse proxy `443 -> localhost:18789`
   - Set `gateway.bind=lan`
   - Add `https://<VM_IP>` to `allowedOrigins`
   - Run `openclaw dashboard --no-open`

5. **WeChat**
   - Install `@tencent-weixin/openclaw-weixin`
   - Enable plugin
   - Run `openclaw channels login --channel openclaw-weixin`
   - Scan QR immediately

6. **Reliability**
   - `sudo loginctl enable-linger <username>`
   - If Portal says `pairing required`, run `openclaw devices list` then `openclaw devices approve <request-id>`
   - If everything is dead, first check whether the VM was **deallocated**

---

## Phase 0: Azure VM Creation

### VM SKU Selection (4C8G Recommended)

⚠️ **SKU availability varies by region and subscription.** Always check first:

```bash
az vm list-skus --location <REGION> --size Standard_B4 --output table
```

**Recommended SKUs (in priority order):**

| SKU | Spec | Notes |
|-----|------|-------|
| `Standard_B4ms` | 4C/8G x86 | Cheapest burstable, best first choice |
| `Standard_B4s_v2` | 4C/8G x86 | Good fallback, check zone availability |
| `Standard_B4pls_v2` | 4C/8G ARM | Cheapest overall, but see ARM caveats below |
| `Standard_D4s_v5` | 4C/16G x86 | Stable performance, higher cost |

### ⚠️ ARM SKU Caveats

ARM-based SKUs (names containing `p`, e.g., `B4pls_v2`, `B4ps_v2`):
- **Require `arm64` OS image**: Use `Canonical:ubuntu-24_04-lts:server-arm64:latest`
- **May NOT support TrustedLaunch**: Some subscriptions require the feature `Microsoft.Compute/UseStandardSecurityType` to be registered before using `--security-type Standard`. If the feature is not registered, ARM SKUs that don't support TrustedLaunch will fail to deploy.
- **Node.js / OpenClaw work fine on ARM64** — no compatibility issues

### Create VM

```bash
# x86 VM (recommended)
az vm create \
  --resource-group <RG> \
  --name <VM_NAME> \
  --location <REGION> \
  --image Canonical:ubuntu-24_04-lts:server:latest \
  --size Standard_B4s_v2 \
  --admin-username <USERNAME> \
  --generate-ssh-keys \
  --nsg <NSG_NAME> \
  --public-ip-address <PIP_NAME> \
  --public-ip-sku Standard \
  --os-disk-size-gb 64 \
  --zone 1 \
  --output json

# ARM VM (if x86 unavailable — check TrustedLaunch support first)
az vm create \
  --resource-group <RG> \
  --name <VM_NAME> \
  --location <REGION> \
  --image Canonical:ubuntu-24_04-lts:server-arm64:latest \
  --size Standard_B4pls_v2 \
  --admin-username <USERNAME> \
  --generate-ssh-keys \
  --nsg <NSG_NAME> \
  --public-ip-address <PIP_NAME> \
  --public-ip-sku Standard \
  --os-disk-size-gb 64 \
  --zone 1 \
  --security-type Standard \
  --output json
```

### Initial NSG Rules

```bash
# Add SSH 3232 + HTTPS 443 rules
az network nsg rule create -g <RG> --nsg-name <NSG> -n SSH-3232 \
  --priority 310 --direction Inbound --access Allow --protocol Tcp \
  --destination-port-ranges 3232

az network nsg rule create -g <RG> --nsg-name <NSG> -n HTTPS \
  --priority 320 --direction Inbound --access Allow --protocol Tcp \
  --destination-port-ranges 443
```

### ⚠️ Azure Subnet NSG Gotcha

Azure can create **both**:
- a NIC-level NSG
- a subnet-level NSG

If you only add rules to the NIC NSG, public access can still fail because the subnet NSG may still have `DenyAllInBound`.

Check both:

```bash
# NIC -> which NSG?
az network nic show -g <RG> -n <NIC_NAME> \
  --query "{nsg:networkSecurityGroup.id, subnet:ipConfigurations[0].subnet.id}" -o json

# Subnet -> is there a subnet NSG?
az network vnet subnet show -g <RG> --vnet-name <VNET_NAME> -n <SUBNET_NAME> \
  --query "networkSecurityGroup.id" -o tsv
```

If a subnet NSG exists, mirror the same `3232` and `443` inbound rules there too:

```bash
az network nsg rule create -g <RG> --nsg-name <SUBNET_NSG> -n Allow-SSH-3232 \
  --priority 310 --direction Inbound --access Allow --protocol Tcp \
  --source-address-prefixes "*" --destination-port-ranges 3232

az network nsg rule create -g <RG> --nsg-name <SUBNET_NSG> -n Allow-HTTPS-443 \
  --priority 320 --direction Inbound --access Allow --protocol Tcp \
  --source-address-prefixes "*" --destination-port-ranges 443
```

### Verify SSH

```bash
ssh <USERNAME>@<VM_IP> "uname -a && lsb_release -d"
```

---

## Phase 1: SSH Hardening (Port Change)

### ⚠️ CRITICAL: Ubuntu 24.04 SSH Socket Activation

Ubuntu 24.04 uses **systemd socket activation** for SSH. Changing the port in `/etc/ssh/sshd_config` alone is **NOT ENOUGH**. You must also override `ssh.socket`.

> **Service name is `ssh`, NOT `sshd`** on Ubuntu 24.04.

### Steps

```bash
# 1. Edit sshd_config
sudo sed -i 's/^#Port 22$/Port 3232/' /etc/ssh/sshd_config

# 2. Create systemd socket override (THIS IS THE KEY STEP)
sudo mkdir -p /etc/systemd/system/ssh.socket.d/
sudo tee /etc/systemd/system/ssh.socket.d/override.conf << 'EOF'
[Socket]
ListenStream=
ListenStream=0.0.0.0:3232
EOF

# 3. Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart ssh.socket

# 4. Verify
ss -tlnp | grep 3232
```

**Explanation:**
- `ListenStream=` (empty) clears the default port 22
- `ListenStream=0.0.0.0:3232` sets the new port (IPv4 only)
- Without the empty line, port 22 remains active alongside 3232

### NSG Rules (Azure)

```bash
# Add new port rule BEFORE changing SSH port (if not done in Phase 0)
az network nsg rule create -g <RG> --nsg-name <NSG> -n SSH-3232 \
  --priority 310 --direction Inbound --access Allow --protocol Tcp \
  --destination-port-ranges 3232

# After verifying new port works, delete old rule
# Note: az vm create generates the default rule named "default-allow-ssh"
az network nsg rule delete -g <RG> --nsg-name <NSG> -n default-allow-ssh
```

> ⚠️ **Always verify SSH on the new port BEFORE deleting the old rule** — otherwise you may lock yourself out.

---

## Phase 2: Azure CLI Installation

```bash
# Install Azure CLI (Ubuntu/Debian)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login via device code (for SSH sessions without browser)
az login --use-device-code

# Verify
az account show --output table
```

---

## Phase 3: OpenClaw Installation

### Install

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

This installs Node.js, npm, and OpenClaw globally.

### PATH Configuration

**IMPORTANT:** Each new SSH session needs:
```bash
export PATH="/home/<user>/.npm-global/bin:$PATH"
```

Add to `~/.bashrc` for persistence:
```bash
echo 'export PATH="/home/<user>/.npm-global/bin:$PATH"' >> ~/.bashrc
```

### Setup (Two Paths)

#### Path A: Interactive Setup (if you have a TTY terminal)

```bash
openclaw
```

Select during onboarding wizard:
1. Security warning → **Yes**
2. Setup mode → **Manual**
3. Gateway → **Local gateway (this machine)**
4. Workspace → default (`~/.openclaw/workspace`)
5. Model/auth → **Copilot** → **GitHub Copilot**
6. Complete device login at https://github.com/login/device

#### Path B: Non-Interactive Setup (for remote/automated deployment)

When deploying via remote SSH commands without TTY (e.g., from Copilot CLI), the onboarding wizard will fail with `/dev/tty: No such device or address`. Use CLI config commands instead:

```bash
# Set gateway mode
openclaw config set gateway.mode local

# Set default model
openclaw config set agents.defaults.model.primary "github-copilot/gpt-5.4"

# Set timezone
openclaw config set agents.defaults.userTimezone "Asia/Shanghai"

# Install and start daemon (auto-generates gateway token)
openclaw daemon install
openclaw daemon start

# Authenticate GitHub Copilot (REQUIRES interactive TTY — use ssh -t)
ssh -t <user>@<VM_IP> -p <SSH_PORT> 'export PATH="/home/<user>/.npm-global/bin:$PATH" && openclaw models auth login-github-copilot'
```

> ⚠️ The `models auth login-github-copilot` command triggers a GitHub device code flow. It **must** run in an interactive terminal (`ssh -t`). You will be given a code to enter at https://github.com/login/device.

### Set Default Model

```bash
# Set and verify model
openclaw models set github-copilot/gpt-5.4
openclaw models list
```

### Install & Start Daemon

```bash
openclaw daemon install
openclaw daemon start

# Check status
openclaw daemon status
```

### Optional: Install `gh` CLI to Enable Bundled GitHub Skills

OpenClaw already ships bundled `github` and `gh-issues` skills. They become `ready` after `gh` CLI is installed.

```bash
(type -p wget >/dev/null || (sudo apt update && sudo apt install wget -y)) && \
sudo mkdir -p -m 755 /etc/apt/keyrings && \
out=$(mktemp) && \
wget -nv -O"$out" https://cli.github.com/packages/githubcli-archive-keyring.gpg && \
cat "$out" | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null && \
sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg && \
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | \
sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
sudo apt update && sudo apt install gh -y

gh --version
openclaw skills list
```

You should then see bundled skills like:
- `github`
- `gh-issues`

---

## Phase 4: HTTPS Access (Choose One Path)

> **Path A: Azure Front Door (Recommended)** — Best security, WAF + DDoS protection, no self-signed cert issues.
> **Path B: Caddy (Simple/Free)** — Good for dev/test, but VM is directly exposed on port 443.

---

## Phase 4A: HTTPS via Azure Front Door + WAF (Recommended)

### Why AFD?

Azure Front Door provides TLS termination at the edge, WAF protection, DDoS mitigation, and ensures your VM is never directly exposed to public HTTP/HTTPS traffic. This prevents security incidents like CitrusPeel (http.sys vulnerability) from affecting your infrastructure.

### Architecture

```
User Browser → AFD Standard (HTTPS, WAF, DDoS)
                    ↓ (HTTP:18789, only AzureFrontDoor.Backend)
              VM: OpenClaw Gateway (:18789)
                    ↓ (outbound)
              WeChat Server (no inbound needed)

Admin SSH → VM:3232 (NSG restrict source IP)
```

### Step 1: Create AFD Profile

```bash
az afd profile create \
  --resource-group <RG> \
  --profile-name <AFD_NAME> \
  --sku Standard_AzureFrontDoor \
  -o table
```

### Step 2: Create Endpoint

```bash
az afd endpoint create \
  --resource-group <RG> \
  --profile-name <AFD_NAME> \
  --endpoint-name <ENDPOINT_NAME> \
  --enabled-state Enabled \
  -o table
```

Note the `HostName` from the output (e.g., `<endpoint>.b02.azurefd.net`).

### Step 3: Create Origin Group + Origin

```bash
# Origin group with health probes
az afd origin-group create \
  --resource-group <RG> \
  --profile-name <AFD_NAME> \
  --origin-group-name <ORIGIN_GROUP> \
  --probe-request-type GET \
  --probe-protocol Http \
  --probe-path "/" \
  --probe-interval-in-seconds 60 \
  --sample-size 4 \
  --successful-samples-required 3 \
  -o table

# Origin pointing to VM on HTTP:18789
az afd origin create \
  --resource-group <RG> \
  --profile-name <AFD_NAME> \
  --origin-group-name <ORIGIN_GROUP> \
  --origin-name <ORIGIN_NAME> \
  --host-name <VM_IP> \
  --origin-host-header <VM_IP> \
  --http-port 18789 \
  --priority 1 \
  --weight 1000 \
  --enabled-state Enabled \
  -o table
```

### Step 4: Create Route (HTTPS → HTTP)

```bash
az afd route create \
  --resource-group <RG> \
  --profile-name <AFD_NAME> \
  --endpoint-name <ENDPOINT_NAME> \
  --route-name <ROUTE_NAME> \
  --origin-group <ORIGIN_GROUP> \
  --supported-protocols Https \
  --forwarding-protocol HttpOnly \
  --https-redirect Enabled \
  --patterns-to-match "/*" \
  --link-to-default-domain Enabled \
  -o table
```

### Step 5: Create WAF Policy (Optional but Recommended)

Create a JSON file `waf.json`:

```json
{
  "location": "Global",
  "sku": {"name": "Standard_AzureFrontDoor"},
  "properties": {
    "policySettings": {"enabledState": "Enabled", "mode": "Prevention"},
    "customRules": {"rules": [{
      "name": "RateLimitRule",
      "priority": 1,
      "enabledState": "Enabled",
      "ruleType": "RateLimitRule",
      "rateLimitDurationInMinutes": 1,
      "rateLimitThreshold": 100,
      "action": "Block",
      "matchConditions": [{"matchVariable": "RemoteAddr", "operator": "IPMatch", "negateCondition": true, "matchValue": ["10.0.0.0/8"]}]
    }]}
  }
}
```

```bash
az rest --method PUT \
  --url "https://management.azure.com/subscriptions/<SUB_ID>/resourceGroups/<RG>/providers/Microsoft.Network/FrontDoorWebApplicationFirewallPolicies/<WAF_NAME>?api-version=2024-02-01" \
  --body @waf.json
```

Associate WAF with endpoint:

```bash
az afd security-policy create \
  --resource-group <RG> \
  --profile-name <AFD_NAME> \
  --security-policy-name <SECURITY_POLICY> \
  --domains /subscriptions/<SUB_ID>/resourceGroups/<RG>/providers/Microsoft.Cdn/profiles/<AFD_NAME>/afdEndpoints/<ENDPOINT_NAME> \
  --waf-policy /subscriptions/<SUB_ID>/resourceGroups/<RG>/providers/Microsoft.Network/frontdoorwebapplicationfirewallpolicies/<WAF_NAME>
```

### Step 6: NSG Rules for AFD Path

```bash
# Port 18789 only from AFD backend (CRITICAL for origin isolation)
az network nsg rule create -g <RG> --nsg-name <NSG> -n AFD-Backend-18789 \
  --priority 320 --direction Inbound --access Allow --protocol Tcp \
  --source-address-prefixes AzureFrontDoor.Backend \
  --destination-port-ranges 18789

# Do NOT open port 443 — AFD handles TLS at the edge
# Do NOT open port 18789 to * — only AzureFrontDoor.Backend
```

> ⚠️ **If a subnet NSG exists**, add the same `AzureFrontDoor.Backend → 18789` rule there too.

### Step 7: OpenClaw Config for AFD

```bash
# Bind gateway to all interfaces (AFD needs to reach it)
openclaw config set gateway.bind lan

# Add AFD endpoint to allowedOrigins
python3 -c "
import json
with open('$HOME/.openclaw/openclaw.json', 'r') as f:
    cfg = json.load(f)
gw = cfg.setdefault('gateway', {})
cui = gw.setdefault('controlUi', {})
cui['enabled'] = True
origins = cui.setdefault('allowedOrigins', [])
afd_origin = 'https://<AFD_ENDPOINT_HOSTNAME>'
if afd_origin not in origins:
    origins.append(afd_origin)
with open('$HOME/.openclaw/openclaw.json', 'w') as f:
    json.dump(cfg, f, indent=2)
"
openclaw daemon restart
```

### Step 8: Get Front Door ID for X-Azure-FDID Validation

```bash
az afd profile show --resource-group <RG> --profile-name <AFD_NAME> --query "frontDoorId" -o tsv
```

> For additional origin security, validate the `X-Azure-FDID` header in your application to ensure requests originate from **your** specific AFD instance.

### Access URL (via AFD)

```
https://<AFD_ENDPOINT_HOSTNAME>/#token=<gateway_token>
```

### Security Benefits vs Direct Exposure

| Feature | Direct (Caddy) | AFD Path |
|---------|----------------|----------|
| TLS termination | Self-signed cert on VM | AFD edge (managed cert) |
| WAF | None | OWASP / Bot / Rate Limit |
| DDoS | None | L3/L4/L7 built-in |
| HTTP/3 | VM processes directly | AFD edge terminates |
| Origin isolation | VM publicly exposed | NSG blocks non-AFD traffic |
| Cost | Free | ~$35/mo AFD + ~$5/mo WAF |

---

## Phase 4B: HTTPS via Caddy (Simple/Free Alternative)

### Why Caddy?

OpenClaw gateway binds to `localhost:18789` by default. For external HTTPS access, use Caddy as a reverse proxy.

### Install Caddy

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install -y caddy
```

### Generate Self-Signed Certificate

> **`tls internal` FAILS on Ubuntu 24.04** because caddy user lacks sudo for root cert install. Use openssl instead.

```bash
sudo mkdir -p /etc/caddy/certs
sudo openssl req -x509 -newkey rsa:2048 -keyout /etc/caddy/certs/key.pem \
  -out /etc/caddy/certs/cert.pem -days 365 -nodes \
  -subj "/CN=<VM_IP>" -addext "subjectAltName=IP:<VM_IP>"

# Fix permissions for caddy
sudo chmod 640 /etc/caddy/certs/key.pem
sudo chown root:caddy /etc/caddy/certs/key.pem
```

### Configure Caddyfile

```bash
sudo tee /etc/caddy/Caddyfile << 'EOF'
:443 {
    tls /etc/caddy/certs/cert.pem /etc/caddy/certs/key.pem
    reverse_proxy localhost:18789
}
EOF

sudo systemctl restart caddy
```

### OpenClaw Gateway Configuration

```bash
# Bind gateway to all interfaces (required for Caddy to proxy)
openclaw config set gateway.bind lan

# Add HTTPS origin to allowed origins
# Edit ~/.openclaw/openclaw.json and add to gateway.controlUi.allowedOrigins:
#   "https://<VM_IP>"

openclaw daemon restart
```

### NSG Rule for HTTPS

```bash
az network nsg rule create -g <RG> --nsg-name <NSG> -n HTTPS \
  --priority 320 --direction Inbound --access Allow --protocol Tcp \
  --destination-port-ranges 443
```

If a subnet NSG exists, add the same rule there too.

### Access URL

```
https://<VM_IP>/#token=<gateway_token>
```

Get the token:
```bash
openclaw dashboard --no-open
```

---

## Phase 5: Device Approval (Pairing)

### Problem

When Caddy proxies requests to localhost, Gateway sees all connections as local and auto-approves them.

### Solution: Trusted Proxies

Configure `gateway.trustedProxies` so Gateway reads the real client IP from `X-Forwarded-For` header:

Edit `~/.openclaw/openclaw.json` using python3 (more reliable than CLI for nested values):
```bash
python3 -c "
import json
with open('$HOME/.openclaw/openclaw.json', 'r') as f:
    cfg = json.load(f)
gw = cfg.setdefault('gateway', {})
cui = gw.setdefault('controlUi', {})
origins = cui.setdefault('allowedOrigins', [])
for o in ['http://localhost:18789', 'http://127.0.0.1:18789', 'https://<VM_IP>']:
    if o not in origins:
        origins.append(o)
gw['trustedProxies'] = ['127.0.0.1']
with open('$HOME/.openclaw/openclaw.json', 'w') as f:
    json.dump(cfg, f, indent=2)
print('Config updated')
"
openclaw daemon restart
```

> ⚠️ **Avoid using `openclaw config set` for complex nested values** like arrays — shell quoting issues can corrupt the config. Use python3 or direct JSON editing instead. If the config gets corrupted, restore from `~/.openclaw/openclaw.json.bak`.

Now external connections require device pairing approval:
```bash
# List pending devices
openclaw devices list

# Approve a device
openclaw devices approve <request-id>
```

### Auth Modes

Valid `gateway.auth.mode` values: `none`, `token`, `password`, `trusted-proxy`

Device pairing is a **separate system**, not an auth mode. It works alongside any auth mode.

---

## Phase 6: WeChat Integration

### ⚠️ WeChat is NOT a Native Channel

Native channels: telegram, whatsapp, discord, irc, googlechat, slack, signal, imessage, line.

WeChat requires the **official Tencent plugin**: `@tencent-weixin/openclaw-weixin`

### Install Plugin

```bash
openclaw plugins install "@tencent-weixin/openclaw-weixin"
```

Security warnings about `child_process` and `env` access will appear — accept them (official Tencent plugin).

### Enable Plugin

```bash
openclaw config set plugins.entries.openclaw-weixin.enabled true
openclaw daemon restart
```

### Login (QR Code)

```bash
openclaw channels login --channel openclaw-weixin
```

This displays a QR code in terminal + a fallback URL. **Scan with WeChat immediately** (QR codes expire in ~60 seconds, max 3 retries before timeout).

> ⚠️ **QR Code Timing Tips:**
> - Have your phone WeChat open and ready **before** running the command
> - If running via remote automation (e.g., Copilot CLI), use `ssh -t` for interactive TTY
> - If the terminal QR code is hard to read, use the fallback URL shown below the QR code
> - On timeout, re-run the command — each attempt gets 3 fresh QR codes
> - Success message: `✅ 与微信连接成功！`

**Requirements:**
- iOS WeChat 8.0.70+ (gray release, primarily iPhone)
- WeChat ClawBot feature must be enabled

### Verify

```bash
openclaw channels list
```

Should show:
```
openclaw-weixin <id>: configured, enabled
```

### Config in openclaw.json

After setup, `openclaw.json` will contain:
```json
{
  "channels": {
    "openclaw-weixin": {
      "accounts": {}
    }
  },
  "plugins": {
    "entries": {
      "openclaw-weixin": {
        "enabled": true
      }
    },
    "installs": {
      "openclaw-weixin": {
        "source": "npm",
        "spec": "@tencent-weixin/openclaw-weixin",
        "version": "2.0.1"
      }
    }
  }
}
```

---

## Phase 7: Assistant Personality

OpenClaw uses three workspace files for personality:

### IDENTITY.md (`~/.openclaw/workspace/IDENTITY.md`)

```markdown
# IDENTITY.md - Who Am I?

- **Name:** <Your AI Name>
- **Creature:** AI 助理 — 一个可靠的智能伙伴
- **Vibe:** 友好随和、有耐心、注重准确性
- **Emoji:** 🤖
- **Language:** 中英文混合，根据对话语境自然切换
```

### SOUL.md (`~/.openclaw/workspace/SOUL.md`)

```markdown
# SOUL.md - Personality Rules

- 准确性第一，不确定时坦诚告知
- 不编造事实，不产生幻觉
- 友好专业的语气
- 支持中英文双语交流
- 简洁明了，避免啰嗦
- 遇到复杂问题分步骤解答
```

### USER.md (`~/.openclaw/workspace/USER.md`)

```markdown
# USER.md - User Profile

- **Name:** <Your Name>
- **Timezone:** Asia/Shanghai (UTC+8)
- **Language:** 中文为主，英文辅助
- **Interests:** <Your interests>
```

### Timezone

```bash
openclaw config set agents.defaults.userTimezone "Asia/Shanghai"
openclaw daemon restart
```

---

## Phase 8: Post-Reboot Resilience

### Problem

After VM reboot, OpenClaw gateway (user-level systemd service) doesn't start until user logs in via SSH. Caddy (system-level service) starts immediately and returns 502 errors.

**Symptom:** `disconnected (1006): no reason` in browser.

### Solution: Enable Lingering

```bash
sudo loginctl enable-linger <username>
```

This ensures user-level systemd services start at boot, regardless of SSH login.

### ⚠️ Reboot vs Deallocate

`enable-linger` only solves **boot/reboot** recovery. It does **not** help if the VM is:
- stopped/deallocated manually
- deallocated by automation/policy

If the entire service disappears from the internet, check VM power state first:

```bash
az vm show -g <RG> -n <VM_NAME> -d --query "{power:powerState, publicIp:publicIps}" -o table
```

If you see `VM deallocated`, recover with:

```bash
az vm start -g <RG> -n <VM_NAME>
```

### Verify

```bash
loginctl show-user <username> | grep Linger
# Should show: Linger=yes
```

### Service Startup Order After Fix

1. ✅ System boot → Caddy starts (system service, if using Path B)
2. ✅ System boot → user@.service starts (lingering) → OpenClaw gateway starts
3. ✅ Both services ready before any browser connection

---

## Phase 9: Anti-Auto-Shutdown (MCAPS Subscriptions)

### Problem

MCAPS and similar governance-managed Azure subscriptions may automatically **deallocate** VMs daily via `MCAPSGov-AutomationApp`. This kills OpenClaw completely.

### Solution: Three-Layer Defense

#### Layer 1: Exemption Tags

```bash
az vm update -g <RG> -n <VM_NAME> --set \
  tags.AutoShutdown=Disabled \
  tags.DoNotShutdown=yes \
  tags.AlwaysOn=yes
```

#### Layer 2: Logic App Auto-Restart (4x Daily)

Create a Logic App with System-Assigned Managed Identity that starts the VM on a schedule:

```bash
# Create Logic App via REST API (az logic CLI may hang)
cat > /tmp/logic.json << 'EOF'
{
  "location": "<REGION>",
  "identity": {"type": "SystemAssigned"},
  "properties": {
    "state": "Enabled",
    "definition": {
      "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
      "contentVersion": "1.0.0.0",
      "triggers": {
        "Recurrence": {
          "type": "Recurrence",
          "recurrence": {
            "frequency": "Day",
            "interval": 1,
            "schedule": {"hours": [1,7,13,17], "minutes": [15]},
            "timeZone": "UTC"
          }
        }
      },
      "actions": {
        "Start_VM": {
          "type": "Http",
          "inputs": {
            "method": "POST",
            "uri": "https://management.azure.com/subscriptions/<SUB_ID>/resourceGroups/<RG>/providers/Microsoft.Compute/virtualMachines/<VM_NAME>/start?api-version=2024-07-01",
            "authentication": {"type": "ManagedServiceIdentity"}
          }
        }
      }
    }
  }
}
EOF

az rest --method PUT \
  --url "https://management.azure.com/subscriptions/<SUB_ID>/resourceGroups/<RG>/providers/Microsoft.Logic/workflows/<LOGIC_APP_NAME>?api-version=2019-05-01" \
  --body @/tmp/logic.json
```

Then assign VM Contributor role to the Logic App's managed identity:

```bash
# Get Logic App principal ID
PRINCIPAL_ID=$(az rest --method GET \
  --url "https://management.azure.com/subscriptions/<SUB_ID>/resourceGroups/<RG>/providers/Microsoft.Logic/workflows/<LOGIC_APP_NAME>?api-version=2019-05-01" \
  --query "identity.principalId" -o tsv)

# Assign VM Contributor scoped to the VM
az role assignment create \
  --assignee-object-id $PRINCIPAL_ID \
  --assignee-principal-type ServicePrincipal \
  --role "Virtual Machine Contributor" \
  --scope "/subscriptions/<SUB_ID>/resourceGroups/<RG>/providers/Microsoft.Compute/virtualMachines/<VM_NAME>"
```

#### Schedule (UTC → Beijing Time)

| UTC | Beijing | Purpose |
|-----|---------|---------|
| 01:15 | 09:15 | Morning check |
| 07:15 | 15:15 | Afternoon check |
| 13:15 | 21:15 | Evening check |
| 17:15 | 01:15 | ~30 min after governance shutdown |

#### Layer 3: `loginctl enable-linger`

Already covered in Phase 8 — ensures OpenClaw auto-starts after VM boot.

---

## Complete Architecture

### Path A: AFD (Recommended)

```
┌─────────────────────────────────────────────────────┐
│                    Internet                         │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────┴────────┐
              │  Azure Front    │
              │  Door (HTTPS)   │
              │  + WAF + DDoS   │
              └────────┬────────┘
                       │ HTTP:18789 (AzureFrontDoor.Backend only)
              ┌────────┴────────┐
              │  Azure NSG      │
              │  Port 3232 SSH  │  ← admin IP only
              │  Port 18789 AFD │  ← AzureFrontDoor.Backend only
              └────────┬────────┘
                       │
              ┌────────┴────────┐
              │  Azure VM       │
              │  Ubuntu 24.04   │
              └────────┬────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    ┌────┴────┐  ┌─────┴─────┐  ┌───┴───┐
    │ SSH     │  │ OpenClaw  │  │       │
    │ :3232   │  │ Gateway   │  │       │
    └─────────┘  │ :18789    │  │       │
                 │ (HTTP)    │  │       │
                 └─────┬─────┘  │       │
                       │        │       │
              ┌────────┴────────┴───────┤
              │  ┌──────────────────┐   │
              │  │ GitHub Copilot   │   │
              │  │ (LLM Provider)   │   │
              │  └──────────────────┘   │
              │  ┌──────────────────┐   │
              │  │ WeChat Plugin    │   │
              │  │ openclaw-weixin  │   │
              │  └──────────────────┘   │
              │  ┌──────────────────┐   │
              │  │ Control UI       │   │
              │  │ (Web Dashboard)  │   │
              │  └──────────────────┘   │
              └─────────────────────────┘
```

### Path B: Caddy (Simple)

```
┌─────────────────────────────────────────────────────┐
│                    Internet                         │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────┴────────┐
              │  Azure NSG      │
              │  Port 3232 SSH  │
              │  Port 443 HTTPS │
              └────────┬────────┘
                       │
              ┌────────┴────────┐
              │  Azure VM       │
              │  Ubuntu 24.04   │
              └────────┬────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    ┌────┴────┐  ┌─────┴─────┐  ┌───┴───┐
    │ SSH     │  │ Caddy     │  │       │
    │ :3232   │  │ :443 TLS  │  │       │
    └─────────┘  │ ↓ proxy   │  │       │
                 └─────┬─────┘  │       │
                       │        │       │
              ┌────────┴────────┴───────┤
              │  OpenClaw Gateway       │
              │  :18789                 │
              │  ┌──────────────────┐   │
              │  │ GitHub Copilot   │   │
              │  │ (LLM Provider)   │   │
              │  └──────────────────┘   │
              │  ┌──────────────────┐   │
              │  │ WeChat Plugin    │   │
              │  │ openclaw-weixin  │   │
              │  └──────────────────┘   │
              │  ┌──────────────────┐   │
              │  │ Control UI       │   │
              │  │ (Web Dashboard)  │   │
              │  └──────────────────┘   │
              └─────────────────────────┘
```

---

## Teammate One-Run Checklist

Use this as the handoff version for colleagues. Replace placeholders first:
- `<RG>`
- `<VM_NAME>`
- `<VM_IP>`
- `<USERNAME>`
- `<AFD_NAME>` (if using AFD path)
- `<NSG_NAME>`
- `<SUBNET_NSG>` (if Azure created one)

### 1) VM and network

```bash
az vm list-skus --location southeastasia --size Standard_B4 --output table

az vm create \
  --resource-group <RG> \
  --name <VM_NAME> \
  --location southeastasia \
  --image Canonical:ubuntu-24_04-lts:server:latest \
  --size Standard_B4s_v2 \
  --admin-username <USERNAME> \
  --generate-ssh-keys \
  --nsg <NSG_NAME> \
  --public-ip-sku Standard \
  --zone 1 \
  --output json

az network nsg rule create -g <RG> --nsg-name <NSG_NAME> -n SSH-3232 \
  --priority 310 --direction Inbound --access Allow --protocol Tcp \
  --destination-port-ranges 3232

# For AFD path: open 18789 only to AFD
az network nsg rule create -g <RG> --nsg-name <NSG_NAME> -n AFD-Backend-18789 \
  --priority 320 --direction Inbound --access Allow --protocol Tcp \
  --source-address-prefixes AzureFrontDoor.Backend \
  --destination-port-ranges 18789

# For Caddy path: open 443 to all
# az network nsg rule create -g <RG> --nsg-name <NSG_NAME> -n HTTPS \
#   --priority 320 --direction Inbound --access Allow --protocol Tcp \
#   --destination-port-ranges 443

# Add exemption tags to prevent auto-shutdown
az vm update -g <RG> -n <VM_NAME> --set \
  tags.AutoShutdown=Disabled tags.DoNotShutdown=yes tags.AlwaysOn=yes
```

If a subnet NSG exists, add the same two rules there too.

### 2) SSH hardening

```bash
ssh <USERNAME>@<VM_IP>

sudo sed -i 's/^#Port 22$/Port 3232/' /etc/ssh/sshd_config
sudo mkdir -p /etc/systemd/system/ssh.socket.d/
sudo tee /etc/systemd/system/ssh.socket.d/override.conf << 'EOF'
[Socket]
ListenStream=
ListenStream=0.0.0.0:3232
EOF

sudo systemctl daemon-reload
sudo systemctl restart ssh.socket
ss -tlnp | grep 3232
```

Verify new SSH works before deleting port 22 rule.

### 3) Install OpenClaw + GitHub Copilot

```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
curl -fsSL https://openclaw.ai/install.sh | bash
echo 'export PATH="/home/<USERNAME>/.npm-global/bin:$PATH"' >> ~/.bashrc
export PATH="/home/<USERNAME>/.npm-global/bin:$PATH"

openclaw config set gateway.mode local
openclaw config set agents.defaults.model.primary "github-copilot/gpt-5.4"
openclaw config set agents.defaults.userTimezone "Asia/Shanghai"

openclaw daemon install
openclaw daemon start
openclaw daemon status
```

Then authenticate GitHub Copilot from an interactive terminal:

```bash
openclaw models auth login-github-copilot
openclaw models set github-copilot/gpt-5.4
openclaw models list
```

### 4) HTTPS portal

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install -y caddy

sudo mkdir -p /etc/caddy/certs
sudo openssl req -x509 -newkey rsa:2048 -keyout /etc/caddy/certs/key.pem \
  -out /etc/caddy/certs/cert.pem -days 365 -nodes \
  -subj "/CN=<VM_IP>" -addext "subjectAltName=IP:<VM_IP>"
sudo chmod 640 /etc/caddy/certs/key.pem
sudo chown root:caddy /etc/caddy/certs/key.pem

sudo tee /etc/caddy/Caddyfile << 'EOF'
:443 {
    tls /etc/caddy/certs/cert.pem /etc/caddy/certs/key.pem
    reverse_proxy localhost:18789
}
EOF

openclaw config set gateway.bind lan
sudo systemctl restart caddy
openclaw daemon restart
openclaw dashboard --no-open
```

### 5) Device approval

Use the tokenized URL from `openclaw dashboard --no-open`.

If Portal says `pairing required`:

```bash
openclaw devices list
openclaw devices approve <request-id>
```

### 6) WeChat

```bash
openclaw plugins install "@tencent-weixin/openclaw-weixin"
openclaw config set plugins.entries.openclaw-weixin.enabled true
openclaw daemon restart
openclaw channels login --channel openclaw-weixin
openclaw channels list
```

Have WeChat ready before running login. QR expires quickly.

### 7) Reliability

```bash
sudo loginctl enable-linger <USERNAME>
loginctl show-user <USERNAME> | grep Linger
```

### 8) Optional bundled GitHub skills

```bash
(type -p wget >/dev/null || (sudo apt update && sudo apt install wget -y)) && \
sudo mkdir -p -m 755 /etc/apt/keyrings && \
out=$(mktemp) && \
wget -nv -O"$out" https://cli.github.com/packages/githubcli-archive-keyring.gpg && \
cat "$out" | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null && \
sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg && \
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | \
sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
sudo apt update && sudo apt install gh -y

gh --version
openclaw skills list
```

Expected bundled skills to become ready:
- `github`
- `gh-issues`

### Final acceptance

- Portal opens over `https://<VM_IP>/#token=...`
- If first access asks for pairing, approval succeeds
- `openclaw channels list` shows `openclaw-weixin ... configured, enabled`
- WeChat can send a message to the bot
- `openclaw daemon status` shows running
- `curl -sk https://127.0.0.1/ -o /dev/null -w "%{http_code}\n"` returns `200`

---

## Troubleshooting

| **Problem** | **Cause** | **Solution** |
|---|---|---|
| `disconnected (1006)` after reboot | Gateway not started (user service needs login) | `sudo loginctl enable-linger <user>` |
| Gateway won't start | `gateway.mode` not set | `openclaw config set gateway.mode local` |
| `gateway.bind: "0.0.0.0"` rejected | Legacy format | Use `"lan"` instead of `"0.0.0.0"` |
| Caddy `tls internal` fails | caddy user lacks sudo for root cert | Use openssl self-signed cert with explicit paths |
| Caddy 502 Bad Gateway | Gateway not running on :18789 | Check `openclaw daemon status`, restart if needed |
| `Unsupported channel: wechat` | WeChat not native | Install plugin: `openclaw plugins install "@tencent-weixin/openclaw-weixin"` |
| WeChat QR code expired | QR codes timeout in ~60s, max 3 retries | Have phone ready before running `openclaw channels login --channel openclaw-weixin` |
| All devices auto-approved | Caddy proxies from localhost | Set `gateway.trustedProxies: ["127.0.0.1"]` |
| SSH port change doesn't work | Ubuntu 24.04 socket activation | Override `ssh.socket`, not just `sshd_config` |
| `openclaw` command not found | PATH not set | `export PATH="/home/<user>/.npm-global/bin:$PATH"` |
| Models list empty | Only configured models shown | Use `openclaw models set <provider>/<model>` to add |
| VM creation fails: `SkuNotAvailable` | SKU capacity exhausted in region | Try another SKU or zone; run `az vm list-skus --location <region> --size Standard_B4 --output table` |
| VM creation fails: `TrustedLaunch` | ARM SKU doesn't support TrustedLaunch | Use x86 SKU, or add `--security-type Standard` (requires feature registration) |
| Onboarding wizard fails: `/dev/tty` | No TTY in non-interactive SSH | Use Path B (non-interactive setup) with `openclaw config set` commands |
| `openclaw.json` corrupted / empty | Bad CLI quoting or failed config update | Restore from `~/.openclaw/openclaw.json.bak`; use python3 for complex edits |
| `disconnected (1008): unauthorized` | Gateway token missing from URL | Run `openclaw dashboard --no-open` to get tokenized URL |
| `plugins.allow is empty` warning | Non-bundled plugins auto-loading | Safe to ignore for official plugins; set `plugins.allow` for explicit control |
| Public HTTPS/SSH still fails after NSG rules | Azure subnet NSG still blocks inbound | Check subnet NSG and mirror `3232` / `443` rules there |
| AFD returns 503 | Origin health probe failing | Ensure VM gateway is running on :18789, NSG allows `AzureFrontDoor.Backend` on 18789 |
| AFD returns 404 on root `/` | OpenClaw root path returns 404 | Normal — access via `https://<afd-endpoint>/#token=<token>` |
| VM still accessible on :18789 directly | NSG not properly restricted | Verify NSG rule uses `AzureFrontDoor.Backend` service tag, not `*` |
| VM deallocated daily | MCAPS governance auto-shutdown | Add exemption tags + Logic App auto-restart (Phase 9) |
| Portal returns `pairing required` | Device approval is working as designed | Run `openclaw devices list`, then `openclaw devices approve <request-id>` |
| Public site suddenly times out / 502 everywhere | VM is deallocated | `az vm show -d` to confirm, then `az vm start` |
| Portal returns 502 just after VM startup | Caddy started before OpenClaw was fully ready | Wait briefly, then re-test `https://<VM_IP>/`; verify `openclaw-gateway.service` is active |

---

## Key Files Reference

| **File** | **Purpose** |
|---|---|
| `~/.openclaw/openclaw.json` | Main config: auth, models, gateway, plugins, channels |
| `~/.openclaw/workspace/IDENTITY.md` | AI assistant identity |
| `~/.openclaw/workspace/SOUL.md` | AI personality rules |
| `~/.openclaw/workspace/USER.md` | User profile |
| `~/.config/systemd/user/openclaw-gateway.service` | OpenClaw daemon service |
| `~/.openclaw/extensions/openclaw-weixin/` | WeChat plugin directory |
| `/etc/caddy/Caddyfile` | Caddy reverse proxy config |
| `/etc/caddy/certs/cert.pem` + `key.pem` | Self-signed TLS cert |
| `/etc/systemd/system/ssh.socket.d/override.conf` | SSH port override |

---

## Example Final openclaw.json

```json
{
  "auth": {
    "profiles": {
      "github-copilot:github": {
        "provider": "github-copilot",
        "mode": "token"
      }
    }
  },
  "agents": {
    "defaults": {
      "model": { "primary": "github-copilot/gpt-5.4" },
      "models": {
        "github-copilot/gpt-4o": {},
        "github-copilot/gpt-5.4": {}
      },
      "userTimezone": "Asia/Shanghai"
    }
  },
  "channels": {
    "openclaw-weixin": { "accounts": {} }
  },
  "gateway": {
    "mode": "local",
    "bind": "lan",
    "controlUi": {
      "allowedOrigins": [
        "http://localhost:18789",
        "http://127.0.0.1:18789",
        "https://<VM_IP>",
        "https://<AFD_ENDPOINT_HOSTNAME>"
      ]
    },
    "auth": { "mode": "token" },
    "trustedProxies": ["127.0.0.1"]
  },
  "plugins": {
    "entries": {
      "openclaw-weixin": { "enabled": true }
    }
  }
}
```

---

## Checklist

- [ ] Azure VM created (check SKU availability first!)
- [ ] NIC NSG rules: SSH custom port + (AFD: 18789 AzureFrontDoor.Backend only / Caddy: HTTPS 443)
- [ ] Subnet NSG rules mirrored when a subnet NSG exists
- [ ] VM exemption tags set (AutoShutdown=Disabled, DoNotShutdown=yes, AlwaysOn=yes)
- [ ] SSH connectivity verified
- [ ] SSH port changed + socket override created
- [ ] Old SSH rule (port 22) deleted after verification
- [ ] Azure CLI installed and logged in
- [ ] OpenClaw installed, PATH configured in `~/.bashrc`
- [ ] `gateway.mode=local` set
- [ ] GitHub Copilot authenticated (device code flow via `ssh -t`)
- [ ] Model set (e.g., `github-copilot/gpt-5.4`)
- [ ] Daemon installed and running
- [ ] Optional: `gh` CLI installed so bundled `github` / `gh-issues` skills become ready
- [ ] Caddy installed with self-signed cert (Path B only)
- [ ] OR: AFD profile + endpoint + origin + route + WAF created (Path A, recommended)
- [ ] `gateway.bind=lan` + `allowedOrigins` configured (include AFD endpoint if using Path A)
- [ ] HTTPS access verified externally
- [ ] `gateway.trustedProxies` configured for device approval
- [ ] Portal tested with device approval flow (`pairing required` -> approve -> access granted)
- [ ] WeChat plugin installed and enabled
- [ ] WeChat QR code scanned and connected
- [ ] IDENTITY.md / SOUL.md / USER.md personalized
- [ ] `loginctl enable-linger` for boot resilience
- [ ] Logic App auto-restart created (Phase 9, for MCAPS subscriptions)
- [ ] VM power state monitoring or manual check process defined (to catch deallocation)
- [ ] Timezone set in `agents.defaults.userTimezone`
