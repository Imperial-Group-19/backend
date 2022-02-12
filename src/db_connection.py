from typing import Dict, List
import dataclasses
import psycopg2
from db_objects import Store, User, Transaction, Product

# from sshtunnel import SSHTunnelForwarder

# PORT = 5432
# server = SSHTunnelForwarder(('35.195.58.180', 4000),
#          ssh_username= USERNAME,
#          ssh_password= PASSWORD,
#          remote_bind_address=('localhost', PORT),
#          local_bind_address=('localhost', PORT))
# server.start()

class postgresDBClient:
    def __init__(self, db_type):
        # Connection establishment
        self.db_type = db_type
        self.conn = psycopg2.connect(
            database=db_type,
            user='postgres',
            password = 'crypto',
            host='localhost', 
            port= '5432'
            # host= server.local_bind_host, 
            # port= server.local_bind_port,
        )
        
        self.conn.autocommit = True

        # Creating a cursor object
        self.cursor= self.conn.cursor()

        # Print when connection is successful
        print("Database has been connected successfully !!");

        # Read data at initialisation
        if(db_type == 'users'):
            self.users_data = {}
            self.users_data = self.get_users()
        elif(db_type == 'transactions'):
            self.transactions_data = {}
            self.transactions_data = self.get_transactions()
        elif(db_type == 'product_store'):
            self.stores_data = {}
            self.products_data = {}
            self.stores_data = self.get_store()
            self.products_data = self.get_product()

    def connect(self): #testing function
        # Connection establishment
        self.conn = psycopg2.connect(
            database='transactions',
            user='postgres',
            password = 'crypto',
            host='localhost', 
            port= '5432'
        )

        self.conn.autocommit = True

        # Creating a cursor object
        self.cursor = self.conn.cursor()

        # Print when connection is successful
        print("Database has been connected successfully !!");

    def close_connection(self): 
        # Closing the connection
        self.cursor.close()
        self.conn.close()


    # read at initialisation and store data in cache - hash to identify each table 
    # store data as dictionary
 
    def get_users(self) -> Dict[User, User]:
        # Query
        self.cursor.execute("SELECT name, email_add, wallet_add FROM userinfo ORDER BY name")
        rows = self.cursor.fetchall()
        print("The number of users: ", self.cursor.rowcount)

        users = {}
        for row in rows:
            user = User(*row)
            users[user] = user

        return users


    def get_transactions(self) -> Dict[Transaction, Transaction]:
        # Query
        self.cursor.execute("SELECT wallet_add, store_add, product, time_stamp FROM transactions ORDER BY wallet_add")
        rows = self.cursor.fetchall()
        print("The number of transactions: ", self.cursor.rowcount)
        
        transactions = {}
        for row in rows:
            txn = Transaction(*row)
            transactions[txn] = txn

        return transactions
    
    def get_store(self) -> Dict[Store, Store]:
        # Query
        self.cursor.execute("SELECT store_id, title, description, store_add FROM stores ORDER BY store_id")
        rows = self.cursor.fetchall()
        print("The number of stores: ", self.cursor.rowcount)
        
        stores = {} #use hash as dict key
        
        for row in rows:
            store = Store(*row)
            stores[store] = store

        return stores

    def get_product(self) -> Dict[Product, Product]:
        # Query
        self.cursor.execute("SELECT product_id, store_id, title, description, price, features FROM products ORDER BY product_id")
        rows = self.cursor.fetchall()
        print("The number of products: ", self.cursor.rowcount)
        
        products = {} #use store hash and product hash as dict key

        for row in rows:
            product = Product(*row)
            products[product] = product

        return products
        

    def add_users(self, user: User):
        user_tuple = dataclasses.astuple(user)

        # Insert user details 
        insert_user = """ INSERT INTO userinfo (NAME, EMAIL_ADD, WALLET_ADD) VALUES (%s,%s,%s)"""
        # insert_user_str = f"INSERT INTO userinfo (NAME, EMAIL_ADD, WALLET_ADD) VALUES ({user})"

        self.cursor.execute(insert_user, user_tuple)


        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into userinfo table")

        # Commit changes
        self.conn.commit()

        
    def add_transactions(self, trxn: Transaction):
        trxn_tuple = dataclasses.astuple(trxn)

        # Insert transaction details 
        insert_transaction = """ INSERT INTO transactions (WALLET_ADD, STORE_ADD, PRODUCT, TIME_STAMP) VALUES (%s,%s,%s,%s)"""

        self.cursor.execute(insert_transaction, trxn_tuple)


        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into transactions table")

        # Commit changes
        self.conn.commit()


    def add_stores(self, st: Store):
            st_tuple = dataclasses.astuple(st)

            # Insert store details 
            insert_store = """ INSERT INTO stores (STORE_ID, TITLE, DESCRIPTION, STORE_ADD) VALUES (%s,%s,%s,%s)"""

            self.cursor.execute(insert_store, st_tuple)

            # Check insertion
            count = self.cursor.rowcount
            print(count, "Record inserted successfully into stores table")

            # Commit changes
            self.conn.commit()

    def add_products(self, prdt: Product):
        prdt_tuple = dataclasses.astuple(prdt)

        # Insert product details 
        insert_product = """ INSERT INTO products (PRODUCT_ID, STORE_ID, TITLE, DESCRIPTION, PRICE, FEATURES) VALUES (%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_product, prdt_tuple)


        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into products table")

        # Commit changes
        self.conn.commit()

if __name__ == "__main__":
    db_user = postgresDBClient('users')
    db_transaction = postgresDBClient('transactions')
    db_product_store = postgresDBClient('product_store')
    
    print(db_user.users_data)
    print(db_transaction.transactions_data)
    print(db_product_store.stores_data)
    print(db_product_store.products_data)
    
    # new_user = User("John Smith", "JS@ic.ac.uk", "1EXAMPLE2Polygon3MATIC456")
    # db_user.add_users(new_user)

    # ERROR IN PRODUCT DATA TYPE
    # new_txn = Transaction("1EXAMPLE2Polygon3MATIC456", "0x329CdCBBD82c934fe32322b423bD8fBd30b4EEB6", new_product, 120000)
    # db_transaction.add_transactions(new_txn)
    
    # new_store = Store("super-algorithms", "Super Algorithms Inc.", 
    #                   "We help you prepare for Tech Interviews", 
    #                   "0x329CdCBBD82c934fe32322b423bD8fBd30b4EEB6")
    # db_product_store.add_stores(new_store)
    # db_product_store.stores_data = db_product_store.stores_data.get_store()
    # print(db_product_store.stores_data)


    # new_product = Product("C++", "super-algorithms", "C++ course", 
    #                     "Try out our original course in C++ and impress your interviewers.", 10,
    #                     ["Full algorithms course in C++",
    #                     "Pointers Cheat Sheet",
    #                     "Memory Management Tips"])
    # db_product_store.add_products(new_product)
    # db_product_store.products_data = db_product_store.products_data.get_product()
    # print(db_product_store.products_data)





    
    