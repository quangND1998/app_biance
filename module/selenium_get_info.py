"""
Module này được sử dụng để tự động hóa trình duyệt Chrome cho ứng dụng Binance P2P Trading.
Mục đích: Tự động hóa các thao tác đăng nhập và lấy thông tin giao dịch từ Binance P2P.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import os
import time
import re
import subprocess
import sys
import logging
from pathlib import Path
import psutil
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config_env import CHROME_DRIVE, CHROME_PATH
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sử dụng Path để xử lý đường dẫn an toàn hơn
BASE_DIR = Path(__file__).parent.parent
PROFILE_PATH = BASE_DIR / "SeleniumProfile"

# Biến global để lưu driver
_login_driver = None
_cached_driver = None  # Cache driver để tái sử dụng

def update_chromedriver():
    """Cập nhật ChromeDriver lên version mới nhất"""
    try:
        logger.info("Đang kiểm tra và cập nhật ChromeDriver...")
        driver_path = ChromeDriverManager().install()
        logger.info(f"ChromeDriver đã được cập nhật: {driver_path}")
        return driver_path
    except Exception as e:
        logger.error(f"Lỗi khi cập nhật ChromeDriver: {e}")
        raise

def kill_chrome_processes():
    """Chỉ đóng các Chrome process được tạo bởi Selenium, không đóng Chrome của user"""
    try:
        # Không đóng Chrome của user, chỉ đóng nếu có lỗi
        logger.info("Bỏ qua việc đóng Chrome processes để tránh ảnh hưởng đến Chrome của user")
        pass
    except Exception as e:
        logger.warning(f"Không thể đóng Chrome processes: {e}")

def extract_info_by_key(data):
    """Trích xuất thông tin từ dữ liệu giao dịch"""
    result = {}
    for key, value in data.items():
        key_lower = key.lower()
        # Map các trường dữ liệu
        if re.search(r'fiat amount', key_lower):
            result['Fiat amount'] = value
        elif re.search(r'reference message', key_lower):
            result['Reference message'] = value
        elif re.search(r'^name$|full name', key_lower):
            result['Full Name'] = value
        elif re.search(r'bank card|account number', key_lower):
            result['Bank Card'] = value
        elif re.search(r'bank name', key_lower):
            result['Bank Name'] = value
    return result

def create_options_new_chrome(headless: bool = True) -> Options:
    """Tạo Chrome options cho Chrome instance mới (không remote debugging)"""
    chrome_options = Options()
    
    # Các tùy chọn cơ bản và bảo mật
    chrome_options.add_argument(f'user-data-dir={str(PROFILE_PATH)}')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--disable-infobars')
    
    # Thêm các tùy chọn để tránh crash
    chrome_options.add_argument('--disable-background-timer-throttling')
    chrome_options.add_argument('--disable-backgrounding-occluded-windows')
    chrome_options.add_argument('--disable-renderer-backgrounding')
    chrome_options.add_argument('--disable-features=TranslateUI')
    chrome_options.add_argument('--disable-ipc-flooding-protection')
    chrome_options.add_argument('--disable-default-apps')
    chrome_options.add_argument('--disable-sync')
    chrome_options.add_argument('--no-first-run')
    chrome_options.add_argument('--no-default-browser-check')
    chrome_options.add_argument('--disable-background-networking')
    chrome_options.add_argument('--disable-component-extensions-with-background-pages')
    chrome_options.add_argument('--disable-client-side-phishing-detection')
    chrome_options.add_argument('--disable-hang-monitor')
    chrome_options.add_argument('--disable-prompt-on-repost')
    chrome_options.add_argument('--disable-domain-reliability')
    chrome_options.add_argument('--disable-component-update')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    
    # Ẩn các lỗi và cảnh báo
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--log-level=3')  # Chỉ hiển thị lỗi nghiêm trọng
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Cài đặt headless nếu cần
    if headless:
        chrome_options.add_argument('--headless=new')
    else:
        chrome_options.add_argument('--window-size=1200,800')
    
    return chrome_options

def create_options(headless: bool = True, port: int = 9222) -> Options:
    """Tạo Chrome options với các cài đặt an toàn"""
    chrome_options = Options()
    
    # Kết nối đến Chrome đã mở sẵn với remote debugging
    chrome_options.debugger_address = f"127.0.0.1:{port}"
    
    # Các tùy chọn cơ bản và bảo mật
    chrome_options.add_argument(f'user-data-dir={str(PROFILE_PATH)}')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--disable-infobars')
    
    # Thêm các tùy chọn để tránh crash
    chrome_options.add_argument('--disable-background-timer-throttling')
    chrome_options.add_argument('--disable-backgrounding-occluded-windows')
    chrome_options.add_argument('--disable-renderer-backgrounding')
    chrome_options.add_argument('--disable-features=TranslateUI')
    chrome_options.add_argument('--disable-ipc-flooding-protection')
    chrome_options.add_argument('--disable-default-apps')
    chrome_options.add_argument('--disable-sync')
    chrome_options.add_argument('--no-first-run')
    chrome_options.add_argument('--no-default-browser-check')
    chrome_options.add_argument('--disable-background-networking')
    chrome_options.add_argument('--disable-component-extensions-with-background-pages')
    chrome_options.add_argument('--disable-client-side-phishing-detection')
    chrome_options.add_argument('--disable-hang-monitor')
    chrome_options.add_argument('--disable-prompt-on-repost')
    chrome_options.add_argument('--disable-domain-reliability')
    chrome_options.add_argument('--disable-component-update')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    
    # Ẩn các lỗi và cảnh báo
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--log-level=3')  # Chỉ hiển thị lỗi nghiêm trọng
    
    # Cài đặt headless nếu cần
    if headless:
        chrome_options.add_argument('--headless=new')
    else:
        chrome_options.add_argument('--window-size=1200,800')
    
    return chrome_options

def create_driver(headless: bool = True, use_existing_chrome: bool = True) -> webdriver.Chrome:
    """Tạo Chrome driver với các cài đặt an toàn"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"Thử tạo driver lần {attempt + 1}/{max_retries}")
            
            if use_existing_chrome:
                # Kết nối đến Chrome đã mở sẵn
                options = create_options(headless=headless)
            else:
                # Tạo Chrome mới
                options = create_options_new_chrome(headless=headless)
            
            # Cập nhật ChromeDriver lên version mới nhất
            driver_path = update_chromedriver()
            
            driver = webdriver.Chrome(
                options=options,
                service=Service(driver_path)
            )
            logger.info("✅ Tạo driver thành công")
            return driver
        except Exception as e:
            logger.error(f"Lỗi khi tạo driver (lần {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                logger.info("Đợi 1 giây trước khi thử lại...")
                time.sleep(1)
                # Xóa cache ChromeDriver để force download version mới
                if attempt == 0:
                    try:
                        import shutil
                        cache_dir = os.path.expanduser("~/.wdm/drivers/chromedriver")
                        if os.path.exists(cache_dir):
                            shutil.rmtree(cache_dir)
                            logger.info("Đã xóa cache ChromeDriver cũ")
                    except Exception as cache_error:
                        logger.warning(f"Không thể xóa cache: {cache_error}")
            else:
                logger.error("Đã thử tối đa số lần, không thể tạo driver")
                raise

def extract_order_info(order_no: str) -> dict:
    def parse_currency(vnd_str):
        try:
            return float(vnd_str.replace("₫", "").replace(",", "").strip())
        except Exception as e:
            logger.error(f"[LỖI] parse_currency: {e}")
            return None

    global _cached_driver
    bank_info = {}
    label,value = None, None
    try:
        logger.info(f"🚀 Bắt đầu trích xuất thông tin cho order: {order_no}")
        
        # Sử dụng cached driver nếu có, nếu không thì tạo mới
        if _cached_driver is None:
            logger.info("Tạo driver mới...")
            _cached_driver = create_driver(False, use_existing_chrome=True)
        else:
            logger.info("Sử dụng cached driver...")
        
        driver = _cached_driver
        
        # Lưu lại handle tab gốc
        original_tab = driver.current_window_handle
        # Mở tab mới trong Chrome hiện tại
        driver.execute_script("window.open('');")
        tabs = driver.window_handles
        new_tab = tabs[-1]
        driver.switch_to.window(new_tab)
        
        url = f"https://p2p.binance.com/en/fiatOrderDetail?orderNo={order_no}"
        logger.info(f"🌐 Đang truy cập URL: {url}")
        driver.get(url)
        
        # Giảm thời gian chờ xuống 0.5 giây cho realtime tracking
        time.sleep(0.5)
        
        logger.info("⏳ Đang chờ trang load...")
        # Tối ưu cho realtime: 6 giây cho lần đầu, 3 giây cho lần retry
        try:
            WebDriverWait(driver, 6).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.subtitle6.text-textBuy'))
                    )
            logger.info("✅ Trang đã load thành công (lần 1)")
        except TimeoutException:
            # Fallback: thử lại với timeout 3 giây
            logger.info("⚠️ Timeout lần 1, thử lại với 3 giây...")
            try:
                WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.subtitle6.text-textBuy'))
                        )
                logger.info("✅ Trang đã load thành công (lần 2)")
            except TimeoutException:
                logger.error("❌ Không thể load trang sau 3 lần thử")
                # Reset cached driver nếu có lỗi nghiêm trọng
                _cached_driver = None
                return bank_info
        
        # Giảm xuống 0.2 giây cho realtime
        time.sleep(1)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        logger.info("📄 Đã parse HTML thành công")
        
        # Tìm fiat amount
        fiat_block = soup.select_one("div.subtitle6.text-textBuy")
        if fiat_block:
            fiat_amount = fiat_block.get_text(strip=True)
            bank_info["Fiat amount"] = parse_currency(fiat_amount)
            logger.info(f"💰 Tìm thấy Fiat Amount: {fiat_amount} -> {bank_info['Fiat amount']}")
        else:
            logger.warning("⚠️ Không tìm thấy Fiat Amount block")

          # Tìm các thông tin khác
        sections = soup.find('div',class_='relative w-full')
        if not sections:
            logger.warning("⚠️ Không tìm thấy section chính")
            return bank_info
            
        label_tag,value_tag = None, None
        found_fields = 0
        
        for section in sections:
            all_divs = section.find_all("div")  
            for div in all_divs:
                if div.get("class") and "body2" in div.get("class") and "text-tertiaryText" in div.get("class"):
                    label_tag = div
                if div.get("class") and "body2" in div.get("class") and "text-right" in div.get("class") and "break-words" in div.get("class"):
                    value_tag = div

                if label_tag and value_tag:
                    label = label_tag.text.strip()
                    value = value_tag.text.strip()
                    bank_info[label] = value
                    found_fields += 1
                    logger.info(f"📋 Tìm thấy field: {label} = {value}")
                    label,value = None, None

        logger.info(f"📊 Tổng số fields tìm thấy: {found_fields}")
        logger.info(f"🎯 Thông tin cuối cùng: {bank_info}")
        
        # Đảm bảo mọi thao tác đã hoàn tất trước khi đóng tab
        time.sleep(1)  # Đảm bảo mọi thao tác đã xong
        # Chỉ đóng tab nếu đã lấy được ít nhất 1 trường dữ liệu
        if found_fields > 0 or bank_info.get("Fiat amount") is not None:
            # Chỉ đóng tab nếu đang ở tab mới script mở ra
            if driver.current_window_handle == new_tab:
                driver.close()
                # Chuyển về tab gốc
                driver.switch_to.window(original_tab)
            logger.info("✅ Hoàn thành trích xuất thông tin và đã đóng tab (nếu cần)")
        else:
            logger.warning("⚠️ Không đóng tab vì chưa lấy được dữ liệu")
        
    except Exception as e:
        logger.error(f"💥 Lỗi khi trích xuất dữ liệu cho order {order_no}: {str(e)}", exc_info=True)
        # Reset cached driver nếu có lỗi
        _cached_driver = None

    finally:
        # Không đóng driver để giữ Chrome mở
        pass
    return bank_info

