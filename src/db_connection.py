from typing import List
import dataclasses
import psycopg2
from db_objects import Store, User, Transaction, Product

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
        )
        
        self.conn.autocommit = True

        # Creating a cursor object
        self.cursor= self.conn.cursor()

        # Print when connection is successful
        print("Database has been connected successfully !!");


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
    # store dictionary
    # product dictionary based on store hash 
    def get_users(self) -> List[User]:
        # Query
        self.cursor.execute("SELECT name, email_add, wallet_add FROM userinfo ORDER BY name")
        rows = self.cursor.fetchall()
        print("The number of users: ", self.cursor.rowcount)

        users = []
        for row in rows:
            users.append(User(*row))

        return users


    def get_transactions(self) -> List[Transaction]:
        # Query
        self.cursor.execute("SELECT wallet_add, store_add, product, timestamp FROM transaction ORDER BY wallet_add")
        rows = self.cursor.fetchall()
        print("The number of transactions: ", self.cursor.rowcount)
        
        transactions = []
        for row in rows:
            transactions.append(Transaction(*row))

        return transactions

    def get_store(self) -> List[Store]:
        # Query
        self.cursor.execute("SELECT id, title, description FROM stores ORDER BY id")
        rows = self.cursor.fetchall()
        print("The number of stores: ", self.cursor.rowcount)
        
        stores = {} #use hash as dict

        return stores

    def get_product(self) -> List[Product]:
        # Query
        self.cursor.execute("SELECT product_id, store_id, title, description, price, features FROM products ORDER BY id")
        rows = self.cursor.fetchall()
        print("The number of products: ", self.cursor.rowcount)
        
        products = {} #use store hash and product hash as dict

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
        insert_transaction = """ INSERT INTO transaction (WALLET_ADD, STORE_ADD, PRODUCT, TIMESTAMP) VALUES (%s,%s,%s,%s)"""

        self.cursor.execute(insert_transaction, trxn_tuple)


        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into transaction table")

        # Commit changes
        self.conn.commit()


#get from store by store_id
#get from product by store_id then product_id

if __name__ == "__main__":
    db_user = postgresDBClient('users')
    db_transaction = postgresDBClient('transactions')
    db_product_store = postgresDBClient('product_store')

    users = db_user.get_users()
    for us in users:
        print(us)
        # db_user.add_users(us)

    new_user = User("John Smith", "JC@ic.ac.uk", "1EXAMPLE2Polygon3MATIC456")
    db_user.add_users(new_user)
    
    transactions = db_transaction.get_transactions()
    for txn in transactions:
        print(txn)
    
    new_txn = User("John Smith", "JC@ic.ac.uk", "1EXAMPLE2Polygon3MATIC456")
    db_transaction.add_transactions(new_txn)
    
    # db_product_store = postgresDBClient('')