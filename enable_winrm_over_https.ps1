Set-StrictMode -Version Latest
$ErrorActionPreference = [System.Management.Automation.ActionPreference]::Stop

$caFilePath = $NULL
Get-ChildItem -Path ".\" -Filter "*.crt" -File | ForEach-Object {
  $caFilePath = $_.FullName
} # ForEach-Object
if ($NULL -eq $caFilePath)
  { throw "Coulnd't find any *.crt files in current directory" }
Write-Output ("Using '{0}' as root CA" -f $caFilePath)

$hostCertFilePath = $NULL
Get-ChildItem -Path ".\" -Filter "*.p12" -File | ForEach-Object {
  $hostCertFilePath = $_.FullName
} # ForEach-Object
if ($NULL -eq $hostCertFilePath)
  { throw "Coulnd't find any *.p12 files in current directory" }
Write-Output ("Using '{0}' as host's certificate" -f $hostCertFilePath)

$installedCACert = Get-ChildItem "Cert:\LocalMachine\Root" | Where-Object {
  $_.Thumbprint -eq (New-Object System.Security.Cryptography.X509Certificates.X509Certificate2 $caFilePath).Thumbprint
}
if ($NULL -eq $installedCACert) {
  Write-Output "Importing CA file"
  $installedCACert = Import-Certificate -FilePath $caFilePath -CertStoreLocation "Cert:\LocalMachine\Root"
} #if
Write-Output "Root CA info:"
Write-Output ("Subject: {0}, Thumbprint: {1}" -f $installedCACert.Subject, $installedCACert.Thumbprint)

$installedHostCert = Get-ChildItem "Cert:\LocalMachine\My" | Where-Object {
  $_.Thumbprint -eq (Get-PfxCertificate -File $hostCertFilePath).Thumbprint
}
if ($NULL -eq $installedHostCert) {
  Write-Output "Importing host's certificate"
  $installedHostCert = Import-PfxCertificate -FilePath $hostCertFilePath -CertStoreLocation "Cert:\LocalMachine\My" -Exportable
} #if
Write-Output "Host's certificate info:"
Write-Output ("Subject: {0}, Thumbprint: {1}" -f $installedHostCert.Subject, $installedHostCert.Thumbprint)
