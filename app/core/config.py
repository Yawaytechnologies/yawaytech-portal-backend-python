import os
from dotenv import load_dotenv
load_dotenv()

APP_NAME = os.getenv('APP_NAME', 'Expenses Tracker')
DB_URL   = os.getenv('DB_URL', 'sqlite:///./dev.db')


# JWT config
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME_IN_PROD")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))