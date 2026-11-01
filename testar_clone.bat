@echo off
chcp 65001 >nul
title Testar Meu Clone Localmente
cd /d "%~dp0"
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" testar_clone.py
pause
