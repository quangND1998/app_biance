@echo off
chcp 65001 >nul
echo 🏗️  Bắt đầu build EXE cho Binance P2P Trading
echo ============================================================

REM Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python không được cài đặt hoặc không có trong PATH
    pause
    exit /b 1
)

REM Cài đặt PyInstaller nếu chưa có
echo 🔍 Kiểm tra PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo 📦 Đang cài đặt PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo ❌ Không thể cài đặt PyInstaller
        pause
        exit /b 1
    )
)

REM Dọn dẹp thư mục build cũ
echo 🧹 Dọn dẹp thư mục build cũ...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

REM Build EXE
echo 🚀 Bắt đầu build EXE...
python -m PyInstaller app.spec --clean --noconfirm

if errorlevel 1 (
    echo ❌ Build thất bại!
    pause
    exit /b 1
)

REM Kiểm tra file output
if exist "dist\Binance P2P Trading.exe" (
    echo ✅ Build thành công!
    
    REM Hiển thị kích thước file
    for %%A in ("dist\Binance P2P Trading.exe") do (
        set size=%%~zA
        set /a sizeMB=!size!/1024/1024
        echo 📏 Kích thước file: !sizeMB! MB
    )
    
    REM Tạo thư mục release
    echo 📦 Tạo package release...
    if exist release rmdir /s /q release
    mkdir release
    
    REM Copy file EXE
    copy "dist\Binance P2P Trading.exe" "release\"
    
    REM Copy README
    if exist README.md copy README.md release\
    
    REM Copy API_KEYS_GUIDE
    if exist API_KEYS_GUIDE.md copy API_KEYS_GUIDE.md release\
    
    REM Copy chromedriver
    if exist chromedriver_win32 xcopy chromedriver_win32 release\chromedriver_win32\ /E /I /Y
    
    echo ============================================================
    echo 🎉 Hoàn thành! File EXE đã được tạo thành công!
    echo 📁 Vị trí: dist\Binance P2P Trading.exe
    echo 📦 Package: release\
    echo ============================================================
) else (
    echo ❌ Không tìm thấy file EXE sau khi build
)

pause 