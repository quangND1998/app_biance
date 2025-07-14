# Hướng dẫn sử dụng API Keys - Binance P2P Trading

## 🚀 Tính năng mới: Nhập API Keys qua giao diện

Ứng dụng Binance P2P Trading giờ đây hỗ trợ nhập API Keys thông qua giao diện người dùng thân thiện, thay vì phải cấu hình trong file `.env`.

## 📋 Cách sử dụng

### 1. Khi khởi động ứng dụng lần đầu

- Nếu chưa có API Keys trong file `.env`, ứng dụng sẽ hiển thị dialog yêu cầu nhập
- Nhập **BINANCE_KEY** và **BINANCE_SECRET** vào các ô tương ứng
- Nhấn **OK** để lưu và tiếp tục

### 2. Thay đổi API Keys trong quá trình sử dụng

- Nhấn nút **"Cấu hình API Keys"** trong giao diện chính
- Dialog sẽ hiển thị với các giá trị hiện tại (nếu có)
- Chỉnh sửa và nhấn **OK** để cập nhật

## 🔧 Tính năng của Dialog

### ✅ Hiển thị/Ẩn mật khẩu
- Tích vào checkbox **"👁️ Hiển thị mật khẩu"** để xem nội dung
- Bỏ tích để ẩn lại

### ✅ Validation
- Kiểm tra đầy đủ thông tin trước khi lưu
- Hiển thị thông báo lỗi chi tiết nếu thiếu trường nào

### ✅ Thử lại
- Nếu người dùng chưa nhập đủ thông tin, ứng dụng sẽ hỏi có muốn thử lại không
- Chỉ thoát khi người dùng chọn "Không"

## 🔑 Lấy API Keys từ Binance

1. Đăng nhập vào [Binance.com](https://binance.com)
2. Vào **API Management** (Quản lý API)
3. Tạo API Key mới
4. **Lưu ý quan trọng**: 
   - Bật quyền **"Enable Spot & Margin Trading"**
   - Bật quyền **"Enable Futures"** (nếu cần)
   - **KHÔNG** bật quyền **"Enable Withdrawals"** (vì lý do bảo mật)

## 🛡️ Bảo mật

- API Keys được lưu trong bộ nhớ tạm thời
- Không lưu vào file cố định (trừ khi có file `.env`)
- Có thể thay đổi bất cứ lúc nào thông qua giao diện

## 🐛 Xử lý lỗi

### Lỗi "Thiếu API Keys"
- Đảm bảo đã nhập đầy đủ cả BINANCE_KEY và BINANCE_SECRET
- Kiểm tra không có khoảng trắng thừa

### Lỗi "API Key không hợp lệ"
- Kiểm tra lại API Key và Secret Key
- Đảm bảo API Key có đủ quyền cần thiết
- Kiểm tra IP whitelist (nếu có)

## 📞 Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra log trong ứng dụng
2. Đảm bảo API Keys có đủ quyền
3. Thử tạo API Key mới từ Binance

---

**Lưu ý**: API Keys rất quan trọng, hãy bảo mật cẩn thận và không chia sẻ với người khác! 