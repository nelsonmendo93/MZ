@echo off
echo ================================================
echo   Marca Zonal - Subiendo cambios a GitHub...
echo ================================================
echo.

cd /d "%~dp0"

git pull origin main
git push origin main

echo.
echo ================================================
if %ERRORLEVEL% == 0 (
    echo   LISTO! Cambios subidos correctamente.
) else (
    echo   Hubo un error. Revisa la conexion.
)
echo ================================================
echo.
pause
