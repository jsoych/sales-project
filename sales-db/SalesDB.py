import csv
import psycopg2


class SalesDB():

    def __init__(self, user, password) -> None:
        self.database = "postgres"
        self.user = user
        self.password = password
        self.host = "localhost"

    def connect(self):
        return psycopg2.connect(
            database=self.database,
            user=self.user,
            password=self.password,
            host=self.host
        )

    def execute(self, sql):
        with self.connect() as conn:
            with conn.cursor() as curr:
                curr.execute(sql)

    def createTable(self, name, col_names, col_types, *alter_table):
        sql = "CREATE TABLE {} (".format(name)
        for col_name, col_type in zip(col_names[:-1], col_types[:-1]):
            sql += col_name + " " + col_type + ", "
        sql += col_names[-1] + " " + col_types[-1] + ")"
        try:
            self.execute(sql)
            if (alter_table):
                for alt in alter_table:
                    self.execute("ALTER TABLE {0} {1}".format(name, alt))
        except psycopg2.errors.DuplicateTable:
            print("DuplicateTable: relation \
                  \"{}\" already exists".format(name))

    def insert(self, name, col_names, values) -> None:
        sql = "INSERT INTO {0} (".format(name)
        myformat = "("
        for col_name in col_names[:-1]:
            sql += "{}, ".format(col_name)
            myformat += "%s, "
        sql += "{}) VALUES ".format(col_names[-1])
        myformat += "%s)"
        sql += myformat
        try:
            self.execute(sql, values)
        except psycopg2.errors.UniqueViolation:
            print("ERROR: {} record already exists".format(values))

    def insertCSV(self, name, filepath) -> None:
        with open(filepath, "r") as file:
            reader = csv.reader(file)
            col_names = reader.__next__()
            for values in reader:
                self.insert(name, col_names, values)

    def selectAll(self, name):
        with self.connect() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("SELECT * FROM {}".format(name))
                    return cur.fetchall()
                except psycopg2.errors.UndefinedTable:
                    print("UndefinedTable: relation \
                          \"{}\" does not exist".format(name))
                    return

    def query(self, sql):
        with self.connect() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(sql)
                    return cur.fetchall()
                except psycopg2.errors.SyntaxError:
                    print("SyntaxError: invalid SQL query \"{}\"".format(sql))
                    return

    def getIds(self):
        sql = \
            "SELECT \
                shop_id \
                ,item_id \
            FROM sales \
            GROUP BY shop_id, item_id \
            ORDER BY shop_id, item_id"
        return self.query(sql)

    def getSalesData(self, shop_id, item_id):
        sql = \
            "SELECT \
                date_block_num \
                ,SUM(item_cnt_day) as item_cnt \
            FROM sales \
            WHERE shop_id = {0} \
                AND item_id = {1} \
            GROUP BY date_block_num".format(shop_id, item_id)
        return self.query(sql)

    def getItemPrice(self, shop_id, item_id):
        sql = \
            "SELECT \
                MAX(item_price) \
            FROM sales \
            WHERE shop_id = {0} \
                AND item_id = {1}".format(shop_id, item_id)
        return self.query(sql)

    def getItemCategory(self, shop_id, item_id):
        sql = \
            "SELECT DISTINCT \
                items.item_category_id \
            FROM sales \
            LEFT JOIN items \
                ON sales.item_id = items.item_id \
            WHERE sales.shop_id = {0} \
                AND sales.item_id = {1}".format(shop_id, item_id)
        return self.query(sql)
