from typing import Dict, List
import dataclasses
import psycopg2
from db_objects import Store, User, Transaction, Product, StoreCreated, StoreRemoved, StoreUpdated, PaymentMade, RefundMade, ProductCreated, ProductRemoved, ProductUpdated, AffiliateRegistered, OwnershipTransferred

from logging import Logger

# TODO: Test for new smart contract


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

        self.logging = logging

        # self.logging.info when connection is successful
        self.logging.info("Database has been connected successfully !!")

        # Initialise stores, products, transactions, affiliates
        self.stores: Dict[Store, Store] = {}
        self.products: Dict[Product, Product] = {}
        # TODO: affiliates commented out
        # self.affiliates: Dict[Affiliate, Affiliate] = {}
        self.paymentmade: List[PaymentMade] = [] #TODO: to send this information to frontend for analytics
        self.refundmade: List[RefundMade] = [] #TODO: to send this information to frontend for analytics

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

        # self.logging.info when connection is successful
        self.logging.info("Database has been connected successfully !!")

    def close_connection(self): 
        # Closing the connection
        self.cursor.close()
        self.conn.close()
    
    def check_stores(self, store_id):
        # Query
        self.cursor.execute("SELECT id FROM stores WHERE id = %s", (store_id, ))
        self.logging.info(f"The number of existing stores: {self.cursor.rowcount}", )

        # return boolean
        return self.cursor.rowcount > 0

    def check_products(self, product, updated = False):
        if not updated:
            # Query
            self.cursor.execute("SELECT product_id FROM products WHERE product_id = %s AND store_id = %s", (product.productName, product.storeAddress))
            self.logging.info(f"The number of existing products: {self.cursor.rowcount}")
            
            # return boolean
            return self.cursor.rowcount > 0
        
        else:
            # Query
            self.cursor.execute("SELECT product_id FROM products WHERE product_id = %s AND store_id = %s AND price = %s", (product.productName, product.storeAddress, product.newPrice))
            self.logging.info(f"The number of existing updated products: {self.cursor.rowcount}")
            
            # return boolean
            return self.cursor.rowcount > 0

    #TODO: Affiliates commented out
    # def check_affiliates(self, affiliate_address):
    #      # Query
    #     self.cursor.execute("SELECT id FROM affiliates WHERE affiliate_address = %s", (affiliate_address, ))
    #     self.logging.info(f"The number of existing affiliates: {self.cursor.rowcount}", )

    #     # return boolean
    #     return self.cursor.rowcount > 0

    def get_stores_db(self, store_id, dynamic = False):
        # Query
        if not dynamic:
            self.cursor.execute("SELECT id, title, description, store_owner FROM stores WHERE id = %s", (store_id, ))
            self.logging.info(f"{self.cursor.rowcount} stores retrieved", )

            row = self.cursor.fetchone()
            (id, title, description, store_owner) = row
            store = Store(id, title, description, store_owner)
            
            return store
        
        else:
            self.cursor.execute("SELECT title, description FROM stores WHERE id = %s", (store_id, ))
            self.logging.info(f"{self.cursor.rowcount} dynamic fields of store retrieved", )
            
            row = self.cursor.fetchone()
            (title, description) = row

            return title, description

    def get_products_db(self, product_id, store_id, dynamic = False):
        # Query
        if not dynamic:
            self.cursor.execute("SELECT product_id, store_id, title, description, price, features, product_type FROM products WHERE product_id = %s AND store_id = %s", (product_id, store_id))
            self.logging.info(f"{self.cursor.rowcount} products retrieved", )

            row = self.cursor.fetchone()
            (product_id, store_id, title, description, price, features) = row
            product = Product(product_id, store_id, title, description, price, features)

            return product
        
        else:
            self.cursor.execute("SELECT title, description, features, product_type FROM products WHERE product_id = %s AND store_id = %s", (product_id, store_id))
            self.logging.info(f"{self.cursor.rowcount} dynamic fields of product retrieved", )

            row = self.cursor.fetchone()
            (title, description, features) = row

            return title, description, features

    #TODO: Affiliates commented out
    # def get_affiliates_db(self, affiliate_address, dynamic = False):
    #     # Query
    #     self.cursor.execute("SELECT affiliate_address FROM affiliates WHERE affiliate_address = %s", (affiliate_address, ))
    #     self.logging.info(f"{self.cursor.rowcount} affiliates retrieved", )

    #     row = self.cursor.fetchone()
    #     (affiliate_address) = row
    #     affiliate = Affiliate(affiliate_address)
        
    #     return affiliate

    def add_stores(self, st: Store):
        st_tuple = (st.id, st.title, st.description, st.storeOwner)

        # Insert store details 
        insert_store = """ INSERT INTO stores (ID, TITLE, DESCRIPTION, STORE_OWNER) VALUES (%s,%s,%s,%s)"""

        try:
            self.cursor.execute(insert_store, st_tuple)

            # Commit changes to db
            self.conn.commit()

        except Exception as e:
            error_msg = f"Unable to add new store: Exception: {e}"
            self.logging.warning(error_msg)

        # Check insertion
        count = self.cursor.rowcount
        self.logging.info(f"{count} Record(s) inserted successfully into Stores table")

    def add_products(self, prdt: Product):
        prdt_tuple = (prdt.productName, prdt.storeAddress, prdt.title, prdt.description, prdt.price, prdt.features, prdt.productType)

        # Insert product details 
        insert_product = """ INSERT INTO products (PRODUCT_ID, STORE_ID, TITLE, DESCRIPTION, PRICE, FEATURES, PRODUCT_TYPE) VALUES (%s,%s,%s,%s,%s,%s,%s)"""

        try:
            self.cursor.execute(insert_product, prdt_tuple)
        
            # Commit changes to db
            self.conn.commit()
        
        except Exception as e:
            error_msg = f"Unable to add new product: Exception: {e}"
            self.logging.warning(error_msg)

        # Check insertion
        count = self.cursor.rowcount
        self.logging.info(f"{count} Record(s) inserted successfully into Products table")

    #TODO: Affiliates commented out
    # def add_affiliates(self, affiliate: Affiliates):
    #     affiliate_tuple = dataclasses.astuple(st)

    #     # Insert affiliate details 
    #     insert_affiliate = """ INSERT INTO affiliates (AFFILIATE_ADDRESS) VALUES (%s)"""

    #     try:
    #         self.cursor.execute(insert_affiliate, affiliate_tuple)

    #         # Commit changes to db
    #         self.conn.commit()

    #     except Exception as e:
    #         error_msg = f"Unable to add new affiliate: Exception: {e}"
    #         self.logging.warning(error_msg)
        

    #     # Check insertion
    #     count = self.cursor.rowcount
    #     self.logging.info(f"{count} Record(s) inserted successfully into Affiliates table")

    def update_store(self, store: Store):
        try:
            # Update by store_address
            self.cursor.execute("UPDATE stores SET title = %s, description = %s WHERE id = %s", (store.title, store.description, store.id))
            # Commit the changes to the database
            self.conn.commit()
        except Exception as e:
            error_msg = f"Unable to update store: Exception: {e}"
            self.logging.warning(error_msg)

        # get the number of updated stores
        rows_updated = self.cursor.rowcount
        self.logging.info(f"{rows_updated} Record(s) updated on Stores table")

        # Create new store
        new_store = Store(
            id=store.id,
            title = store.title,
            description = store.description,
            store_owner = store.storeOwner,
        )

        # Update dictionary
        for current_store in self.stores:
                if(current_store.id == new_store.id):
                    self.stores.pop(current_store)
                    break

        self.stores[new_store] = new_store

    def update_product(self, product: Product):
        try:
            # Update by product_id and store_id
            self.cursor.execute("UPDATE products SET title = %s, description = %s, features = %s WHERE product_id = %s AND store_id = %s", (product.title, product.description, self.to_array(product.features), product.productName, product.storeAddress))
        except Exception as e:
            error_msg = f"Unable to update product: Exception: {e}"
            self.logging.warning(error_msg)

        # get the number of updated stores
        rows_updated = self.cursor.rowcount
        self.logging.info(f" {rows_updated} Record(s) updated on Products table")

        # Commit the changes to the database
        self.conn.commit()

        # Create new product
        new_product = Product(
            product_id = product.productName,
            store_id = product.storeAddress,
            title = product.title,
            description = product.description,
            price = product.price,
            features = product.features,
            product_type = product.productType
        )

        # Update dictionary
        for current_product in self.products:
            if(current_product.productName == new_product.productName):
                self.products.pop(current_product)
                break

        self.products[new_product] = new_product

    def delete_stores(self, store: Store):
        store_address = store.id
        
        try:        
           # Delete store by store_address
            self.cursor.execute("DELETE FROM stores WHERE id = %s", (store_address,))
            # Commit the changes to the database
            self.conn.commit()
        except Exception as e:
            error_msg = f"Unable to delete store: Exception: {e}"
            self.logging.warning(error_msg)
        

        # get the number of updated rows
        rows_deleted = self.cursor.rowcount
        self.logging.info(f"{rows_deleted} Record(s) deleted from Stores table")
        
    def delete_products(self, product: Product):
        product_name = product.productName

        try:
            # Delete products by product_id
            self.cursor.execute("DELETE FROM products WHERE product_id = %s", (product_name,))
            # Commit the changes to the database
            self.conn.commit()
        except Exception as e:
            error_msg = f"Unable to delete product: Exception: {e}"
            self.logging.warning(error_msg)

        # get the number of updated rows
        rows_deleted = self.cursor.rowcount
        self.logging.info(f" {rows_deleted} Record(s) deleted from Products table")

    def write_store_created(self, store: StoreCreated):
        storecreate_tuple = (store.blockHash, store.transactionHash, store.blockNumber, store.address, store.data,
                             store.transaction_idx, store.storeAddress, store.storeOwner)

        # Insert StoreCreated event details 
        insert_store_created = """ INSERT INTO storecreated (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, STOREOWNER) VALUES (%s,%s,%s,%s,%s,%s,%s, %s)"""
        self.cursor.execute(insert_store_created, storecreate_tuple)

        # Check insertion
        count = self.cursor.rowcount
        self.logging.info(f"{count} Record(s) inserted successfully into StoreCreated table")

        # Commit changes
        self.conn.commit()

        # Check if store exists in db and add existing store to dictionary 
        if self.check_stores(store.storeAddress):
            existing_store = self.get_stores_db(store.storeAddress)
            self.stores[existing_store] = existing_store
            self.logging.info(f"{store.storeAddress} id: store exists")
        
        else:
            # Add new store to stores db and stores dictionary
            # Create new store
            new_store = Store(
                id=store.storeAddress,
                title="",
                description = "",
                store_owner = store.storeOwner,
            )

            # Add to dictionary 
            self.stores[new_store] = new_store

            # Add to dynamic store table in DB
            self.add_stores(new_store)

    def write_store_removed(self, store: StoreRemoved): 
        storeremove_tuple = dataclasses.astuple(store)

        # Insert StoreRemoved event details 
        insert_store_removed = """ INSERT INTO storeremoved (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS) VALUES (%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_store_removed, storeremove_tuple)

        # Check insertion
        count = self.cursor.rowcount
        self.logging.info(f"{count} Record(s) inserted successfully into StoreRemoved table")

        # Commit changes
        self.conn.commit()

        # Remove store from dictionary and DB and also remove related products in store                
        for current_product in self.products:
            if(current_product.storeAddress == store.storeAddress):
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
        self.logging.info(f"{count} Record(s) inserted successfully into StoreUpdated table")

        # Commit changes
        self.conn.commit()

        # Check if updated store exists in db and add existing store to dictionary 
        if self.check_stores(store.newStoreAddress):
            existing_updated_store = self.get_stores_db(store.newStoreAddress)
            self.stores[existing_updated_store] = existing_updated_store
            self.logging.info(f"{store.newStoreAddress} id: updated store exists")

        # Check if non-updated store exists in db and update store  
        elif self.check_stores(store.storeAddress):
            self.logging.info(f"{store.storeAddress} id: non-updated store exists")
            existing_title, existing_description = self.get_stores_db(store.storeAddress, dynamic = True)

            # Create new store
            # NOTE: This is already updated for new smart contract
            new_store = Store(
                id=store.newStoreAddress,
                title=existing_title,
                description = existing_description,
                store_owner = store.newStoreAddress
            )

            # NOTE: All products tied to previous store have been deleted and updated store is empty
            for current_product in self.products:
                if(current_product.storeAddress == store.storeAddress):
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

        
        else:
            self.logging.info(f"{store.storeAddress} id: store does not exist. To add store first.")

    def write_product_created(self, product: ProductCreated):
        productcreate_tuple = dataclasses.astuple(product)

        # Insert ProductCreated event details 
        insert_product_created = """ INSERT INTO productcreated (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, PRODUCTNAME, PRODUCTTYPE, PRICE) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        self.cursor.execute(insert_product_created, productcreate_tuple)

        # Check insertion
        count = self.cursor.rowcount
        self.logging.info(f"{count} Record(s) inserted successfully into ProductCreated table")

        # Commit changes
        self.conn.commit()

        # Check if product exists in db and add existing product to dictionary 
        if self.check_products(product):
            existing_product = self.get_products_db(product.productName, product.storeAddress)
            self.products[existing_product] = existing_product
            self.logging.info(f"{product.productName} id: product exists")
        
        else:
            # Create new product
            new_product = Product(
                productName=product.productName,
                storeAddress=product.storeAddress,
                title="",
                description="",
                price=product.price,
                features=[],
                productType=product.productType
            )

            # Add to dictionary
            self.products[new_product] = new_product

            # Add to dynamic product table in DB
            self.add_products(new_product)

    def write_product_removed(self, product: ProductRemoved): 
        productremove_tuple = dataclasses.astuple(product)

        # Insert ProductRemoved event details 
        insert_product_removed = """ INSERT INTO productremoved (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, PRODUCTNAME) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_product_removed, productremove_tuple)

        # Check insertion
        count = self.cursor.rowcount
        self.logging.info(f"{count} Record(s) inserted successfully into ProductRemoved table")

        # Commit changes
        self.conn.commit()

        # Remove product from dictionary and DB
        for current_product in self.products:
            if current_product.productName == product.productName:
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
        self.logging.info(f"{count} Record(s) inserted successfully into ProductUpdated table")

        # Commit changes
        self.conn.commit()

        # Check if updated product exists in db and add existing product to dictionary 
        if self.check_products(product_update, updated = True):
            existing_product = self.get_products_db(product_update.productName, product_update.storeAddress)
            self.products[existing_product] = existing_product
            self.logging.info(f"{product_update.productName} id: updated product exists")

        elif self.check_products(product_update):
            existing_title, existing_description, existing_features = self.get_products_db(product_update.productName, product_update.storeAddress, dynamic = True)
            
            # Create new product
            new_product = Product(
                productName=product_update.productName,
                storeAddress=product_update.storeAddress,
                title=existing_title,
                description=existing_description,
                price=product_update.newPrice,
                features=existing_features,
                productType=0
            )

            # Remove old product from dictionary and DB and add new product
            if new_product in self.products:
                old_product = self.products.get(new_product)
                new_product.productType = old_product.productType
                self.delete_products(old_product)

            self.products[new_product] = new_product

            # Add to product table in DB
            self.add_products(new_product)

        else:
            self.logging.info(f"{product_update.productName} id: product does not exist. To add product first.")

    def to_array(self, value):
        return '{' + ','.join(value) + '}'

    def write_payment_made(self, transaction: PaymentMade):
        paymentmade_tuple = (transaction.blockHash, transaction.transactionHash, transaction.blockNumber,
                             transaction.address, transaction.data, transaction.transaction_idx, transaction.customer,
                             transaction.storeAddress, self.to_array(transaction.productNames))

        # Insert PaymentMade event details
        insert_payment_made = """ INSERT INTO paymentmade (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, CUSTOMER, STOREADDRESS, PRODUCTNAMES) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_payment_made, paymentmade_tuple)

        # Check insertion
        count = self.cursor.rowcount
        self.logging.info(f"{count} Record(s) inserted successfully into PaymentMade table")

        # Commit changes
        self.conn.commit()

        # Add to list
        self.paymentmade.append(transaction)

    def write_refund_made(self, transaction: RefundMade):
        refundmade_tuple = (transaction.blockHash, transaction.transactionHash, transaction.blockNumber,
                            transaction.address, transaction.data, transaction.transaction_idx,
                            transaction.customer, transaction.storeAddress, self.to_array(transaction.product_names))

        # Insert RefundMade event details 
        insert_refund_made = """ INSERT INTO refundmade (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, CUSTOMER, STOREADDRESS, PRODUCTNAMES) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_refund_made, refundmade_tuple)

        # Check insertion
        count = self.cursor.rowcount
        self.logging.info(f"{count} Record(s) inserted successfully into RefundMade table")

        # Commit changes
        self.conn.commit()

        # Add to list
        self.refundmade.append(transaction)

    #TODO: Affiliates commented out
    # def write_affiliate_registered(self, affiliate: AffiliateRegistered): 
    #     affiliate_tuple = dataclasses.astuple(affiliate)

    #     # Insert AffiliateRegistered event details 
    #     insert_affiliate_registered = """ INSERT INTO affiliateregistered (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, STOREADDRESS, AFFILIATEADDRESS) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""

    #     self.cursor.execute(insert_affiliate_registered, affiliate_tuple)

    #     # Check insertion
    #     count = self.cursor.rowcount
    #     self.logging.info(f"{count} Record(s) inserted successfully into AffiliateRegistered table")

    #     # Commit changes
    #     self.conn.commit()

    #     # Add affiliate to dynamic affiliate table
    #     if self.check_affiliates(affiliate.affiliateAddress):
    #         existing_affiliate = self.get_affiliates_db(affiliate.affiliateAddress)
    #         self.affiliates[existing_affiliate] = existing_affiliate
    #         self.logging.info(f"{affiliate.affiliateAddress} id: affiliate exists")
        
    #     else:
    #         # Create new affiliate
    #         new_affiliate = Affiliate(
    #             affiliate_address=affiliate.affiliateAddress,
    #         )

    #         # Add to dictionary 
    #         self.affiliates[new_affiliate] = new_affiliate

    #         # Add to dynamic affiliate table in DB
    #         self.add_affiliates(new_affiliate)

   
    def write_ownership_transferred(self, store: OwnershipTransferred): 
        store_tuple = dataclasses.astuple(store)

        # Insert OwnershipTransferred event details 
        insert_ownership_transferred = """ INSERT INTO ownershiptransferred (BLOCK_HASH, TRANSACTION_HASH, BLOCK_NUMBER, ADDRESS, DATA, TRANSACTION_IDX, PREVIOUSOWNER, NEWOWNER) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""

        self.cursor.execute(insert_ownership_transferred, store_tuple)

        # Check insertion
        count = self.cursor.rowcount
        self.logging.info(f"{count} Record(s) inserted successfully into OwnershipTransferred table")

        # Commit changes
        self.conn.commit()


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
    # self.logging.info(db_stores)


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
    # self.logging.info(db_products)
