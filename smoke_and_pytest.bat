@echo off
chcp 65001 > nul
echo ============================================================
echo  SQM v8.6.8 smoke_and_pytest
echo ============================================================
cd /d "%~dp0"

echo [1] py_compile...
python -m py_compile main_webview.py backend\api\inbound.py version.py
if errorlevel 1 ( echo FAIL & pause & exit /b 1 )
echo PASS

echo [2] node --check...
node --check frontend\js\sqm-inline.js frontend\js\sqm-inventory.js
if errorlevel 1 ( echo FAIL & pause & exit /b 1 )
echo PASS

echo [3] pytest...
python -m pytest tests\test_smoke_workflow.py tests\test_ai_fallback_router.py tests\test_ai_fallback_parity.py tests\test_ai_fallback_policy.py -v 2>&1 | tee pytest_output.txt
if errorlevel 1 (
    echo [3] pytest 실패 -- auto_hotfix 실행
    python auto_hotfix.py pytest_output.txt
) else (
    echo [3] PASS
)

echo [4] H-7 진단...
python auto_hotfix.py

echo ============================================================
echo  완료. 빌드 준비: build_v868.bat
echo ============================================================
pause
