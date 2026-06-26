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
if exist "C:\Windows\py.exe" (
    py server.py
) else if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe" (
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe" server.py
) else (
    python server.py
)

echo.
echo [!] Server berhenti atau terjadi error.
pause
