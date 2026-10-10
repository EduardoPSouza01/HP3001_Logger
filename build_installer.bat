@echo off
REM Gera o instalador: installer_out\HP3001-Setup.exe
REM Requer o Inno Setup 6 (https://jrsoftware.org/isdl.php). Feche o HP3001 antes (bandeja > Sair).
cd /d "%~dp0"

set ISCC=
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if "%ISCC%"=="" (
  echo Inno Setup 6 nao encontrado. Instale em https://jrsoftware.org/isdl.php
  exit /b 1
)

call build.bat
if errorlevel 1 exit /b 1

"%ISCC%" installer.iss
if errorlevel 1 exit /b 1
echo.
echo Pronto: installer_out\HP3001-Setup.exe
