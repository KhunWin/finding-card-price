import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class Config:
    # Boutir credentials
    BOUTIR_EMAIL = os.getenv('BOUTIR_EMAIL', 'your_email@example.com')
    BOUTIR_PASSWORD = os.getenv('BOUTIR_PASSWORD', 'your_password')
    BOUTIR_URL = 'https://www.boutir.com'
    BOUTIR_DASHBOARD = f'{BOUTIR_URL}/dashboard'
    
    # File paths
    # DOWNLOAD_DIR = Path(os.getenv('DOWNLOAD_DIR', './downloads'))
    # UPLOAD_DIR = Path(os.getenv('UPLOAD_DIR', './uploads'))
    
    # Upload settings
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    TIMEOUT = 30
    
    # Create directories
    # DOWNLOAD_DIR.mkdir(exist_ok=True)
    # UPLOAD_DIR.mkdir(exist_ok=True)
    
    @staticmethod
    def validate_credentials():
        """Validate that credentials are set"""
        if Config.BOUTIR_EMAIL == 'your_email@example.com':
            raise ValueError("Please set BOUTIR_EMAIL in .env file")
        if Config.BOUTIR_PASSWORD == 'your_password':
            raise ValueError("Please set BOUTIR_PASSWORD in .env file")
        return True