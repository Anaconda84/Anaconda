@echo off
echo Shutting down servers...
taskkill /IM nginx.exe /F
taskkill /IM php-cgi.exe /F
taskkill /IM deluged.exe /F
taskkill /IM python.exe /F

rem net stop MySQL55
