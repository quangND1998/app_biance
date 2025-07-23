import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_env import VIETQR_KEY, VIETQR_SECRET, ACQID, ACCOUNTNAME, ACQID, ACCOUNTNO
import requests
import base64
import io
import logging
import json
from rapidfuzz import process,fuzz
import unicodedata
import re
import os
import time


bank_dict_path =  os.path.join(os.path.dirname(os.path.dirname(__file__)), "bank_list.json")
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def generate_vietqr(accountno=ACCOUNTNO, accountname=ACCOUNTNAME, acqid=ACQID, addInfo='', amount='', template=''):
    logger.info(f"Start generating QR code for account {accountno}")
    start_time = time.time()
    url = "https://api.vietqr.io/v2/generate"
    headers = {
        "x-client-id": VIETQR_KEY,
        "x-api-key": VIETQR_SECRET,
        "Content-Type": "application/json"
    }
    payload = {
        "accountNo": accountno,
        "accountName": accountname,
        "acqId": acqid,
        "addInfo": addInfo, # Additional information for the transaction
        "amount": amount, # Amount in VND
        "template": template # Template for the QR code
    }

    logger.info(f"[generate_vietqr] Bắt đầu tạo QR cho account: {accountno}, bank: {acqid}, amount: {amount}")
    response = requests.post(url, json=payload, headers=headers)
    response_json = response.json()
    elapsed = (time.time() - start_time) * 1000  # ms
    logger.info(f"[generate_vietqr] Xử lý xong sau {elapsed:.2f} ms, status_code={response.status_code}")
    if response.status_code == 200 and "data" in response_json and "qrDataURL" in response_json["data"]:
        qr_data_url = response_json["data"]["qrDataURL"]
        header, encoded = qr_data_url.split(",", 1)
        image_data = base64.b64decode(encoded)
        return io.BytesIO(image_data)
    else:
        logger.error(f"Lỗi tạo QR: {response_json}")
        raise Exception(f"Lỗi tạo QR: {response_json}")

def get_nganhang_api():
    """
    Lấy danh sách ngân hàng từ API VietQR và lưu vào file bank_list.json
    Returns:
        dict: Danh sách ngân hàng dạng dictionary nếu thành công, None nếu thất bại
    """
    url = 'https://api.vietqr.io/v2/banks'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        banks_data = response.json()
        
        # Chuyển đổi format dữ liệu
        formatted_banks = {}
        for bank in banks_data.get('data', []):
            bank_code = bank.get('code')
            if bank_code:
                formatted_banks[bank.get('shortName', bank_code)] = {
                    "id": bank.get('id'),
                    "name": bank.get('name'),
                    "code": bank_code,
                    "bin": bank.get('bin'),
                    "logo": bank.get('logo'),
                    "transferSupported": bank.get('transferSupported', 0),
                    "lookupSupported": bank.get('lookupSupported', 0),
                    "short_name": bank.get('short_name'),
                    "support": bank.get('support', 0),
                    "isTransfer": bank.get('isTransfer', 0),
                    "swift_code": bank.get('swift_code')
                }
        
        # Lưu vào file bank_list.json
        with open(bank_dict_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_banks, f, ensure_ascii=False, indent=4)
            
        logger.info("Đã cập nhật danh sách ngân hàng thành công vào file bank_list.json")
        return formatted_banks
    except requests.RequestException as e:
        logger.error(f"Lỗi khi lấy danh sách ngân hàng: {e}")
        return None
    except Exception as e:
        logger.error(f"Lỗi không xác định: {e}")
        return None

def normalize_text(text):
    if not text:
        return ""
    # Loại bỏ dấu tiếng Việt, chuyển về lower, loại bỏ khoảng trắng
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])
    return text.lower().replace(" ", "")

# def get_nganhang_id(name_bank: str) -> str:
#     try:
#         with open(bank_dict_path, 'r', encoding="utf-8") as f:
#             banks = json.load(f)
#             name_bank_norm = normalize_text(name_bank)
#             # 1. So sánh chính xác với nhiều trường
#             for key, info in banks.items():
#                 candidates = [
#                     key,
#                     info.get("name", ""),
#                     info.get("code", ""),
#                     info.get("short_name", "")
#                 ]
#                 for candidate in candidates:
#                     if normalize_text(candidate) == name_bank_norm:
#                         logger.info(f"Match found: {candidate} for input: {name_bank}")
#                         return info.get("bin")
#             # 2. Nếu không tìm thấy, dùng so sánh gần đúng (find_best_match với key)
#             list_banks = list(banks.keys())
#             result = find_best_match(name_bank, list_banks)
#             if result:
#                 key, score = result
#                 if score >= 88:
#                     logger.info(f"Best match: {key} with accuracy: {score}")
#                     return banks[key].get("bin")
#                 else:
#                     logger.warning(f"Low confidence match for '{name_bank}': {key} ({score})")
#             else:
#                 logger.warning(f"No match found for {name_bank}")
#             return None
#     except FileNotFoundError:
#         logger.error("bank_list.json not found.")
#         return None
#     except json.JSONDecodeError:
#         logger.error("Invalid JSON format in bank_list.json.")
#         return None
#     except Exception as e:  
#         logger.error(f"Unexpected error: {e}")
#         return None

