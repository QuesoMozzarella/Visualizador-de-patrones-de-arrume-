@echo off
rem Abre Arrume con doble clic: el backend Flask sirve la pagina de React.
rem La ventana queda minimizada; cerrarla apaga el programa.
title Arrume
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo No encuentro el entorno .venv en esta carpeta.
  echo.
  echo Crealo una sola vez con:
  echo     python -m venv .venv
  echo     .venv\Scripts\python.exe -m pip install -e backend
  echo.
  pause
  exit /b 1
)

if not exist "frontend\dist\index.html" (
  echo Preparando la pagina por primera vez, puede tardar un minuto...
  pushd frontend
  call npm install --no-fund --no-audit || goto :sin_node
  call npm run build || goto :sin_node
  popd
)

if not "%1"=="min" (
  start "Arrume" /min "%~f0" min
  exit /b 0
)

rem Esta es la copia minimizada: al terminar el programa se cierra la ventana
".venv\Scripts\python.exe" -m arrume_api --abrir
exit

:sin_node
popd
echo.
echo No se pudo compilar la pagina. Hace falta Node.js (https://nodejs.org).
pause
exit /b 1
