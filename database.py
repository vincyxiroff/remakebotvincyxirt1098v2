import mysql.connector
import yaml

config = yaml.safe_load(open("config.yml", 'r', encoding="utf-8")).get("database")


class Database:
    def __init__(self, print_out_state=True):
        try:
            self.get_connection()
            self.db.close()
            if print_out_state:
                print("Database connected, tables created!")
        except Exception as exc:
            if print_out_state:
                print("Something went wrong with database! See the error below:")
            print(exc)

    def get_connection(self):
        self.db = mysql.connector.connect(
            host=config.get("host"),
            user=config.get("user"),
            password=config.get("password"),
            database=config.get("databaseName"),
            port=config.get("port")
        )
        self.cursor = self.db.cursor()

    def close_connection(self):

        self.cursor.close()
        self.db.close()

    def check_create_table(self, tbname, columns):
        self.get_connection()
        self.cursor.execute(f"create table if not exists {tbname} ({columns});")
        self.close_connection()

    def get_boolean(self, tbname, column, id):
        self.get_connection()
        self.cursor.execute(f"select {column} from {tbname} where {id}=1;")
        result = self.cursor.fetchall()
        self.close_connection()
        if len(result):
            return True
        return False

    def check_contains(self, tbname, column, value):
        self.get_connection()
        self.cursor.execute(f"select * from {tbname} where {column}={value};")
        result = self.cursor.fetchall()
        self.close_connection()
        if len(result):
            return True
        return False

    def insert(self, tbname, columns, values):
        self.get_connection()
        self.cursor.execute(f"insert into {tbname} ({columns}) values ({values});")
        self.db.commit()
        self.close_connection()

    def get_next_auto_increment(self, tbname):
        self.get_connection()
        self.cursor.execute(f"SHOW TABLE STATUS LIKE '{tbname}';")
        result = self.cursor.fetchone()
        self.close_connection()
        return result[10]

    def get_count(self, tbname, condition):
        self.get_connection()
        self.cursor.execute(f"select count(*) from {tbname} where {condition}")
        result = self.cursor.fetchone()
        self.close_connection()
        return result[0]

    def get_id(self, tbname, condition):
        self.get_connection()
        self.cursor.execute(f"select id from {tbname} where {condition}")
        result = self.cursor.fetchone()
        self.close_connection()
        return result[0]

    def update_data(self, tbname, column, value, condition):
        self.get_connection()
        self.cursor.execute(f"update {tbname} set {column}={value} where {condition}")
        self.db.commit()
        self.close_connection()

    def get_value_general(self, tbname, column, condition):
        self.get_connection()
        self.cursor.execute(f"select {column} from {tbname} where {condition};")
        result = self.cursor.fetchone()
        self.close_connection()
        return result[0]

    def delete_value_general(self, table_name, condition):
        self.get_connection()
        self.cursor.execute(f"delete from {table_name} where {condition}")
        self.db.commit()
        self.close_connection()

    def get_values_general(self, table_name, columns, condition):
        self.get_connection()
        self.cursor.execute(f"select {columns} from {table_name} where {condition};")
        result = list(self.cursor)
        self.close_connection()
        return result
