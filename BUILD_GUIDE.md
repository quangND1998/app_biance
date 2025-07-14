# 🏗️ Hướng dẫn Build EXE - Binance P2P Trading

Hướng dẫn chi tiết cách build file EXE từ source code Python.

## 📋 Yêu cầu hệ thống

### 🔧 Phần mềm cần thiết
- **Python 3.7+** - [Tải Python](https://www.python.org/downloads/)
- **Git** (tùy chọn) - [Tải Git](https://git-scm.com/)
- **Windows 10/11** (64-bit)

### 📦 Dependencies
Tất cả dependencies đã được liệt kê trong `requirements.txt` và sẽ được cài đặt tự động.

## 🚀 Cách build

### **Phương pháp 1: Sử dụng script tự động (Khuyến nghị)**

#### Bước 1: Chuẩn bị
```bash
# Clone hoặc tải source code
cd app_p2p
```

#### Bước 2: Chạy script build
```bash
# Cách 1: Sử dụng Python script
python build_exe.py

# Cách 2: Sử dụng batch file (Windows)
build.bat
```

#### Bước 3: Kiểm tra kết quả
- File EXE: `dist/Binance P2P Trading.exe`
- Package: `release/` (bao gồm EXE + tài liệu)

### **Phương pháp 2: Build thủ công**

#### Bước 1: Cài đặt dependencies
```bash
# Cài đặt PyInstaller
pip install pyinstaller

# Cài đặt các dependencies khác
pip install -r requirements.txt
```

#### Bước 2: Build EXE
```bash
# Build với file spec
pyinstaller app.spec --clean --noconfirm
```

#### Bước 3: Kiểm tra kết quả
```bash
# Kiểm tra file EXE
dir dist
```

## 📁 Cấu trúc file sau khi build

```
app_p2p/
├── dist/
│   └── Binance P2P Trading.exe    # File EXE chính
├── build/                         # Thư mục build tạm thời
├── release/                       # Package release
│   ├── Binance P2P Trading.exe
│   ├── README.md
│   ├── API_KEYS_GUIDE.md
│   └── chromedriver_win32/
└── *.spec                         # File cấu hình PyInstaller
```

## ⚙️ Tùy chỉnh build

### **Thay đổi tên file EXE**
Sửa file `app.spec`:
```python
exe = EXE(
    # ...
    name='Tên File Mới',  # Thay đổi tên ở đây
    # ...
)
```

### **Thêm icon**
1. Tạo file `.ico` (ví dụ: `app_icon.ico`)
2. Sửa file `app.spec`:
```python
exe = EXE(
    # ...
    icon='app_icon.ico',  # Thêm icon
    # ...
)
```

### **Bật/tắt console**
Sửa file `app.spec`:
```python
exe = EXE(
    # ...
    console=True,   # Bật console (debug)
    console=False,  # Tắt console (production)
    # ...
)
```

## 🔧 Troubleshooting

### **Lỗi "Module not found"**
```bash
# Thêm module vào hiddenimports trong app.spec
hiddenimports=[
    'module_name',
    # ...
]
```

### **Lỗi "File not found"**
```bash
# Kiểm tra đường dẫn trong app.spec
datas=[
    ('file_path', 'destination'),
    # ...
]
```

### **EXE quá lớn**
```bash
# Thêm vào excludes trong app.spec
excludes=[
    'unused_module',
    # ...
]
```

### **Lỗi antivirus**
- Thêm thư mục `dist/` vào whitelist
- Tắt real-time protection tạm thời
- Sử dụng `--upx-exclude` trong PyInstaller

## 📊 Tối ưu hóa

### **Giảm kích thước file**
1. **Loại bỏ module không cần thiết:**
```python
excludes=[
    'tkinter', 'matplotlib', 'scipy', 'PIL',
    'numpy.random._examples',
]
```

2. **Sử dụng UPX compression:**
```bash
pip install upx
# Thêm vào app.spec: upx=True
```

3. **Tối ưu imports:**
```python
# Chỉ import những gì cần thiết
hiddenimports=[
    'PyQt5.QtCore',
    'PyQt5.QtWidgets',
    # ...
]
```

### **Tăng tốc độ build**
```bash
# Sử dụng cache
pyinstaller app.spec --clean --noconfirm --cachepath=cache

# Build song song (nếu có nhiều CPU)
pyinstaller app.spec --clean --noconfirm --parallel
```

## 🧪 Testing

### **Test file EXE**
```bash
# Chạy file EXE
cd dist
"Binance P2P Trading.exe"

# Kiểm tra log
type app.log
```

### **Test trên máy khác**
1. Copy thư mục `release/` sang máy khác
2. Chạy file EXE
3. Kiểm tra hoạt động

## 📦 Distribution

### **Tạo installer**
Sử dụng tools như:
- **Inno Setup** - Tạo installer Windows
- **NSIS** - Nullsoft Scriptable Install System
- **Advanced Installer** - Tool chuyên nghiệp

### **Tạo portable package**
```bash
# Copy toàn bộ thư mục release
# Người dùng chỉ cần giải nén và chạy
```

## 🔒 Bảo mật

### **Code signing**
```bash
# Sử dụng certificate để ký file EXE
signtool sign /f certificate.pfx /p password "Binance P2P Trading.exe"
```

### **Obfuscation**
```bash
# Sử dụng pyarmor để obfuscate code
pip install pyarmor
pyarmor obfuscate main.py
```

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra log build
2. Thử build với `console=True` để xem lỗi
3. Kiểm tra dependencies
4. Tạo issue trên GitHub

---

**Lưu ý**: File EXE có thể bị antivirus cảnh báo do sử dụng PyInstaller. Đây là false positive bình thường. 