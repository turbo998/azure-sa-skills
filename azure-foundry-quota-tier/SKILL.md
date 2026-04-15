---
name: azure-foundry-quota-tier
description: Query Azure Foundry/OpenAI model quota tier (Tier 1-6) for a given Azure subscription. Use this skill when the user asks about their Azure OpenAI or Foundry model quota tier, quota level, or wants to know which tier their subscription is on.
---

# Azure Foundry Model Quota Tier 查询

## 背景

Azure Foundry 使用 Quota Tier 机制（Free Tier + Tier 1~6）管理模型配额。Tier 越高，可用的 TPM/RPM 限额越大。

- 初始 Tier 取决于：使用量、与 Microsoft 的关系（如 EA/MCA-E）
- 系统会根据消费趋势**自动升级** Tier
- 官方文档：https://learn.microsoft.com/en-us/azure/foundry/openai/quotas-limits

## 查询步骤

### 第 1 步：确认订阅信息

确保用户已登录正确的 Azure 租户和订阅。如果未登录，执行：

```bash
az login --tenant <TENANT_ID>
az account set --subscription <SUBSCRIPTION_ID>
az account show --query "{name:name, id:id, tenantId:tenantId, state:state}" -o table
```

### 第 2 步：通过 REST API 查询 Quota Tier

使用 `Microsoft.CognitiveServices/quotaTiers` API 查询当前 Tier：

**PowerShell 版本**：

```powershell
$token = (az account get-access-token --resource https://management.azure.com --query accessToken -o tsv)
$headers = @{ "Authorization" = "Bearer $token"; "Content-Type" = "application/json" }
$uri = "https://management.azure.com/subscriptions/<SUBSCRIPTION_ID>/providers/Microsoft.CognitiveServices/quotaTiers/default?api-version=2025-10-01-preview"
$resp = Invoke-RestMethod -Uri $uri -Headers $headers -Method Get
$resp | ConvertTo-Json -Depth 10
```

**Bash/curl 版本**：

```bash
TOKEN=$(az account get-access-token --resource https://management.azure.com --query accessToken -o tsv)
curl -s "https://management.azure.com/subscriptions/<SUBSCRIPTION_ID>/providers/Microsoft.CognitiveServices/quotaTiers/default?api-version=2025-10-01-preview" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

### 第 3 步：解读返回结果

返回 JSON 包含以下关键字段：

| 字段 | 含义 |
|------|------|
| `properties.currentTierName` | 当前所在 Tier（如 "Tier 1"） |
| `properties.assignmentDate` | Tier 分配/生效日期 |
| `properties.tierUpgradePolicy` | 升级策略：`OnceUpgradeIsAvailable`（自动升级）或 `NoAutoUpgrade`（禁用） |

## 补充操作

### 查看每个模型的具体配额限额

```bash
# 列出订阅下的 AI Services 资源
az cognitiveservices account list --subscription <SUBSCRIPTION_ID> \
  --query "[].{name:name, kind:kind, location:location, rg:resourceGroup}" -o table

# 查看指定区域的 quota 使用情况
az cognitiveservices usage list --subscription <SUBSCRIPTION_ID> --location <LOCATION> \
  --query "[?limit!=\`0\`].{Model:name.value, Limit:limit, Used:currentValue}" -o table
```

### 查看可用模型及支持的 Tier

```bash
az cognitiveservices account list-models \
  --name <RESOURCE_NAME> --resource-group <RESOURCE_GROUP> --subscription <SUBSCRIPTION_ID> \
  --query "[?lifecycleStatus!='Deprecated'].{Model:name, Version:version, Status:lifecycleStatus, Tiers:join(', ', skus[].name)}" -o table
```

### 关闭自动 Tier 升级

```bash
TOKEN=$(az account get-access-token --resource https://management.azure.com --query accessToken -o tsv)
curl -X PATCH \
  "https://management.azure.com/subscriptions/<SUBSCRIPTION_ID>/providers/Microsoft.CognitiveServices/quotaTiers/default?api-version=2025-10-01-preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"properties": {"tierUpgradePolicy": "NoAutoUpgrade"}}'
```

### 手动申请更高配额

访问：https://aka.ms/oai/stuquotarequest

## 常见问题

| 问题 | 解答 |
|------|------|
| API 报 InvalidAuthenticationTokenTenant 错误？ | 确保 `az login --tenant` 使用订阅所属的租户 ID |
| 如何升级 Tier？ | 随使用量增长自动升级，或通过申请表手动请求 |
| EA 企业客户有优势吗？ | 是的，EA/MCA-E 客户会被分配更高的初始 Tier |
| 升级后会降级吗？ | 不会，已批准的配额不会被减少 |
| API 版本要求？ | 需使用 `2025-10-01-preview` 或更新版本 |

## 快速一行脚本

**PowerShell**：
```powershell
$sub="<SUBSCRIPTION_ID>"; $t=(az account get-access-token --resource https://management.azure.com -o tsv --query accessToken); (Invoke-RestMethod -Uri "https://management.azure.com/subscriptions/$sub/providers/Microsoft.CognitiveServices/quotaTiers/default?api-version=2025-10-01-preview" -Headers @{Authorization="Bearer $t"}).properties | Format-List
```

**Bash**：
```bash
SUB="<SUBSCRIPTION_ID>" && TOKEN=$(az account get-access-token --resource https://management.azure.com -o tsv --query accessToken) && curl -s "https://management.azure.com/subscriptions/$SUB/providers/Microsoft.CognitiveServices/quotaTiers/default?api-version=2025-10-01-preview" -H "Authorization: Bearer $TOKEN" | python -m json.tool
```
