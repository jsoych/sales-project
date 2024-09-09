import os
from dotenv import load_dotenv
from database import SalesDB


load_dotenv()
DATA_DIR = os.getenv("DATA_DIR")
USER = os.getenv("POSTGRES_USER")
PASSWORD = os.getenv("POSTGRES_PASSWORD")

# Create SalesDB instance
db = SalesDB(USER,PASSWORD)

# Insert the needed csv files into the database
db.insertCSV("itemcategories", os.path.join(DATA_DIR,"item_categories.csv"))

db.insertCSV("shops", os.path.join(DATA_DIR,"shops.csv"))

db.insertCSV( "items", os.path.join(DATA_DIR,"items.csv"))

db.insertCSV("sales", os.path.join(DATA_DIR,"sales_train.csv"))