def launch_chrome_remote_debugging(port: int = 9222) -> None:
    """Khởi chạy Chrome với chế độ remote debugging"""
    chrome_path = Path(CHROME_PATH)
    if not chrome_path.exists():
        raise FileNotFoundError(f"Không tìm thấy Chrome tại: {chrome_path}")
    
    # Tạo command với các tham số an toàn
    command = [
        str(chrome_path),
        f"--remote-debugging-port={port}",
        f'--user-data-dir={str(PROFILE_PATH)}',
        "--no-first-run",
        "--no-default-browser-check",
        "--new-window",
        "--disable-extensions",
        "--disable-popup-blocking",
        "--disable-notifications"
    ]
    
    try:
        # Sử dụng subprocess.Popen với các tham số an toàn
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW  # Ẩn console window
        )
        time.sleep(3)  # Đợi Chrome khởi động
        logger.info("Chrome đã được khởi chạy thành công")
    except Exception as e:
        logger.error(f"Lỗi khi khởi chạy Chrome: {e}")
        raise

def login_app():
    global _login_driver
    bank_info = {}
    try:
        # Sử dụng Chrome đã mở sẵn với remote debugging
        _login_driver = create_driver(False, use_existing_chrome=True)
        
        # Mở tab mới trong Chrome hiện tại
        _login_driver.execute_script("window.open('');")
        tabs = _login_driver.window_handles
        _login_driver.switch_to.window(tabs[-1])
        
        # Điều hướng đến Binance P2P
        _login_driver.get(f"https://p2p.binance.com/en")
        _login_driver.implicitly_wait(60)
        print(f"[THÀNH CÔNG] - Đã mở Binance P2P trong Chrome hiện tại")
        
        # Giữ Chrome mở để người dùng có thể đăng nhập
        # Không đóng driver ở đây

    except Exception as e:
        print(f"[LỖI]: {e}")
        # Chỉ đóng driver khi có lỗi
        if _login_driver:
            _login_driver.quit()
            _login_driver = None
    # Loại bỏ finally block để không đóng driver
    return bank_info

