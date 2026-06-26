@echo off
title MT5 Trading Dashboard Server
cd /d "%~dp0"
cls
echo ======================================================================
echo MT5 DIRECT TECHNICAL ANALYZER DASHBOARD
echo ======================================================================

echo [*] Membangunkan aplikasi MetaTrader 5 Terminal...
if exist "C:\Program Files\MetaTrader 5\terminal64.exe" (
    start "" "C:\Program Files\MetaTrader 5\terminal64.exe"
)

echo [*] Menjalankan server lokal dan membuka browser...

if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" server.py
    goto :end
)
if exist "%USERPROFILE%\AppData\Local\Programs\Python\Python313\python.exe" (
    "%USERPROFILE%\AppData\Local\Programs\Python\Python313\python.exe" server.py
    goto :end
)
where py >nul 2>nul
if not errorlevel 1 (
    py server.py
    goto :end
)
python server.py

:end
echo.
echo [!] Server berhenti atau keluar.
pause
