@echo off
chcp 65001 > nul
title Marca Zonal — Subir a GitHub

echo ============================================
echo   MARCA ZONAL — Subida a GitHub
echo ============================================
echo.

:: Ir a la carpeta del proyecto
cd /d "%~dp0"
echo Carpeta: %CD%
echo.

:: Mostrar archivos modificados
echo --- Cambios detectados ---
git status --short
echo.

:: Agregar todos los cambios
git add -A

:: Commit (si no hay nada nuevo git lo indica pero no falla)
git commit -m "update: datos Apertura 2026"

:: Push con credenciales guardadas en Windows
echo.
echo Subiendo a GitHub...
git push origin main

echo.
echo ============================================
echo  Listo! La app se actualiza en 1-2 minutos.
echo ============================================
echo.
pause
