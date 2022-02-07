from typing import List
import dataclasses
import psycopg2
from dbinfo import User, Transaction

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
        self.cursor.execute("SELECT name, email_add, wallet_id FROM userinfo ORDER BY name")
        rows = self.cursor.fetchall()
        print("The number of users: ", self.cursor.rowcount)

        users = []
        for row in rows:
            users.append(User(*row))

        return users


    def get_transactions(self):
        # Query
        self.cursor.execute("SELECT payer_id, payee_id, coin, amount, gas_spend FROM transaction ORDER BY payer_id")
        rows = self.cursor.fetchall()
        print("The number of transactions: ", self.cursor.rowcount)
        
        for row in rows:
            print(row)
        

    def add_users(self, user: User):
        user_tuple = dataclasses.astuple(user)

        # Insert user details 
        insert_user = """ INSERT INTO userinfo (NAME, EMAIL_ADD, WALLET_ID) VALUES (%s,%s,%s)"""
        # insert_user_str = f"INSERT INTO userinfo (NAME, EMAIL_ADD, WALLET_ID) VALUES ({user})"

        self.cursor.execute(insert_user, user_tuple)


        # Check insertion
        count = self.cursor.rowcount
        print(count, "Record inserted successfully into userinfo table")

        # Commit changes
        self.conn.commit()

        
    def add_transactions(self, trxn: Transaction):
        trxn_tuple = dataclasses.astuple(trxn)

        # Insert transaction details 
        insert_transaction = """ INSERT INTO transaction (PAYER_ID, PAYEE_ID, COIN, AMOUNT, GAS_SPEND) VALUES (%s,%s,%s,%s,%s)"""

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

    users = db_user.get_users()
    for us in users:
        print(us)
        # db_user.add_users(us)

    
    
    
    # db_product_store = postgresDBClient('')