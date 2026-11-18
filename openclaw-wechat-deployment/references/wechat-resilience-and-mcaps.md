# WeChat Integration, Persona, Reboot Lingering & MCAPS Anti-Shutdown

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

