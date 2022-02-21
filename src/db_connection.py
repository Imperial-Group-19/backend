from typing import Dict, List
import dataclasses
import psycopg2
from db_objects import Store, User, Transaction, Product

#to shift to websocket server
from sshtunnel import SSHTunnelForwarder
from getpass import getpass

username = getpass(prompt = 'Enter SSH username: ')
pkey = getpass(prompt = 'Enter SSH private key: ')
pw = getpass(prompt = 'Enter SSH private key password: ')

PORT = 5432
server = SSHTunnelForwarder(('35.195.58.180', 22),
         ssh_username= username,
         ssh_pkey = pkey, 
         ssh_private_key_password= pw,
         remote_bind_address=('localhost', PORT),
         local_bind_address=('localhost', PORT),
         allow_agent=False)
server.start()

class postgresDBClient:
    def __init__(self, db_type):
        # Connection establishment
        self.db_type = db_type
        self.conn = psycopg2.connect(
            database='salesfunnel',
            user='postgres',
            password = 'crypto',
            host='127.0.0.1', 
            port= '5432'
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
            self.stores_data = self.get_stores()
            self.products_data = self.get_products()

        self.stores: Dict[Store, Store] = {}
        self.products: Dict[Product, Product] = {}
        self.paymentmade: List[PaymentMade] = [] 
        self.refundmade: List[RefundMade] = []

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


    # DB read functions
 
    def get_users(self) -> Dict[User, User]:
        # Query
        self.cursor.execute("SELECT name, email_address, wallet_address FROM users ORDER BY name")
        rows = self.cursor.fetchall()
        print("The number of users: ", self.cursor.rowcount)

        users = {}
        for row in rows:
            user = User(*row)
            users[user] = user

        return users


    # def get_transactions(self) -> Dict[Transaction, Transaction]:
    #     # Query
    #     self.cursor.execute("SELECT wallet_address, store_address, product, timestamp FROM transactions ORDER BY wallet_address")
    #     rows = self.cursor.fetchall()
    #     print("The number of transactions: ", self.cursor.rowcount)
        
    #     transactions = {}
    #     for row in rows:
    #         txn = Transaction(*row)
    #         transactions[txn] = txn

    #     return transactions
    
    def get_stores(self) -> Dict[Store, Store]:
        # Query
        self.cursor.execute("SELECT id, title, description, store_address FROM stores ORDER BY id")
        rows = self.cursor.fetchall()
        print("The number of stores: ", self.cursor.rowcount)
        
        stores = {} #use hash as dict key
        
        for row in rows:
            store = Store(*row)
            stores[store] = store

        return stores

    def get_products(self) -> Dict[Product, Product]:
        # Query
        self.cursor.execute("SELECT product_id, store_id, title, description, price, features FROM products ORDER BY product_id")
        rows = self.cursor.fetchall()
        print("The number of products: ", self.cursor.rowcount)
        
        products = {} #use store hash and product hash as dict key

        for row in rows:
            product = Product(*row)
            products[product] = product

        return products

    # DB write functions    

    def add_users(self, user: User):
        user_tuple = dataclasses.astuple(user)

        # Insert user details 
        insert_user = """ INSERT INTO users (NAME, email_address, wallet_address) VALUES (%s,%s,%s)"""
        # insert_user_str = f"INSERT INTO userinfo (NAME, email_address, wallet_address) VALUES ({user})"

        self.cursor.execute(insert_user, user_tuple)


        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into users table")

        # Commit changes
        self.conn.commit()

        
    def add_transactions(self, trxn: Transaction):
        trxn_tuple = dataclasses.astuple(trxn)

        # Insert transaction details 
        insert_transaction = """ INSERT INTO transactions (wallet_address, store_address, PRODUCT, timestamp) VALUES (%s,%s,%s,%s)"""

        self.cursor.execute(insert_transaction, trxn_tuple)


        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into transactions table")

        # Commit changes
        self.conn.commit()


    def add_stores(self, st: Store):
            st_tuple = dataclasses.astuple(st)

            # Insert store details 
            insert_store = """ INSERT INTO stores (ID, TITLE, DESCRIPTION, store_address) VALUES (%s,%s,%s,%s)"""

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

    def write_StoreCreated(self, store: StoreCreated):
        storecreate_tuple = dataclasses.astuple(store)

        # Insert StoreCreated event details 
        insert_StoreCreated = """ INSERT INTO storecreated (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, STOREOWNER) VALUES (%s,%s,%s,%s,%s,%s,%s, %s)"""
        self.cursor.execute(insert_StoreCreated, storecreate_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into StoreCreated table")

        # Commit changes
        self.conn.commit()

        actual_store = Store(
            id=store.storeAddress,
            store_address = store.storeOwner,
            title="",

        )
        self.stores[actual_store] = actual_store


     def write_StoreRemoved(self, store: StoreRemoved): 
        storeremove_tuple = dataclasses.astuple(store)

        # Insert StoreRemoved event details 
        insert_StoreRemoved = """ INSERT INTO storeremoved (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS) VALUES (%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_StoreRemoved, storeremove_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into StoreRemoved table")

        # Commit changes
        self.conn.commit()

     def write_StoreUpdated(self, store: StoreUpdated): 
        storeupdate_tuple = dataclasses.astuple(store)

        # Insert StoreUpdated event details 
        insert_StoreUpdated = """ INSERT INTO storeupdated (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, NEWSTOREADDRESS) VALUES (%s,%s,%s,%s,%s,%s,%s, %s)"""

        self.cursor.execute(insert_StoreUpdated, storeupdate_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into StoreUpdated table")

        # Commit changes
        self.conn.commit()

        #change for store - delete old store and add new ; change for product

     def write_ProductCreated(self, product: ProductCreated):
        productcreate_tuple = dataclasses.astuple(product)

        # Insert ProductCreated event details 
        insert_ProductCreated = """ INSERT INTO productcreated (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, PRODUCTNAME, PRICE) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        self.cursor.execute(insert_ProductCreated, productcreate_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into ProductCreated table")

        # Commit changes
        self.conn.commit()

     def write_ProductRemoved(self, product: ProductRemoved): 
        productremove_tuple = dataclasses.astuple(product)

        # Insert ProductRemoved event details 
        insert_ProductRemoved = """ INSERT INTO productremoved (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, PRODUCTNAME) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_ProductRemoved, productremove_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into ProductRemoved table")

        # Commit changes
        self.conn.commit()

     def write_ProductUpdated(self, product: ProductUpdated): 
        productupdate_tuple = dataclasses.astuple(product)

        # Insert ProductUpdated event details 
        insert_ProductUpdated = """ INSERT INTO productupdated (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, PRODUCTNAME, NEWPRICE) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_ProductUpdated, productupdate_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into ProductUpdated table")

        # Commit changes
        self.conn.commit()
    
    def write_PaymentMade(self, transaction: PaymentMade): 
        paymentmade_tuple = dataclasses.astuple(transaction)

        # Insert PaymentMade event details 
        insert_PaymentMade = """ INSERT INTO paymentmade (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, CUSTOMER, STOREADDRESS, PRODUCTNAME) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_PaymentMade, paymentmade_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into PaymentMade table")

        # Commit changes
        self.conn.commit()

     def write_RefundMade(self, transaction: RefundMade): 
        refundmade_tuple = dataclasses.astuple(transaction)

        # Insert RefundMade event details 
        insert_RefundMade = """ INSERT INTO refundmade (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, CUSTOMER, STOREADDRESS, PRODUCTNAME) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_RefundMade, refundmade_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into RefundMade table")

        # Commit changes
        self.conn.commit()


if __name__ == "__main__":
    db_user = postgresDBClient('users')
    # db_transaction = postgresDBClient('transactions')
    db_product_store = postgresDBClient('product_store')
    
    print(db_user.users_data)
    # print(db_transaction.transactions_data)
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
    # db_product_store.stores_data = db_product_store.get_stores()
    # print(db_product_store.stores_data)


    # new_product = Product("Java", "super-algorithms", "Java course", 
    #                     "Try out our updated course in Java and impress your interviewers.", 25000,
    #                     ["Full algorithms course in Java",
    #                     "OODP Cheat Sheet",
    #                     "Design Convention Tips"])
    # db_product_store.add_products(new_product)
    # db_product_store.products_data = db_product_store.get_products()
    # print(db_product_store.products_data)





    
    