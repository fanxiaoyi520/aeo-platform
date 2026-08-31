@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "SRC=%~dp0install-docker-cli.ps1"
set "DST=D:\Software\Docker\install-docker-cli.ps1"

echo ========================================
echo  AEO Platform - Docker CLI Installer
echo  Data: D:\Software\Docker\wsl\data
echo ========================================
echo.

if not exist "D:\Software\Docker" mkdir "D:\Software\Docker"
copy /Y "%SRC%" "%DST%" >nul
if errorlevel 1 (
    echo ERROR: Cannot copy installer to D:\Software\Docker
    pause
    exit /b 1
)

echo Requesting administrator privileges...
echo If UAC appears, click YES.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$code = 1; try { $p = Start-Process powershell -Verb RunAs -Wait -PassThru -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-NoExit','-File','D:\Software\Docker\install-docker-cli.ps1'); if ($p) { $code = $p.ExitCode } } catch { Write-Host $_.Exception.Message -ForegroundColor Red }; exit $code"

set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
    echo [SUCCESS] Docker CLI install completed.
    echo Log: D:\Software\Docker\install.log
) else (
    echo [FAILED] Exit code: %RC%
    echo Check the admin PowerShell window and:
    echo   D:\Software\Docker\install.log
)
echo.
pause
exit /b %RC%
