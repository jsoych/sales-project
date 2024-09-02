import csv
import psycopg2


class SalesDB():
    """
    SalesDB is an object that manages connections, makes tables, inserts
    values, and queries to our database. It also includes specific methods
    needed to fetch past data for machine learning applications.
    """

    def __init__(self, user, password) -> None:
        self.database = "sales_db"
        self.user = user
        self.password = password
        self.host = "localhost"

    def connect(self):
        """
        Returns a connection object to our database.

        Returns:
        - psycopg2.connection object
        """
        return psycopg2.connect(
            database=self.database,
            user=self.user,
            password=self.password,
            host=self.host
        )

    def execute(self, sql, values=None) -> None:
        """
        Executes a single sql query within our database.

        Arguments:
        - sql (str): The sql query.
        - values (list|optional): A list of values.
        """
        conn = self.connect()
        with conn:
            with conn.cursor() as curs:
                if values:
                    curs.execute(sql,values)
                else:
                    curs.execute(sql)
        conn.close()

    def createTable(self, name, col_names, col_types, *alter_table) -> None:
        """
        Creates a table within our database.

        Arguments:
        - name (str): The new table name.
        - col_names (list): The list of column names.
        - col_types (list): The list of column postgres types.
        - alter_table (iter|optional): A collection of table alterations.

        Side Effects:
        - Creates a permantant table within our database.
        """
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
        """
        Inserts values into an existing table.

        Arguments:
        - name (str): The table name.
        - col_names (list): The list of column names.
        - values (list): The list of values.

        Side Effects:
        - Inserts a new row into the table within our database
        """
        sql = "INSERT INTO {0} (".format(name)
        myformat = "("
        for col_name in col_names[:-1]:
            sql += "{}, ".format(col_name)
            myformat += "%s, "
        sql += "{}) VALUES ".format(col_names[-1])
        myformat += "%s)"
        sql += myformat
        try:
            self.execute(sql,values)
        except psycopg2.errors.UniqueViolation:
            print("ERROR: {} record already exists".format(values))

    def insertCSV(self, name, filepath) -> None:
        """
        Inserts a csv file into an existing table.

        Arguments:
        - name (str): The table name.
        - filepath (str): The filepath to the csv file.

        Side Effects:
        - Inserts every row from the csv file into a new row within
        our database
        """
        conn = self.connect()

        file = open(filepath, "r")
        reader = csv.reader(file)

        col_names = reader.__next__()
        sql = "INSERT INTO {} (".format(name)
        myformat = "("
        for col_name in col_names[:-1]:
            sql += "{}, ".format(col_name)
            myformat += "%s, "
        sql += "{}) VALUES ".format(col_names[-1])
        myformat += "%s)"
        sql += myformat

        curs = conn.cursor()
        for values in reader:
            try:
                curs.execute(sql,values)
            except psycopg2.errors.UniqueViolation:
                    print("ERROR: {} record already exists in table {}".format(values,name))
                    conn.rollback()
        curs.close()

        file.close()

        conn.commit()
        conn.close()

    def fetch(self, sql):
        """
        Fetches and returns the query results from our database.

        Arguments:
        - sql (str): The query.

        Returns:
        - list[tuples]: A list of the query results.
        """
        conn = self.connect()
        results = None
        with conn:
            with conn.cursor() as curs:
                curs.execute(sql)
                results = curs.fetchall()
        conn.close()
        return results

    def selectAll(self, name):
        """
        Selects all columns, and rows from the table.

        Arguments:
        - name (str): The table name.

        Returns:
        - list: A list of rows from the table.
        """
        try:
            return self.fetch("SELECT * FROM {}".format(name))
        except psycopg2.errors.UndefinedTable:
            print("UndefinedTable: relation \
                  \"{}\" does not exist".format(name))
            return

    def getIds(self):
        """Gets shop and item id pairs from the sales table."""
        sql = \
            "SELECT \
                shop_id \
                ,item_id \
            FROM sales \
            GROUP BY shop_id, item_id \
            ORDER BY shop_id, item_id"
        return self.fetch(sql)

    def getSalesData(self, shop_id, item_id):
        """
        Gets monthly sales data from the sales table.

        Arguments:
        - shop_id (int): The shop id.
        - item_id (int): The item id.

        Returns:
        - list: A list of sales data for the shop and item id pair.
        """
        sql = \
            "SELECT \
                date_block_num \
                ,SUM(item_cnt_day) as item_cnt \
            FROM sales \
            WHERE shop_id = {0} \
                AND item_id = {1} \
            GROUP BY date_block_num".format(shop_id, item_id)
        return self.fetch(sql)

    def getItemPrice(self, shop_id, item_id):
        """
        Gets max item price for shop and item pair.

        Arguments:
        - shop_id (int): The shop id.
        - item_id (int): The item id.

        Returns:
        - float: The max price for the item.
        """
        sql = \
            "SELECT \
                MAX(item_price) \
            FROM sales \
            WHERE shop_id = {0} \
                AND item_id = {1}".format(shop_id, item_id)
        return self.fetch(sql)

    def getItemCategory(self, shop_id, item_id):
        """
        Gets item category id for shop and item pair.

        Arguments:
        - shop_id (int): The shop id.
        - item_id (int): The item id.

        Returns:
        - int: A category id.
        """
        sql = \
            "SELECT DISTINCT \
                items.item_category_id \
            FROM sales \
            LEFT JOIN items \
                ON sales.item_id = items.item_id \
            WHERE sales.shop_id = {0} \
                AND sales.item_id = {1}".format(shop_id, item_id)
        return self.fetch(sql)

