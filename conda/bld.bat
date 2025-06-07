@echo off
REM Build script for conda package on Windows
%PYTHON% -m pip install . -vv
if errorlevel 1 exit 1
