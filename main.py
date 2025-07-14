from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, 
                           QLabel, QVBoxLayout, QPlainTextEdit, QFileDialog, 
                           QDateEdit, QMessageBox, QHBoxLayout, QTabWidget, 
                           QGroupBox, QLineEdit, QTextEdit, QComboBox, 
                           QSpinBox, QDoubleSpinBox, QTableWidget, QHeaderView, 
                           QTableWidgetItem, QScrollArea, QAbstractItemView, 
                           QFormLayout, QCheckBox, QProgressDialog, QProgressBar,
                           QFrame, QSplitter, QDialog, QDialogButtonBox, QTimeEdit,
                           QSizePolicy)
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QDate, QThread, Qt, QTimer, QTime
from PyQt5.QtGui import QFont, QIcon, QPixmap, QImage

import sys
import logging
from module.selenium_get_info import login_app, launch_chrome_remote_debugging
from module.binance_p2p import P2PBinance
from datetime import datetime
import tracemalloc
import os
import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from module.generate_qrcode import generate_vietqr, get_bank_bin, get_nganhang_api
from dotenv import load_dotenv
from module.transaction_storage import TransactionStorage
from transaction_viewer import TransactionViewer
from module.resource_path import resource_path
from config_env import VERSION

# Load biến môi trường
load_dotenv()
BINANCE_KEY = os.getenv("BINANCE_KEY")
BINANCE_SECRET = os.getenv("BINANCE_SECRET")

# Kiểm tra hạn sử dụng nếu có APP_EXPIRE_DATE
load_dotenv()
expire_date_str = os.getenv("APP_EXPIRE_DATE", None)
if expire_date_str:
    if expire_date_str.lower() == "true":
        from PyQt5.QtWidgets import QMessageBox, QApplication
        import sys
        app = QApplication.instance() or QApplication([])
        QMessageBox.critical(None, "Hết hạn", "Ứng dụng đã hết hạn sử dụng. Vui lòng liên hệ admin để gia hạn.")
        sys.exit(1)
    elif expire_date_str.lower() != "false":
        try:
            expire_date = datetime.strptime(expire_date_str, "%Y-%m-%d").date()
            today = datetime.now().date()
            if today > expire_date:
                from PyQt5.QtWidgets import QMessageBox, QApplication
                import sys
                app = QApplication.instance() or QApplication([])
                QMessageBox.critical(None, "Hết hạn", "Ứng dụng đã hết hạn sử dụng. Vui lòng liên hệ admin để gia hạn.")
                sys.exit(1)
        except ValueError:
            pass  # Nếu không phải ngày hợp lệ, cho dùng app bình thường

tracemalloc.start()

class LogHandler(logging.Handler, QObject):
    log_signal = pyqtSignal(str)

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)

