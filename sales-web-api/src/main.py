import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.getenv("SALES_DB_DIR"))
from database import SalesDB

db = SalesDB("admin", "root")