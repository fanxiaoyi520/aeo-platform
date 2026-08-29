@echo off
setlocal
chcp 65001 >nul
echo Offline Ubuntu install (when Microsoft Store/CDN unreachable)
copy /Y "%~dp0install-ubuntu-offline.ps1" "D:\Software\Docker\install-ubuntu-offline.ps1" >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -Verb RunAs -Wait -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-NoExit','-File','D:\Software\Docker\install-ubuntu-offline.ps1')"
pause
