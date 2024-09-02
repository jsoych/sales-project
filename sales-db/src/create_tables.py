from database import SalesDB


# Create SalesDB instance
db = SalesDB(user="admin", password="root")

# Create itemscategories table
db.createTable(
    "itemcategories", 
    ["item_category_name", "item_category_id"], 
    ["character varying (64)", "serial"],
    "ADD PRIMARY KEY (item_category_id)"
)

# Create shops table
db.createTable(
    "shops",
    ["shop_name", "shop_id"],
    ["character varying (256)", "serial"],
    "ADD PRIMARY KEY (shop_id)"
)

# Create items table
db.createTable(
    "items",
    ["item_name", "item_id", "item_category_id"],
    ["character varying (256)", "serial", "serial"],
    "ADD PRIMARY KEY (item_id)",
    "ADD FOREIGN KEY (item_category_id) \
        REFERENCES itemcategories(item_category_id)"
)

# Create sales
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