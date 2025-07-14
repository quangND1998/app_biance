#!/usr/bin/env python3
"""
Script build EXE cho Binance P2P Trading
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_dependencies():
    """Kiểm tra dependencies cần thiết"""
    print("🔍 Kiểm tra dependencies...")
    
    try:
        import PyInstaller
        print("✅ PyInstaller đã cài đặt")
    except ImportError:
        print("❌ PyInstaller chưa cài đặt. Đang cài đặt...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ Đã cài đặt PyInstaller")
    
    # Kiểm tra các file cần thiết
    required_files = [
        "main.py",
        "app.spec",
        "requirements.txt",
        "bank_list.json",
        "chromedriver_win32/chromedriver.exe"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Thiếu các file: {missing_files}")
        return False
    
    print("✅ Tất cả dependencies đã sẵn sàng")
    return True

def clean_build():
    """Dọn dẹp thư mục build cũ"""
    print("🧹 Dọn dẹp thư mục build cũ...")
    
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✅ Đã xóa {dir_name}")
    
    # Xóa file .spec cũ nếu có
    spec_files = [f for f in os.listdir(".") if f.endswith(".spec") and f != "app.spec"]
    for spec_file in spec_files:
        os.remove(spec_file)
        print(f"✅ Đã xóa {spec_file}")

def build_exe():
    """Build file EXE"""
    print("🚀 Bắt đầu build EXE...")
    
    try:
        # Chạy PyInstaller với file spec
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "app.spec",
            "--clean",
            "--noconfirm"
        ]
        
        print(f"📋 Chạy lệnh: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build thành công!")
            return True
        else:
            print(f"❌ Build thất bại!")
            print(f"Lỗi: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi khi build: {str(e)}")
        return False

def check_output():
    """Kiểm tra file output"""
    print("🔍 Kiểm tra file output...")
    
    exe_path = "dist/Binance P2P Trading.exe"
    if os.path.exists(exe_path):
        size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
        print(f"✅ File EXE đã tạo: {exe_path}")
        print(f"📏 Kích thước: {size:.2f} MB")
        return True
    else:
        print(f"❌ Không tìm thấy file EXE: {exe_path}")
        return False

def create_installer():
    """Tạo package installer"""
    print("📦 Tạo package installer...")
    
    # Tạo thư mục release
    release_dir = "release"
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir)
    
    # Copy file EXE
    exe_source = "dist/Binance P2P Trading.exe"
    exe_dest = f"{release_dir}/Binance P2P Trading.exe"
    shutil.copy2(exe_source, exe_dest)
    
    # Copy README
    if os.path.exists("README.md"):
        shutil.copy2("README.md", f"{release_dir}/README.md")
    
    # Copy API_KEYS_GUIDE
    if os.path.exists("API_KEYS_GUIDE.md"):
        shutil.copy2("API_KEYS_GUIDE.md", f"{release_dir}/API_KEYS_GUIDE.md")
    
    # Copy chromedriver nếu cần
    chromedriver_dir = f"{release_dir}/chromedriver_win32"
    if os.path.exists("chromedriver_win32"):
        shutil.copytree("chromedriver_win32", chromedriver_dir)
    
    print(f"✅ Package đã tạo trong thư mục: {release_dir}")
    return True

def main():
    """Hàm chính"""
    print("🏗️  Bắt đầu quá trình build EXE cho Binance P2P Trading")
    print("=" * 60)
    
    # Bước 1: Kiểm tra dependencies
    if not check_dependencies():
        print("❌ Không thể tiếp tục do thiếu dependencies")
        return False
    
    # Bước 2: Dọn dẹp
    clean_build()
    
    # Bước 3: Build EXE
    if not build_exe():
        print("❌ Build thất bại")
        return False
    
    # Bước 4: Kiểm tra output
    if not check_output():
        print("❌ Không tìm thấy file output")
        return False
    
    # Bước 5: Tạo package
    create_installer()
    
    print("=" * 60)
    print("🎉 Hoàn thành! File EXE đã được tạo thành công!")
    print("📁 Vị trí: dist/Binance P2P Trading.exe")
    print("📦 Package: release/")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 