import os
from dotenv import load_dotenv
load_dotenv()

APP_NAME = os.getenv('APP_NAME', 'Expenses Tracker')
DB_URL   = os.getenv('DB_URL', 'sqlite:///./dev.db')
