@echo off
winget install python3
:CHECK_PIP
pip --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo pip no esta disponible. Instalando Python...
    timeout /t 2 /nobreak >nul
    GOTO CHECK_PIP
)
pip install Flask --upgrade
