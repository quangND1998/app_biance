import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QPushButton, QTableWidget, 
                           QTableWidgetItem, QDateEdit, QMessageBox, QHeaderView)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QPixmap
from datetime import datetime
from module.transaction_storage import TransactionStorage
import os
from PyQt5.QtCore import pyqtSignal

class TransactionViewer(QMainWindow):
    # Signal khi có thay đổi giao dịch
    transaction_added = pyqtSignal()
    transaction_updated = pyqtSignal()
    transaction_deleted = pyqtSignal()

    def __init__(self, storage=None):
        super().__init__()
        self.storage = storage if storage else TransactionStorage()
        self.initUI()
        
    def initUI(self):
        """Khởi tạo giao diện"""
        self.setWindowTitle('Xem Giao Dịch')
        self.setGeometry(100, 100, 1200, 800)
        
        # Widget chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Phần chọn ngày
        date_layout = QHBoxLayout()
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.dateChanged.connect(self.load_transactions)
        
        date_layout.addWidget(QLabel('Chọn ngày:'))
        date_layout.addWidget(self.date_picker)
        date_layout.addStretch()
        
        # Nút xem QR
        self.view_qr_btn = QPushButton('Xem QR')
        self.view_qr_btn.clicked.connect(self.show_qr)
        self.view_qr_btn.setEnabled(False)
        date_layout.addWidget(self.view_qr_btn)
        
        layout.addLayout(date_layout)
        
        # Bảng hiển thị giao dịch
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            'Loại', 'Số Order', 'Số tiền', 'Ngân hàng',
            'Số TK', 'Tên TK', 'Thông tin', 'Thời gian'
        ])
        
        # Căn chỉnh cột
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.Stretch)  # Cột thời gian co giãn
        
        # Cho phép chọn một dòng
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_selection_change)
        
        layout.addWidget(self.table)
        
        # Label hiển thị QR
        self.qr_label = QLabel()
        self.qr_label.setMinimumSize(200, 200)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        self.qr_label.hide()
        layout.addWidget(self.qr_label)
        
        # Load dữ liệu ban đầu
        self.load_transactions()
        
    def load_transactions(self):
        """Load danh sách giao dịch theo ngày đã chọn"""
        try:
            # Lấy ngày từ date picker
            qdate = self.date_picker.date()
            date = datetime(qdate.year(), qdate.month(), qdate.day())
            
            # Lấy danh sách giao dịch
            transactions = self.storage.get_transactions_by_date(date)
            
            # Hiển thị lên bảng
            self.table.setRowCount(len(transactions))
            for row, trans in enumerate(transactions):
                # Loại giao dịch
                self.table.setItem(row, 0, QTableWidgetItem(
                    "Mua" if trans['type'] == 'buy' else "Bán"
                ))
                
                # Số order
                self.table.setItem(row, 1, QTableWidgetItem(
                    str(trans['order_number'])
                ))
                
                # Số tiền
                amount = f"{int(trans['amount']):,} VND"
                self.table.setItem(row, 2, QTableWidgetItem(amount))
                
                # Ngân hàng
                self.table.setItem(row, 3, QTableWidgetItem(
                    trans.get('bank_name', '')
                ))
                
                # Số tài khoản
                self.table.setItem(row, 4, QTableWidgetItem(
                    trans.get('account_number', '')
                ))
                
                # Tên tài khoản
                self.table.setItem(row, 5, QTableWidgetItem(
                    trans.get('account_name', '')
                ))
                
                # Thông tin thêm
                self.table.setItem(row, 6, QTableWidgetItem(
                    trans.get('message', '')
                ))
                
                # Thời gian
                timestamp = trans.get('timestamp', 0)
                time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
                self.table.setItem(row, 7, QTableWidgetItem(time_str))
                
                # Lưu đường dẫn QR vào item
                if 'qr_path' in trans:
                    self.table.item(row, 1).setData(Qt.UserRole, trans['qr_path'])
            
            # Căn giữa các cột
            for row in range(self.table.rowCount()):
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setTextAlignment(Qt.AlignCenter)
            
            # Thông báo nếu không có giao dịch
            if not transactions:
                # QMessageBox.information(
                #     self,
                #     "Thông báo",
                #     f"Không có giao dịch nào vào ngày {date.strftime('%d/%m/%Y')}"
                # )
                pass # Giữ lại pass để tránh lỗi cú pháp nếu không có lệnh nào khác
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Lỗi",
                f"Không thể load giao dịch: {str(e)}"
            )
            
    def on_selection_change(self):
        """Xử lý khi chọn một dòng trong bảng"""
        selected = self.table.selectedItems()
        if selected:
            # Lấy đường dẫn QR từ dòng được chọn
            row = selected[0].row()
            qr_path = self.table.item(row, 1).data(Qt.UserRole)
            self.view_qr_btn.setEnabled(bool(qr_path))
        else:
            self.view_qr_btn.setEnabled(False)
            self.qr_label.hide()
            
    def show_qr(self):
        """Hiển thị mã QR của giao dịch được chọn"""
        try:
            selected = self.table.selectedItems()
            if not selected:
                return
                
            # Lấy đường dẫn QR
            row = selected[0].row()
            qr_path = self.table.item(row, 1).data(Qt.UserRole)
            
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
            self.qr_label.setPixmap(scaled_pixmap)
            self.qr_label.show()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Lỗi",
                f"Không thể hiển thị QR code: {str(e)}"
            )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = TransactionViewer()
    viewer.show()
    sys.exit(app.exec_()) 