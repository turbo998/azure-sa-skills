// Storage account + SMB Azure Files share used as the persistent volume for Chorus's embedded
// PGlite database. Standard_LRS keeps the cost minimal; SMB avoids the VNet/private-endpoint
// requirement that NFS shares would impose.

@description('Azure region.')
param location string

@description('Storage account name (3-24 chars, lowercase letters and digits only, globally unique).')
@minLength(3)
@maxLength(24)
param storageAccountName string

@description('Name of the Azure Files share that will be mounted to /app/data inside the container.')
param fileShareName string = 'chorus-data'

@description('File share quota in GiB. SMB Standard_LRS is billed by *used* capacity, so this is just an upper bound.')
@minValue(1)
@maxValue(102400)
param shareQuotaGiB int = 100

@description('Resource tags applied to the storage account.')
param tags object = {}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowSharedKeyAccess: true
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }
}

resource fileServices 'Microsoft.Storage/storageAccounts/fileServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {}
}

resource share 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-05-01' = {
  parent: fileServices
  name: fileShareName
  properties: {
    enabledProtocols: 'SMB'
    accessTier: 'TransactionOptimized'
    shareQuota: shareQuotaGiB
  }
}

output storageAccountId string = storage.id
output storageAccountName string = storage.name
output fileShareName string = share.name
@description('Storage account primary key — used by the ACA managed environment to mount the share. Treat as secret.')
@secure()
output accountKey string = storage.listKeys().keys[0].value
