@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Instalacija neizdevas. Atsuti saja loga redzamo kludu.
) else (
    echo Gatavs. Palaid PALAIST.bat un atver http://localhost:8000
)
pause
