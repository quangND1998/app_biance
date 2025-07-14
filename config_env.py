import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)  # take environment variables from .env file

# Common Environment Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHAT_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

# Specific Environment Variables
BINANCE_KEY = os.getenv("BINANCE_KEY")
BINANCE_SECRET = os.getenv("BINANCE_SECRET")

# Specific Environment Variables
VIETQR_KEY = os.getenv("VIETQR_KEY")
VIETQR_SECRET = os.getenv("VIETQR_SECRET")

# Specific Environment Variables
ACQID = os.getenv("ACQID")
ACCOUNTNO = os.getenv("ACCOUNTNO")
ACCOUNTNAME= os.getenv("ACCOUNTNAME")

# telegram url
TELEGRAM_URL = os.getenv("TELEGRAM_URL")

# CHROME
CHROME_PATH = os.getenv("CHROME_PATH")
CHROME_DRIVE = os.getenv("CHROME_DRIVE")

# Version
VERSION = os.getenv("VERSION", "1.0.0")