def get_nganhang_id(name_bank: str) -> str:
    # Nếu name_bank là 'MB' (không phân biệt hoa thường, bỏ khoảng trắng), đổi thành 'MBBank'
    if normalize_text(name_bank) == 'mb':
        name_bank = 'MBBank'
    try:
        with open(bank_dict_path, 'r', encoding="utf-8") as f:
            banks = json.load(f)
            name_bank_norm = normalize_text(name_bank)
          
            # 1. So khớp chính xác với key
            for key in banks.keys():
                if normalize_text(key) == name_bank_norm:
                    logger.info(f"Exact key match: {key} for input: {name_bank}")
                    return banks[key].get("bin")
            # 2. So khớp chính xác hoặc gần giống (chứa trong nhau)
            for key, info in banks.items():
                candidates = [
                    key,
                    info.get("name", ""),
                    info.get("code", ""),
                    info.get("short_name", "")
                ]

                for candidate in candidates:
                    candidate_norm = normalize_text(candidate)
                    if (
                        name_bank_norm == candidate_norm or
                        name_bank_norm in candidate_norm
                    ):
                        logger.info(f"Match found: {candidate} for input: {name_bank}")
                        return info.get("bin")

            # 3. So khớp gần đúng với fuzzy matching nếu không tìm được ở bước 1
            all_candidates = set()
            for key, info in banks.items():
                all_candidates.update([
                    key,
                    info.get("name", ""),
                    info.get("code", ""),
                    info.get("short_name", "")
                ])

            result = find_best_match(name_bank, list(all_candidates))
            if result:
                match_text, score = result
                if score >= 66:
                    logger.info(f"Best fuzzy match: {match_text} (accuracy: {score})")
                    # Tìm ra ngân hàng chứa match_text
                    for info in banks.values():
                        if match_text in [
                            info.get("name", ""),
                            info.get("code", ""),
                            info.get("short_name", "")
                        ]:
                            return info.get("bin")
                else:
                    logger.warning(f"Low confidence match for '{name_bank}': {match_text} ({score})")
            else:
                logger.warning(f"No match found for '{name_bank}'")
            return None

    except FileNotFoundError:
        logger.error("bank_list.json not found.")
        return None
    except json.JSONDecodeError:
        logger.error("Invalid JSON format in bank_list.json.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None

# def find_best_match(query, choices):
#     try:
#         norm_query = normalize_text(query)
#         norm_choices = [normalize_text(c) for c in choices]
#         match = process.extractOne(norm_query, norm_choices)
#         if match:
#             original_match = choices[norm_choices.index(match[0])]
#             return original_match, match[1]
#         return None
#     except Exception as e:
#         logger.error(f"Error finding best match: {e}")
#         return None
def find_best_match(query, choices):
    try:
        norm_query = normalize_text(query)

        # Map: normalized → original
        norm_map = {normalize_text(c): c for c in choices}
        norm_choices = list(norm_map.keys())

        match = process.extractOne(norm_query, norm_choices, scorer=fuzz.token_sort_ratio)
        if match:
            matched_norm, score, _ = match  # <- FIX: unpack đúng 3 phần tử
            original_match = norm_map[matched_norm]
            return original_match, score
        return None
    except Exception as e:
        logger.error(f"Error finding best match: {e}")
        return None

def get_bank_bin(bank_name: str) -> str:
    """
    Lấy mã BIN của ngân hàng từ tên ngân hàng
    Args:
        bank_name (str): Tên ngân hàng (có thể là tên đầy đủ hoặc tên viết tắt)
    Returns:
        str: Mã BIN của ngân hàng, nếu không tìm thấy trả về None
    """
    try:
        # Đọc file bank_list.json
        current_dir = os.path.dirname(os.path.abspath(__file__))
        bank_list_path = os.path.join(os.path.dirname(current_dir), "bank_list.json")
        
        with open(bank_list_path, 'r', encoding='utf-8') as f:
            banks = json.load(f)
        
        # Tìm kiếm ngân hàng theo tên
        bank_name = bank_name.upper()
        for bank_code, bank_info in banks.items():
            if (bank_name in bank_code.upper() or 
                bank_name in bank_info['name'].upper() or 
                bank_name in bank_info['short_name'].upper()):
                return bank_info['bin']
        
        return None
    except Exception as e:
        print(f"Lỗi khi lấy mã BIN ngân hàng: {e}")
        return None

if __name__ == '__main__':
    banks_to_test = [
        "Vietinbank",
        "Vietcombank",
        "Teckcombanh",  # Sai chính tả
        "MB Bank",
        "ACB",
        "TPBank",
        "Sacombank",
        "Bong bong bank",  # Sai hoàn toàn
        'Ngân hàng Quân đội',
        'MBank',
        'Ngân hàng thương mại cổ phần Việt Nam Thịnh Vượng (VPBank)',
        'Ngân hàng TMCP Công thương Việt Nam (Vietcombank)'
        'VCB-Vietcombank',
        'VietBank',
        'Ngân hàng Thương mại cổ phần Quân đội',
        'MB',
        'Ngân hàng TMCP Việt nam thịnh Vượng',
        'Vietcombank',
        'Vietinbank'

        # 'ABC bank'
    ]
    for name in banks_to_test:
        print(f"{name} → {get_nganhang_id(name)}")