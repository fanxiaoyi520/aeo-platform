# Check WSL + Docker CLI install status

$ErrorActionPreference = "SilentlyContinue"

Write-Host "==> Docker CLI status" -ForegroundColor Cyan
Write-Host ""

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)
if ($isAdmin) {
    Write-Host "Admin PowerShell: YES"
} else {
    Write-Host "Admin PowerShell: NO - install requires administrator"
}

Write-Host ""
Write-Host "D:\Software\Docker:" -ForegroundColor Cyan
$paths = @(
    "D:\Software\Docker",
    "D:\Software\Docker\wsl\data",
    "D:\Software\Docker\install.log"
)
foreach ($p in $paths) {
    if (Test-Path $p) {
        Write-Host "  [OK] $p"
    } else {
        Write-Host "  [--] $p"
    }
}

Write-Host ""
Write-Host "WSL distros:" -ForegroundColor Cyan
$wslOut = wsl -l -v 2>&1 | Out-String
if ($wslOut -match "wslstore|Store") {
    Write-Host "  NOT INSTALLED - need WSL and Ubuntu" -ForegroundColor Yellow
} else {
    wsl -l -v
}

Write-Host ""
Write-Host "Docker CLI:" -ForegroundColor Cyan
if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker --version
    docker compose version
} else {
    $distro = wsl -l -q 2>$null | Where-Object { $_ -like "Ubuntu*" } | Select-Object -First 1
    if ($distro) {
        wsl -d $distro -e bash -lc "docker --version; docker compose version" 2>&1
    } else {
        Write-Host "  NOT FOUND" -ForegroundColor Yellow
    }
}

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Right-click PowerShell -> Run as administrator"
Write-Host "  2. cd $root"
Write-Host "  3. .\scripts\install-docker-cli.ps1"
