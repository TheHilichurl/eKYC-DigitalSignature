@echo off
title Build eKYC Digital Signature Android APK
color 0A
echo ========================================================
echo    eKYC Digital Signature - Android APK Build Tool
echo    Theme: Cobalt Blue (#1D4ED8) & Orange (#EA580C)
echo    Security: Scheme v1 + v2 + v3, Anti-Hooking, RSA-2048
echo ========================================================
echo.

set APKTOOL="C:\Tools\apktool\apktool.jar"
set JADX_JAR="C:\Tools\JADX\lib\jadx-1.5.6-all.jar"
set KEYSTORE="android\keystore\release.keystore"
set UNSIGNED="android\eKYC_DigitalSignature_unsigned.apk"
set SIGNED="android\eKYC_DigitalSignature.apk"

cd /d "%~dp0\.."

echo [*] Step 1: Compiling Smali, XML Manifest and Resources with Apktool...
java -jar %APKTOOL% b android\app_src -o %UNSIGNED%
if %errorlevel% neq 0 (
    echo [ERROR] Apktool compilation failed!
    pause
    exit /b 1
)

echo [*] Step 2: Compiling APK Signer Tools (Google ApkSigner v1+v2+v3)...
javac -cp %JADX_JAR% -d "android\tools\bin" "android\tools\SignApkV2.java" "android\tools\VerifyApk.java"
if %errorlevel% neq 0 (
    echo [ERROR] Java compilation for SignApkV2 failed!
    pause
    exit /b 1
)

echo [*] Step 3: Signing APK with Google ApkSigner (Scheme v1 + v2 + v3 Full Compatibility)...
java -cp "android\tools\bin;%JADX_JAR%" com.tools.SignApkV2 %UNSIGNED% %SIGNED% %KEYSTORE% ekyc_secure_2026 ekyc_release_key
if %errorlevel% neq 0 (
    echo [ERROR] ApkSigner failed!
    pause
    exit /b 1
)

echo.
echo [*] Step 4: Verifying APK Signature Schemes...
java -cp "android\tools\bin;%JADX_JAR%" com.tools.VerifyApk %SIGNED%

echo.
echo ========================================================
echo [SUCCESS] APK built and signed successfully!
echo           Ready to install on all Android devices:
echo           %SIGNED%
echo ========================================================
echo.
pause
