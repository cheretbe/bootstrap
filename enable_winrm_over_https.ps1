[CmdletBinding()]
param(
  [switch]$KeepHTTP
)

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

$httpListener = Get-ChildItem WSMan:\Localhost\listener | Where-Object { $_.Keys -contains "Transport=HTTP" }
$httpsListener = Get-ChildItem WSMan:\Localhost\listener | Where-Object { $_.Keys -contains "Transport=HTTPS" }
if (($NULL -eq $httpListener) -and ($NULL -eq $httpsListener))
  { Enable-PSRemoting }

if ($NULL -eq $httpsListener) {
  Write-Output "Enabling HTTPS listener"
  New-Item -Path WSMan:\LocalHost\Listener -Transport HTTPS -Address * `
    -CertificateThumbPrint $installedHostCert.Thumbprint -Force | Out-Null
} #if

if ($NULL -eq (Get-NetFirewallRule -Name "WINRM-HTTPS-In-TCP-NoScope" -ErrorAction SilentlyContinue)) {
  Write-Output "Adding firewall rule for WinRM over HTTPS"
  if ((Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Nls\Language").InstallLanguage -eq "0419") {
    $fwDisplayName = "��������� ���������� Windows (HTTPS - �������� ������)"
    $fwDescription = "������� ��������� ������� ��� ���������� ���������� Windows ����� WS-Management. [TCP 5986]"
  } else {
    $fwDisplayName = "Windows Remote Management (HTTPS-In)"
    $fwDescription = "Inbound rule for Windows Remote Management via WS-Management. [TCP 5986]"
  } #if
  (
    New-NetFirewallRule -Name 'WINRM-HTTPS-In-TCP-NoScope'-DisplayName $fwDisplayName `
      -Group '@FirewallAPI.dll,-30267' -Description $fwDescription -Profile Any `
      -LocalPort 5986 -Protocol TCP
  ) | Out-Null
} #if

if (-not($KeepHTTP.IsPresent)) {
  if ($httpListener) {
    Write-Output "Disabling HTTP listener"
    $httpListener | Remove-Item -Recurse
  } #if
  $fwEnabled = [Microsoft.PowerShell.Cmdletization.GeneratedTypes.NetSecurity.Enabled]::True
  if ((Get-NetFirewallRule -Name "WINRM-HTTP-In-TCP-NoScope").Enabled -eq $fwEnabled) {
    Write-Output "Disabling firewall rule for WinRM over HTTP"
    Disable-NetFirewallRule -Name "WINRM-HTTP-In-TCP-NoScope"
  } #if
} #if
