@echo off
cd /d %~dp0
if not exist .venv py -m venv .venv
call .venv\Scripts\activate
python -m pip install -r requirements.txt
set DATA_DIR=%CD%\data
if "%SECRET_KEY%"=="" set SECRET_KEY=local-dev-secret-change-me
if "%ADMIN_EMAIL%"=="" set ADMIN_EMAIL=admin@natureswireless.org
if "%ADMIN_PASSWORD%"=="" set ADMIN_PASSWORD=ChangeMe123!
python -m uvicorn main:app --host 127.0.0.1 --port 8000
