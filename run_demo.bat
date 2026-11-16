@echo off
title eKYC AI Biometric System
echo ========================================================
echo   HE THONG eKYC - QUET MAT ^& NHAN DIEN SINH TRAC HOC
echo ========================================================
echo Dang khoi dong may chu tai http://127.0.0.1:8000 ...
python -m uvicorn app:app --host 127.0.0.1 --port 8000
pause

