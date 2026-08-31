# Fix Docker daemon: move data-root off Windows mount (9p breaks overlayfs in WSL)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "docker-config.ps1")

Write-Host "==> Fixing Docker daemon for WSL" -ForegroundColor Cyan

$fixScript = @'
set -e
if [ "$(id -u)" -ne 0 ]; then exec sudo bash -s "$@"; fi

# Fix iptables on WSL (nft backend missing addrtype match)
if command -v update-alternatives >/dev/null 2>&1; then
  update-alternatives --set iptables /usr/sbin/iptables-legacy 2>/dev/null || true
  update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy 2>/dev/null || true
fi

mkdir -p /etc/docker
cat >/etc/docker/daemon.json <<EOF
{
  "data-root": "/var/lib/docker",
  "registry-mirrors": [
    "https://docker.m.daocloud.io"
  ]
}
EOF

service docker stop 2>/dev/null || true
pkill dockerd 2>/dev/null || true
sleep 1
service docker start 2>/dev/null || nohup dockerd >/tmp/dockerd.log 2>&1 &
sleep 4

if docker info >/dev/null 2>&1; then
  echo "OK: Docker daemon running"
  docker --version
  docker compose version 2>/dev/null || true
else
  echo "FAILED: see /tmp/dockerd.log"
  tail -30 /tmp/dockerd.log 2>/dev/null || true
  exit 1
fi
'@

$fixScript = ($fixScript -replace "`r`n", "`n") -replace "`r", "`n"
$dockerRoot = Ensure-AeoDockerRoot
$path = Join-Path $dockerRoot "fix-docker-daemon.sh"
$wslMount = Get-AeoDockerWslMountPath
$utf8 = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllBytes($path, $utf8.GetBytes($fixScript))

wsl -d Ubuntu -e bash "$wslMount/fix-docker-daemon.sh"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Docker daemon fixed" -ForegroundColor Green
Write-Host "Next: cd aeo-platform && .\scripts\dev-up.ps1"
