from database import SalesDB
from zipfile import ZipFile


with ZipFile("competitive-data-science-predict-future-sales.zip") as zipfile:
    zipfile.extractall("data")

# the following inserts the needed csv files into our database
db = SalesDB(user="admin", password="root")
db.insertCSV("itemcategories", "data/item_categories.csv")
db.insertCSV("shops", "data/shops.csv")
db.insertCSV("items", "data/items.csv")
db.insertCSV("sales", "data/sales_train.csv")