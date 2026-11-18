# HTTPS Portal (AFD + WAF vs Caddy) & Device Approval

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

