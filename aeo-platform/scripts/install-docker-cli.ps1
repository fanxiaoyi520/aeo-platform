# Install Docker Engine (CLI only) in WSL Ubuntu — NO Docker Desktop
# Data root: D:\Software\Docker\wsl\data

$ErrorActionPreference = "Stop"

$DataRoot = "D:\Software\Docker\wsl\data"
$LogFile = "D:\Software\Docker\install.log"

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
    Write-Host $Message -ForegroundColor $Color
}

New-Item -ItemType Directory -Force -Path "D:\Software\Docker" | Out-Null
New-Item -ItemType Directory -Force -Path $DataRoot | Out-Null
Set-Content -Path $LogFile -Value "=== Install started $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===" -Encoding UTF8

Write-Log "==> AEO Platform - Docker CLI (WSL, no Desktop)" "Cyan"
Write-Log "    Script: $PSCommandPath"
Write-Log "    Data root: $DataRoot"
Write-Log ""

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)
if (-not $isAdmin) {
    Write-Log "ERROR: Not running as Administrator." "Red"
    exit 1
}

function Get-WslDistroNames {
    $names = New-Object System.Collections.Generic.List[string]
    $raw = (wsl -l -v 2>&1 | Out-String)
    Write-Log "WSL list output captured ($($raw.Length) chars)" "Gray"

    foreach ($line in ($raw -split "`r?`n")) {
        $t = $line.Trim()
        if ($t -match "^(Ubuntu|Debian|docker-desktop|kali|openSUSE)") {
            $names.Add(($t -split "\s+")[0])
        }
    }

    if ($names.Count -eq 0) {
        foreach ($line in (wsl -l -q 2>&1)) {
            $t = ($line -replace "`0", "").Trim()
            if ($t -and $t -notmatch "http|Store|wslstore") {
                $names.Add($t)
            }
        }
    }

    return @($names | Select-Object -Unique)
}

function Convert-ToWslPath {
    param(
        [Parameter(Mandatory = $true)][string]$Distro,
        [Parameter(Mandatory = $true)][string]$WindowsPath
    )
    $normalized = ($WindowsPath -replace "\\", "/")
    $result = wsl -d $Distro -- wslpath -a $normalized 2>&1
    if ($LASTEXITCODE -ne 0) {
        return ($result | Out-String).Trim()
    }
    return ($result | Out-String).Trim()
}

function Test-WslFeature {
    try {
        $wsl = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -ErrorAction Stop
        $vm = Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -ErrorAction Stop
        return ($wsl.State -eq "Enabled") -and ($vm.State -eq "Enabled")
    } catch {
        return $false
    }
}

if (-not (Test-WslFeature)) {
    Write-Log "==> Enabling WSL + VirtualMachinePlatform..." "Yellow"
    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
    Write-Log "    Features enabled. REBOOT may be required." "Yellow"
}

# Skip wsl --update: hangs on older WSL / no Store access on this machine.
Write-Log "==> Skipping wsl --update (known to hang on this host)" "Yellow"
Write-Log "    If Ubuntu install fails, run manually: wsl --install -d Ubuntu" "Gray"

$distros = Get-WslDistroNames
$activeDistro = $distros | Where-Object { $_ -like "Ubuntu*" } | Select-Object -First 1

if (-not $activeDistro) {
    Write-Log "==> No Ubuntu distro found. Installing Ubuntu (online)..." "Yellow"
    $installOut = wsl --install -d Ubuntu 2>&1 | Out-String
    $installOut -split "`r?`n" | Where-Object { $_.Trim() } | ForEach-Object { Write-Log $_ "Gray" }

    $distros = Get-WslDistroNames
    $activeDistro = $distros | Where-Object { $_ -like "Ubuntu*" } | Select-Object -First 1

    if (-not $activeDistro) {
        if ($installOut -match "80072ee7|80072EE7") {
            Write-Log "Online install failed: 0x80072ee7 (cannot reach Microsoft CDN)" "Yellow"
            Write-Log "==> Trying offline Ubuntu import from cloud-images.ubuntu.com..." "Cyan"
            $offlineScript = Join-Path $PSScriptRoot "install-ubuntu-offline.ps1"
            if (Test-Path $offlineScript) {
                & $offlineScript
                $distros = Get-WslDistroNames
                $activeDistro = $distros | Where-Object { $_ -like "Ubuntu*" } | Select-Object -First 1
            }
        }
    }

    if (-not $activeDistro) {
        Write-Log "" "White"
        Write-Log "Ubuntu not ready. Options:" "Yellow"
        Write-Log "  A. Fix network/proxy, then run install-docker-admin.cmd again" "White"
        Write-Log "  B. Run as admin: .\scripts\install-ubuntu-offline.ps1" "White"
        Write-Log "     (downloads from ubuntu.com instead of Microsoft Store)" "White"
        Write-Log "" "White"
        Write-Host "Press Enter to close..." -ForegroundColor Gray
        Read-Host | Out-Null
        exit 2
    }
}

