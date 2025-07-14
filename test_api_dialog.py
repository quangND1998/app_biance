#!/usr/bin/env python3
"""
Test script để kiểm tra dialog API keys
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from main import ApiKeyDialog

def test_api_dialog():
    """Test dialog API keys"""
    app = QApplication(sys.argv)
    
    print("🔧 Testing API Key Dialog...")
    
    # Test dialog
    dialog = ApiKeyDialog()
    result = dialog.exec_()
    
    if result == ApiKeyDialog.Accepted:
        key, secret = dialog.get_api_keys()
        print(f"✅ Dialog accepted!")
        print(f"🔑 Key: {key[:10]}..." if key else "❌ No key")
        print(f"🔐 Secret: {secret[:10]}..." if secret else "❌ No secret")
    else:
        print("❌ Dialog cancelled")
    
    return result

if __name__ == "__main__":
    test_api_dialog() 