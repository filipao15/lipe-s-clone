@echo off
chcp 65001 >nul
title Meu Clone no Telegram
cd /d "%~dp0"
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -u bot.py
pause