class ApiKeyDialog(QDialog):
    """Dialog để người dùng nhập BINANCE_KEY và BINANCE_SECRET"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.binance_key = ""
        self.binance_secret = ""
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Cấu hình API Keys - Binance")
        self.setModal(True)
        self.setFixedSize(500, 300)
        
        layout = QVBoxLayout()
        
        # Thêm label mô tả
        description_label = QLabel("Vui lòng nhập API Key và Secret Key của Binance:")
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #666; margin-bottom: 10px; font-weight: bold;")
        layout.addWidget(description_label)
        
        # Thêm thông tin hướng dẫn
        help_label = QLabel("💡 Lưu ý: API Keys có thể được tạo tại Binance.com > API Management")
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #888; font-size: 10px; margin-bottom: 15px;")
        layout.addWidget(help_label)
        
        # Form layout cho các input
        form_layout = QFormLayout()
        
        # Input cho BINANCE_KEY
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Nhập BINANCE_KEY")
        self.key_input.setEchoMode(QLineEdit.Password)
        # Hiển thị giá trị hiện tại nếu có
        if BINANCE_KEY:
            self.key_input.setText(BINANCE_KEY)
        form_layout.addRow("🔑 BINANCE_KEY:", self.key_input)
        
        # Input cho BINANCE_SECRET
        self.secret_input = QLineEdit()
        self.secret_input.setPlaceholderText("Nhập BINANCE_SECRET")
        self.secret_input.setEchoMode(QLineEdit.Password)
        # Hiển thị giá trị hiện tại nếu có
        if BINANCE_SECRET:
            self.secret_input.setText(BINANCE_SECRET)
        form_layout.addRow("🔐 BINANCE_SECRET:", self.secret_input)
        
        layout.addLayout(form_layout)
        
        # Thêm checkbox để hiển thị/ẩn mật khẩu
        self.show_password_checkbox = QCheckBox("👁️ Hiển thị mật khẩu")
        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password_checkbox)
        
        # Thêm spacer
        layout.addStretch()
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def toggle_password_visibility(self, state):
        """Chuyển đổi hiển thị/ẩn mật khẩu"""
        if state == Qt.Checked:
            self.key_input.setEchoMode(QLineEdit.Normal)
            self.secret_input.setEchoMode(QLineEdit.Normal)
        else:
            self.key_input.setEchoMode(QLineEdit.Password)
            self.secret_input.setEchoMode(QLineEdit.Password)
        
    def accept(self):
        """Xử lý khi người dùng nhấn OK"""
        self.binance_key = self.key_input.text().strip()
        self.binance_secret = self.secret_input.text().strip()
        
        # Kiểm tra từng trường và hiển thị thông báo cụ thể
        missing_fields = []
        if not self.binance_key:
            missing_fields.append("BINANCE_KEY")
        if not self.binance_secret:
            missing_fields.append("BINANCE_SECRET")
            
        if missing_fields:
            QMessageBox.warning(
                self, 
                "Thiếu thông tin", 
                f"Vui lòng nhập đầy đủ các trường sau:\n• {', '.join(missing_fields)}"
            )
            return
            
        super().accept()
        
    def get_api_keys(self):
        """Trả về API keys đã nhập"""
        return self.binance_key, self.binance_secret
        
class ChromeThread(QThread):
    def run(self):
        launch_chrome_remote_debugging()

class Worker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, func):
        super().__init__()
        self.func = func

    def run(self):
        try:
            self.func()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
        finally:
            QThread.currentThread().quit()

class ExcelExportWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress_update = pyqtSignal(int, str)

    def __init__(self, p2p_instance, start_timestamp, end_timestamp, file_path):
        super().__init__()
        self.p2p_instance = p2p_instance
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.file_path = file_path

    def run(self):
        print("ExcelExportWorker: Bắt đầu chạy.")
        try:
            print("ExcelExportWorker: Phát tín hiệu progress_update (10)...")
            self.progress_update.emit(10, "Đang lấy dữ liệu giao dịch...")
            print("ExcelExportWorker: Đã phát tín hiệu progress_update (10).")
            df_grouped = self.p2p_instance.get_all_c2c_trades(
                start_timestamp=self.start_timestamp,
                end_timestamp=self.end_timestamp
            )
            print("ExcelExportWorker: Phát tín hiệu progress_update (40)...")
            self.progress_update.emit(40, "Đã lấy dữ liệu giao dịch.")
            print("ExcelExportWorker: Đã phát tín hiệu progress_update (40).")

            if df_grouped.empty:
                print("ExcelExportWorker: DataFrame rỗng. Phát tín hiệu lỗi...")
                self.error.emit("Không có dữ liệu giao dịch trong khoảng thời gian đã chọn")
                self.finished.emit()
                print("ExcelExportWorker: Đã phát tín hiệu lỗi và finished.")
                return

            print("ExcelExportWorker: Phát tín hiệu progress_update (60)...")
            self.progress_update.emit(60, "Đang xuất dữ liệu ra Excel...")
            print("ExcelExportWorker: Đã phát tín hiệu progress_update (60).")
            with pd.ExcelWriter(self.file_path) as writer:
                df_grouped.to_excel(writer, sheet_name="Tổng hợp", index=False)
            
            print("ExcelExportWorker: Hoàn thành. Phát tín hiệu finished.")
            self.finished.emit()
        except Exception as e:
            print(f"ExcelExportWorker: Lỗi trong quá trình chạy - {str(e)}. Phát tín hiệu lỗi.")
            self.error.emit(str(e))
        finally:
            QThread.currentThread().quit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Khởi tạo P2PBinance với API keys đã được cập nhật
        self.p2p_instance = P2PBinance(api_key=BINANCE_KEY, api_secret=BINANCE_SECRET)
        self.chrome_thread = ChromeThread()
        self.bank_cache = None  # Cache cho danh sách ngân hàng
        self.current_page = 0  # Trang hiện tại của danh sách ngân hàng
        self.rows_per_page = 20  # Số dòng mỗi trang của danh sách ngân hàng
        self.transaction_cache = None  # Cache cho danh sách giao dịch
        self.transaction_page = 0  # Trang hiện tại của danh sách giao dịch
        self.transaction_rows_per_page = 20  # Số dòng mỗi trang của danh sách giao dịch
        
        # Khởi tạo storage trước
        self.transaction_storage = TransactionStorage()
        
        # Khởi tạo logging và UI
        self.init_logging()
        self.initUI()
        
        # Khởi tạo transaction viewer sau khi đã có storage và UI
        self.transaction_viewer = TransactionViewer(self.transaction_storage)
        self.transaction_viewer.transaction_added.connect(self.refresh_transaction_list)
        self.transaction_viewer.transaction_updated.connect(self.refresh_transaction_list)
        self.transaction_viewer.transaction_deleted.connect(self.refresh_transaction_list)
        
        # Load dữ liệu ban đầu
        self.refresh_transaction_list()
        
        # Khởi tạo timer cho realtime update
        self.realtime_timer = QTimer()
        self.realtime_timer.timeout.connect(self.realtime_refresh)
        self.realtime_enabled = False  # Mặc định tắt realtime
        self.realtime_interval = 5000  # 5 giây mặc định
        self.last_update_time = None  # Thời gian cập nhật cuối cùng

    def initUI(self):
        """Khởi tạo giao diện"""
        self.setWindowTitle('Binance P2P Trading')
        self.setGeometry(100, 100, 900, 600)  # Giảm từ 1200x800 xuống 900x600
        
        # Cho phép resize nhỏ hơn
        self.setMinimumSize(600, 400)  # Kích thước tối thiểu mới
        
        # Widget chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Thêm label hiển thị version
        self.version_label = QLabel(f"Phiên bản: {VERSION}")
        self.version_label.setStyleSheet("color: #888; font-size: 12px; font-style: italic; margin-bottom: 5px;")
        layout.addWidget(self.version_label)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self.on_tab_changed)  # Kết nối signal tab changed
        
        # Cho phép tab widget resize linh hoạt
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout.addWidget(self.tab_widget)
        
        # Tab chính (giữ nguyên giao diện cũ)
        main_tab = QWidget()
        main_layout = QVBoxLayout(main_tab)
        
        # Phần Chrome và đăng nhập
        self.label_open = QLabel("Google Chrome")
        self.open_button = QPushButton("Open Chrome")
        self.open_button.clicked.connect(self.chrome_thread.start)

        self.label_login = QLabel("Đăng nhập Binance")
        self.login_button = QPushButton("Đăng nhập")
        self.login_button.clicked.connect(self.handle_login)

        self.label_run_app = QLabel("Chạy chương trình")
        self.run_button = QPushButton("RUN")
        self.run_button.clicked.connect(self.handle_run_app)

        self.stop_button = QPushButton("DỪNG")
        self.stop_button.clicked.connect(self.handle_stop)
        self.stop_button.setEnabled(False)

        self.clear_log_button = QPushButton("Xóa Log")
        self.clear_log_button.clicked.connect(self.clear_log)

        # Thêm nút đồng bộ danh sách ngân hàng
        self.sync_bank_button = QPushButton("Đồng bộ danh sách ngân hàng")
        self.sync_bank_button.clicked.connect(self.sync_bank_list)

        # Thêm nút cấu hình API Keys
        self.config_api_button = QPushButton("Cấu hình API Keys")
        self.config_api_button.clicked.connect(self.config_api_keys)

        # Thêm các widget vào layout chính
        for widget in [
            self.label_open, self.open_button,
            self.label_login, self.login_button,
            self.label_run_app, self.run_button, self.stop_button,
            self.clear_log_button, self.sync_bank_button, self.config_api_button
        ]:
            main_layout.addWidget(widget)

        # Phần QR code (giữ nguyên)
        self.generate_qr_button = QPushButton("Tạo QR")
        self.generate_qr_button.clicked.connect(self.generate_qr)

        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setMinimumSize(200, 200)  # Giảm từ 300x300 xuống 200x200
        self.qr_label.setStyleSheet("QLabel { background-color: white; border: 1px solid #ccc; }")
        self.qr_label.hide()

        self.save_qr_button = QPushButton("Lưu mã QR")
        self.save_qr_button.clicked.connect(self.handle_save_vietqr)
        self.save_qr_button.setEnabled(False)
        self.save_qr_button.hide()

        qr_layout = QVBoxLayout()
        qr_layout.addWidget(QLabel("Mã QR VietQR:"))
        qr_layout.addWidget(self.qr_label)
        qr_layout.addWidget(self.save_qr_button)
        qr_layout.addWidget(self.generate_qr_button)
        main_layout.addLayout(qr_layout)

        # Phần log
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumBlockCount(1000)
        self.log_output.setFont(QFont("Arial", 10))  # Giảm cỡ chữ log
        # Cho phép log output resize linh hoạt hơn
        self.log_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # Tab giao dịch
        trade_tab = QWidget()
        trade_layout = QVBoxLayout()
        
        # Group tìm kiếm
        search_group = QGroupBox("Tìm kiếm giao dịch")
        search_layout = QHBoxLayout()
        
        # Date picker
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.dateChanged.connect(self.refresh_transaction_list)
        self.date_edit.setFont(QFont("Arial", 12)) # Tăng cỡ chữ
        search_layout.addWidget(QLabel("Chọn ngày:"))
        search_layout.addWidget(self.date_edit)
        
        # Order number input
        self.order_number_input = QLineEdit()
        self.order_number_input.setPlaceholderText("Nhập số order...")
        self.order_number_input.textChanged.connect(self.filter_transactions)
        self.order_number_input.setFont(QFont("Arial", 12)) # Tăng cỡ chữ
        search_layout.addWidget(QLabel("Số order:"))
        search_layout.addWidget(self.order_number_input)
        
        # Transaction type combo
        self.transaction_type_combo = QComboBox()
        self.transaction_type_combo.addItems(["Tất cả", "Mua", "Bán"])
        self.transaction_type_combo.currentTextChanged.connect(self.filter_transactions)
        self.transaction_type_combo.setFont(QFont("Arial", 12)) # Tăng cỡ chữ
        search_layout.addWidget(QLabel("Loại giao dịch:"))
        search_layout.addWidget(self.transaction_type_combo)
        
        # Order status combo
        self.order_status_combo = QComboBox()
        self.order_status_combo.addItems([
            "Tất cả", "TRADING", "COMPLETED", "PENDING", 
            "BUYER_PAYED", "DISTRIBUTING", "IN_APPEAL", 
            "CANCELLED", "CANCELLED_BY_SYSTEM", "ERROR_BANK_NAME"
        ])
        self.order_status_combo.setCurrentText("TRADING")  # Mặc định là TRADING
        self.order_status_combo.currentTextChanged.connect(self.filter_transactions)
        self.order_status_combo.setFont(QFont("Arial", 12)) # Tăng cỡ chữ
        search_layout.addWidget(QLabel("Trạng thái:"))
        search_layout.addWidget(self.order_status_combo)
        
        search_group.setLayout(search_layout)
        trade_layout.addWidget(search_group)
        
        # Group realtime update
        realtime_group = QGroupBox("Cập nhật realtime")
        realtime_layout = QHBoxLayout()
        
        # Checkbox bật/tắt realtime
        self.realtime_checkbox = QCheckBox("Bật cập nhật tự động")
        self.realtime_checkbox.stateChanged.connect(self.toggle_realtime)
        realtime_layout.addWidget(self.realtime_checkbox)
        
        # Combobox chọn interval
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["3 giây", "5 giây", "10 giây", "30 giây", "1 phút"])
        self.interval_combo.setCurrentText("5 giây")  # Mặc định 5 giây
        self.interval_combo.currentTextChanged.connect(self.change_interval)
        self.interval_combo.setFont(QFont("Arial", 10))
        realtime_layout.addWidget(QLabel("Tần suất:"))
        realtime_layout.addWidget(self.interval_combo)
        
        # Label hiển thị trạng thái
        self.realtime_status_label = QLabel("Đã tắt")
        self.realtime_status_label.setStyleSheet("color: red; font-weight: bold;")
        realtime_layout.addWidget(self.realtime_status_label)
        
        # Nút refresh thủ công
        self.manual_refresh_btn = QPushButton("🔄 Làm mới ngay")
        self.manual_refresh_btn.clicked.connect(lambda: self.refresh_transaction_list(silent=False))
        self.manual_refresh_btn.setFont(QFont("Arial", 10))
        realtime_layout.addWidget(self.manual_refresh_btn)
        
        realtime_layout.addStretch()
        realtime_group.setLayout(realtime_layout)
        trade_layout.addWidget(realtime_group)
        
        # Bảng giao dịch
        self.trade_table = QTableWidget()
        self.trade_table.setColumnCount(10)  # Tăng lên 10 cột
        self.trade_table.setFont(QFont("Arial", 10))  # Giảm cỡ chữ bảng giao dịch
        self.trade_table.setHorizontalHeaderLabels([
            "Loại", "Số Order", "Số tiền", "Ngân hàng",
            "Số TK", "Tên TK", "Thông tin", "Thời gian", "Trạng thái", "Action"
        ])
        # Tự động điều chỉnh độ rộng cột
        self.trade_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # Làm cho cột 'Thông tin' tự động co giãn để lấp đầy không gian còn lại
        self.trade_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        # Cho phép chọn từng ô và cho phép chọn nhiều ô
        self.trade_table.setSelectionBehavior(QTableWidget.SelectItems)
        self.trade_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # Tắt chỉnh sửa
        self.trade_table.setEditTriggers(QTableWidget.NoEditTriggers)
        # Kết nối sự kiện chọn dòng
        self.trade_table.itemSelectionChanged.connect(self.on_trade_selection_change)
        
        # Cho phép bảng resize linh hoạt hơn
        self.trade_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        trade_layout.addWidget(self.trade_table)
        
        # Thêm phân trang cho giao dịch
        trade_pagination_layout = QHBoxLayout()
        self.trade_prev_page_btn = QPushButton("Trang trước")
        self.trade_prev_page_btn.clicked.connect(self.prev_transaction_page)
        self.trade_next_page_btn = QPushButton("Trang sau")
        self.trade_next_page_btn.clicked.connect(self.next_transaction_page)
        self.trade_page_label = QLabel("Trang 1")
        trade_pagination_layout.addWidget(self.trade_prev_page_btn)
        trade_pagination_layout.addWidget(self.trade_page_label)
        trade_pagination_layout.addWidget(self.trade_next_page_btn)
        trade_layout.addLayout(trade_pagination_layout)
        
        # Thêm nút xem QR và label hiển thị QR
        qr_layout = QHBoxLayout()
        self.view_qr_btn = QPushButton("Xem QR")
        self.view_qr_btn.clicked.connect(self.show_trade_qr)
        self.view_qr_btn.setEnabled(False)
        qr_layout.addWidget(self.view_qr_btn)
        qr_layout.addStretch()
        trade_layout.addLayout(qr_layout)
        
        # Label hiển thị QR
        self.trade_qr_label = QLabel()
        self.trade_qr_label.setMinimumSize(200, 200)  # Giảm từ 300x300 xuống 200x200
        self.trade_qr_label.setAlignment(Qt.AlignCenter)
        self.trade_qr_label.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        self.trade_qr_label.hide()
        trade_layout.addWidget(self.trade_qr_label)
        
        trade_tab.setLayout(trade_layout)
        self.tab_widget.addTab(trade_tab, "Giao dịch")

        # Tab xuất Excel
        excel_tab = QWidget()
        excel_layout = QVBoxLayout(excel_tab)
        
        # Thêm thông tin hướng dẫn
        info_label = QLabel("📊 Xuất dữ liệu giao dịch P2P ra file Excel")
        info_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; padding: 10px; background-color: #ecf0f1; border-radius: 5px;")
        info_label.setAlignment(Qt.AlignCenter)
        excel_layout.addWidget(info_label)
        
        # Phần chọn ngày và thời gian
        date_time_group = QGroupBox("Chọn khoảng thời gian")
        date_time_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; }")
        date_time_layout = QVBoxLayout()
        
        # Dòng 1: Chọn ngày
        date_layout = QHBoxLayout()
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate().addDays(-7))
        self.date_start.setFont(QFont("Arial", 12))
        date_layout.addWidget(QLabel('Từ ngày:'))
        date_layout.addWidget(self.date_start)
        
        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setFont(QFont("Arial", 12))
        date_layout.addWidget(QLabel('Đến ngày:'))
        date_layout.addWidget(self.date_end)
        date_layout.addStretch()
        date_time_layout.addLayout(date_layout)
        
        # Dòng 2: Chọn thời gian chi tiết
        time_layout = QHBoxLayout()
        self.time_start = QTimeEdit()
        self.time_start.setTime(QTime(0, 0, 0))  # 00:00:00
        self.time_start.setFont(QFont("Arial", 12))
        time_layout.addWidget(QLabel('Từ giờ:'))
        time_layout.addWidget(self.time_start)
        
        self.time_end = QTimeEdit()
        self.time_end.setTime(QTime(23, 59, 59))  # 23:59:59
        self.time_end.setFont(QFont("Arial", 12))
        time_layout.addWidget(QLabel('Đến giờ:'))
        time_layout.addWidget(self.time_end)
        time_layout.addStretch()
        date_time_layout.addLayout(time_layout)
        
        # Dòng 3: Nút shortcut chọn thời gian nhanh
        shortcut_layout = QHBoxLayout()
        shortcut_layout.addWidget(QLabel("Chọn nhanh:"))
        
        # Style chung cho các nút shortcut
        shortcut_button_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
        """
        
        # Nút chọn hôm nay
        today_btn = QPushButton("Hôm nay")
        today_btn.clicked.connect(self.set_today_range)
        today_btn.setFont(QFont("Arial", 10))
        today_btn.setStyleSheet(shortcut_button_style)
        shortcut_layout.addWidget(today_btn)
        
        # Nút chọn hôm qua
        yesterday_btn = QPushButton("Hôm qua")
        yesterday_btn.clicked.connect(self.set_yesterday_range)
        yesterday_btn.setFont(QFont("Arial", 10))
        yesterday_btn.setStyleSheet(shortcut_button_style)
        shortcut_layout.addWidget(yesterday_btn)
        
        # Nút chọn tuần này
        this_week_btn = QPushButton("Tuần này")
        this_week_btn.clicked.connect(self.set_this_week_range)
        this_week_btn.setFont(QFont("Arial", 10))
        this_week_btn.setStyleSheet(shortcut_button_style)
        shortcut_layout.addWidget(this_week_btn)
        
        # Nút chọn tháng này
        this_month_btn = QPushButton("Tháng này")
        this_month_btn.clicked.connect(self.set_this_month_range)
        this_month_btn.setFont(QFont("Arial", 10))
        this_month_btn.setStyleSheet(shortcut_button_style)
        shortcut_layout.addWidget(this_month_btn)
        
        # Nút chọn 7 ngày qua
        last_7_days_btn = QPushButton("7 ngày qua")
        last_7_days_btn.clicked.connect(self.set_last_7_days_range)
        last_7_days_btn.setFont(QFont("Arial", 10))
        last_7_days_btn.setStyleSheet(shortcut_button_style)
        shortcut_layout.addWidget(last_7_days_btn)
        
        shortcut_layout.addStretch()
        date_time_layout.addLayout(shortcut_layout)
        
        # Label hiển thị khoảng thời gian đã chọn
        self.time_range_label = QLabel()
        self.time_range_label.setStyleSheet("""
            color: #2c3e50; 
            font-weight: bold; 
            padding: 8px; 
            background-color: #f8f9fa; 
            border: 1px solid #dee2e6; 
            border-radius: 4px;
            font-size: 11px;
        """)
        self.time_range_label.setAlignment(Qt.AlignCenter)
        date_time_layout.addWidget(self.time_range_label)
        
        # Kết nối signal để cập nhật label
        self.date_start.dateChanged.connect(self.update_time_range_label)
        self.date_end.dateChanged.connect(self.update_time_range_label)
        self.time_start.timeChanged.connect(self.update_time_range_label)
        self.time_end.timeChanged.connect(self.update_time_range_label)
        
        date_time_group.setLayout(date_time_layout)
        excel_layout.addWidget(date_time_group)
        
        # Nút xuất Excel
        export_group = QGroupBox("Xuất dữ liệu")
        export_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; }")
        export_layout = QVBoxLayout()
        
        self.export_excel_button = QPushButton('📊 Xuất Excel')
        self.export_excel_button.clicked.connect(self.export_to_excel)
        self.export_excel_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.export_excel_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        export_layout.addWidget(self.export_excel_button)
        
        # Thêm thông tin về định dạng file
        format_info = QLabel("💡 File Excel sẽ chứa tất cả giao dịch P2P trong khoảng thời gian đã chọn")
        format_info.setStyleSheet("color: #7f8c8d; font-size: 11px; padding: 5px;")
        format_info.setAlignment(Qt.AlignCenter)
        format_info.setWordWrap(True)
        export_layout.addWidget(format_info)
        
        # Label hiển thị tên file mặc định
        self.filename_label = QLabel()
        self.filename_label.setStyleSheet("""
            color: #27ae60; 
            font-weight: bold; 
            padding: 5px; 
            background-color: #e8f5e8; 
            border: 1px solid #27ae60; 
            border-radius: 3px;
            font-size: 10px;
        """)
        self.filename_label.setAlignment(Qt.AlignCenter)
        self.filename_label.setWordWrap(True)
        export_layout.addWidget(self.filename_label)
        
        # Thông tin về format tên file
        filename_info = QLabel("📝 Tên file sẽ tự động bao gồm ngày tháng và thời gian để dễ quản lý")
        filename_info.setStyleSheet("color: #95a5a6; font-size: 10px; padding: 3px;")
        filename_info.setAlignment(Qt.AlignCenter)
        filename_info.setWordWrap(True)
        export_layout.addWidget(filename_info)
        
        export_group.setLayout(export_layout)
        excel_layout.addWidget(export_group)
        
        # Cập nhật label ban đầu
        self.update_time_range_label()
        
        # Tab danh sách ngân hàng mới
        bank_tab = QWidget()
        bank_layout = QVBoxLayout(bank_tab)

        # Group tìm kiếm
        search_group = QGroupBox("Tìm kiếm")
        search_layout = QHBoxLayout()
        self.bank_search = QLineEdit()
        self.bank_search.setPlaceholderText("Nhập tên ngân hàng để tìm kiếm...")
        self.bank_search.textChanged.connect(self.filter_banks)
        self.bank_search.setFont(QFont("Arial", 12)) # Tăng cỡ chữ
        search_layout.addWidget(self.bank_search)
        
        # Nút đồng bộ
        sync_button = QPushButton("Đồng bộ danh sách ngân hàng")
        sync_button.clicked.connect(self.sync_bank_list)
        search_layout.addWidget(sync_button)
        search_group.setLayout(search_layout)
        bank_layout.addWidget(search_group)
        
        # Bảng danh sách ngân hàng
        self.bank_table = QTableWidget()
        self.bank_table.setColumnCount(8)
        self.bank_table.setHorizontalHeaderLabels([
            "Tên viết tắt", "Tên đầy đủ", "Mã ngân hàng", 
            "Mã BIN", "Logo URL", "Hỗ trợ chuyển khoản",
            "Hỗ trợ tra cứu", "Swift Code"
        ])
        # Tự động điều chỉnh độ rộng cột
        self.bank_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # Chỉ cho phép chọn dòng
        self.bank_table.setSelectionBehavior(QTableWidget.SelectRows)
        # Tắt chỉnh sửa
        self.bank_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Cho phép bảng resize linh hoạt hơn
        self.bank_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        bank_layout.addWidget(self.bank_table)
        
        # Thêm phân trang
        pagination_layout = QHBoxLayout()
        self.prev_page_btn = QPushButton("Trang trước")
        self.prev_page_btn.clicked.connect(self.prev_page)
        self.next_page_btn = QPushButton("Trang sau")
        self.next_page_btn.clicked.connect(self.next_page)
        self.page_label = QLabel("Trang 1")
        pagination_layout.addWidget(self.prev_page_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_page_btn)
        bank_layout.addLayout(pagination_layout)
        
        bank_tab.setLayout(bank_layout)
        self.tab_widget.addTab(main_tab, "Chính")
        self.tab_widget.addTab(trade_tab, "Giao dịch")
        self.tab_widget.addTab(excel_tab, "Xuất Excel")
        self.tab_widget.addTab(bank_tab, "Danh sách ngân hàng")
        
        # Load danh sách ngân hàng
        self.load_bank_list()

        # Tab tạo QR VietQR
        qr_tab = QWidget()
        qr_layout = QVBoxLayout(qr_tab)
        form_layout = QFormLayout()

        # Số tài khoản
        self.qr_account_no = QLineEdit()
        self.qr_account_no.setPlaceholderText("Nhập số tài khoản")
        self.qr_account_no.setFont(QFont("Arial", 13))
        form_layout.addRow("Số tài khoản:", self.qr_account_no)

        # Tên tài khoản
        self.qr_account_name = QLineEdit()
        self.qr_account_name.setPlaceholderText("Nhập tên tài khoản")
        self.qr_account_name.setFont(QFont("Arial", 13))
        form_layout.addRow("Tên tài khoản:", self.qr_account_name)

        # Ngân hàng (QComboBox)
        self.qr_bank_combo = QComboBox()
        self.qr_bank_combo.setEditable(True)
        self.qr_bank_combo.setFont(QFont("Arial", 13))
        # Load danh sách ngân hàng từ bank_list.json
        try:
            with open(resource_path('bank_list.json'), 'r', encoding='utf-8') as f:
                banks = json.load(f)
            self.qr_bank_map = {}
            display_items = []
            for info in banks.values():
                name = info.get('name', '')
                short_name = info.get('short_name', '')
                code = info.get('code', '')
                display = name
                if short_name and code:
                    display += f" ({short_name}/{code})"
                elif short_name:
                    display += f" ({short_name})"
                elif code:
                    display += f" ({code})"
                self.qr_bank_map[display] = info.get('bin')
                display_items.append(display)
            self.qr_bank_combo.addItems(sorted(display_items))
            from PyQt5.QtWidgets import QCompleter
            completer = QCompleter(sorted(display_items))
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            self.qr_bank_combo.setCompleter(completer)
        except Exception as e:
            self.qr_bank_map = {}
            self.qr_bank_combo.addItem("Không tải được danh sách ngân hàng")
        form_layout.addRow("Ngân hàng:", self.qr_bank_combo)

        # Số tiền
        self.qr_amount_edit = QLineEdit()
        self.qr_amount_edit.setPlaceholderText("Nhập số tiền (VD: 1,000,000)")
        self.qr_amount_edit.textChanged.connect(self.format_amount_input)
        self.qr_amount_edit.setFont(QFont("Arial", 13))
        form_layout.addRow("Số tiền:", self.qr_amount_edit)

        # Nội dung chuyển khoản
        self.qr_message = QLineEdit()
        self.qr_message.setPlaceholderText("Nội dung chuyển khoản (tùy chọn)")
        self.qr_message.setFont(QFont("Arial", 13))
        form_layout.addRow("Nội dung:", self.qr_message)

        qr_layout.addLayout(form_layout)

        # Nút clear input
        self.qr_clear_btn = QPushButton("Clear")
        self.qr_clear_btn.setFont(QFont("Arial", 12))
        self.qr_clear_btn.clicked.connect(self.handle_clear_vietqr_inputs)
        qr_layout.addWidget(self.qr_clear_btn)

        # Nút tạo QR
        self.qr_generate_btn = QPushButton("Tạo mã QR VietQR")
        self.qr_generate_btn.clicked.connect(self.handle_generate_vietqr)
        self.qr_generate_btn.setFont(QFont("Arial", 12))
        qr_layout.addWidget(self.qr_generate_btn)

        # Hiển thị QR
        self.qr_image_label = QLabel()
        self.qr_image_label.setAlignment(Qt.AlignCenter)
        self.qr_image_label.setMinimumSize(200, 200)  # Giảm từ 300x300 xuống 200x200
        self.qr_image_label.setStyleSheet("QLabel { background-color: white; border: 1px solid #ccc; }")
        qr_layout.addWidget(self.qr_image_label)

        # Nút lưu QR
        self.qr_save_btn = QPushButton("Lưu mã QR")
        self.qr_save_btn.setEnabled(False)
        self.qr_save_btn.clicked.connect(self.handle_save_vietqr)
        qr_layout.addWidget(self.qr_save_btn)

        # self.tab_widget.addTab(qr_tab, "Tạo QR VietQR")  # Ẩn Tab tạo QR VietQR

    def format_amount_input(self, text):
        # Chỉ giữ lại số, bỏ ký tự khác
        digits = ''.join(c for c in text if c.isdigit())
        if not digits:
            self.qr_amount_edit.blockSignals(True)
            self.qr_amount_edit.setText("")
            self.qr_amount_edit.blockSignals(False)
            return
        # Format lại với dấu phẩy
        formatted = f"{int(digits):,}"
        # Để tránh lặp vô hạn khi setText, chỉ set nếu khác
        if self.qr_amount_edit.text().replace(",", "") != digits or self.qr_amount_edit.text() != formatted:
            self.qr_amount_edit.blockSignals(True)
            self.qr_amount_edit.setText(formatted)
            self.qr_amount_edit.blockSignals(False)

    def handle_generate_vietqr(self):
        account_no = self.qr_account_no.text().strip()
        account_name = self.qr_account_name.text().strip()
        bank_name = self.qr_bank_combo.currentText()
        acqid = self.qr_bank_map.get(bank_name, "")
        amount_text = self.qr_amount_edit.text().replace(",", "")
        try:
            amount = int(amount_text)
        except Exception:
            amount = 0
        message = self.qr_message.text().strip()
        if not account_no or not account_name or not acqid:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập đầy đủ Số tài khoản, Tên tài khoản và chọn Ngân hàng.")
            return
        try:
            qr_bytesio = generate_vietqr(accountno=account_no, accountname=account_name, acqid=acqid, addInfo=message, amount=amount, template="rc9Vk60")
            image = QImage.fromData(qr_bytesio.getvalue())
            pixmap = QPixmap.fromImage(image)
            self.qr_image_label.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.qr_save_btn.setEnabled(True)
            self._last_qr_bytes = qr_bytesio.getvalue()
            # Không tự động lưu file, chỉ hiển thị QR và bật nút lưu
        except Exception as e:
            QMessageBox.critical(self, "Lỗi tạo QR", f"Không thể tạo mã QR: {e}")
            self.qr_image_label.clear()
            self.qr_save_btn.setEnabled(False)

    def handle_save_vietqr(self):
        if not hasattr(self, '_last_qr_bytes') or not self._last_qr_bytes:
            QMessageBox.warning(self, "Chưa có mã QR", "Vui lòng tạo mã QR trước khi lưu.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Lưu mã QR", "vietqr.png", "PNG Files (*.png)")
        if file_path:
            with open(file_path, 'wb') as f:
                f.write(self._last_qr_bytes)
            QMessageBox.information(self, "Đã lưu", f"Đã lưu mã QR thành công: {file_path}")

    def load_bank_list(self):
        """Load danh sách ngân hàng từ file bank_list.json hoặc cache"""
        try:
            # Nếu đã có cache và không phải đang đồng bộ, sử dụng cache
            if self.bank_cache is not None and not hasattr(self, '_syncing_banks'):
                self.display_bank_page()
                return

            # Sử dụng resource_path để lấy đường dẫn chính xác
            bank_list_path = resource_path('bank_list.json')
            
            if not os.path.exists(bank_list_path):
                self.log("⚠️ Không tìm thấy file bank_list.json, đang tải từ API...")
                banks = get_nganhang_api()
                if not banks:
                    raise Exception("Không thể tải danh sách ngân hàng từ API")
            else:
                with open(bank_list_path, 'r', encoding='utf-8') as f:
                    banks = json.load(f)
            
            # Lưu vào cache
            self.bank_cache = banks
            self.current_page = 0
            self.display_bank_page()
            
            self.log(f"✅ Đã tải {len(banks)} ngân hàng thành công")
            
        except Exception as e:
            self.log(f"❌ Lỗi khi tải danh sách ngân hàng: {str(e)}")
            QMessageBox.critical(
                self,
                "Lỗi",
                f"Không thể tải danh sách ngân hàng: {str(e)}"
            )

    def display_bank_page(self):
        """Hiển thị trang hiện tại của danh sách ngân hàng"""
        self.log(f"Gọi display_bank_page. Current page: {self.current_page}")
        if not self.bank_cache:
            self.log("Bank cache rỗng, không hiển thị trang.")
            return

        # Tính toán phạm vi dữ liệu cần hiển thị
        start_idx = self.current_page * self.rows_per_page
        
        # Lấy danh sách ngân hàng đã lọc (nếu có)
        filtered_banks = self.get_filtered_banks()
        
        end_idx = min(start_idx + self.rows_per_page, len(filtered_banks))
        
        self.log(f"Hiển thị từ {start_idx} đến {end_idx}. Tổng số ngân hàng đã lọc: {len(filtered_banks)}")
        
        # Cập nhật bảng
        self.bank_table.setRowCount(end_idx - start_idx)
        
        # Hiển thị dữ liệu cho trang hiện tại
        for row, (bank_code, bank_info) in enumerate(list(filtered_banks.items())[start_idx:end_idx]):
            # Tên viết tắt
            self.bank_table.setItem(row, 0, QTableWidgetItem(bank_code))
            
            # Tên đầy đủ
            self.bank_table.setItem(row, 1, QTableWidgetItem(bank_info['name']))
            
            # Mã ngân hàng
            self.bank_table.setItem(row, 2, QTableWidgetItem(bank_info['code']))
            
            # Mã BIN
            self.bank_table.setItem(row, 3, QTableWidgetItem(bank_info['bin']))
            
            # Logo URL
            self.bank_table.setItem(row, 4, QTableWidgetItem(bank_info['logo']))
            
            # Hỗ trợ chuyển khoản
            transfer_supported = "Có" if bank_info['transferSupported'] == 1 else "Không"
            self.bank_table.setItem(row, 5, QTableWidgetItem(transfer_supported))
            
            # Hỗ trợ tra cứu
            lookup_supported = "Có" if bank_info['lookupSupported'] == 1 else "Không"
            self.bank_table.setItem(row, 6, QTableWidgetItem(lookup_supported))
            
            # Swift Code
            self.bank_table.setItem(row, 7, QTableWidgetItem(str(bank_info.get('swift_code', ''))))
            
            # Căn giữa các cột
            for col in range(self.bank_table.columnCount()):
                item = self.bank_table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)
        
        # Cập nhật thông tin phân trang
        total_pages = (len(filtered_banks) + self.rows_per_page - 1) // self.rows_per_page
        self.page_label.setText(f"Trang {self.current_page + 1}/{total_pages}")
        self.prev_page_btn.setEnabled(self.current_page > 0)
        self.next_page_btn.setEnabled(self.current_page < total_pages - 1)

    def get_filtered_banks(self):
        """Lấy danh sách ngân hàng đã được lọc theo từ khóa tìm kiếm"""
        self.log(f"Đang gọi get_filtered_banks. Bank cache: {len(self.bank_cache) if self.bank_cache else 'None'}")
        if not self.bank_cache:
            return {}
            
        search_text = self.bank_search.text().lower()
        self.log(f"Search text: '{search_text}'")
        if not search_text:
            self.log("Trả về toàn bộ cache vì không có từ khóa tìm kiếm.")
            return self.bank_cache
            
        filtered_banks = {
            code: info for code, info in self.bank_cache.items()
            if search_text in code.lower() or 
               search_text in info['name'].lower() or
               search_text in info['code'].lower() or
               search_text in info['bin'].lower()
        }
        self.log(f"Đã lọc, tìm thấy {len(filtered_banks)} ngân hàng.")
        return filtered_banks

    def filter_banks(self):
        """Lọc danh sách ngân hàng theo từ khóa tìm kiếm"""
        self.log("Gọi filter_banks: Đang reset trang và hiển thị lại.")
        self.current_page = 0  # Reset về trang đầu
        self.display_bank_page()

    def prev_page(self):
        """Chuyển đến trang trước"""
        if self.current_page > 0:
            self.current_page -= 1
            self.display_bank_page()

    def next_page(self):
        """Chuyển đến trang sau"""
        filtered_banks = self.get_filtered_banks()
        total_pages = (len(filtered_banks) + self.rows_per_page - 1) // self.rows_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.display_bank_page()

    def sync_bank_list(self):
        """Đồng bộ danh sách ngân hàng từ API VietQR"""
        try:
            self._syncing_banks = True  # Đánh dấu đang đồng bộ
            self.log("🔄 Đang đồng bộ danh sách ngân hàng...")
            banks = get_nganhang_api()
            if banks:
                self.bank_cache = banks  # Cập nhật cache
                self.current_page = 0  # Reset về trang đầu
                self.display_bank_page()
                self.log(f"✅ Đã cập nhật {len(banks)} ngân hàng thành công")
                QMessageBox.information(
                    self,
                    "Thành công",
                    f"Đã cập nhật {len(banks)} ngân hàng thành công"
                )
            else:
                self.log("❌ Không thể cập nhật danh sách ngân hàng")
                QMessageBox.warning(
                    self,
                    "Cảnh báo",
                    "Không thể cập nhật danh sách ngân hàng. Vui lòng thử lại sau."
                )
        except Exception as e:
            self.log(f"❌ Lỗi khi đồng bộ danh sách ngân hàng: {str(e)}")
            QMessageBox.critical(
                self,
                "Lỗi",
                f"Không thể đồng bộ danh sách ngân hàng: {str(e)}"
            )
        finally:
            self._syncing_banks = False  # Xóa đánh dấu đồng bộ

    def config_api_keys(self):
        """Cấu hình API Keys"""
        try:
            was_running = False
            # Nếu thread đang chạy thì dừng trước khi cấu hình lại API Keys
            if hasattr(self, 'run_thread') and self.run_thread is not None and self.run_thread.isRunning():
                was_running = True
                self.log("🛑 Dừng chương trình trước khi cập nhật API Keys...")
                if self.p2p_instance:
                    self.p2p_instance.stop()
                self.run_thread.quit()
                self.run_thread.wait(5000)
                self.run_thread = None

            dialog = ApiKeyDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                new_key, new_secret = dialog.get_api_keys()
                
                # Cập nhật biến toàn cục
                global BINANCE_KEY, BINANCE_SECRET
                BINANCE_KEY = new_key
                BINANCE_SECRET = new_secret
                
                # Cập nhật biến môi trường
                os.environ["BINANCE_KEY"] = BINANCE_KEY
                os.environ["BINANCE_SECRET"] = BINANCE_SECRET
                
                # Tạo lại P2PBinance instance với API keys mới
                self.p2p_instance = P2PBinance(api_key=BINANCE_KEY, api_secret=BINANCE_SECRET)
                
                self.log("✅ API Keys đã được cập nhật thành công")
                QMessageBox.information(
                    self,
                    "Thành công",
                    "API Keys đã được cập nhật thành công!"
                )
                # Nếu trước đó app đang chạy thì tự động RUN lại
                if was_running:
                    self.log("🔄 Đang tự động chạy lại chương trình với API Keys mới...")
                    self.handle_run_app()
                else:
                    self.log("ℹ️ App không ở trạng thái RUN trước khi cập nhật API Keys, không tự động chạy lại.")
            else:
                self.log("❌ Hủy cập nhật API Keys")
        except Exception as e:
            self.log(f"❌ Lỗi khi cập nhật API Keys: {str(e)}")
            QMessageBox.critical(
                self,
                "Lỗi",
                f"Không thể cập nhật API Keys: {str(e)}"
            )

    def show_transaction_viewer(self):
        """Mở giao diện xem giao dịch"""
        try:
            self.viewer = TransactionViewer()
            self.viewer.show()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Lỗi",
                f"Không thể mở giao diện xem giao dịch: {str(e)}"
            )

    def create_order(self):
        """Tạo lệnh giao dịch mới"""
        try:
            # Lấy thông tin từ form
            trade_type = self.trade_type.currentText().lower()  # 'mua' hoặc 'bán'
            amount = int(self.amount_input.value())
            bank_name = self.bank_name.text().strip()
            account_number = self.account_number.text().strip()
            account_name = self.account_name.text().strip()
            message = self.message.text().strip()

            # Kiểm tra thông tin bắt buộc
            if not all([bank_name, account_number, account_name]):
                QMessageBox.warning(
                    self,
                    "Cảnh báo",
                    "Vui lòng nhập đầy đủ thông tin ngân hàng"
                )
                return

            # Tạo thông tin giao dịch
            transaction_info = {
                'type': trade_type,
                'amount': amount,
                'bank_name': bank_name,
                'account_number': account_number,
                'account_name': account_name,
                'message': message,
                'timestamp': int(datetime.now().timestamp())
            }

            # Lưu giao dịch
            order_number = self.transaction_storage.save_transaction(transaction_info)
            
            # Cập nhật giao diện
            self.generate_qr_button.setEnabled(True)
            self.log(f"✅ Đã tạo lệnh {trade_type.upper()} thành công")
            self.log(f"📝 Số lệnh: {order_number}")
            self.log(f"💰 Số tiền: {amount:,} VND")
            self.log(f"🏦 Ngân hàng: {bank_name}")
            self.log(f"📋 Số TK: {account_number}")
            self.log(f"👤 Tên TK: {account_name}")
            if message:
                self.log(f"💬 Nội dung: {message}")

            # Lưu thông tin giao dịch hiện tại
            self.p2p_instance.current_transaction = transaction_info
            self.p2p_instance.current_transaction['order_number'] = order_number

            # Xóa form
            self.clear_form()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Lỗi",
                f"Không thể tạo lệnh: {str(e)}"
            )
            self.log(f"❌ Lỗi khi tạo lệnh: {str(e)}")

    def clear_form(self):
        """Xóa thông tin trong form"""
        self.amount_input.setValue(1000000)
        self.bank_name.clear()
        self.account_number.clear()
        self.account_name.clear()
        self.message.clear()

    def init_logging(self):
        """Khởi tạo logging"""
        self.log_handler = LogHandler()
        self.log_handler.log_signal.connect(self.append_log)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        self.log_handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        root_logger.setLevel(logging.INFO)

        self.logger = logging.getLogger("MyApp")
        self.logger.info("🚀 Ứng dụng khởi động")

    def append_log(self, msg):
        """Thêm log vào text box"""
        if hasattr(self, 'log_output'):
            self.log_output.appendPlainText(msg)
            self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

    def log(self, msg):
        """Ghi log với level INFO"""
        if hasattr(self, 'logger'):
            self.logger.info(msg)
        else:
            print(msg)  # Fallback nếu logger chưa được khởi tạo

    def clear_log(self):
        self.log_output.clear()
        self.log("🗑️ Log đã được xóa")

    def handle_login(self):
        self.log("🔐 Đăng nhập...")
        self.label_login.setText("Đang đăng nhập...")
        self.login_button.setEnabled(False)

        self.login_thread = QThread()
        self.login_worker = Worker(login_app)
        self.login_worker.moveToThread(self.login_thread)

        self.login_thread.started.connect(self.login_worker.run)
        self.login_worker.finished.connect(self.login_success)
        self.login_worker.error.connect(self.login_failed)
        self.login_worker.finished.connect(self.login_thread.quit)
        self.login_worker.error.connect(self.login_thread.quit)
        self.login_worker.finished.connect(self.login_worker.deleteLater)
        self.login_worker.error.connect(self.login_worker.deleteLater)
        self.login_thread.finished.connect(self.login_thread.deleteLater)

        self.login_thread.start()

    def login_success(self):
        self.label_login.setText("Đăng nhập thành công!")
        self.login_button.setEnabled(True)
        self.log("✅ Đăng nhập thành công")

    def login_failed(self, err):
        self.label_login.setText("Đăng nhập thất bại!")
        self.login_button.setEnabled(True)
        self.log(f"❌ Lỗi: {err}")

    def handle_run_app(self):
        # Nếu thread đang chạy thì không cho RUN tiếp
        if hasattr(self, 'run_thread') and self.run_thread is not None and self.run_thread.isRunning():
            self.log("⚠️ Chương trình đang chạy, không thể RUN tiếp!")
            return
        self.log("🚀 Chạy chương trình...")
        self.label_run_app.setText("Đang chạy...")
        self.run_button.setEnabled(False)
        self.login_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.run_thread = QThread()
        self.run_worker = Worker(self.p2p_instance.transactions_trading)
        self.run_worker.moveToThread(self.run_thread)

        self.run_thread.started.connect(self.run_worker.run)
        self.run_worker.finished.connect(self.run_success)
        self.run_worker.error.connect(self.run_failed)
        self.run_worker.finished.connect(self.run_thread.quit)
        self.run_worker.error.connect(self.run_thread.quit)
        self.run_worker.finished.connect(self.run_worker.deleteLater)
        self.run_worker.error.connect(self.run_worker.deleteLater)
        self.run_thread.finished.connect(self.run_thread.deleteLater)

        self.run_thread.start()

    def run_success(self):
        self.label_run_app.setText("Hoàn thành!")
        self.log("✅ Chạy xong")
        self.run_button.setEnabled(True)
        self.login_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.run_thread = None  # Đặt lại để tránh lỗi

    def run_failed(self, err):
        self.label_run_app.setText("Lỗi!")
        self.log(f"❌ Lỗi: {err}")
        self.run_button.setEnabled(True)
        self.login_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.run_thread = None  # Đặt lại để tránh lỗi

    def handle_stop(self):
        self.log("🛑 Dừng chương trình...")
        self.label_run_app.setText("Đã yêu cầu dừng")
        self.stop_button.setEnabled(False)
        self.run_button.setEnabled(True)
        self.login_button.setEnabled(True)

        if self.p2p_instance:
            self.p2p_instance.stop()
        # Đảm bảo thread dừng hoàn toàn
        if hasattr(self, 'run_thread') and self.run_thread is not None:
            self.run_thread.quit()
            self.run_thread.wait(5000)  # Chờ tối đa 5 giây
            self.run_thread = None

    def export_to_excel(self):
        """Xuất dữ liệu giao dịch ra file Excel"""
        print("export_to_excel: Bắt đầu hàm.")
        try:
            # Lấy ngày và thời gian bắt đầu và kết thúc từ date/time picker
            start_date = self.date_start.date().toPyDate()
            end_date = self.date_end.date().toPyDate()
            start_time = self.time_start.time().toPyTime()
            end_time = self.time_end.time().toPyTime()
            
            # Validation: Kiểm tra thời gian bắt đầu và kết thúc
            start_dt = datetime.combine(start_date, start_time)
            end_dt = datetime.combine(end_date, end_time)
            
            # Kiểm tra thời gian bắt đầu không được sau thời gian kết thúc
            if start_dt >= end_dt:
                QMessageBox.warning(
                    self,
                    "Lỗi thời gian",
                    "Thời gian bắt đầu phải trước thời gian kết thúc!\n\n"
                    f"Thời gian bắt đầu: {start_dt.strftime('%d/%m/%Y %H:%M:%S')}\n"
                    f"Thời gian kết thúc: {end_dt.strftime('%d/%m/%Y %H:%M:%S')}"
                )
                return
            
            # Kiểm tra khoảng thời gian không được quá lớn (ví dụ: không quá 1 năm)
            time_diff = end_dt - start_dt
            if time_diff.days > 365:
                reply = QMessageBox.question(
                    self,
                    "Cảnh báo",
                    f"Khoảng thời gian bạn chọn khá lớn ({time_diff.days} ngày).\n"
                    "Việc xuất dữ liệu có thể mất nhiều thời gian.\n\n"
                    "Bạn có muốn tiếp tục không?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # Chuyển đổi sang timestamp (milliseconds)
            start_timestamp = int(start_dt.timestamp() * 1000)
            end_timestamp = int(end_dt.timestamp() * 1000)
            
            # Hỏi người dùng nơi lưu file
            # Tạo tên file mặc định với format ddmmyyyy và không có thời gian
            if start_date == end_date:
                # Cùng ngày
                date_str = start_date.strftime('%d%m%Y')
                default_filename = f"binance_p2p_{date_str}.xlsx"
            else:
                # Khác ngày
                start_date_readable = start_date.strftime('%d%m%Y')
                end_date_readable = end_date.strftime('%d%m%Y')
                default_filename = f"binance_p2p_{start_date_readable}_{end_date_readable}.xlsx"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Lưu file Excel",
                default_filename,
                "Excel Files (*.xlsx)"
            )
            
            if not file_path:
                self.log("❌ Người dùng đã hủy việc xuất file")
                print("export_to_excel: Người dùng đã hủy.")
                return
                
            # Tạo progress dialog
            self.progress = QProgressDialog("Đang chuẩn bị xuất dữ liệu...", "Hủy", 0, 100, self)
            self.progress.setWindowTitle("Xuất Excel")
            self.progress.setWindowModality(Qt.WindowModal)
            self.progress.setMinimumDuration(0)
            self.progress.setAutoClose(True)
            self.progress.setAutoReset(True)
            self.progress.show()
            print("export_to_excel: Đã hiển thị QProgressDialog.")
            
            self.log(f"Đang xuất dữ liệu từ {start_dt.strftime('%d/%m/%Y %H:%M:%S')} đến {end_dt.strftime('%d/%m/%Y %H:%M:%S')}")
            self.progress.setValue(10)
            self.progress.setLabelText("Đang lấy dữ liệu giao dịch...")
            
            if self.progress.wasCanceled():
                self.log("❌ Người dùng đã hủy việc xuất file")
                self.progress.close()
                print("export_to_excel: Người dùng đã hủy sau khi hiển thị dialog.")
                return
            
            # Tạo luồng mới cho việc xuất Excel
            self.export_thread = QThread()
            self.export_worker = ExcelExportWorker(self.p2p_instance, start_timestamp, end_timestamp, file_path)
            self.export_worker.moveToThread(self.export_thread)

            # Kết nối các tín hiệu
            self.export_thread.started.connect(self.export_worker.run)
            self.export_worker.progress_update.connect(self.update_export_progress)
            self.export_worker.finished.connect(self.export_thread.quit)
            self.export_worker.finished.connect(self.export_worker.deleteLater)
            self.export_thread.finished.connect(self.export_thread.deleteLater)
            self.export_worker.finished.connect(lambda: self.export_success(file_path))
            self.export_worker.error.connect(self.export_failed)

            # Bắt đầu luồng
            self.export_thread.start()
            print("export_to_excel: Đã bắt đầu luồng xuất Excel.")

        except Exception as e:
            error_msg = f"❌ Lỗi khi khởi tạo xuất Excel: {str(e)}"
            self.log(error_msg)
            print(f"export_to_excel: Lỗi - {error_msg}")
            QMessageBox.critical(
                self,
                "Lỗi",
                error_msg
            )
            if hasattr(self, 'progress'):
                self.progress.close()

    def update_export_progress(self, value, text):
        print(f"update_export_progress: Nhận tín hiệu - Value: {value}, Text: {text}")
        if hasattr(self, 'progress') and self.progress is not None:
            self.progress.setValue(value)
            self.progress.setLabelText(text)
            if self.progress.wasCanceled():
                self.export_thread.requestInterruption() # Yêu cầu luồng dừng
                self.log("❌ Người dùng đã hủy việc xuất file")
                self.progress.close()

    def export_success(self, file_path):
        print(f"export_success: Hoàn thành xuất file vào {file_path}")
        if hasattr(self, 'progress') and self.progress is not None:
            self.progress.setValue(100)
            self.progress.setLabelText("Hoàn thành!")
            self.progress.close()
        self.log(f"✅ Đã xuất dữ liệu ra file thành công: {file_path}")
        QMessageBox.information(
            self,
            "Thành công",
            f"Đã xuất dữ liệu ra file:\n{file_path}"
        )

    def export_failed(self, error_msg):
        print(f"export_failed: Lỗi xuất file - {error_msg}")
        if hasattr(self, 'progress') and self.progress is not None:
            self.progress.close()
        error_msg = f"❌ Lỗi khi xuất Excel: {error_msg}"
        self.log(error_msg)
        QMessageBox.critical(
            self,
            "Lỗi",
            error_msg
        )

    def save_qr_image(self):
        """Lưu hình ảnh QR vào file"""
        if not hasattr(self, 'current_qr_path'):
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Lưu mã QR",
            self.current_qr_path,
            "PNG Files (*.png);;All Files (*)"
        )
        
        if file_path:
            try:
                import shutil
                shutil.copy2(self.current_qr_path, file_path)
                self.log(f"✅ Đã lưu mã QR tại: {file_path}")
            except Exception as e:
                self.log(f"❌ Lỗi khi lưu mã QR: {str(e)}")
                QMessageBox.critical(self, "Lỗi", f"Không thể lưu mã QR: {str(e)}")

    def generate_qr(self):
        """Tạo mã QR cho giao dịch hiện tại"""
        try:
            # Kiểm tra xem có giao dịch hiện tại không
            if not self.p2p_instance.current_transaction:
                QMessageBox.warning(
                    self,
                    "Cảnh báo",
                    "Không có giao dịch nào đang được xử lý. Vui lòng đợi có giao dịch mới."
                )
                return

            tx = self.p2p_instance.current_transaction
            
            # Lấy thông tin từ giao dịch hiện tại
            amount = tx.get("amount", "1000000")
            account_number = tx.get("account_number", "")
            account_name = tx.get("account_name", "")
            bank_name = tx.get("bank_name", "")
            reference = tx.get("reference", "")
            order_number = tx.get("order_number", "")

            # Kiểm tra thông tin bắt buộc
            if not all([amount, account_number, account_name, bank_name]):
                QMessageBox.warning(
                    self,
                    "Cảnh báo",
                    "Thiếu thông tin cần thiết để tạo mã QR. Vui lòng kiểm tra lại giao dịch."
                )
                return

            # Tạo mã QR
            acqid_bank = get_bank_bin(bank_name)
            qr_image = generate_vietqr(
                accountno=account_number,
                accountname=account_name,
                acqid=acqid_bank,
                addInfo=reference or order_number,
                amount=amount,
                template="rc9Vk60"
            )

            # Hiển thị mã QR
            pixmap = QPixmap()
            pixmap.loadFromData(qr_image.getvalue())
            self.qr_label.setPixmap(pixmap.scaled(
                300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
            self.qr_label.setAlignment(Qt.AlignCenter)
            
            # Hiển thị thông tin giao dịch
            info_text = (
                f"Số tiền: {amount} VND\n"
                f"Ngân hàng: {bank_name}\n"
                f"Số tài khoản: {account_number}\n"
                f"Tên người nhận: {account_name}\n"
                f"Mã tham chiếu: {reference or order_number}"
            )
            self.transaction_info.setText(info_text)
            
            # Hiển thị nút lưu QR
            self.save_qr_button.setEnabled(True)
            
            # Log thông tin giao dịch
            self.log(f"Đã tạo mã QR cho giao dịch {order_number}")
            self.log(f"Thông tin giao dịch:\n{info_text}")

        except Exception as e:
            self.log(f"Lỗi khi tạo mã QR: {str(e)}")
            QMessageBox.critical(
                self,
                "Lỗi",
                f"Không thể tạo mã QR: {str(e)}"
            )

    def closeEvent(self, event):
        self.log("🔚 Đóng ứng dụng...")
        if self.p2p_instance:
            self.p2p_instance.stop()
        if self.login_thread:
            try:
                if self.login_thread.isRunning():
                    self.login_thread.quit()
                    self.login_thread.wait()
            except RuntimeError:
                pass  # Thread có thể đã bị delete

        if self.run_thread:
            try:
                if self.run_thread.isRunning():
                    self.run_thread.quit()
                    self.run_thread.wait()
            except RuntimeError:
                pass  # Thread có thể đã bị delete

        logging.getLogger().removeHandler(self.log_handler)
        event.accept()

    def refresh_transaction_list(self, silent=False):
        """Refresh danh sách giao dịch trong bảng"""
        try:
            if not silent:
                self.log("Đang làm mới danh sách giao dịch...")
            # Lấy ngày hiện tại từ date picker
            date = self.date_edit.date().toPyDate()
            if not silent:
                self.log(f"Ngày đã chọn: {date.strftime('%d/%m/%Y')}")
            
            # Lấy danh sách giao dịch từ storage
            transactions = self.transaction_storage.get_transactions_by_date(date)
            
            # Kiểm tra xem có giao dịch mới không
            old_count = len(self.transaction_cache) if self.transaction_cache else 0
            new_count = len(transactions)
            
            # Lưu vào cache
            self.transaction_cache = transactions
            
            # Chỉ reset trang nếu không phải realtime update
            if not silent:
                self.transaction_page = 0  # Reset về trang đầu
            
            if not silent:
                self.log(f"Đã tải {len(transactions)} giao dịch từ storage.")
            
            # Hiển thị danh sách
            self.display_transaction_page()
            
            if not transactions:
                if not silent:
                    self.log(f"ℹ️ Không tìm thấy giao dịch nào cho ngày {date.strftime('%d/%m/%Y')}")
            else:
                if silent and new_count > old_count:
                    # Chỉ log khi có giao dịch mới trong realtime
                    self.log(f"🆕 Phát hiện {new_count - old_count} giao dịch mới! (Tổng: {new_count})")
                elif not silent:
                    self.log(f"🔄 Đã cập nhật danh sách giao dịch ({len(transactions)} giao dịch)")
            
        except Exception as e:
            self.log(f"❌ Lỗi khi cập nhật danh sách giao dịch: {str(e)}")
            if not silent:
                QMessageBox.critical(
                    self,
                    "Lỗi",
                    f"Không thể cập nhật danh sách giao dịch: {str(e)}"
                )

    def display_transaction_page(self):
        """Hiển thị trang hiện tại của danh sách giao dịch"""
        self.log(f"Gọi display_transaction_page. Trang hiện tại: {self.transaction_page}")
        
        # Lấy danh sách giao dịch đã lọc
        filtered_transactions = self.get_filtered_transactions()
        self.log(f"Tổng số giao dịch sau khi lọc: {len(filtered_transactions)}")
        
        # Tính toán phạm vi dữ liệu cần hiển thị
        start_idx = self.transaction_page * self.transaction_rows_per_page
        end_idx = min(start_idx + self.transaction_rows_per_page, len(filtered_transactions))
        
        self.log(f"Phạm vi hiển thị: từ {start_idx} đến {end_idx}. Số hàng sẽ hiển thị: {end_idx - start_idx}")
        
        # Tắt sorting trước khi cập nhật dữ liệu
        self.trade_table.setSortingEnabled(False)
        # Cập nhật bảng
        self.trade_table.setRowCount(end_idx - start_idx)
        
        # Hiển thị dữ liệu cho trang hiện tại
        for row, trans in enumerate(filtered_transactions[start_idx:end_idx]):
            # Loại giao dịch
            trans_type = trans.get('type', '').lower()
            display_type = "Mua" if trans_type == 'buy' else "Bán"
            self.trade_table.setItem(row, 0, QTableWidgetItem(display_type))
            
            # Số order
            self.trade_table.setItem(row, 1, QTableWidgetItem(
                str(trans['order_number'])
            ))
            
            # Số tiền
            amount = f"{int(trans['amount']):,} VND"
            self.trade_table.setItem(row, 2, QTableWidgetItem(amount))
            
            # Ngân hàng
            self.trade_table.setItem(row, 3, QTableWidgetItem(
                trans.get('bank_name', '')
            ))
            
            # Số tài khoản
            self.trade_table.setItem(row, 4, QTableWidgetItem(
                trans.get('account_number', '')
            ))
            
            # Tên tài khoản
            self.trade_table.setItem(row, 5, QTableWidgetItem(
                trans.get('account_name', '')
            ))
            
            # Thông tin thêm
            self.trade_table.setItem(row, 6, QTableWidgetItem(
                trans.get('message', '')
            ))
            
            # Thời gian
            timestamp = trans.get('timestamp', 0)
            time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            item_time = QTableWidgetItem(time_str)
            item_time.setData(Qt.UserRole, timestamp)
            self.trade_table.setItem(row, 7, item_time)
            
            # Trạng thái
            order_status = trans.get('order_status', 'TRADING')
            self.trade_table.setItem(row, 8, QTableWidgetItem(order_status))
            
            # Lưu đường dẫn QR vào item nếu có
            if 'qr_path' in trans:
                self.trade_table.item(row, 1).setData(Qt.UserRole, trans['qr_path'])
            
            # Căn giữa các cột
            for col in range(9):
                item = self.trade_table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)
            # Thêm nút Action cho BUY
            # if trans.get('type', '').lower() == 'buy':
            #     action_btn = QPushButton("Tạo QR")
            #     action_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
            #     def make_action_func(tr=trans):
            #         return lambda: self.handle_action_create_qr(tr)
            #     action_btn.clicked.connect(make_action_func())
            #     self.trade_table.setCellWidget(row, 9, action_btn)
            # else:
            #     self.trade_table.setCellWidget(row, 9, None)
        
        # Bật lại sorting sau khi cập nhật dữ liệu
        self.trade_table.setSortingEnabled(True)
        
        # Cập nhật thông tin phân trang
        total_pages = (len(filtered_transactions) + self.transaction_rows_per_page - 1) // self.transaction_rows_per_page
        self.trade_page_label.setText(f"Trang {self.transaction_page + 1}/{total_pages}")
        self.trade_prev_page_btn.setEnabled(self.transaction_page > 0)
        self.trade_next_page_btn.setEnabled(self.transaction_page < total_pages - 1)

    def get_filtered_transactions(self):
        """Lấy danh sách giao dịch đã được lọc theo điều kiện tìm kiếm"""
        self.log(f"Gọi get_filtered_transactions. Transaction cache: {len(self.transaction_cache) if self.transaction_cache is not None else 'None'}")
        if not self.transaction_cache: # Kiểm tra None thay vì chỉ if not
            self.log("Cache giao dịch rỗng, trả về []")
            return []
        
        filtered = self.transaction_cache
        self.log(f"Cache ban đầu: {len(filtered)} giao dịch")
        
        # Lọc theo số order (tìm kiếm theo số cuối)
        order_number = self.order_number_input.text().strip()
        if order_number:
            filtered = [t for t in filtered if str(t.get('order_number', '')).endswith(order_number)]
        
        # Lọc theo loại giao dịch
        trade_type = self.transaction_type_combo.currentText()
        if trade_type != "Tất cả":
            type_map = {
                "Mua": "buy",
                "Bán": "sell"
            }
            target_type = type_map.get(trade_type)
            if target_type:
                filtered = [t for t in filtered if t.get('type', '').lower() == target_type.lower()]
        
        # Lọc theo trạng thái order
        order_status = self.order_status_combo.currentText()
        if order_status != "Tất cả":
            filtered = [t for t in filtered if t.get('order_status', '') == order_status]
        
        # Sắp xếp theo thời gian giảm dần (mới nhất lên đầu)
        filtered.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        self.log(f"Sau khi sắp xếp: {len(filtered)} giao dịch")
        
        return filtered

    def filter_transactions(self):
        """Lọc danh sách giao dịch theo điều kiện tìm kiếm"""
        self.transaction_page = 0  # Reset về trang đầu
        self.display_transaction_page()

    def prev_transaction_page(self):
        """Chuyển đến trang trước của danh sách giao dịch"""
        if self.transaction_page > 0:
            self.transaction_page -= 1
            self.display_transaction_page()

    def next_transaction_page(self):
        """Chuyển đến trang sau của danh sách giao dịch"""
        filtered_transactions = self.get_filtered_transactions()
        total_pages = (len(filtered_transactions) + self.transaction_rows_per_page - 1) // self.transaction_rows_per_page
        if self.transaction_page < total_pages - 1:
            self.transaction_page += 1
            self.display_transaction_page()

    def on_tab_changed(self, index):
        """Xử lý khi chuyển tab"""
        try:
            tab_name = self.tab_widget.tabText(index)
            if tab_name == "Giao dịch":
                # Chỉ refresh nếu đã có transaction_storage
                if hasattr(self, 'transaction_storage'):
                    self.refresh_transaction_list()
                    self.log("🔄 Đã tải lại dữ liệu giao dịch")
            elif tab_name == "Danh sách ngân hàng":
                self.load_bank_list()
                self.log("🔄 Đã tải lại danh sách ngân hàng")
        except Exception as e:
            self.log(f"❌ Lỗi khi chuyển tab: {str(e)}")

    def on_trade_selection_change(self):
        """Xử lý khi chọn một dòng trong bảng giao dịch"""
        selected = self.trade_table.selectedItems()
        if selected:
            # Lấy đường dẫn QR từ dòng được chọn
            row = selected[0].row()
            qr_path = self.trade_table.item(row, 1).data(Qt.UserRole)
            self.view_qr_btn.setEnabled(bool(qr_path))
            # Tự động hiển thị QR khi chọn dòng
            self.show_trade_qr()
        else:
            self.view_qr_btn.setEnabled(False)
            self.trade_qr_label.hide()

    def show_trade_qr(self):
        """Hiển thị mã QR của giao dịch được chọn"""
        try:
            selected = self.trade_table.selectedItems()
            if not selected:
                return
            
            # Lấy đường dẫn QR
            row = selected[0].row()
            qr_path = self.trade_table.item(row, 1).data(Qt.UserRole)
            
            if not qr_path or not os.path.exists(qr_path):
                QMessageBox.warning(
                    self,
                    "Cảnh báo",
                    "Không tìm thấy file QR code"
                )
                return
            
            # Hiển thị QR
            pixmap = QPixmap(qr_path)
            scaled_pixmap = pixmap.scaled(
                300, 300,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.trade_qr_label.setPixmap(scaled_pixmap)
            self.trade_qr_label.show()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Lỗi",
                f"Không thể hiển thị QR code: {str(e)}"
            )
            self.log(f"❌ Lỗi khi hiển thị QR code: {str(e)}")

    def toggle_realtime(self, state):
        """Bật/tắt cập nhật realtime"""
        if state == Qt.Checked:
            self.realtime_enabled = True
            self.realtime_timer.start(self.realtime_interval)
            self.realtime_status_label.setText("Đang cập nhật...")
            self.realtime_status_label.setStyleSheet("color: green; font-weight: bold;")
            self.log("🔄 Đã bật cập nhật realtime")
        else:
            self.realtime_enabled = False
            self.realtime_timer.stop()
            self.realtime_status_label.setText("Đã tắt")
            self.realtime_status_label.setStyleSheet("color: red; font-weight: bold;")
            self.log("⏹️ Đã tắt cập nhật realtime")

    def change_interval(self, text):
        """Thay đổi tần suất cập nhật"""
        interval_map = {
            "3 giây": 3000,
            "5 giây": 5000,
            "10 giây": 10000,
            "30 giây": 30000,
            "1 phút": 60000
        }
        
        new_interval = interval_map.get(text, 5000)
        self.realtime_interval = new_interval
        
        # Nếu đang bật realtime, restart timer với interval mới
        if self.realtime_enabled:
            self.realtime_timer.stop()
            self.realtime_timer.start(new_interval)
            self.log(f"🔄 Đã thay đổi tần suất cập nhật: {text}")

    def realtime_refresh(self):
        """Hàm thực hiện refresh danh sách giao dịch trong realtime"""
        self.refresh_transaction_list(silent=True)
        self.last_update_time = datetime.now()
        # Cập nhật status label với thời gian
        if self.last_update_time:
            time_str = self.last_update_time.strftime('%H:%M:%S')
            self.realtime_status_label.setText(f"Đang cập nhật... (Cuối: {time_str})")

    def update_time_range_label(self):
        """Cập nhật label hiển thị khoảng thời gian đã chọn"""
        start_date = self.date_start.date().toPyDate()
        end_date = self.date_end.date().toPyDate()
        time_start = self.time_start.time().toPyTime()
        time_end = self.time_end.time().toPyTime()
        
        # Tính khoảng thời gian
        start_dt = datetime.combine(start_date, time_start)
        end_dt = datetime.combine(end_date, time_end)
        time_diff = end_dt - start_dt
        
        # Hiển thị thông tin chi tiết
        if start_date == end_date:
            # Cùng ngày
            date_str = start_date.strftime('%d/%m/%Y')
            time_str = f"{time_start.strftime('%H:%M')} - {time_end.strftime('%H:%M')}"
            duration_str = f"({time_diff.total_seconds() / 3600:.1f} giờ)"
        else:
            # Khác ngày
            date_str = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
            time_str = f"{time_start.strftime('%H:%M')} - {time_end.strftime('%H:%M')}"
            duration_str = f"({time_diff.days} ngày, {time_diff.total_seconds() / 3600:.1f} giờ)"
        
        self.time_range_label.setText(f"📅 {date_str} | 🕐 {time_str} | ⏱️ {duration_str}")
        
        # Cập nhật tên file mặc định
        self.update_filename_label()
    
    def update_filename_label(self):
        """Cập nhật label hiển thị tên file mặc định"""
        start_date = self.date_start.date().toPyDate()
        end_date = self.date_end.date().toPyDate()
        
        # Tạo tên file với format ddmmyyyy và không có thời gian
        if start_date == end_date:
            # Cùng ngày
            date_str = start_date.strftime('%d%m%Y')
            filename = f"binance_p2p_{date_str}.xlsx"
        else:
            # Khác ngày
            start_date_readable = start_date.strftime('%d%m%Y')
            end_date_readable = end_date.strftime('%d%m%Y')
            filename = f"binance_p2p_{start_date_readable}_{end_date_readable}.xlsx"
        
        self.filename_label.setText(f"📄 Tên file mặc định: {filename}")

    def set_today_range(self):
        """Set thời gian hiện tại"""
        self.date_start.setDate(QDate.currentDate())
        self.date_end.setDate(QDate.currentDate())
        self.time_start.setTime(QTime(0, 0, 0))
        self.time_end.setTime(QTime(23, 59, 59))
        self.update_time_range_label()

    def set_yesterday_range(self):
        """Set thời gian hôm qua"""
        self.date_start.setDate(QDate.currentDate().addDays(-1))
        self.date_end.setDate(QDate.currentDate().addDays(-1))
        self.time_start.setTime(QTime(0, 0, 0))
        self.time_end.setTime(QTime(23, 59, 59))
        self.update_time_range_label()

    def set_this_week_range(self):
        """Set thời gian tuần này"""
        self.date_start.setDate(QDate.currentDate().addDays(-7))
        self.date_end.setDate(QDate.currentDate())
        self.time_start.setTime(QTime(0, 0, 0))
        self.time_end.setTime(QTime(23, 59, 59))
        self.update_time_range_label()

    def set_this_month_range(self):
        """Set thời gian tháng này"""
        self.date_start.setDate(QDate(QDate.currentDate().year(), QDate.currentDate().month(), 1))
        self.date_end.setDate(QDate.currentDate())
        self.time_start.setTime(QTime(0, 0, 0))
        self.time_end.setTime(QTime(23, 59, 59))
        self.update_time_range_label()

    def set_last_7_days_range(self):
        """Set thời gian 7 ngày qua"""
        self.date_start.setDate(QDate.currentDate().addDays(-7))
        self.date_end.setDate(QDate.currentDate())
        self.time_start.setTime(QTime(0, 0, 0))
        self.time_end.setTime(QTime(23, 59, 59))
        self.update_time_range_label()

    def handle_clear_vietqr_inputs(self):
        self.qr_account_no.clear()
        self.qr_account_name.clear()
        self.qr_bank_combo.setCurrentIndex(0)
        self.qr_amount_edit.clear()
        self.qr_message.clear()
        self.qr_image_label.clear()
        self.qr_save_btn.setEnabled(False)
        if hasattr(self, '_last_qr_bytes'):
            self._last_qr_bytes = b''

    def handle_action_create_qr(self, trans):
        """Chuyển sang tab tạo QR và tự động điền thông tin từ transaction"""
        # Chuyển sang tab Tạo QR VietQR
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "Tạo QR VietQR":
                self.tab_widget.setCurrentIndex(i)
                break
        # Điền thông tin vào form
        self.qr_account_no.setText(str(trans.get('account_number', '')))
        self.qr_account_name.setText(str(trans.get('account_name', '')))
        # Tìm và chọn ngân hàng phù hợp
        bank_name = trans.get('bank_name', '')
        idx = self.qr_bank_combo.findText(bank_name, Qt.MatchContains)
        if idx >= 0:
            self.qr_bank_combo.setCurrentIndex(idx)
        self.qr_amount_edit.setText(f"{int(trans.get('amount', 0)):,}")
        self.qr_message.setText(str(trans.get('message', '')))
        # Gọi hàm tạo QR như khi bấm nút
        self.handle_generate_vietqr()

    def resizeEvent(self, event):
        """Xử lý khi cửa sổ được resize"""
        super().resizeEvent(event)
        
        # Điều chỉnh font size dựa trên kích thước cửa sổ
        width = self.width()
        if width < 800:
            # Cửa sổ nhỏ, giảm font size
            small_font = QFont("Arial", 9)
            self.trade_table.setFont(small_font)
            self.bank_table.setFont(small_font)
            self.log_output.setFont(small_font)
        else:
            # Cửa sổ lớn, dùng font size nhỏ hơn trước
            normal_font = QFont("Arial", 10)
            self.trade_table.setFont(normal_font)
            self.bank_table.setFont(normal_font)
            self.log_output.setFont(normal_font)

# Hàm để lấy API keys từ người dùng
def get_api_keys_from_user():
    """Hiển thị dialog để người dùng nhập API keys"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    dialog = ApiKeyDialog()
    if dialog.exec_() == QDialog.Accepted:
        return dialog.get_api_keys()
    else:
        return None, None

# Kiểm tra và lấy API keys nếu chưa có
while not BINANCE_KEY or not BINANCE_SECRET:
    user_key, user_secret = get_api_keys_from_user()
    if user_key and user_secret:
        BINANCE_KEY = user_key
        BINANCE_SECRET = user_secret
        # Cập nhật biến môi trường
        os.environ["BINANCE_KEY"] = BINANCE_KEY
        os.environ["BINANCE_SECRET"] = BINANCE_SECRET
        print("✅ API Keys đã được cập nhật thành công!")
        break
    else:
        # Hiển thị dialog hỏi người dùng có muốn thử lại không
        reply = QMessageBox.question(
            None, 
            "Thiếu API Keys", 
            "Bạn chưa nhập API Keys. Bạn có muốn nhập lại không?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.No:
            print("Ứng dụng sẽ thoát.")
            sys.exit(1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
