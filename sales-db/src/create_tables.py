from database import SalesDB


# the following creates a SalesDB instance for creating tables
db = SalesDB(user="admin", password="root")

db.createTable(
    "itemcategories", 
    ["item_category_name", "item_category_id"], 
    ["character varying (64)", "serial"],
    "ADD PRIMARY KEY (item_category_id)"
)

db.createTable(
    "shops",
    ["shop_name", "shop_id"],
    ["character varying (256)", "serial"],
    "ADD PRIMARY KEY (shop_id)"
)

db.createTable(
    "items",
    ["item_name", "item_id", "item_category_id"],
    ["character varying (256)", "serial", "serial"],
    "ADD PRIMARY KEY (item_id)",
    "ADD FOREIGN KEY (item_category_id) \
        REFERENCES itemcategories(item_category_id)"
)

db.createTable(
    "sales",
    [
        "date", 
        "date_block_num", 
        "shop_id", "item_id", 
        "item_price", 
        "item_cnt_day"
    ],
    [
        "character varying (16)", 
        "integer", 
        "serial", 
        "serial", 
        "numeric", 
        "numeric"
    ],
    "ADD FOREIGN KEY (shop_id) REFERENCES shops(shop_id)",
    "ADD FOREIGN KEY (item_id) REFERENCES items(item_id)"
)