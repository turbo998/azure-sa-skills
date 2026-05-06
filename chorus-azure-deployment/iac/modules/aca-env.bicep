// Azure Container Apps managed environment + Azure Files (SMB) storage binding.
// The environment is in the "Consumption" workload profile (no dedicated nodes -> cheapest).

@description('Azure region.')
param location string

@description('Managed environment name.')
param name string

@description('Log Analytics workspace customer ID (GUID).')
param logAnalyticsCustomerId string

@description('Log Analytics primary shared key.')
@secure()
param logAnalyticsSharedKey string

@description('Storage account name that hosts the SMB file share. Required only when bindAzureFileStorage is true.')
param storageAccountName string = ''

@description('Storage account primary key (used for SMB mount). Required only when bindAzureFileStorage is true.')
@secure()
param storageAccountKey string = ''

@description('SMB file share name to bind to the environment. Required only when bindAzureFileStorage is true.')
param fileShareName string = ''

@description('Logical name of the storage definition exposed to container apps. Must be lowercase alphanumeric (with optional hyphens).')
param envStorageName string = 'chorusdata'

@description('Whether to attach an Azure Files SMB storage binding. Set false when subscription policy disables storage account local auth (in which case container apps must use ephemeral / EmptyDir volumes).')
param bindAzureFileStorage bool = true

@description('Resource tags applied to the managed environment.')
param tags object = {}

resource managedEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsSharedKey
      }
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
    zoneRedundant: false
  }
}

resource envStorage 'Microsoft.App/managedEnvironments/storages@2024-03-01' = if (bindAzureFileStorage) {
  parent: managedEnv
  name: envStorageName
  properties: {
    azureFile: {
      accountName: storageAccountName
      accountKey: storageAccountKey
      shareName: fileShareName
      accessMode: 'ReadWrite'
    }
  }
}

output environmentId string = managedEnv.id
output environmentName string = managedEnv.name
output defaultDomain string = managedEnv.properties.defaultDomain
output envStorageName string = bindAzureFileStorage ? envStorage.name : ''
