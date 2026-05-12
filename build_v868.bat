@echo off
chcp 65001 > nul
echo ============================================================
echo  SQM v8.6.8 EXE Build
echo ============================================================
cd /d "%~dp0"

echo [Gate 1] pytest...
python -m pytest tests\test_smoke_workflow.py tests\test_ai_fallback_router.py tests\test_ai_fallback_parity.py -x -q
if errorlevel 1 ( echo [FAIL] pytest 실패. 빌드 중단. & pause & exit /b 1 )
echo [Gate 1] PASS

echo [Gate 2] 구문 검사...
python -m py_compile main_webview.py backend\api\inbound.py version.py
if errorlevel 1 ( echo [FAIL] py_compile & pause & exit /b 1 )
node --check frontend\js\sqm-inline.js frontend\js\sqm-inventory.js
if errorlevel 1 ( echo [FAIL] node --check & pause & exit /b 1 )
echo [Gate 2] PASS

echo [Build] PyInstaller...
pyinstaller SQM_v868.spec --clean --noconfirm
if errorlevel 1 ( echo [FAIL] 빌드 실패 & pause & exit /b 1 )

echo ============================================================
echo  완료: dist\SQM_v868.exe
echo ============================================================
pause