def smart_wait_for_element(driver, selector, timeout=8, fallback_timeout=5, element_name="element"):
    """
    Chờ element xuất hiện với retry logic thông minh
    """
    try:
        logger.info(f"⏳ Đang chờ {element_name}...")
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        logger.info(f"✅ {element_name} đã xuất hiện (lần 1)")
        return True
    except TimeoutException:
        logger.warning(f"⚠️ Timeout lần 1 cho {element_name}, thử lại với {fallback_timeout}s...")
        try:
            WebDriverWait(driver, fallback_timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            logger.info(f"✅ {element_name} đã xuất hiện (lần 2)")
            return True
        except TimeoutException:
            logger.error(f"❌ Không thể tìm thấy {element_name} sau 2 lần thử")
            return False

def wait_for_page_load(driver, url, main_selector='div.subtitle6.text-textBuy'):
    """
    Chờ trang load hoàn toàn với timeout tối ưu
    """
    logger.info(f"🌐 Đang truy cập URL: {url}")
    driver.get(url)
    
    # Chờ trang bắt đầu load
    time.sleep(1)
    
    # Chờ element chính xuất hiện
    if smart_wait_for_element(driver, main_selector, 8, 5, "trang chính"):
        # Thêm thời gian để đảm bảo content render hoàn toàn
        time.sleep(0.5)
        return True
    return False

def adaptive_sleep(base_delay=1, network_condition="normal"):
    """
    Thời gian chờ thích ứng dựa trên điều kiện mạng
    """
    delays = {
        "fast": base_delay * 0.5,
        "normal": base_delay,
        "slow": base_delay * 1.5,
        "very_slow": base_delay * 2
    }
    delay = delays.get(network_condition, base_delay)
    time.sleep(delay)

if __name__ == "__main__":
    login_app()
