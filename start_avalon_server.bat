@echo off
:: THE AXIOM: Macrocosm Startup Protocol v9.2.1 [Port-Master Edition]
:: วัตถุประสงค์: บังคับล้างพอร์ต 8000 และหน่วงเวลาเพื่อให้โปรเซสคลายตัว 100%

TITLE Avalon Hub Command Center - v9.2.1 [Strategic Orchestrator]
COLOR 0B

echo ========================================================
echo         THE AXIOM: AVALON HUB SYSTEM IGNITION
echo ========================================================

D:
cd "D:\Dev\kaytep\avalon_backend"

:: 1. ยุทธวิธีล้างพอร์ต: ค้นหาและทำลายโปรเซสที่ขวางทาง
echo [CLEAN] Purging zombie processes on Port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    if not "%%a"=="0" (
        echo [INFO] Terminating Process PID: %%a
        taskkill /F /PID %%a >nul 2>&1
    )
)

:: 2. หน่วงเวลาเชิงยุทธศาสตร์: ป้องกันสภาวะพอร์ตยังไม่คลายตัว
echo [WAIT] Waiting for Port 8000 to stabilize...
timeout /t 2 /nobreak >nul

:: 3. ตรวจสอบความพร้อม
if not exist "original_system_core_v9.py" (
    echo [ERROR] Macrocosm core file is missing!
    pause
    exit /b
)

:: 4. เริ่มปฏิบัติการ
echo [START] Launching Macrocosm Core v9.1.1 (Resilience Patch)...
echo --------------------------------------------------------

python original_system_core_v9.py

if %errorlevel% neq 0 (
    echo.
    echo [CRITICAL] Server execution failed with exit code %errorlevel%.
)
pause