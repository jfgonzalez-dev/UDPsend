@echo off
cd %~dp0..
start /B python app\main.py
timeout /t 1 /nobreak >nul
start http:/localhost:5000