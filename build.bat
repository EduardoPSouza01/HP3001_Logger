@echo off
REM Gera o executavel e atualiza dist\HP3001 SEM apagar banco, config nem settings do usuario.
REM Feche o HP3001 (icone da bandeja > Sair) antes de rodar.
cd /d "%~dp0"
python -m pip install -q pyinstaller pywebview pystray pillow
python -m PyInstaller --noconfirm --clean --windowed --name HP3001 ^
  --distpath build_out --workpath build_tmp ^
  --add-data "hp3001\views;hp3001\views" ^
  --collect-all hid --collect-submodules sqlalchemy.dialects ^
  --hidden-import pyodbc --hidden-import pystray._win32 ^
  desktop.py
if errorlevel 1 exit /b 1

if not exist dist\HP3001 mkdir dist\HP3001
robocopy build_out\HP3001 dist\HP3001 /MIR /XF config.ini hp3001.db settings.json hp3001.log /XD logs >nul
if errorlevel 8 (
  echo Falha ao copiar. O HP3001 ainda esta aberto? Use Sair no icone da bandeja.
  exit /b 1
)
if not exist dist\HP3001\config.ini copy config.ini dist\HP3001\config.ini >nul
rmdir /s /q build_out build_tmp
del /q HP3001.spec 2>nul
echo.
echo Pronto: dist\HP3001\HP3001.exe
