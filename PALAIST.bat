@echo off
cd /d "%~dp0"
echo Pec servera starta atver parluka http://localhost:8000
echo So logu atstaj atvertu. Apturet: Ctrl+C.
python app.py
if errorlevel 1 pause
