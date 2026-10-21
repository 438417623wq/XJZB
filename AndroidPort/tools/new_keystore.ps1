# Regenerates the personal release keystore consumed by app/app/build.gradle.kts.
# A new key means Android refuses an in-place update over a build signed with
# the old one, so uninstall first. Credentials match the signingConfig block.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$ks = Join-Path $root "signing/xjzb-release.jks"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ks) | Out-Null
if (Test-Path $ks) { throw "$ks already exists; delete it first if you really want a new key." }
& keytool -genkeypair -v -keystore $ks -alias xjzb -keyalg RSA -keysize 2048 `
    -validity 10000 -storepass xjzb2026 -keypass xjzb2026 `
    -dname "CN=XJZB AndroidPort, OU=Personal, O=XJZB, C=CN"
Write-Host "wrote $ks"
