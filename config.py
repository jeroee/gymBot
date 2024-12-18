import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('API_KEY')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
DB_NAME = os.getenv('DB_NAME')
COLLECTION_NAME = os.getenv('COLLECTION_NAME')