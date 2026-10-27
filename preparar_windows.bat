@echo off
REM ============================================================
REM  Preparacion en una maquina nueva (Windows).
REM  Paso previo unico: instalar dependencias con pip.
REM  Todo lo demas lo hace un solo comando: manage.py preparar
REM ============================================================
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    .venv\Scripts\python.exe -m pip install --upgrade pip
)

.venv\Scripts\python.exe -m pip install -r back\requirements.txt

.venv\Scripts\python.exe manage.py preparar

echo.
echo   Para levantar el servidor:
echo     .venv\Scripts\python.exe manage.py runserver
endlocal
