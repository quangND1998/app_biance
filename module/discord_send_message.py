import logging
import os
import sys
import requests
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config_env import DISCORD_WEBHOOK
from module.generate_qrcode import generate_vietqr

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class DiscordBot:
    def __init__(self, webhook_url):
        self.webhook_url = DISCORD_WEBHOOK if webhook_url is None else webhook_url

    def send_message(self, content):
        data = {"content": content}
        try:
            response = requests.post(self.webhook_url, json=data)
            if response.status_code == 204:
                logger.info("📨 Gửi tin nhắn thành công")
                return {"ok": True}
            else:
                logger.error(f"❌ Gửi thất bại: {response.status_code}, {response.text}")
                return {"ok": False, "error": response.text}
        except Exception as e:
            logger.exception("❌ Lỗi gửi webhook")
            return {"ok": False, "error": str(e)}

    def send_photo(self, image, caption=""):
        try:
                files = {
                    'file': ('image.png', image, 'image/png')
                }
                payload = {'content': caption}
                response = requests.post(self.webhook_url, data=payload, files=files)
                if response.status_code in (200, 204):
                    logger.info("🖼 Ảnh gửi thành công")
                    return {"ok": True}
                else:
                    logger.error(f"❌ Gửi ảnh thất bại: {response.status_code}, {response.text}")
                    return {"ok": False, "error": response.text}
        except Exception as e:
            logger.exception("❌ Lỗi gửi ảnh")
            return {"ok": False, "error": str(e)}

if __name__ == "__main__":
    bot = DiscordBot(webhook_url='https://discord.com/api/webhooks/1381122297104175246/oyttLr1x76JL52K896ZiU8vbH87D82pD-CdMesReyVo749L9yyYayDWeM7oKlXiN79hh')
    bot.send_message(f"""
                🔔 [Thông báo]!
                Thông tin người bán:
                Đối chiếu với QR code bên dưới!"""
                )
    image = generate_vietqr(
                accountno="0818331300",
                accountname="An Hoàng Anh",
                acqid="970436",
                addInfo="reference_message",
                amount=150000,
                template="rc9Vk60")
    bot.send_photo(image, "📷 Đây là ảnh test gửi từ bot Discord.")