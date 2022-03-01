from typing import Dict, List
import dataclasses
import psycopg2
from db_objects import Store, User, Transaction, Product, StoreCreated, StoreRemoved, StoreUpdated, PaymentMade, RefundMade, ProductCreated, ProductRemoved, ProductUpdated

from sshtunnel import SSHTunnelForwarder
from getpass import getpass

from logging import Logger

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
    def __init__(self, logging):
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

        self.logging = logging

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
        self.cursor.execute("SELECT id, title, description, store_owner FROM stores ORDER BY id")
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
        insert_store = """ INSERT INTO stores (ID, TITLE, DESCRIPTION, STORE_OWNER) VALUES (%s,%s,%s,%s)"""

        try:
            self.cursor.execute(insert_store, st_tuple)
        except Exception as e:
            error_msg = f"Unable to add new store: Exception: {e}"
            self.logging.warning(error_msg)
            return

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record(s) inserted successfully into Stores table")

        # Commit changes
        self.conn.commit()

    def add_products(self, prdt: Product):
        prdt_tuple = dataclasses.astuple(prdt)

        # Insert product details 
        insert_product = """ INSERT INTO products (PRODUCT_ID, STORE_ID, TITLE, DESCRIPTION, PRICE, FEATURES) VALUES (%s,%s,%s,%s,%s,%s)"""

        try:
            self.cursor.execute(insert_product, prdt_tuple)
        except Exception as e:
            error_msg = f"Unable to add new product: Exception: {e}"
            self.logging.warning(error_msg)
            return
            
        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record(s) inserted successfully into Products table")

        # Commit changes
        self.conn.commit()

    def update_store(self, store: Store):
        # Update by store_address
        self.cursor.execute("UPDATE stores SET title = %s, description = %s WHERE id = %s", (store.title, store.description, store.id))

        # get the number of updated stores
        rows_updated = self.cursor.rowcount
        print(rows_updated, "Record(s) updated on Stores table")

        # Commit the changes to the database
        self.conn.commit()

        # Create new store
        new_store = Store(
            id=store.id,
            title = store.title,
            description = store.description,
            store_owner = store.store_owner,
        )

        # Add to dictionary
        self.stores[new_store] = new_store


    def update_product(self, product: Product):
        product_list = list(dataclasses.asdict(product).values()) 
        features = self.to_array(product_list[-1])

        # Update by product_address
        self.cursor.execute("UPDATE products SET title = %s, description = %s, features = %s WHERE product_id = %s", (product.title, product.description, features, product.product_id))

        # get the number of updated stores
        rows_updated = self.cursor.rowcount
        print(rows_updated, "Record(s) updated on Products table")

        # Commit the changes to the database
        self.conn.commit()

         # Create new product
        new_product = Product(
            product_id = product.product_id,
            store_id = product.store_id,
            title = product.title,
            description = product.description,
            price = product.price,
            features = product.features
        )

        # Add to dictionary
        self.products[new_product] = new_product


    def delete_stores(self, store: Store):
        store_address = store.id
        
        # Delete store by store_address
        self.cursor.execute("DELETE FROM stores WHERE id = %s", (store_address,))

        # get the number of updated rows
        rows_deleted = self.cursor.rowcount
        print(rows_deleted, "Record(s) deleted from Stores table")

        # Commit the changes to the database
        self.conn.commit()
        
    def delete_products(self, product: Product):
        product_name = product.product_id
        
        # Delete store by store_address
        self.cursor.execute("DELETE FROM products WHERE product_id = %s", (product_name,))

        # get the number of updated rows
        rows_deleted = self.cursor.rowcount
        print(rows_deleted, "Record(s) deleted from Products table")

        # Commit the changes to the database
        self.conn.commit()


    def write_store_created(self, store: StoreCreated):
        storecreate_tuple = dataclasses.astuple(store)

        # Insert StoreCreated event details 
        insert_store_created = """ INSERT INTO storecreated (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, STOREOWNER) VALUES (%s,%s,%s,%s,%s,%s,%s, %s)"""
        self.cursor.execute(insert_store_created, storecreate_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record(s) inserted successfully into StoreCreated table")

        # Commit changes
        self.conn.commit()

        # Create new store
        new_store = Store(
            id=store.storeAddress,
            title="",
            description = "",
            store_owner = store.storeOwner,
        )

        # Add to dictionary - NOTE: to remove this when actual data is updated from front end
        # This should only be in updated_store but required for update/delete functions now
        self.stores[new_store] = new_store

        # Add to uneditable store table in DB
        self.add_stores(new_store)


    def write_store_removed(self, store: StoreRemoved): 
        storeremove_tuple = dataclasses.astuple(store)

        # Insert StoreRemoved event details 
        insert_store_removed = """ INSERT INTO storeremoved (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS) VALUES (%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_store_removed, storeremove_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record(s) inserted successfully into StoreRemoved table")

        # Commit changes
        self.conn.commit()

        # Remove store from dictionary and DB and also remove related products in store                
        for current_product in self.products:
            if(current_product.store_id == store.storeAddress):
                self.products.pop(current_product)
                self.delete_products(current_product) 
                break
                
        for current_store in self.stores:
            if(current_store.id == store.storeAddress):
                self.stores.pop(current_store)
                self.delete_stores(current_store)
                break 


    def write_store_updated(self, store: StoreUpdated): 
        storeupdate_tuple = dataclasses.astuple(store)

        # Insert StoreUpdated event details 
        insert_store_updated = """ INSERT INTO storeupdated (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, NEWSTOREADDRESS) VALUES (%s,%s,%s,%s,%s,%s,%s, %s)"""

        self.cursor.execute(insert_store_updated, storeupdate_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record(s) inserted successfully into StoreUpdated table")

        # Commit changes
        self.conn.commit()

        # Create new store
        new_store = Store(
            id=store.newStoreAddress,
            title="",
            description = "",
            store_owner = store.storeAddress, #to change to storeOwner when available on smartcontract
        )

        # Delete old store and add new store to dictionary and DB
        # Delete related products

        for current_product in self.products:
            if(current_product.store_id == store.storeAddress):
                self.products.pop(current_product)
                self.delete_products(current_product)
                break 

        for current_store in self.stores:
            if(current_store.id == store.storeAddress):
                self.stores.pop(current_store)
                self.delete_stores(current_store) 
                break

        self.stores[new_store] = new_store
        self.add_stores(new_store)
    


    def write_product_created(self, product: ProductCreated):
        productcreate_tuple = dataclasses.astuple(product)

        # Insert ProductCreated event details 
        insert_product_created = """ INSERT INTO productcreated (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, PRODUCTNAME, PRICE) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        self.cursor.execute(insert_product_created, productcreate_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record(s) inserted successfully into ProductCreated table")

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

        # Add to dictionary - NOTE: to remove this when actual data is updated from front end
        # This should only be in updated_product but required for update/delete functions now
        self.products[new_product] = new_product

        # Add to uneditable product table in DB
        self.add_products(new_product)


    def write_product_removed(self, product: ProductRemoved): 
        productremove_tuple = dataclasses.astuple(product)

        # Insert ProductRemoved event details 
        insert_product_removed = """ INSERT INTO productremoved (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, PRODUCTNAME) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_product_removed, productremove_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record(s) inserted successfully into ProductRemoved table")

        # Commit changes
        self.conn.commit()

        # Remove product from dictionary and DB
        for current_product in self.products:
            if(current_product.product_id == product.productName):
                self.products.pop(current_product)
                self.delete_products(current_product)
                break 


    def write_product_updated(self, product_update: ProductUpdated): 
        productupdate_tuple = dataclasses.astuple(product_update)

        # Insert ProductUpdated event details 
        insert_product_updated = """ INSERT INTO productupdated (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, PRODUCTNAME, NEWPRICE) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_product_updated, productupdate_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record(s) inserted successfully into ProductUpdated table")

        # Commit changes
        self.conn.commit()

        # Create new product
        new_product = Product(
            product_id = product_update.productName,
            store_id = product_update.storeAddress,
            title = " ",
            description = " ",
            price = product_update.newPrice,
            features = []
        )

        # Remove old product from dictionary and DB and add new product
        for current_product in self.products:
            if(current_product.product_id == product_update.productName):
                self.products.pop(current_product)
                self.delete_products(current_product)
                break 
        
        self.products[new_product] = new_product

        # Add to product table in DB
        self.add_products(new_product)
    
    def to_array(self, value):
        return '{' + ','.join(value) + '}'

    def write_payment_made(self, transaction: PaymentMade): 
        paymentmade_list = list(dataclasses.asdict(transaction).values()) 

        paymentmade_list[-1] = self.to_array(paymentmade_list[-1])
        
        paymentmade_tuple = tuple(paymentmade_list)

        # Insert PaymentMade event details 
        insert_payment_made = """ INSERT INTO paymentmade (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, CUSTOMER, STOREADDRESS, PRODUCTNAMES) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_payment_made, paymentmade_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record(s) inserted successfully into PaymentMade table")

        # Commit changes
        self.conn.commit()

        # Add to list
        self.paymentmade.append(transaction)

    def write_refund_made(self, transaction: RefundMade):
        refundmade_list = list(dataclasses.asdict(transaction).values()) 

        refundmade_list[-1] = self.to_array(refundmade_list[-1])
        
        refundmade_tuple = tuple(refundmade_list)

        # Insert RefundMade event details 
        insert_refund_made = """ INSERT INTO refundmade (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, CUSTOMER, STOREADDRESS, PRODUCTNAMES) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_refund_made, refundmade_tuple)

        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record(s) inserted successfully into RefundMade table")

        # Commit changes
        self.conn.commit()

        # Add to list
        self.refundmade.append(transaction)

    def get_products(self):
        return self.products.values()

    def get_stores(self):
        return self.stores.values()


# if __name__ == "__main__":
#     import logging
#     import os 

#     log_file = os.path.join("middle-tier-service.log")
#     logging.basicConfig(filename=log_file, level=logging.DEBUG)

#     db = postgresDBClient(logging)

#     blank_store = Store('hey1', " ", 
#                     " ", 
#                     '123')
    
    # new_store = Store('hey', "Super Algorithms Inc.", 
    #                   "We help you prepare for Tech Interviews", 
    #                   '0x599410057bc933fd2f7319a5a835c88a9300bfb0')
    # db.add_stores(blank_store)
    # db.update_store(new_store)
    # db_stores = db.get_store()
    # print(db_stores)


    # blank_product = Product("C#", "hey", " ", 
    #                         " ", 45000,
    #                         [])

    # new_product = Product("C++", "super-algorithms", "C++ course", 
    #                     "Try out our original course in C++ and impress your interviewers.", 10000,
    #                     ["Full algorithms course in C++",
    #                     "Pointers Cheat Sheet",
    #                     "Memory Management Tips"])
    # db.add_products(blank_product)
    # db.update_product(new_product)
    # db_products = db.get_product()
    # print(db_products)
