@echo off
title THE AXIOM - Backend Setup Protocol
color 0B

echo ========================================================
echo       THE AXIOM: Dependency Installation Protocol
echo ========================================================
echo.
echo Target Directory: D:\Dev\kaytep\avalon_backend
echo.

:: ย้ายไปยังไดร์ฟ D และเข้าสู่โฟลเดอร์เป้าหมาย
D:
cd "D:\Dev\kaytep\avalon_backend"

echo [1/3] Upgrading PIP to the latest version...
python -m pip install --upgrade pip

echo.
echo [2/3] Installing Core Libraries from requirements.txt...
pip install -r requirements.txt

echo.
echo [3/3] Installing Playwright Chromium Engine...
playwright install chromium

echo.
echo ========================================================
echo   SYSTEM READY: All modules installed successfully.
echo ========================================================
pause