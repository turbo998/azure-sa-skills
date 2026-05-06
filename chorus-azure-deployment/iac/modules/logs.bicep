// Log Analytics workspace for Azure Container Apps environment logs.
// Uses PerGB2018 (pay-per-GB) which has the best signal/cost for low-traffic test workloads.

@description('Azure region.')
param location string

@description('Workspace name (must be unique within the resource group).')
param name string

@description('Retention in days. 30 is the default free-tier retention.')
@minValue(30)
@maxValue(730)
param retentionInDays int = 30

@description('Resource tags applied to the workspace.')
param tags object = {}

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: retentionInDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

output workspaceId string = workspace.id
output customerId string = workspace.properties.customerId
@description('Primary shared key — consumers should treat as a secret.')
@secure()
output primarySharedKey string = workspace.listKeys().primarySharedKey
