#!/usr/bin/env python3
"""
Script debug để test việc xử lý order TRADING
"""

import logging
import sys
import os
sys.path.append(os.path.dirname(__file__))

from module.binance_p2p import P2PBinance
from module.selenium_get_info import extract_order_info, extract_info_by_key

# Thiết lập logging chi tiết
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_order.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_order_extraction(order_number):
    """Test việc trích xuất thông tin order"""
    logger.info(f"🧪 Bắt đầu test trích xuất order: {order_number}")
    
    try:
        # Test extract_order_info
        logger.info("1️⃣ Test extract_order_info...")
        raw_info = extract_order_info(order_number)
        logger.info(f"📊 Raw info: {raw_info}")
        
        if not raw_info:
            logger.error("❌ Không thể trích xuất thông tin cơ bản")
            return False
            
        # Test extract_info_by_key
        logger.info("2️⃣ Test extract_info_by_key...")
        processed_info = extract_info_by_key(raw_info)
        logger.info(f"🔧 Processed info: {processed_info}")
        
        # Kiểm tra các trường bắt buộc
        required_fields = ["Fiat amount", "Full Name", "Bank Card", "Bank Name", "Reference message"]
        missing_fields = []
        
        for field in required_fields:
            value = processed_info.get(field)
            if not value:
                missing_fields.append(field)
            logger.info(f"📋 {field}: {value}")
            
        if missing_fields:
            logger.warning(f"⚠️ Thiếu fields: {missing_fields}")
            return False
        else:
            logger.info("✅ Đủ tất cả thông tin cần thiết")
            return True
            
    except Exception as e:
        logger.error(f"💥 Lỗi trong quá trình test: {str(e)}", exc_info=True)
        return False

def test_p2p_handling(order_number):
    """Test việc xử lý order trong P2PBinance"""
    logger.info(f"🧪 Bắt đầu test P2P handling cho order: {order_number}")
    
    try:
        p2p = P2PBinance()
        
        # Tạo message giả lập
        message = f"""
        Status: TRADING
        Type: BUY
        Price: ₫26085
        Fiat Amount: 16301820.00000000 VND
        Crypto Amount: 624.95000000 USDT
        Order No.: {order_number}
        """
        
        logger.info("🛒 Gọi handle_buy_order...")
        p2p.handle_buy_order(order_number, message)
        
        logger.info("✅ Hoàn thành test P2P handling")
        
    except Exception as e:
        logger.error(f"💥 Lỗi trong P2P handling: {str(e)}", exc_info=True)

def main():
    """Main function"""
    # Order number từ log của bạn
    order_number = "22768168737054167040"
    
    logger.info("🚀 Bắt đầu debug order processing")
    logger.info(f"📋 Order number: {order_number}")
    
    # Test 1: Trích xuất thông tin
    success = test_order_extraction(order_number)
    
    if success:
        # Test 2: Xử lý trong P2P
        test_p2p_handling(order_number)
    else:
        logger.error("❌ Test trích xuất thất bại, bỏ qua test P2P")
    
    logger.info("🏁 Kết thúc debug")

if __name__ == "__main__":
    main() 