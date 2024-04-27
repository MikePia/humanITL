import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Setup logging configuration
def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "WARNING").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# Accessible variables
CHROME_DOWNLOAD_DIR = os.getenv("CHROME_DOWNLOAD_DIR")
FIREFOX_DOWNLOAD_DIR = os.getenv("FIREFOX_DOWNLOAD_DIR")
FILE_WATCH_DIR = CHROME_DOWNLOAD_DIR


setup_logging()
