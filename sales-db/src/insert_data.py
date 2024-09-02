import os
from dotenv import load_dotenv
from database import SalesDB

load_dotenv()
data_dir = os.getenv("DATA_DIR")

# the following inserts the needed csv files into our database
db = SalesDB(user="admin", password="root")
db.insertCSV(
    "itemcategories", 
    os.path.join(data_dir,"item_categories.csv")
)
db.insertCSV(
    "shops",
    os.path.join(data_dir,"shops.csv")
)
db.insertCSV(
    "items",
    os.path.join(data_dir,"items.csv")
)
db.insertCSV(
    "sales",
    os.path.join(data_dir,"sales_train.csv")
)