# Central Docker paths for AEO Platform Windows scripts.
# Override: set env AEO_DOCKER_ROOT to a custom directory.

$ErrorActionPreference = "Stop"

function Get-AeoDockerRoot {
    if ($env:AEO_DOCKER_ROOT) {
        return $env:AEO_DOCKER_ROOT.TrimEnd('\', '/')
    }
    return Join-Path $env:LOCALAPPDATA "aeo-platform\docker"
}

function Get-AeoDockerDataRoot {
    return Join-Path (Get-AeoDockerRoot) "wsl\data"
}

function Get-AeoDockerLogFile {
    return Join-Path (Get-AeoDockerRoot) "install.log"
}

function Get-AeoDockerWslMountPath {
    $root = (Get-AeoDockerRoot).TrimEnd('\')
    if ($root -match '^([A-Za-z]):\\(.*)$') {
        $drive = $Matches[1].ToLower()
        $rest = $Matches[2] -replace '\\', '/'
        return "/mnt/$drive/$rest"
    }
    throw "Unsupported AEO_DOCKER_ROOT (expected Windows drive path): $root"
}

function Ensure-AeoDockerRoot {
    $root = Get-AeoDockerRoot
    New-Item -ItemType Directory -Force -Path $root | Out-Null
    New-Item -ItemType Directory -Force -Path (Get-AeoDockerDataRoot) | Out-Null
    return $root
}
