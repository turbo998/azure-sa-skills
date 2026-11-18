---
name: openclaw-wechat-deployment
description: "Deploy OpenClaw AI gateway on Azure Ubuntu VM with GitHub Copilot models (gpt-6.2-sol, gemini-4-carbon, grok-4.7), AFD/Caddy TLS, and WeChat QR."
---

# OpenClaw + WeChat Deployment on Azure VM with GitHub Copilot

End-to-end runbook for deploying a persistent OpenClaw personal AI assistant on an Azure Ubuntu 24.04 VM, backed by GitHub Copilot frontier models and connected to personal WeChat via Tencent's official plugin.

## Model Tier Selection (`github-copilot/*`)

| Workload Profile | Recommended Model ID | Notes |
|---|---|---|
| Default Agent & Engineering | `github-copilot/gpt-6.2-sol` | Best multi-step tool execution, code/ops reliability |
| Multimodal & Long-Context Docs | `github-copilot/gemini-4-carbon` | Image/PDF understanding, large context synthesis |
| Low-Latency Chat & Live Triage | `github-copilot/grok-4.7` | Fast WeChat conversational turnaround & web triage |
| High-Throughput Lightweight | `github-copilot/gemini-3.8-flash` | Low-cost background checks and simple Q&A |

Always verify live account entitlement after login via `openclaw models list`.

## Architecture & Phase Map

| Phase | Summary | Detailed Reference |
|---|---|---|
| **0. Azure VM & NSG** | Ubuntu 24.04 (`Standard_D4s_v5` x86 preferred; avoid unsupported TrustedLaunch ARM combos). Mirror inbound rules on **both NIC NSG and Subnet NSG**! | Inline below |
| **1. SSH Hardening** | Custom port (e.g. `3232`). **Ubuntu 24.04 uses `ssh.socket`**: override `/etc/systemd/system/ssh.socket.d/override.conf` (`ListenStream=`, `ListenStream=3232`) + `systemctl daemon-reload && systemctl restart ssh.socket ssh`. | Inline below |
| **2–3. OpenClaw + Copilot** | Install via `https://openclaw.ai/install.sh` (`--no-onboard`), configure `~/.npm-global/bin` PATH, set `gateway.mode=local`, authenticate via `ssh -t ... openclaw models auth login-github-copilot`. | Inline below |
| **4–5. HTTPS & Device Pairing** | **Path A (Recommended)**: Azure Front Door Standard + WAF (`AzureFrontDoor.Backend` service tag on port `18789`). **Path B**: Caddy self-signed TLS on `443`. Configure `gateway.trustedProxies`. | [references/https-afd-and-caddy.md](references/https-afd-and-caddy.md) |
| **6–7. WeChat & Persona** | Install `@tencent-weixin/openclaw-weixin` (`npx -y @tencent-weixin/openclaw-weixin-cli@latest install`), QR login via `openclaw channels login --channel openclaw-weixin`, configure `IDENTITY.md` / `SOUL.md` / `USER.md`. | [references/wechat-resilience-and-mcaps.md](references/wechat-resilience-and-mcaps.md) |
| **8–9. Resilience & MCAPS** | `sudo loginctl enable-linger $USER` (survives reboot) + MCAPS 3-layer anti-deallocation (exemption tags + 4x daily Logic App `Start` via ARM REST API). | [references/wechat-resilience-and-mcaps.md](references/wechat-resilience-and-mcaps.md) |
| **Runbook & Troubleshooting** | Copy/paste single-run deployment script, `openclaw.json` full reference, and error lookup table. | [references/one-run-checklist-and-troubleshooting.md](references/one-run-checklist-and-troubleshooting.md) |

## Quick Deployment Path (Non-Interactive SSH + TTY Auth)

### 1. Provision VM & NSG (Check Both NIC and Subnet NSGs)

```bash
az vm create -g <RG> -n <VM_NAME> --location <LOCATION> \
  --image Canonical:ubuntu-24_04-lts:server:latest --size Standard_D4s_v5 \
  --admin-username azureuser --generate-ssh-keys --public-ip-sku Standard \
  --tags AutoShutdown=Disabled DoNotShutdown=yes AlwaysOn=yes

# Inspect both NIC NSG and Subnet NSG! If subnet has an NSG, mirror SSH + 18789/443 rules on BOTH.
az network nic show --ids $(az vm show -g <RG> -n <VM_NAME> --query 'networkProfile.networkInterfaces[0].id' -o tsv) \
  --query '{nicNsg:networkSecurityGroup.id, subnetId:ipConfigurations[0].subnet.id}' -o json
```

### 2. Ubuntu 24.04 SSH Port Change (`ssh.socket` Trap)

Editing `/etc/ssh/sshd_config` alone does **not** change the port on Ubuntu 24.04:

```bash
# Add NSG rule for <NEW_PORT> BEFORE restarting SSH!
sudo sed -i 's/^#*Port 22/Port <NEW_PORT>/' /etc/ssh/sshd_config
sudo mkdir -p /etc/systemd/system/ssh.socket.d
printf "[Socket]\nListenStream=\nListenStream=0.0.0.0:<NEW_PORT>\nListenStream=[::]:<NEW_PORT>\n" | sudo tee /etc/systemd/system/ssh.socket.d/override.conf
sudo systemctl daemon-reload && sudo systemctl restart ssh.socket ssh
```

### 3. Install OpenClaw & Configure GitHub Copilot Model

```bash
curl -fsSL https://openclaw.ai/install.sh | bash -s -- --no-onboard
export PATH="$HOME/.npm-global/bin:$PATH"
grep -q '.npm-global/bin' ~/.bashrc || echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc

openclaw config set gateway.mode local
openclaw config set agents.defaults.model.primary "github-copilot/gpt-6.2-sol"
openclaw config set agents.defaults.userTimezone "Asia/Shanghai"
openclaw daemon install && openclaw daemon start
sudo loginctl enable-linger "$USER"
```

Run GitHub Copilot device-code login in an **interactive TTY** (`ssh -t`):

```bash
ssh -t azureuser@<VM_IP> -p <NEW_PORT> 'export PATH="$HOME/.npm-global/bin:$PATH" && openclaw models auth login-github-copilot && openclaw models list'
```

### 4. Complete HTTPS, WeChat QR Login & MCAPS Hardening

- Follow [references/https-afd-and-caddy.md](references/https-afd-and-caddy.md) to expose Control UI safely via **AFD + WAF** (recommended) or **Caddy**, then approve your browser via `openclaw devices list` / `openclaw devices approve <ID>`.
- Follow [references/wechat-resilience-and-mcaps.md](references/wechat-resilience-and-mcaps.md) to install `@tencent-weixin/openclaw-weixin`, scan the WeChat QR code, and deploy the MCAPS Logic App auto-start guard.
- Use [references/one-run-checklist-and-troubleshooting.md](references/one-run-checklist-and-troubleshooting.md) for the full `openclaw.json` template and troubleshooting fixes.
