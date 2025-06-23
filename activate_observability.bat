@echo off
REM Claude Code Observability Environment Activation Script
echo 🚀 Activating Claude Code observability environment...
call venv_observability\Scripts\activate.bat
echo ✅ Environment activated! You can now run:
echo   - make start-logger
echo   - make generate-cost-report
echo   - make generate-user-report
echo   - make test-observability
echo.
echo To deactivate: deactivate