Write-Log "==> Using WSL distro: $activeDistro" "Cyan"

$probe = wsl -d $activeDistro -e bash -lc "echo ok" 2>&1
if ($LASTEXITCODE -ne 0 -or ($probe -join " ") -notmatch "ok") {
    Write-Log "Ubuntu not initialized. Open Ubuntu from Start menu and set user/password." "Yellow"
    Write-Log "Probe output: $probe" "Gray"
    Write-Host "Press Enter to close..." -ForegroundColor Gray
    Read-Host | Out-Null
    exit 3
}

Write-Log "==> Installing Docker Engine inside WSL..." "Cyan"

$wslDataPath = Convert-ToWslPath -Distro $activeDistro -WindowsPath $DataRoot
if (-not $wslDataPath -or $wslDataPath -match "error|No such") {
    Write-Log "ERROR: Cannot map data path: $DataRoot -> $wslDataPath" "Red"
    Read-Host "Press Enter to close" | Out-Null
    exit 4
}

$bashScript = @'
set -e
export DEBIAN_FRONTEND=noninteractive
DATA_ROOT="__DATA_ROOT__"
APT_OPTS="-o DPkg::Lock::Timeout=120"

if [ "$(id -u)" -eq 0 ]; then SUDO=""; else SUDO="sudo"; fi

wait_for_apt() {
  echo ">>> Waiting for apt lock (if another install is running)..."
  for i in $(seq 1 90); do
    if ! fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 \
      && ! fuser /var/lib/apt/lists/lock >/dev/null 2>&1 \
      && ! fuser /var/lib/dpkg/lock >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "ERROR: apt is still locked after 3 minutes. Close other apt windows or reboot WSL:"
  echo "  wsl -d Ubuntu -e bash -lc 'sudo killall apt apt-get dpkg 2>/dev/null; sudo dpkg --configure -a'"
  exit 1
}

wait_for_apt

if ! command -v docker >/dev/null 2>&1; then
  echo ">>> Installing Docker Engine via apt (WSL, no Desktop)..."
  $SUDO apt-get $APT_OPTS update -qq
  $SUDO apt-get $APT_OPTS install -y ca-certificates curl gnupg lsb-release
  $SUDO install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | $SUDO gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  $SUDO chmod a+r /etc/apt/keyrings/docker.gpg
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" | $SUDO tee /etc/apt/sources.list.d/docker.list >/dev/null
  $SUDO apt-get $APT_OPTS update -qq
  $SUDO apt-get $APT_OPTS install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
  echo ">>> Docker already installed:"
  docker --version
fi

if ! docker compose version >/dev/null 2>&1; then
  echo ">>> Installing docker-compose-plugin..."
  wait_for_apt
  $SUDO apt-get $APT_OPTS update -qq
  $SUDO apt-get $APT_OPTS install -y docker-compose-plugin
fi

$SUDO mkdir -p "$DATA_ROOT"
# Docker data must live on native Linux FS (not /mnt/d — overlayfs breaks on 9p)
DOCKER_ROOT="/var/lib/docker"
$SUDO mkdir -p "$DOCKER_ROOT"
$SUDO tee /etc/docker/daemon.json >/dev/null <<EOF
{
  "data-root": "$DOCKER_ROOT"
}
EOF

$SUDO service docker restart 2>/dev/null || $SUDO service docker start
if id docker >/dev/null 2>&1; then $SUDO usermod -aG docker "$USER" 2>/dev/null || true; fi

echo ""
echo ">>> Docker CLI ready:"
docker --version
docker compose version 2>/dev/null || docker compose --version 2>/dev/null || true
'@

$bashScript = $bashScript.Replace("__DATA_ROOT__", $wslDataPath)
$bashScript = ($bashScript -replace "`r`n", "`n") -replace "`r", "`n"
$installSh = "D:\Software\Docker\docker-install.sh"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllBytes($installSh, $utf8NoBom.GetBytes($bashScript))
$wslScript = Convert-ToWslPath -Distro $activeDistro -WindowsPath $installSh

wsl -d $activeDistro -e bash $wslScript 2>&1 | ForEach-Object { Write-Log $_ "Gray" }
$dockerOk = wsl -d $activeDistro -e bash -lc "docker --version" 2>&1
if ($LASTEXITCODE -ne 0 -or $dockerOk -notmatch "Docker version") {
    Write-Log "Docker install failed. See: $LogFile" "Red"
    Read-Host "Press Enter to close" | Out-Null
    exit 5
}

Write-Log ""
Write-Log "==> Docker CLI installed successfully!" "Green"
Write-Log "Verify: wsl -d $activeDistro docker --version" "Cyan"
Write-Log "Then run dev-up.ps1 in aeo-platform folder" "Cyan"
Write-Host ""
Write-Host "Press Enter to close..." -ForegroundColor Gray
Read-Host | Out-Null
exit 0
