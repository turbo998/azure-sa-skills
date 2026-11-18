# One-Run Checklist, Troubleshooting & Final Config

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
openclaw config set agents.defaults.model.primary "github-copilot/gpt-6.2-sol"
openclaw config set agents.defaults.userTimezone "Asia/Shanghai"

openclaw daemon install
openclaw daemon start
openclaw daemon status
```

Then authenticate GitHub Copilot from an interactive terminal:

```bash
openclaw models auth login-github-copilot
openclaw models set github-copilot/gpt-6.2-sol
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
      "model": { "primary": "github-copilot/gpt-6.2-sol" },
      "models": {
        "github-copilot/gpt-6.2-sol": {},
        "github-copilot/gemini-4-carbon": {},
        "github-copilot/grok-4.7": {},
        "github-copilot/gemini-3.8-flash": {}
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
- [ ] Model set (e.g., `github-copilot/gpt-6.2-sol`)
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
