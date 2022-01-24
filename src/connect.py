import dataclasses
import psycopg2
from dbinfo import User, Transaction

class postgresDBClient:
    def __init__():
        pass

    def connect(): #testing function
        # Connection establishment
        conn = psycopg2.connect(
            database='transactions',
            user='postgres',
            password = 'crypto',
            host='localhost', 
            port= '5432'
        )

        conn.autocommit = True

        # Creating a cursor object
        cursor = conn.cursor()

        # Print when connection is successful
        print("Database has been connected successfully !!");

        # Closing the connection
        cursor.close()
        conn.close()

    def get_users():
        # Connection establishment
        conn = psycopg2.connect( #repetition included for testing purposes
            database='users',
            user='postgres',
            password = 'crypto',
            host='localhost', 
            port= '5432'
        )

        cursor = conn.cursor()

        # Query
        cursor.execute("SELECT name, email_add, wallet_id FROM userinfo ORDER BY name")
        rows = cursor.fetchall()
        print("The number of users: ", cursor.rowcount)

        for row in rows:
            print(row)

        cursor.close()

        # Close connection
        conn.close() 


    def get_transactions():
        # Connection establishment
        conn = psycopg2.connect( #repetition included for testing purposes
            database='transactions',
            user='postgres',
            password = 'crypto',
            host='localhost', 
            port= '5432'
        )
        
        cursor = conn.cursor()
        
        # Query
        cursor.execute("SELECT payer_id, payee_id, coin, amount, gas_spend FROM transaction ORDER BY payer_id")
        rows = cursor.fetchall()
        print("The number of transactions: ", cursor.rowcount)
        
        for row in rows:
            print(row)
        
        cursor.close()
        
        # Close connection
        conn.close() 
        
    def add_users(self, user: User):
        user_tuple = dataclasses.astuple(user)

        # Connection establishment
        conn = psycopg2.connect( #repetition included for testing purposes
            database='users',
            user='postgres',
            password = 'crypto',
            host='localhost', 
            port= '5432'
        )

        cursor = conn.cursor()

        # Insert user details 
        insert_user = """ INSERT INTO userinfo (NAME, EMAIL_ADD, WALLET_ID) VALUES (%s,%s,%s)"""
        cursor.execute(insert_user, user_tuple)

        # Check insertion
        count = cursor.rowcount
        print(count, "Record inserted successfully into userinfo table")

        # Commit changes
        conn.commit()

        # Close connection
        conn.close()     

        
    def add_transactions(self, trxn: Transaction):
        trxn_tuple = dataclasses.astuple(trxn)
        
        # Connection establishment
        conn = psycopg2.connect( #repetition included for testing purposes
            database='transactions',
            user='postgres',
            password = 'crypto',
            host='localhost', 
            port= '5432'
        )

        cursor = conn.cursor()

        # Insert transaction details 
        insert_transaction = """ INSERT INTO transaction (PAYER_ID, PAYEE_ID, COIN, AMOUNT, GAS_SPEND) VALUES (%s,%s,%s,%s,%s)"""
        cursor.execute(insert_transaction, trxn_tuple)

        # Check insertion
        count = cursor.rowcount
        print(count, "Record inserted successfully into transaction table")

        # Commit changes
        conn.commit()

        # Close connection
        conn.close()

