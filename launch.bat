@echo off
%~d0
cd "%~dp0"
call .venv\Scripts\activate.bat
python launch.pyw
pause