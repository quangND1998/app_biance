import unittest
from datetime import datetime, timedelta
import os
import shutil
import sys
from pathlib import Path

# Thêm thư mục gốc vào PYTHONPATH
root_dir = str(Path(__file__).parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from module.transaction_storage import TransactionStorage
from module.generate_qrcode import generate_vietqr
from io import BytesIO

class TestTransactionStorage(unittest.TestCase):
    def setUp(self):
        """Chuẩn bị môi trường test"""
        # Tạo thư mục test riêng với đường dẫn tuyệt đối
        self.test_dir = os.path.abspath("test_transactions")
        print(f"\nThư mục test sẽ được tạo tại: {self.test_dir}")
        
        self.storage = TransactionStorage(self.test_dir)
        
        # Dữ liệu test
        self.test_transaction = {
            "type": "buy",
            "order_number": "TEST123",
            "amount": 1000000,
            "bank_name": "Vietcombank",
            "account_number": "1234567890",
            "account_name": "Test User",
            "reference": "TEST_REF",
            "message": "Test transaction",
            "acq_id": "970436"  # Vietcombank
        }
        
        # Tạo QR code thật
        try:
            print("Đang tạo QR code...")
            qr_io = generate_vietqr(
                accountno=self.test_transaction["account_number"],
                accountname=self.test_transaction["account_name"],
                acqid=self.test_transaction["acq_id"],
                amount=str(self.test_transaction["amount"]),
                addInfo=self.test_transaction["message"]
            )
            # Chuyển BytesIO thành bytes
            self.test_qr = qr_io.getvalue()
            print("Đã tạo QR code thành công!")
        except Exception as e:
            print(f"Lỗi khi tạo QR code: {e}")
            self.fail(f"Không thể tạo QR code: {e}")
            
    def tearDown(self):
        """Dọn dẹp sau khi test"""
        # Xóa thư mục test
        if os.path.exists(self.test_dir):
            print(f"\nĐang xóa thư mục test: {self.test_dir}")
            shutil.rmtree(self.test_dir)
            print("Đã xóa thư mục test")
            
    def test_save_and_get_transaction(self):
        """Test lưu và lấy transaction"""
        print("\n=== Test lưu và lấy transaction ===")
        
        # Lưu transaction
        print("Đang lưu transaction...")
        saved_transaction = self.storage.save_transaction(
            self.test_transaction.copy(),
            self.test_qr
        )
        
        # Kiểm tra thông tin cơ bản
        print("Kiểm tra thông tin transaction...")
        self.assertEqual(saved_transaction["order_number"], "TEST123")
        self.assertEqual(saved_transaction["type"], "buy")
        self.assertTrue("qr_path" in saved_transaction)
        
        # Kiểm tra file QR đã được tạo
        qr_path = saved_transaction["qr_path"]
        qr_path_abs = os.path.abspath(qr_path)
        print(f"Kiểm tra file QR tại: {qr_path_abs}")
        self.assertTrue(os.path.exists(qr_path))
        print(f"Kích thước file QR: {os.path.getsize(qr_path)} bytes")
        
        # Lấy transaction theo order number
        print("Lấy transaction theo order number...")
        retrieved = self.storage.get_transaction_by_order("TEST123")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["order_number"], "TEST123")
        print("Transaction được lấy thành công!")
        
        # Hiển thị nội dung file JSON
        json_path = os.path.join(self.test_dir, f"transactions_{datetime.now().strftime('%Y-%m-%d')}.json")
        if os.path.exists(json_path):
            print(f"\nNội dung file JSON tại: {json_path}")
            with open(json_path, 'r', encoding='utf-8') as f:
                print(f.read())
        
        # Tạm dừng để người dùng có thể kiểm tra file
        input("\nNhấn Enter để tiếp tục...")
        
    def test_get_transactions_by_date(self):
        """Test lấy transaction theo ngày"""
        print("\n=== Test lấy transaction theo ngày ===")
        
        # Lưu một số transaction ở các ngày khác nhau
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        # Transaction hôm nay
        print("Lưu transaction hôm nay...")
        today_trans = self.test_transaction.copy()
        today_trans["order_number"] = "TODAY123"
        today_trans["timestamp"] = today.timestamp()
        self.storage.save_transaction(today_trans, self.test_qr)
        
        # Transaction hôm qua
        print("Lưu transaction hôm qua...")
        yesterday_trans = self.test_transaction.copy()
        yesterday_trans["order_number"] = "YESTERDAY123"
        yesterday_trans["timestamp"] = yesterday.timestamp()
        self.storage.save_transaction(yesterday_trans, self.test_qr)
        
        # Lấy transaction hôm nay
        print("Lấy transaction hôm nay...")
        today_transactions = self.storage.get_transactions_by_date(today)
        self.assertEqual(len(today_transactions), 1)
        self.assertEqual(today_transactions[0]["order_number"], "TODAY123")
        print(f"Tìm thấy {len(today_transactions)} transaction hôm nay")
        
        # Lấy transaction hôm qua
        print("Lấy transaction hôm qua...")
        yesterday_transactions = self.storage.get_transactions_by_date(yesterday)
        self.assertEqual(len(yesterday_transactions), 1)
        self.assertEqual(yesterday_transactions[0]["order_number"], "YESTERDAY123")
        print(f"Tìm thấy {len(yesterday_transactions)} transaction hôm qua")
        
    def test_get_transactions_by_date_range(self):
        """Test lấy transaction trong khoảng thời gian"""
        print("\n=== Test lấy transaction trong khoảng thời gian ===")
        
        # Lưu transaction trong 3 ngày liên tiếp
        today = datetime.now()
        transactions = []
        
        print("Lưu transaction trong 3 ngày...")
        for i in range(3):
            trans = self.test_transaction.copy()
            trans["order_number"] = f"ORDER{i}"
            trans["timestamp"] = (today - timedelta(days=i)).timestamp()
            self.storage.save_transaction(trans, self.test_qr)
            transactions.append(trans)
            print(f"Đã lưu transaction ORDER{i}")
            
        # Lấy transaction trong 2 ngày gần nhất
        print("Lấy transaction trong 2 ngày gần nhất...")
        start_date = today - timedelta(days=1)
        end_date = today
        result = self.storage.get_transactions_by_date_range(start_date, end_date)
        
        self.assertEqual(len(result), 2)
        order_numbers = [t["order_number"] for t in result]
        self.assertIn("ORDER0", order_numbers)
        self.assertIn("ORDER1", order_numbers)
        print(f"Tìm thấy {len(result)} transaction trong khoảng thời gian")
        
    def test_get_recent_transactions(self):
        """Test lấy transaction gần đây"""
        print("\n=== Test lấy transaction gần đây ===")
        
        # Lưu 5 transaction
        print("Lưu 5 transaction...")
        for i in range(5):
            trans = self.test_transaction.copy()
            trans["order_number"] = f"RECENT{i}"
            trans["timestamp"] = (datetime.now() - timedelta(minutes=i)).timestamp()
            self.storage.save_transaction(trans, self.test_qr)
            print(f"Đã lưu transaction RECENT{i}")
            
        # Lấy 3 transaction gần nhất
        print("Lấy 3 transaction gần nhất...")
        recent = self.storage.get_recent_transactions(limit=3)
        self.assertEqual(len(recent), 3)
        
        # Kiểm tra thứ tự (mới nhất lên đầu)
        self.assertEqual(recent[0]["order_number"], "RECENT0")
        self.assertEqual(recent[1]["order_number"], "RECENT1")
        self.assertEqual(recent[2]["order_number"], "RECENT2")
        print("Thứ tự transaction đúng!")

if __name__ == '__main__':
    unittest.main(verbosity=2) 