#connect to postgres db using postgres role
sudo -i -u postgres

#access postgres
psql

#check db list
\l

#access db - to fill in db name
"""
1. users
2. transactions
3. product_store
"""

\c #<dbname>

#exit postgres
#\q

#return to regular system user
#exit