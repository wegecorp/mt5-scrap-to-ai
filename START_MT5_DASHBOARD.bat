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
python server.py

echo.
echo [!] Server berhenti atau terjadi error.
pause
