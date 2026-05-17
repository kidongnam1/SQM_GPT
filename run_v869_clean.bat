@echo off
chcp 65001 > nul
setlocal
cd /d "%~dp0"

title SQM Inventory V869 CLEAN

echo.
echo ====================================================
echo  SQM Inventory V869 CLEAN - canonical launcher
echo ====================================================
echo  ROOT  : %CD%
echo  ENTRY : main_webview.py
echo  PORT  : http://127.0.0.1:8765
echo ====================================================
echo.

python main_webview.py

if errorlevel 2 (
    echo.
    echo [ERROR] 실행 실패. 아래를 확인하세요:
    echo   1. Python 설치 여부     ^(python --version^)
    echo   2. 의존성 설치 여부     ^(pip install -r requirements_webview.txt^)
    pause
)
endlocal
