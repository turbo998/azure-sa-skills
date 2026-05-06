// Container App that runs the Chorus image.
// - Single replica (PGlite is single-process, embedded in the container).
// - SMB Azure Files volume mounted at /app/data so PGlite data persists across restarts.
// - External HTTPS ingress on port 8637 (ACA terminates TLS automatically).

@description('Azure region.')
param location string

@description('Container app name.')
param name string

@description('Resource ID of the Azure Container Apps managed environment.')
param environmentId string

@description('Default domain of the managed environment (e.g. <random>.<region>.azurecontainerapps.io).')
param environmentDefaultDomain string

@description('Logical storage name registered on the managed environment. Only used when volumeMode == azureFile.')
param environmentStorageName string = ''

@description('Persistent volume backing for /app/data. "azureFile" mounts the SMB share defined on the env. "emptyDir" uses node-local ephemeral storage (data lost on revision change but kept across container restarts within a replica). Choose emptyDir if your subscription policy blocks storage account shared-key auth.')
@allowed([
  'azureFile'
  'emptyDir'
])
param volumeMode string = 'azureFile'

@description('Container image reference. Defaults to the published Chorus image at the version that has been validated for this template.')
param image string = 'chorusaidlc/chorus-app:v0.7.1'

@description('Email address of the bootstrap admin user (Chorus auto-provisions on first login).')
param defaultUser string = 'admin@example.com'

@description('Password for the bootstrap admin user. Compared via bcrypt at runtime.')
@secure()
param defaultPassword string

@description('Secret used by NextAuth to sign session JWTs. Generate via: [Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Max 256 } | ForEach-Object { [byte]$_ })).')
@secure()
param nextAuthSecret string

@description('Optional: fix the public hostname Chorus will use for OAuth/redirect callbacks. Defaults to https://<name>.<environmentDefaultDomain>.')
param nextAuthUrl string = 'https://${name}.${environmentDefaultDomain}'

@description('CPU cores per replica.')
param cpu string = '1.0'

@description('Memory per replica.')
param memory string = '2.0Gi'

@description('Mount path inside the container for the persistent volume.')
param dataMountPath string = '/app/data'

@description('Minimum/maximum replica count. Pinned to 1/1 because the embedded PGlite database cannot run in multiple replicas.')
@allowed([
  1
])
param replicaCount int = 1

@description('Optional list of IP CIDR ranges allowed to reach the public ingress. Empty array = open to internet (default).')
param allowedSourceIps array = []

@description('Resource tags applied to the container app.')
param tags object = {}

var ipSecurityRestrictions = [for (ip, idx) in allowedSourceIps: {
  name: 'allow-${idx}'
  description: 'Allow inbound from configured operator range'
  ipAddressRange: ip
  action: 'Allow'
}]

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    environmentId: environmentId
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8637
        transport: 'auto'
        allowInsecure: false
        ipSecurityRestrictions: empty(allowedSourceIps) ? null : ipSecurityRestrictions
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      secrets: [
        {
          name: 'nextauth-secret'
          value: nextAuthSecret
        }
        {
          name: 'default-password'
          value: defaultPassword
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'chorus'
          image: image
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: [
            {
              name: 'NEXTAUTH_URL'
              value: nextAuthUrl
            }
            {
              name: 'NEXTAUTH_SECRET'
              secretRef: 'nextauth-secret'
            }
            {
              name: 'COOKIE_SECURE'
              value: 'true'
            }
            {
              name: 'DEFAULT_USER'
              value: defaultUser
            }
            {
              name: 'DEFAULT_PASSWORD'
              secretRef: 'default-password'
            }
            {
              name: 'LOG_LEVEL'
              value: 'info'
            }
          ]
          volumeMounts: [
            {
              volumeName: 'data'
              mountPath: dataMountPath
            }
          ]
          probes: [
            {
              type: 'Startup'
              tcpSocket: {
                port: 8637
              }
              initialDelaySeconds: 10
              periodSeconds: 10
              timeoutSeconds: 5
              // Allow up to ~5 minutes for first-boot Prisma migrations on a cold PGlite share.
              failureThreshold: 30
            }
            {
              type: 'Readiness'
              tcpSocket: {
                port: 8637
              }
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: replicaCount
        maxReplicas: replicaCount
      }
      volumes: [
        volumeMode == 'azureFile' ? {
          name: 'data'
          storageType: 'AzureFile'
          storageName: environmentStorageName
        } : {
          name: 'data'
          storageType: 'EmptyDir'
        }
      ]
    }
  }
}

output appName string = app.name
output appFqdn string = app.properties.configuration.ingress.fqdn
output appUrl string = 'https://${app.properties.configuration.ingress.fqdn}'
