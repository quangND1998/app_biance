# 🚀 Binance P2P Trading Bot

Ứng dụng tự động hóa giao dịch P2P trên Binance với giao diện người dùng thân thiện và tính năng tạo mã QR VietQR.

## 📋 Mục lục

- [Tính năng](#-tính-năng)
- [Cài đặt](#-cài-đặt)
- [Cấu hình](#-cấu-hình)
- [Sử dụng](#-sử-dụng)
- [API Keys](#-api-keys)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)
- [Troubleshooting](#-troubleshooting)
- [Đóng góp](#-đóng-góp)
- [License](#-license)

## ✨ Tính năng

### 🔄 Tự động hóa giao dịch
- Tự động xử lý đơn hàng P2P mua/bán
- Tích hợp với Selenium để lấy thông tin giao dịch
- Hỗ trợ nhiều loại ngân hàng Việt Nam

### 💳 Tạo mã QR VietQR
- Tự động tạo mã QR cho giao dịch
- Hỗ trợ hơn 50 ngân hàng Việt Nam
- Tích hợp API VietQR chính thức

### 📊 Quản lý giao dịch
- Giao diện xem danh sách giao dịch
- Tìm kiếm và lọc theo nhiều tiêu chí
- Xuất dữ liệu ra Excel
- Cập nhật realtime

### 🔐 Bảo mật API Keys
- Nhập API Keys qua giao diện thân thiện
- Không lưu trữ cố định (tùy chọn)
- Validation và kiểm tra lỗi

### 📱 Thông báo
- Tích hợp Discord bot
- Tích hợp Telegram bot
- Thông báo realtime về giao dịch

## 🛠️ Cài đặt

### Yêu cầu hệ thống
- Python 3.7+
- Google Chrome
- Windows 10/11

### Bước 1: Clone repository
```bash
git clone <repository-url>
cd app_p2p
```

### Bước 2: Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### Bước 3: Tải ChromeDriver
- Tải ChromeDriver từ [trang chủ](https://chromedriver.chromium.org/)
- Giải nén vào thư mục `chromedriver_win32/`

## ⚙️ Cấu hình

### 1. API Keys (Bắt buộc)
Có 2 cách cấu hình API Keys:

#### Cách 1: Qua giao diện (Khuyến nghị)
- Chạy ứng dụng: `python main.py`
- Nhập API Keys khi được yêu cầu

#### Cách 2: File .env
Tạo file `.env` trong thư mục gốc:
```env
BINANCE_KEY=your_binance_api_key
BINANCE_SECRET=your_binance_secret_key
```

### 2. Thông báo (Tùy chọn)
Thêm vào file `.env`:
```env
# Discord
DISCORD_TOKEN=your_discord_token
DISCORD_CHANNEL_ID=your_channel_id
DISCORD_WEBHOOK=your_webhook_url

# Telegram
TELEGRAM_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_URL=your_telegram_url

# VietQR
VIETQR_KEY=your_vietqr_key
VIETQR_SECRET=your_vietqr_secret
```

## 🚀 Sử dụng

### Khởi động ứng dụng
```bash
python main.py
```

### Các bước sử dụng

1. **Cấu hình API Keys** (nếu chưa có)
   - Nhập BINANCE_KEY và BINANCE_SECRET
   - Nhấn "OK" để lưu

2. **Mở Chrome**
   - Nhấn nút "Open Chrome"
   - Đợi Chrome khởi động

3. **Đăng nhập Binance**
   - Nhấn nút "Đăng nhập"
   - Thực hiện đăng nhập thủ công

4. **Chạy bot**
   - Nhấn nút "RUN"
   - Bot sẽ bắt đầu xử lý giao dịch

5. **Theo dõi giao dịch**
   - Chuyển sang tab "Giao dịch"
   - Xem danh sách giao dịch realtime

### Tính năng chính

#### 🔍 Tìm kiếm giao dịch
- Chọn ngày cụ thể
- Tìm theo số order
- Lọc theo loại giao dịch (Mua/Bán)
- Lọc theo trạng thái

#### 📊 Xuất Excel
- Chọn khoảng thời gian
- Xuất dữ liệu ra file Excel
- Bao gồm thống kê chi tiết

#### 💳 Tạo QR Code
- Tạo mã QR VietQR cho giao dịch
- Lưu và hiển thị QR code
- Hỗ trợ nhiều ngân hàng

## 🔑 API Keys

### Lấy API Keys từ Binance

1. Đăng nhập [Binance.com](https://binance.com)
2. Vào **API Management**
3. Tạo API Key mới
4. **Quyền cần thiết:**
   - ✅ Enable Spot & Margin Trading
   - ✅ Enable Futures (nếu cần)
   - ❌ Enable Withdrawals (không cần)

### Bảo mật
- Không chia sẻ API Keys
- Không bật quyền rút tiền
- Sử dụng IP whitelist nếu có thể

## 📁 Cấu trúc dự án

```
app_p2p/
├── main.py                 # File chính
├── app.py                  # File app cũ
├── requirements.txt        # Dependencies
├── README.md              # Hướng dẫn này
├── API_KEYS_GUIDE.md      # Hướng dẫn API Keys
├── .env                   # Cấu hình (tùy chọn)
├── module/
│   ├── binance_p2p.py     # Xử lý giao dịch Binance
│   ├── selenium_get_info.py # Selenium automation
│   ├── generate_qrcode.py # Tạo QR VietQR
│   ├── discord_send_message.py # Discord bot
│   ├── telegram_send_message.py # Telegram bot
│   ├── transaction_storage.py # Lưu trữ giao dịch
│   └── resource_path.py   # Quản lý tài nguyên
├── chromedriver_win32/    # ChromeDriver
├── transactions/          # Thư mục lưu giao dịch
└── logs/                  # File log
```

## 🔧 Troubleshooting

### Lỗi thường gặp

#### 1. "ChromeDriver not found"
```bash
# Tải ChromeDriver và đặt vào thư mục chromedriver_win32/
```

#### 2. "API Key không hợp lệ"
- Kiểm tra lại API Key và Secret
- Đảm bảo có đủ quyền cần thiết
- Kiểm tra IP whitelist

#### 3. "Không thể kết nối Binance"
- Kiểm tra kết nối internet
- Thử VPN nếu cần
- Kiểm tra trạng thái Binance

#### 4. "Selenium lỗi"
- Cập nhật Chrome và ChromeDriver
- Kiểm tra quyền truy cập
- Thử chạy với quyền admin

### Log files
- `app.log` - Log chính
- `selenium_automation.log` - Log Selenium
- `qrcode_generation.log` - Log tạo QR

## 🤝 Đóng góp

1. Fork dự án
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📄 License

Dự án này được phân phối dưới giấy phép MIT. Xem file `LICENSE` để biết thêm chi tiết.

## ⚠️ Disclaimer

- Dự án này chỉ dành cho mục đích giáo dục
- Sử dụng trên trách nhiệm của riêng bạn
- Không đảm bảo lợi nhuận từ giao dịch
- Tuân thủ quy định của Binance và pháp luật địa phương

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra [Troubleshooting](#-troubleshooting)
2. Xem log files
3. Tạo issue trên GitHub
4. Liên hệ qua Discord/Telegram

---

**Lưu ý**: Giao dịch tiền điện tử có rủi ro cao. Hãy đầu tư có trách nhiệm! 🚀 