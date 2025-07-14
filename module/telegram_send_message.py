import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import requests
import logging
from config_env import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_URL
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token):
        self.token = TELEGRAM_TOKEN if token is None else token
        self.chat_id = TELEGRAM_CHAT_ID
        self.base_url = f"{TELEGRAM_URL}/bot{self.token}"

    def send_message(self, text, parse_mode="html", disable_web_page_preview=True):
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        try:
            print(url, data)
            response = requests.post(url, data=data)
            result = response.json()
            logger.debug(f"SendMessage Result: {result}")
        except Exception as e:
            logger.exception(f"Exception while sending message: {e}")
            return {"ok": False, "error": str(e)}

        if result.get("ok"):
            message_id = result.get("result", {}).get("message_id", "unknown")
            logger.info(f"[MessageID:{message_id}] Message delivered to {self.chat_id,}")
        else:
            logger.warning(f"Failed to send message to {self.chat_id,}: {result.get('description', 'No description')}")
            logger.debug(f"Message content: {text}")
        return result

    def send_photo(self, photo_data, caption="", parse_mode="html"):
        url = f"{self.base_url}/sendPhoto"
        data = {
            "chat_id": self.chat_id,
            "caption": "<b>🔔 Thanh toán gấp!</b>\nMã QR ở bên dưới. \n" + caption,
            "parse_mode": parse_mode
        }
        files = {
            "photo": ("image.png", photo_data)
        }
        try:
            response = requests.post(url, data=data, files=files)
            result = response.json()
            logger.debug(f"SendPhoto Result: {result}")
        except Exception as e:
            logger.exception(f"Exception while sending photo: {e}")
            return {"ok": False, "error": str(e)}

        if result.get("ok"):
            message_id = result.get("result", {}).get("message_id", "unknown")
            logger.info(f"[MessageID:{message_id}] Photo delivered to {self.chat_id,}")
        else:
            logger.warning(f"Failed to send photo to {self.chat_id,}: {result.get('description', 'No description')}")
        return result
if __name__ == "__main__":
    send_bot = TelegramBot(TELEGRAM_TOKEN).send_message("test")

