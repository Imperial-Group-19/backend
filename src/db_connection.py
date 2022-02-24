from typing import Dict, List
import dataclasses
import psycopg2
from db_objects import Store, User, Transaction, Product, StoreCreated, StoreRemoved, StoreUpdated, PaymentMade, RefundMade, ProductCreated, ProductRemoved, ProductUpdated

from sshtunnel import SSHTunnelForwarder
from getpass import getpass

username = input("Enter SSH username: ")
pkey = input("Enter SSH private key: ")
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
    def __init__(self):
        # Connection establishment
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

        # Initialise stores, products, transactions
        self.stores: Dict[Store, Store] = {}
        self.products: Dict[Product, Product] = {}
        self.paymentmade: List[PaymentMade] = [] 
        self.refundmade: List[RefundMade] = []

    def connect(self): #testing function
        # Connection establishment
        self.conn = psycopg2.connect(
            database='salesfunnel',
            user='postgres',
            password = 'crypto',
            host='127.0.0.1', 
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

    # def update_store_title_description #to confirm params

    # def update_product_title_description_features #to confirm params

    def delete_stores(self, store: Store):
        store_address = store.id
        
        # Delete store by store_address
        self.cursor.execute("DELETE FROM stores WHERE id = %s", (store_address,))

        # get the number of updated rows
        rows_deleted = self.cursor.rowcount
        print(rows_deleted, "Record deleted from stores table")

        # Commit the changes to the database
        conn.commit()
        
    def delete_products(self, product: Product):
        product_name = product.product_id
        
        # Delete store by store_address
        self.cursor.execute("DELETE FROM products WHERE product_id = %s", (product_name,))

        # get the number of updated rows
        rows_deleted = self.cursor.rowcount
        print(rows_deleted, "Record deleted from products table")

        # Commit the changes to the database
        conn.commit()


    def write_store_created(self, store: StoreCreated):
        storecreate_tuple = dataclasses.astuple(store)

        # Insert StoreCreated event details 
        insert_store_created = """ INSERT INTO storecreated (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, STOREOWNER) VALUES (%s,%s,%s,%s,%s,%s,%s, %s)"""
        self.cursor.execute(insert_store_created, storecreate_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into StoreCreated table")

        # Commit changes
        self.conn.commit()

        # Create new store
        new_store = Store(
            id=store.storeAddress,
            title="",
            description = "",
            store_owner = store.storeOwner,
        )

        # Add to dictionary
        self.stores[new_store] = new_store

        # Add to store table in DB
        add_stores(new_store)


    def write_store_removed(self, store: StoreRemoved): 
        storeremove_tuple = dataclasses.astuple(store)

        # Insert StoreRemoved event details 
        insert_store_removed = """ INSERT INTO storeremoved (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS) VALUES (%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_store_removed, storeremove_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into StoreRemoved table")

        # Commit changes
        self.conn.commit()

        # Remove store from dictionary and DB -> and also remove related products in store
        for current_store in self.stores:
            if(current_store.id == store.storeAddress):
                self.stores.pop(current_store)
                delete_stores(current_store) 

        
        for current_product in self.product:
            if(current_product.store_id == store.storeAddress):
                self.products.pop(current_product)
                delete_products(current_product) 


    def write_store_updated(self, store: StoreUpdated): 
        storeupdate_tuple = dataclasses.astuple(store)

        # Insert StoreUpdated event details 
        insert_store_updated = """ INSERT INTO storeupdated (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, NEWSTOREADDRESS) VALUES (%s,%s,%s,%s,%s,%s,%s, %s)"""

        self.cursor.execute(insert_store_updated, storeupdate_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into StoreUpdated table")

        # Commit changes
        self.conn.commit()

        # Create new store
        new_store = Store(
            id=store.newStoreAddress,
            title="",
            description = "",
            store_owner = store.storeOwner,
        )

        # Delete old store and add new store to dictionary and DB
        # Delete related products
        for current_store in self.stores:
            if(current_store.id == store.storeAddress):
                self.stores.pop(current_store)
                delete_stores(current_store) 

        self.stores[new_store] = new_store
        add_stores(new_store)
    
        for current_product in self.product:
            if(current_product.store_id == store.storeAddress):
                self.products.pop(current_product)
                delete_products(current_product) 


    def write_product_created(self, product: ProductCreated):
        productcreate_tuple = dataclasses.astuple(product)

        # Insert ProductCreated event details 
        insert_product_created = """ INSERT INTO productcreated (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, PRODUCTNAME, PRICE) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        self.cursor.execute(insert_product_created, productcreate_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into ProductCreated table")

        # Commit changes
        self.conn.commit()

        # Create new product
        new_product = Product(
            product_id = product.productName,
            store_id = product.storeAddress,
            title = " ",
            description = " ",
            price = product.price,
            features = []
        )

        # Add to dictionary
        self.products[new_product] = new_product

        # Add to product table in DB
        add_products(new_product)


    def write_product_removed(self, product: ProductRemoved): 
        productremove_tuple = dataclasses.astuple(product)

        # Insert ProductRemoved event details 
        insert_product_removed = """ INSERT INTO productremoved (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, PRODUCTNAME) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_product_removed, productremove_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into ProductRemoved table")

        # Commit changes
        self.conn.commit()

        # Remove product from dictionary and DB
        for current_product in self.product:
            if(current_product.product_id == product.productName):
                self.products.pop(current_product)
                delete_products(current_product) 


    def write_product_updated(self, product: ProductUpdated): 
        productupdate_tuple = dataclasses.astuple(product)

        # Insert ProductUpdated event details 
        insert_product_updated = """ INSERT INTO productupdated (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, PRODUCTNAME, NEWPRICE) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_product_updated, productupdate_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into ProductUpdated table")

        # Commit changes
        self.conn.commit()

        # Create new product
        new_product = Product(
            product_id = product.productName,
            store_id = product.storeAddress,
            title = " ",
            description = " ",
            price = product.newPrice,
            features = []
        )

        # Remove old product from dictionary and DB and add new product
        for current_product in self.product:
            if(current_product.product_id == product.productName):
                self.products.pop(current_product)
                delete_products(current_product) 
        
        self.products[new_product] = new_product

        # Add to product table in DB
        add_products(new_product)
    
    def write_payment_made(self, transaction: PaymentMade): 
        paymentmade_tuple = dataclasses.astuple(transaction)

        # Insert PaymentMade event details 
        insert_payment_made = """ INSERT INTO paymentmade (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, CUSTOMER, STOREADDRESS, PRODUCTNAME) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_payment_made, paymentmade_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into PaymentMade table")

        # Commit changes
        self.conn.commit()

        # Add to list
        self.paymentmade.append(transaction)

    def write_refund_made(self, transaction: RefundMade): 
        refundmade_tuple = dataclasses.astuple(transaction)

        # Insert RefundMade event details 
        insert_refund_made = """ INSERT INTO refundmade (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, CUSTOMER, STOREADDRESS, PRODUCTNAME) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_refund_made, refundmade_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into RefundMade table")

        # Commit changes
        self.conn.commit()

        # Add to list
        self.refundmade.append(transaction)


if __name__ == "__main__":
    db = postgresDBClient('salesfunnel')
    
    # new_store = Store("super-algorithms", "Super Algorithms Inc.", 
    #                   "We help you prepare for Tech Interviews", 
    #                   "0x329CdCBBD82c934fe32322b423bD8fBd30b4EEB6")
    # db.add_stores(new_store)
    # db.stores = db.stores.get_store()
    # print(db.stores)


    # new_product = Product("C++", "super-algorithms", "C++ course", 
    #                     "Try out our original course in C++ and impress your interviewers.", 10,
    #                     ["Full algorithms course in C++",
    #                     "Pointers Cheat Sheet",
    #                     "Memory Management Tips"])
    # db_product_store.add_products(new_product)
    # db_product_store.products_data = db_product_store.products_data.get_product()
    # print(db_product_store.products_data)
