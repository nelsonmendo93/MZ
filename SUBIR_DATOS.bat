@echo off
chcp 65001 > nul
title Marca Zonal — Subir datos a GitHub

:: Buscar Python (Anaconda primero, luego Python normal)
where conda >nul 2>&1
if %ERRORLEVEL%==0 (
    for /f "tokens=*" %%i in ('where conda') do (
        set "CONDA_PATH=%%~dpi"
    )
    set "PYTHON=%CONDA_PATH%python.exe"
) else (
    set "PYTHON=python"
)

:: Ir a la carpeta del script
cd /d "%~dp0"

:: Ejecutar
"%PYTHON%" SUBIR_DATOS.py

:: Si Python no se encontró correctamente, intentar con python directo
if %ERRORLEVEL%==9009 (
    python SUBIR_DATOS.py
)
