from module.binance_p2p import P2PBinance
from module.telegram_send_message import TelegramBot 
from module.selenium_get_info import extract_order_info, launch_chrome_remote_debugging
from datetime import datetime, timedelta
import logging
def thongke_job_sync():
    start_time = int((datetime.now() - timedelta(days=40)).timestamp() * 1000)
    end_time = int(datetime.now().timestamp() * 1000)
    df = P2PBinance().get_all_c2c_trades(start_timestamp=start_time, end_timestamp=end_time)
    print(df)

if __name__ == "__main__":
    infor_seller =  extract_order_info("22764873980271484928")
    print(infor_seller)    #launch_chrome_remote_debugging(port=9222)
