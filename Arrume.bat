@echo off
rem Abre la interfaz grafica de Arrume con doble clic.
title Arrume
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo No encuentro el entorno .venv en esta carpeta.
  echo.
  echo Crealo una sola vez con:
  echo     python -m venv .venv
  echo     .venv\Scripts\python.exe -m pip install -e .
  echo.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" -m arrume.web.servidor
pause
