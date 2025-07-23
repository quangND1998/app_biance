import logging
import time
from datetime import datetime
from binance.client import Client
from binance.exceptions import BinanceAPIException
from config_env import BINANCE_KEY, BINANCE_SECRET
from module.generate_qrcode import generate_vietqr, get_nganhang_id
import re
from unidecode import unidecode
# from module.telegram_send_message import TelegramBot
from module.discord_send_message import DiscordBot
from module.selenium_get_info import extract_order_info, extract_info_by_key
import pandas as pd
from module.transaction_storage import TransactionStorage
from dotenv import load_dotenv
import os

# Load biến môi trường
load_dotenv()
BINANCE_KEY = os.getenv("BINANCE_KEY")
BINANCE_SECRET = os.getenv("BINANCE_SECRET")

logging.basicConfig(
    format="%(asctime)s  %(name)s  %(levelname)s: %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class P2PBinance:
    def __init__(self, storage_dir: str = "transactions", api_key: str = None, api_secret: str = None):
        """
        Khởi tạo P2PBinance
        Args:
            storage_dir: Thư mục lưu trữ dữ liệu giao dịch
            api_key: Binance API key (nếu không truyền sẽ sử dụng từ biến môi trường)
            api_secret: Binance API secret (nếu không truyền sẽ sử dụng từ biến môi trường)
        """
        self._stop_flag = False
        self._running = False
        self.current_transaction = None
        self.logger = logging.getLogger("P2P")
        self.storage = TransactionStorage(storage_dir)

        # Sử dụng API keys được truyền vào hoặc từ biến môi trường
        self.api_key = api_key or BINANCE_KEY
        self.api_secret = api_secret or BINANCE_SECRET

        # Khởi tạo Binance client
        try:
            self.logger.info(
                f"Initializing Binance client with key: {self.api_key[:5]}..."
            )
            self.client = Client(self.api_key, self.api_secret)
            self.logger.info("Binance client initialized successfully")
            self.sync_time_with_binance()
        except Exception as e:
            self.logger.error(f"Failed to initialize Binance client: {e}")
            raise

    def sync_time_with_binance(self):
        """
        Đồng bộ thời gian local với server Binance để tránh lỗi timestamp (-1021)
        """
        try:
            server_time = self.client.get_server_time()
            local_time = int(time.time() * 1000)
            offset = server_time["serverTime"] - local_time
            self.client.TIME_OFFSET = offset
            # self.logger.info(f"Đã đồng bộ thời gian với Binance. TIME_OFFSET = {offset} ms")
        except Exception as e:
            self.logger.error(f"Lỗi khi đồng bộ thời gian với Binance: {e}")

    def handle_buy_order(self, order_number, message):
        """Xử lý đơn hàng mua"""
        self.logger.info(f"🔍 Bắt đầu xử lý BUY order: {order_number}")
        try:
            t0 = time.time()
            existing_tx = self.storage.get_transaction_by_order(order_number)
            t1 = time.time()
            self.logger.info(f"[handle_buy_order] get_transaction_by_order: {(t1-t0)*1000:.2f} ms")
            if existing_tx:
                self.logger.info(f"✅ Order {order_number} đã tồn tại trong database, bỏ qua xử lý.")
                self.current_transaction = existing_tx
                return
            # Trích xuất thông tin từ order
            self.logger.info(f"📋 Đang trích xuất thông tin cho order: {order_number}")
            infor_seller = extract_order_info(order_number)
            t2 = time.time()
            self.logger.info(f"[handle_buy_order] extract_order_info: {(t2-t1)*1000:.2f} ms")
            self.logger.info(f"📊 Thông tin trích xuất ban đầu: {infor_seller}")
            if not infor_seller:
                self.logger.error(f"❌ Không thể trích xuất thông tin cho order: {order_number}")
                return
            message = "".join(f"{k}: {v}\n" for k, v in infor_seller.items())
            self.logger.debug(f"📝 Message được tạo: {message}")
            infor_seller = extract_info_by_key(infor_seller)
            self.logger.info(f"🔧 Thông tin sau khi xử lý: {infor_seller}")
            fiat_amount = infor_seller.get("Fiat amount")
            full_name = infor_seller.get("Full Name")
            bank_card_raw = infor_seller.get("Bank Card")
            bank_card = re.sub(r"\\D", "", bank_card_raw) if bank_card_raw else ""
            bank_name = infor_seller.get("Bank Name")
            reference_message = infor_seller.get("Reference message")
            # Log từng trường thông tin
            self.logger.info(f"💰 Fiat Amount: {fiat_amount}")
            self.logger.info(f"👤 Full Name: {full_name}")
            self.logger.info(f"💳 Bank Card: {bank_card}")
            self.logger.info(f"🏦 Bank Name: {bank_name}")
            self.logger.info(f"📝 Reference Message: {reference_message}")
            # Tạo thông tin giao dịch
            transaction_info = {
                "type": "buy",
                "order_number": order_number,
                "amount": fiat_amount,
                "bank_name": bank_name,
                "account_number": bank_card,
                "account_name": full_name,
                "reference": reference_message,
                "message": message,
            }
            # Kiểm tra điều kiện đầy đủ thông tin
            required_fields = [fiat_amount, bank_card, bank_name, reference_message, full_name]
            missing_fields = []
            if not fiat_amount:
                missing_fields.append("Fiat Amount")
            if not bank_card:
                missing_fields.append("Bank Card")
            if not bank_name:
                missing_fields.append("Bank Name")
            if not reference_message:
                missing_fields.append("Reference Message")
            if not full_name:
                missing_fields.append("Full Name")
            if missing_fields:
                self.logger.warning(f"⚠️ Thiếu thông tin cho order {order_number}: {missing_fields}")
                self.logger.info(f"📋 Thông tin hiện có: {transaction_info}")
                return
            self.logger.info(f"✅ Đủ thông tin, bắt đầu tạo QR code cho order: {order_number}")
            # Đảm bảo chỉ xử lý tiếp khi đủ thông tin
            if all([fiat_amount, bank_card, bank_name, reference_message, full_name]):
                acqid_bank = get_nganhang_id(bank_name)
                if not acqid_bank:
                    self.logger.error(f"❌ Không tìm được mã ngân hàng cho: {bank_name}. Vẫn lưu transaction với trạng thái lỗi.")
                    transaction_info['qr_error'] = "Không tìm được mã ngân hàng"
                    qr_image = generate_vietqr()
                    qr_bytes = qr_image.getvalue()
                    t3 = time.time()
                    qr_path = self.storage.save_transaction(transaction_info, None, "ERROR_BANK_NAME")
                    t4 = time.time()
                    self.logger.info(f"[handle_buy_order] save_transaction (ERROR_BANK_NAME): {(t4-t3)*1000:.2f} ms")
                    self.current_transaction = transaction_info
                    self.current_transaction["qr_path"] = qr_path
                    self.logger.info(f"🎉 Hoàn thành xử lý BUY order: {order_number}")
                    self.logger.info(f"[handle_buy_order] Tổng thời gian xử lý: {(t4-t0)*1000:.2f} ms")
                    return
                self.logger.info(f"🏦 Bank ID: {acqid_bank} cho ngân hàng: {bank_name}")
                t3 = time.time()
                if full_name:
                    full_name_latin = unidecode(full_name)
                else:
                    full_name_latin = ""
                qr_image = generate_vietqr(
                    accountno=bank_card,
                    accountname=full_name_latin,
                    acqid=acqid_bank,
                    addInfo=reference_message,
                    amount=fiat_amount,
                    template="rc9Vk60",
                )
                qr_bytes = qr_image.getvalue()
                self.logger.info(f"📸 Đã tạo QR code, kích thước: {len(qr_bytes)} bytes")
                t4 = time.time()
                self.logger.info(f"[handle_buy_order] generate_vietqr: {(t4-t3)*1000:.2f} ms")
                qr_path = self.storage.save_transaction(transaction_info, qr_bytes, "TRADING")
                t5 = time.time()
                self.logger.info(f"[handle_buy_order] save_transaction: {(t5-t4)*1000:.2f} ms")
                self.current_transaction = transaction_info
                self.current_transaction["qr_path"] = qr_path
                self.logger.info(f"🎉 Hoàn thành xử lý BUY order: {order_number}")
                self.logger.info(f"[handle_buy_order] Tổng thời gian xử lý: {(t5-t0)*1000:.2f} ms")
            else:
                self.logger.error(f"❌ Điều kiện all() không thỏa mãn cho order: {order_number}")
        except Exception as e:
            self.logger.error(f"💥 Lỗi khi xử lý BUY order {order_number}: {str(e)}", exc_info=True)

    def handle_sell_order(self, order_number, fiat_amount, message):
        """Xử lý đơn hàng bán"""
        self.logger.info(f"🔍 Bắt đầu xử lý SELL order: {order_number}")
        try:
            # Kiểm tra nếu order_number đã tồn tại thì không tạo lại
            existing_tx = self.storage.get_transaction_by_order(order_number)
            if existing_tx:
                # Nếu transaction đã tồn tại, dù có QR hay không cũng bỏ qua để tránh tracking liên tục
                self.logger.info(f"✅ Order {order_number} đã tồn tại trong database, bỏ qua xử lý.")
                self.current_transaction = existing_tx
                return
            
            qr_image = generate_vietqr(
                addInfo=order_number, amount=fiat_amount, template="rc9Vk60"
            )

            # Chuyển đổi BytesIO thành bytes
            qr_bytes = qr_image.getvalue()
            self.logger.info(f"📸 Đã tạo QR code cho SELL order, kích thước: {len(qr_bytes)} bytes")

            # Tạo thông tin giao dịch
            transaction_info = {
                "type": "sell",
                "order_number": order_number,
                "amount": fiat_amount,
                "message": message,
            }

            # Lưu thông tin giao dịch và mã QR
            qr_path = self.storage.save_transaction(transaction_info, qr_bytes, "TRADING")
            self.logger.info(f"💾 Đã lưu QR code tại: {qr_path}")

            # Cập nhật thông tin giao dịch hiện tại
            self.current_transaction = transaction_info
            self.current_transaction["qr_path"] = qr_path
            
            self.logger.info(f"🎉 Hoàn thành xử lý SELL order: {order_number}")
        except Exception as e:
            self.logger.error(f"💥 Lỗi khi xử lý SELL order {order_number}: {str(e)}", exc_info=True)

    def get_recent_transactions(self, limit: int = 10) -> list:
        """Lấy danh sách giao dịch gần đây"""
        return self.storage.get_recent_transactions(limit)

    def get_transaction(self, order_number: str) -> dict:
        """Lấy thông tin giao dịch theo mã đơn hàng"""
        return self.storage.get_transaction(order_number)

    def get_transactions_by_date(self, start_date: str, end_date: str) -> list:
        """Lấy danh sách giao dịch trong khoảng thời gian"""
        return self.storage.get_transactions_by_date(start_date, end_date)

    def transactions_trading(self):
        self._stop_flag = False  # Reset cờ dừng khi bắt đầu RUN mới

        time.sleep(2)  # Test: giữ worker chạy 3 giây để kiểm tra nút DỪNG
        status = {
            "COMPLETED": "COMPLETED",
            "PENDING": "PENDING",
            "TRADING": "TRADING",
            "BUYER_PAYED": "BUYER PAYED",
            "DISTRIBUTING": "DISTRIBUTING",
            "IN_APPEAL": "IN APPEAL",
            "CANCELLED": "CANCELLED",
            "CANCELLED_BY_SYSTEM": "CANCELLED BY SYSTEM",
        }
        side = {"BUY": "BUY", "SELL": "SELL"}
        
        # Load used_orders từ JSON thay vì khởi tạo rỗng
        end = int(datetime.utcnow().timestamp() * 1000)
        start = end - 2700000  # ~45 minutes
        used_orders = self.storage.load_used_orders(start_timestamp=start, end_timestamp=end)
        self.logger.info(f"📋 Đã load {len(used_orders)} orders từ used_orders.json")
        
        err_count = 0
        self.startup_update(used_orders)
        while not self._stop_flag:
            try:
                # 🔄 Reload used_orders từ JSON mỗi lần lặp để đảm bảo đồng bộ
                end = int(datetime.utcnow().timestamp() * 1000)
                start = end - 2700000  # ~45 minutes
                used_orders = self.storage.load_used_orders(start_timestamp=start, end_timestamp=end)
                
                for trade_type in ["BUY", "SELL"]:
                    if self._stop_flag:
                        break
                    end = int(datetime.utcnow().timestamp() * 1000)
                    start = end - 2700000  # ~45 minutes

                    result = self.get_c2c_trade_history(
                        tradeType=trade_type, startDate=start, endDate=end
                    )

                    for order in result["data"]:
                        if self._stop_flag:
                            break
                        order_status = order["orderStatus"]
                        order_number = order["orderNumber"]
                        previous_status = used_orders.get(order_number)
                        # self.logger.info(
                        #     f"[Order] #{order_number} | Status: {order_status} | Type: {order['tradeType']} | "
                        #     f"Price: {order['fiatSymbol']}{order['unitPrice']} | "
                        #     f"Fiat Amount: {order['totalPrice']} {order['fiat']} | "
                        #     f"Crypto Amount: {order['amount']} {order['asset']} | "
                        #     f"Created at: {datetime.fromtimestamp(order['createTime']/1000).strftime('%Y-%m-%d %H:%M:%S')}"
                        # )
                        # if order_status == "TRADING":
                        #     self.logger.info(
                        #         f"[Order] #{order_number} | Status: {order_status} | Type: {order['tradeType']} | "
                        #         f"Price: {order['fiatSymbol']}{order['unitPrice']} | "
                        #         f"Fiat Amount: {order['totalPrice']} {order['fiat']} | "
                        #         f"Crypto Amount: {order['amount']} {order['asset']} | "
                        #         f"Created at: {datetime.fromtimestamp(order['createTime']/1000).strftime('%Y-%m-%d %H:%M:%S')}"
                        #     )
                        #     self.logger.info(
                        #         f"[Order] #{order_number} | Pervious Status: {previous_status}  "
                        #     )
                            # Log toàn bộ thông tin order
                            # self.logger.info(f"📋 Toàn bộ thông tin order {order_number}:")
                            # for key, value in order.items():
                            #     self.logger.info(f"   {key}: {value}")

                        if previous_status is None or previous_status != order_status:
                            if order_status == 'TRADING':
                                self.logger.info(f"🔄 Status thay đổi cho order {order_number}: {previous_status} -> {order_status}")
                            
                            # Log toàn bộ thông tin order khi có thay đổi status
                            # self.logger.info(f"📋 Toàn bộ thông tin order {order_number} (Status: {order_status}):")
                            # for key, value in order.items():
                            #     self.logger.info(f"   {key}: {value}")
                            
                            message = (
                                f"Status: {status.get(order_status)}\n"
                                f"Type: {side.get(order['tradeType'])}\n"
                                f"Price: {order['fiatSymbol']}{order['unitPrice']}\n"
                                f"Fiat Amount: {float(order['totalPrice'])} {order['fiat']}\n"
                                f"Crypto Amount: {float(order['amount'])} {order['asset']}\n"
                                f"Order No.: {order_number}"
                            )

                            used_orders[order_number] = order_status
                            # Cập nhật vào JSON
                            self.storage.update_used_orders(order_number, order_status)
                            self._send_notification(message)

                            if order_status == 'TRADING':
                                self.logger.info(f"🎯 Bắt đầu xử lý order TRADING: {order_number} (Type: {trade_type})")
                                if trade_type == "BUY":
                                    self.logger.info(f"🛒 Gọi handle_buy_order cho order: {order_number}")
                                    self.handle_buy_order(order_number, message)
                                elif trade_type == "SELL":
                                    self.logger.info(f"🛍️ Gọi handle_sell_order cho order: {order_number}")
                                    self.handle_sell_order(
                                        order_number,
                                        float(order["totalPrice"]),
                                        message,
                                    )
                                else:
                                    self.logger.warning(f"⚠️ Trade type không xác định: {trade_type}")
                            # else:
                                # self.logger.info(f"📝 Order {order_number} có status {order_status} (không phải TRADING)")

                if self._stop_flag:
                    break
                time.sleep(1)
                if self._stop_flag:
                    break
            except Exception as e:
                err_count += 1
                if err_count > 3:
                    self._running = False
                    self._send_notification(f"Error Count is {err_count}. Bot Stopped.")
                if self._stop_flag:
                    break
        self.logger.info("🛑 Đã thoát vòng lặp transactions_trading.")

    def stop(self):
        self._stop_flag = True
        logger.info("🛑 Yêu cầu dừng Binance P2P...")

    def get_c2c_trade_history(self, tradeType, startDate=None, endDate=None):
        """Lấy lịch sử giao dịch C2C"""
        try:
            self.sync_time_with_binance()  # Luôn đồng bộ lại trước khi gọi API
            return self.client.get_c2c_trade_history(
                tradeType=tradeType, startDate=startDate, endDate=endDate, recvWindow=10000
            )
        except Exception as e:
            raise

    def _send_notification(self, message):
        """Gửi thông báo qua các kênh đã cấu hình"""
        try:
            if hasattr(self, "telegram_bot"):
                self.telegram_bot.send_message(message)
            if hasattr(self, "discord_bot"):
                self.discord_bot.send_message(message)
        except Exception as e:
            pass  # Bỏ qua lỗi khi gửi thông báo

    def get_all_c2c_trades(self, start_timestamp=None, end_timestamp=None):
        """Lấy tất cả giao dịch C2C trong khoảng thời gian và trả về DataFrame đã xử lý"""
        rows = 100
        all_trades = []

        if start_timestamp:
            start_timestamp = int(start_timestamp)
        if end_timestamp:
            end_timestamp = int(end_timestamp)

        for trade_type in ["BUY", "SELL"]:
            page = 1
            while True:
                params = {"tradeType": trade_type, "page": page, "rows": rows}
                if start_timestamp:
                    params["startTimestamp"] = start_timestamp
                if end_timestamp:
                    params["endTimestamp"] = end_timestamp

                try:
                    result = self.client.get_c2c_trade_history(**params)
                except BinanceAPIException as e:
                    break
                except Exception as e:
                    break

                trades = result.get("data", [])
                if trades:
                    all_trades.extend(trades)
                else:
                    break

                if page >= 100:
                    break

                page += 1

        if not all_trades:
            return pd.DataFrame()

        try:
            # Chuyển đổi thành DataFrame
            df = pd.json_normalize(all_trades)

            # Lọc chỉ lấy giao dịch hoàn thành
            df = df[df["orderStatus"] == "COMPLETED"]

            if df.empty:
                return pd.DataFrame()

            # Xử lý thời gian
            df["createTime"] = pd.to_datetime(df["createTime"], unit="ms")
            df["createDay"] = df["createTime"].dt.date

            # Chuyển đổi kiểu dữ liệu số
            numeric_columns = ["totalPrice", "commission", "takerCommission"]
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            # Groupby và tính tổng
            df_grouped = (
                df.groupby(["createDay", "tradeType", "orderStatus"])
                .agg(
                    totalPrice_sum=("totalPrice", "sum"),
                    commission_sum=("commission", "sum"),
                    takercommission_sum=("takerCommission", "sum"),
                )
                .reset_index()
            )

            return df_grouped

        except Exception as e:
            return pd.DataFrame()

    def thongke_today(self):
        all_data = []
        try:
            for trd in ["BUY", "SELL"]:
                res = self.client.get_c2c_trade_history(
                    tradeType=trd,
                )
                logger.debug(f"Trade History Result for {trd}: {res}")
                if res.get("data"):
                    all_data.extend(res["data"])

            if not all_data:
                logger.info("No trade data found for today.")
                return pd.DataFrame()

            df = pd.json_normalize(all_data)
            df["createTime"] = df["createTime"].apply(
                lambda x: datetime.fromtimestamp(x / 1000).strftime("%Y-%m-%d %H:%M:%S")
            )
            df["createDay"] = pd.to_datetime(
                df["createTime"], format="%Y-%m-%d %H:%M:%S"
            ).dt.date
            today = datetime.utcnow().date()
            # df_today = df[df["createDay"] == today]
            df_today = df
            df_today = df_today[
                [
                    "createDay",
                    "tradeType",
                    "orderStatus",
                    "totalPrice",
                    "unitPrice",
                    "commission",
                ]
            ]
            df_today["totalPrice"] = df_today["totalPrice"].astype(float)
            df_today["commission"] = df_today["commission"].astype(float)
            df_today = (
                df_today.groupby(["createDay", "tradeType", "orderStatus"])
                .agg({"totalPrice": ["sum"], "commission": ["sum"]})
                .reset_index()
            )
        except Exception as e:
            logger.error(f"Error in thongke_today: {e}", exc_info=True)
            df_today = pd.DataFrame()
        return df_today

    def startup_update(self, database: dict):
        """Cập nhật database với dữ liệu từ Binance API và lưu vào JSON"""
        self.logger.info("🚀 Bắt đầu startup_update...")
        
        try:
            for trd in ["BUY", "SELL"]:
                res = self.get_c2c_trade_history(tradeType=trd)
                self.logger.debug(f"Startup Trade History Result for {trd}: {res}")
                
                if res.get("data"):
                    for k in res["data"]:
                        order_number = k["orderNumber"]
                        order_status = k["orderStatus"]
                        database[order_number] = order_status
                        
                        # Cập nhật vào JSON
                        self.storage.update_used_orders(order_number, order_status)
            
            self.logger.info(f"✅ Startup_update hoàn thành, đã cập nhật {len(database)} orders")
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi trong startup_update: {e}")
            # Vẫn tiếp tục với database hiện tại nếu có lỗi