import os
import sys

def resource_path(relative_path):
    """
    Lấy đường dẫn tuyệt đối cho file resource, hoạt động cho cả dev và PyInstaller
    
    Args:
        relative_path (str): Đường dẫn tương đối của file resource
        
    Returns:
        str: Đường dẫn tuyệt đối của file resource
    """
    try:
        # PyInstaller tạo một thư mục tạm và lưu đường dẫn trong _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Nếu không phải PyInstaller thì sử dụng thư mục hiện tại
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path) 