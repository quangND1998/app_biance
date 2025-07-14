#!/usr/bin/env python3
"""
Script test chức năng used_orders với JSON
"""

import sys
import os
import json
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(__file__))

from module.transaction_storage import TransactionStorage

def test_used_orders_from_transactions():
    """Test chức năng used_orders từ transactions"""
    print("🧪 Bắt đầu test used_orders từ transactions...")
    
    try:
        # Tạo storage instance
        storage = TransactionStorage("test_used_orders")
        
        # Test 1: Load used_orders khi chưa có transactions
        print("\n1️⃣ Test load used_orders khi chưa có transactions...")
        used_orders = storage.load_used_orders()
        print(f"✅ Kết quả: {len(used_orders)} orders")
        assert len(used_orders) == 0, "Should be empty when no transactions exist"
        
        # Test 2: Tạo một số transactions với order_status
        print("\n2️⃣ Test tạo transactions với order_status...")
        test_transactions = [
            {
                "type": "buy",
                "order_number": "22768168737054167040",
                "amount": 16301820,
                "order_status": "TRADING",
                "message": "Test transaction 1",
                "timestamp": datetime.now().timestamp()
            },
            {
                "type": "sell", 
                "order_number": "22768177956560101376",
                "amount": 523161307,
                "order_status": "COMPLETED",
                "message": "Test transaction 2",
                "timestamp": datetime.now().timestamp()
            },
            {
                "type": "buy",
                "order_number": "22768202909832933376", 
                "amount": 100000000,
                "order_status": "PENDING",
                "message": "Test transaction 3",
                "timestamp": datetime.now().timestamp()
            }
        ]
        
        for transaction in test_transactions:
            saved_transaction = storage.save_transaction(transaction)
            print(f"   📝 Đã lưu transaction {transaction['order_number']} với status {transaction['order_status']}")
        
        # Test 3: Load used_orders sau khi có transactions
        print("\n3️⃣ Test load used_orders sau khi có transactions...")
        loaded_orders = storage.load_used_orders()
        print(f"✅ Đã load {len(loaded_orders)} orders:")
        for order_number, status in loaded_orders.items():
            print(f"   📋 {order_number}: {status}")
        
        # Test 4: Test filter theo thời gian
        print("\n4️⃣ Test filter theo thời gian...")
        current_time = int(datetime.now().timestamp() * 1000)
        one_hour_ago = current_time - (60 * 60 * 1000)  # 1 giờ trước
        
        filtered_orders = storage.load_used_orders(
            start_timestamp=one_hour_ago,
            end_timestamp=current_time
        )
        print(f"✅ Orders trong 1 giờ qua: {len(filtered_orders)}")
        
        # Test 5: Test update_used_orders
        print("\n5️⃣ Test update_used_orders...")
        success = storage.update_used_orders("22768168737054167040", "COMPLETED")
        print(f"✅ Update order status: {'✅' if success else '❌'}")
        
        # Test 6: Load lại để kiểm tra update
        print("\n6️⃣ Test load sau khi update...")
        final_orders = storage.load_used_orders()
        updated_status = final_orders.get("22768168737054167040", "NOT_FOUND")
        print(f"✅ Status sau update: {updated_status}")
        
        print("\n🎉 Test hoàn thành thành công!")
        return True
        
    except Exception as e:
        print(f"💥 Lỗi trong quá trình test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_with_real_data():
    """Test với dữ liệu thực từ transactions"""
    print("\n🧪 Test với dữ liệu thực từ transactions...")
    
    try:
        storage = TransactionStorage("transactions")
        
        # Load used_orders từ transactions thực
        used_orders = storage.load_used_orders()
        print(f"📊 Đã load {len(used_orders)} orders từ transactions thực:")
        
        for order_number, status in used_orders.items():
            print(f"   📋 {order_number}: {status}")
        
        return True
            
    except Exception as e:
        print(f"💥 Lỗi trong test với dữ liệu thực: {str(e)}")
        return False

def test_save_transaction_with_status():
    """Test save_transaction với order_status"""
    print("\n🧪 Test save_transaction với order_status...")
    
    try:
        storage = TransactionStorage("test_used_orders")
        
        # Test transaction với order_status
        transaction_info = {
            "type": "buy",
            "order_number": "TEST_STATUS_123",
            "amount": 1000000,
            "bank_name": "Vietcombank",
            "account_number": "1234567890",
            "account_name": "Test User",
            "reference": "Test reference",
            "message": "Test transaction with status"
        }
        
        # Tạo QR code test
        from module.generate_qrcode import generate_vietqr
        qr_image = generate_vietqr(
            accountno="1234567890",
            accountname="Test User",
            acqid="970436",
            addInfo="Test reference",
            amount=1000000,
            template="rc9Vk60"
        )
        qr_bytes = qr_image.getvalue()
        
        # Lưu với order_status
        saved_transaction = storage.save_transaction(
            transaction_info, 
            qr_bytes, 
            "TRADING"
        )
        
        print(f"✅ Đã lưu transaction với status: {saved_transaction.get('order_status', 'N/A')}")
        
        # Kiểm tra xem order_status có được lưu không
        if 'order_status' in saved_transaction:
            print(f"✅ order_status được lưu: {saved_transaction['order_status']}")
        else:
            print("❌ order_status không được lưu")
        
        return True
        
    except Exception as e:
        print(f"💥 Lỗi trong test save_transaction với status: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Bắt đầu test used_orders từ transactions")
    
    # Test cơ bản
    success1 = test_used_orders_from_transactions()
    
    # Test với dữ liệu thực
    success2 = test_with_real_data()
    
    # Test save_transaction với order_status
    success3 = test_save_transaction_with_status()
    
    if success1 and success2 and success3:
        print("\n✅ Tất cả test đều thành công!")
    else:
        print("\n❌ Có test thất bại!") 