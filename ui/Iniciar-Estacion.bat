@echo off
REM Estacion de tierra Sigatoka: doble clic para abrirla en el navegador.
title Estacion Sigatoka
cd /d "%~dp0.."

if exist "%USERPROFILE%\venvs\dron-vision\Scripts\activate.bat" (
    call "%USERPROFILE%\venvs\dron-vision\Scripts\activate.bat"
) else (
    echo No encontre el entorno dron-vision. Revisa vision\GUIA-MODELO.md, fase 0.
    pause
    exit /b 1
)

python -c "import flask" 2>nul || (
    echo Instalando Flask por unica vez...
    pip install flask
)

python ui\estacion.py
pause
