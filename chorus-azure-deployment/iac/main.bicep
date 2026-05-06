// Chorus on Azure — single-instance test deployment.
//
// Components:
//   - Log Analytics workspace (ACA log sink)
//   - Storage account + SMB Azure Files share (persistent volume for embedded PGlite)
//   - Container Apps managed environment (Consumption profile)
//   - Container app running chorusaidlc/chorus-app
//
// Deploy with:
//   az deployment group create -g <rg> -f main.bicep -p main.parameters.json \
//      -p nextAuthSecret=<random> defaultPassword=<password>

targetScope = 'resourceGroup'

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Short, lowercase prefix used to derive resource names. 3-11 chars, [a-z0-9]. Avoid reserved words.')
@minLength(3)
@maxLength(11)
param namePrefix string = 'chorus'

@description('Image tag to deploy. Pin to a specific version for reproducibility; "latest" works but drifts.')
param imageTag string = 'v0.7.1'

@description('Email address of the bootstrap admin user.')
param defaultUser string = 'admin@example.com'

@description('Password for the bootstrap admin user. Compared via bcrypt at runtime.')
@secure()
param defaultPassword string

@description('Secret used by NextAuth to sign session cookies. Use a 32-byte random value.')
@secure()
param nextAuthSecret string

@description('File share quota in GiB. SMB Standard storage is billed by used capacity, so this is only an upper bound.')
@minValue(1)
@maxValue(102400)
param shareQuotaGiB int = 100

@description('Persistent volume backing for /app/data. "azureFile" requires the storage account to allow shared-key access (some subscription policies block this). "emptyDir" uses node-local ephemeral storage (data is preserved across container restarts but lost on revision change).')
@allowed([
  'azureFile'
  'emptyDir'
])
param volumeMode string = 'azureFile'

@description('Optional list of IP CIDR ranges allowed to access the public ingress. Empty = open to the internet.')
param allowedSourceIps array = []

@description('Resource tags applied to all resources for cost attribution and cleanup.')
param tags object = {
  app: 'chorus'
  env: 'test'
  managedBy: 'bicep'
}

// Storage account names must be globally unique; mix prefix + RG-scoped uniqueString.
var storageAccountName = toLower(replace('${namePrefix}${uniqueString(resourceGroup().id)}', '-', ''))
var truncatedStorageName = length(storageAccountName) > 24 ? substring(storageAccountName, 0, 24) : storageAccountName

var logsName = '${namePrefix}-logs'
var envName = '${namePrefix}-env'
var appName = namePrefix

module logs 'modules/logs.bicep' = {
  name: 'logs'
  params: {
    location: location
    name: logsName
    tags: tags
  }
}

module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    location: location
    storageAccountName: truncatedStorageName
    fileShareName: 'chorus-data'
    shareQuotaGiB: shareQuotaGiB
    tags: tags
  }
}

module acaEnv 'modules/aca-env.bicep' = {
  name: 'aca-env'
  params: {
    location: location
    name: envName
    logAnalyticsCustomerId: logs.outputs.customerId
    logAnalyticsSharedKey: logs.outputs.primarySharedKey
    bindAzureFileStorage: volumeMode == 'azureFile'
    storageAccountName: storage.outputs.storageAccountName
    storageAccountKey: storage.outputs.accountKey
    fileShareName: storage.outputs.fileShareName
    envStorageName: 'chorusdata'
    tags: tags
  }
}

module acaApp 'modules/aca-app.bicep' = {
  name: 'aca-app'
  params: {
    location: location
    name: appName
    environmentId: acaEnv.outputs.environmentId
    environmentDefaultDomain: acaEnv.outputs.defaultDomain
    environmentStorageName: acaEnv.outputs.envStorageName
    volumeMode: volumeMode
    image: 'chorusaidlc/chorus-app:${imageTag}'
    defaultUser: defaultUser
    defaultPassword: defaultPassword
    nextAuthSecret: nextAuthSecret
    allowedSourceIps: allowedSourceIps
    tags: tags
  }
}

@description('Public HTTPS URL of the Chorus instance.')
output appUrl string = acaApp.outputs.appUrl

@description('Storage account hosting the PGlite data volume. Empty when volumeMode != azureFile.')
output storageAccount string = volumeMode == 'azureFile' ? storage.outputs.storageAccountName : ''

@description('ACA managed environment name.')
output environment string = acaEnv.outputs.environmentName
