# Offline Ubuntu for WSL when wsl --install fails (error 0x80072ee7 = no Microsoft CDN)
# Requires: Administrator PowerShell

$ErrorActionPreference = "Stop"

$LogFile = "D:\Software\Docker\install.log"
$UbuntuDir = "D:\Software\Docker\wsl\ubuntu"
$TarFile = "D:\Software\Docker\ubuntu-rootfs.tar.gz"
$DistroName = "Ubuntu"
$MinSizeBytes = 100MB

$RootfsUrls = @(
    "https://cloud-images.ubuntu.com/wsl/jammy/current/ubuntu-jammy-wsl-amd64-ubuntu22.04lts.rootfs.tar.gz",
    "https://cloud-images.ubuntu.com/wsl/releases/24.04/current/ubuntu-noble-wsl-amd64-wsl.rootfs.tar.gz"
)

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
    Write-Host $Message -ForegroundColor $Color
}

function Test-ValidRootfs {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $false }
    return (Get-Item $Path).Length -ge $MinSizeBytes
}

New-Item -ItemType Directory -Force -Path "D:\Software\Docker" | Out-Null
New-Item -ItemType Directory -Force -Path $UbuntuDir | Out-Null

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)
if (-not $isAdmin) {
    Write-Log "ERROR: Run as Administrator." "Red"
    exit 1
}

Write-Log "==> Offline Ubuntu install for WSL" "Cyan"
Write-Log "    Target: $UbuntuDir" "Gray"

$existing = (wsl -l -q 2>&1 | ForEach-Object { $_.Trim() }) | Where-Object { $_ -like "Ubuntu*" }
if ($existing) {
    Write-Log "Ubuntu already registered: $($existing[0])" "Green"
    Read-Host "Press Enter to close" | Out-Null
    exit 0
}

if (-not (Test-ValidRootfs $TarFile)) {
    if (Test-Path $TarFile) {
        Write-Log "Removing invalid download ($(Get-Item $TarFile).Length bytes)" "Yellow"
        Remove-Item $TarFile -Force
    }

    $downloaded = $false
    foreach ($url in $RootfsUrls) {
        Write-Log "==> Downloading Ubuntu rootfs..." "Yellow"
        Write-Log "    URL: $url" "Gray"
        Write-Log "    File: $TarFile (about 330MB, several minutes)" "Gray"

        curl.exe -L --retry 3 --connect-timeout 30 -o $TarFile $url
        if ((Test-ValidRootfs $TarFile)) {
            $sizeMb = [math]::Round((Get-Item $TarFile).Length / 1MB, 1)
            Write-Log "    Downloaded: ${sizeMb} MB" "Green"
            $downloaded = $true
            break
        }
        Write-Log "    Download invalid, trying next mirror..." "Yellow"
        Remove-Item $TarFile -Force -ErrorAction SilentlyContinue
    }

    if (-not $downloaded) {
        Write-Log "" "White"
        Write-Log "Download failed. Manual steps:" "Yellow"
        Write-Log "  1. Download one of:" "White"
        foreach ($url in $RootfsUrls) { Write-Log "     $url" "Gray" }
        Write-Log "  2. Save as: $TarFile" "White"
        Write-Log "  3. Run this script again" "White"
        Read-Host "Press Enter to close" | Out-Null
        exit 2
    }
} else {
    $sizeMb = [math]::Round((Get-Item $TarFile).Length / 1MB, 1)
    Write-Log "Using existing rootfs: $TarFile (${sizeMb} MB)" "Gray"
}

Write-Log "==> Importing Ubuntu into WSL..." "Cyan"
wsl --import $DistroName $UbuntuDir $TarFile --version 2 2>&1 | ForEach-Object { Write-Log $_ "Gray" }
if ($LASTEXITCODE -ne 0) {
    Write-Log "wsl --import failed." "Red"
    Read-Host "Press Enter to close" | Out-Null
    exit 3
}

wsl --set-default $DistroName 2>&1 | Out-Null
$probe = wsl -d $DistroName -e bash -lc "echo ok" 2>&1
if ($probe -match "ok") {
    Write-Log "==> Ubuntu imported successfully!" "Green"
    Write-Log "Next: run install-docker-admin.cmd to install Docker Engine" "Cyan"
} else {
    Write-Log "Import done but probe failed: $probe" "Yellow"
}

Read-Host "Press Enter to close" | Out-Null
exit 0
