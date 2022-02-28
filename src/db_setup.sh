# ssh into Google Cloud VM
ssh 35.195.58.180

# To run these commands within VM:
# set to postgres user 
sudo -i -u postgres

# enter postgres
psql

# search db
\l

# add db
CREATE DATABASE salesfunnel;

# enter db
\c salesfunnel

# create table
CREATE TABLE PaymentMade(
block_hash TEXT NOT NULL,
transaction_hash TEXT NOT NULL,
block_number INT NOT NULL,
address TEXT NOT NULL, 
data TEXT NOT NULL,
transaction_idx INT NOT NULL,
customer TEXT NOT NULL,
storeAddress TEXT NOT NULL,
productNames TEXT[]);

CREATE TABLE RefundMade(
block_hash TEXT NOT NULL,
transaction_hash TEXT NOT NULL,
block_number INT NOT NULL,
address TEXT NOT NULL, 
data TEXT NOT NULL,
transaction_idx INT NOT NULL,
customer TEXT NOT NULL,
storeAddress TEXT NOT NULL,
productNames TEXT[]);


CREATE TABLE ProductCreated(
block_hash TEXT NOT NULL,
transaction_hash TEXT NOT NULL,
block_number INT NOT NULL,
address TEXT NOT NULL, 
data TEXT NOT NULL,
transaction_idx INT NOT NULL,
storeAddress TEXT NOT NULL,
productName TEXT NOT NULL,
price INT NOT NULL);

CREATE TABLE ProductRemoved(
block_hash TEXT NOT NULL,
transaction_hash TEXT NOT NULL,
block_number INT NOT NULL,
address TEXT NOT NULL, 
data TEXT NOT NULL,
transaction_idx INT NOT NULL,
storeAddress TEXT NOT NULL,
productName TEXT NOT NULL);


CREATE TABLE ProductUpdated(
block_hash TEXT NOT NULL,
transaction_hash TEXT NOT NULL,
block_number INT NOT NULL,
address TEXT NOT NULL, 
data TEXT NOT NULL,
transaction_idx INT NOT NULL,
storeAddress TEXT NOT NULL,
productName TEXT NOT NULL,
newPrice INT);

CREATE TABLE StoreCreated(
block_hash TEXT NOT NULL,
transaction_hash TEXT NOT NULL,
block_number INT NOT NULL,
address TEXT NOT NULL, 
data TEXT NOT NULL,
transaction_idx INT NOT NULL,
storeAddress TEXT NOT NULL,
storeOwner TEXT NOT NULL)
;

CREATE TABLE StoreRemoved(
block_hash TEXT NOT NULL,
transaction_hash TEXT NOT NULL,
block_number INT NOT NULL,
address TEXT NOT NULL, 
data TEXT NOT NULL,
transaction_idx INT NOT NULL,
storeAddress TEXT NOT NULL);


CREATE TABLE StoreUpdated(
block_hash TEXT NOT NULL,
transaction_hash TEXT NOT NULL,
block_number INT NOT NULL,
address TEXT NOT NULL, 
data TEXT NOT NULL,
transaction_idx INT NOT NULL,
storeAddress TEXT NOT NULL,
newStoreAddress TEXT NOT NULL);

CREATE TABLE Stores(
id TEXT NOT NULL,
title TEXT,
description TEXT,
store_owner TEXT NOT NULL,
PRIMARY KEY (id));

CREATE TABLE Products(
product_id TEXT NOT NULL,
store_id TEXT NOT NULL,
title TEXT,
description TEXT,
price INT NOT NULL,
features TEXT[],
PRIMARY KEY (product_id, store_id),
FOREIGN KEY (store_id)
REFERENCES stores(id));

CREATE TABLE StoresEditable(
id TEXT NOT NULL,
title TEXT,
description TEXT,
store_owner TEXT NOT NULL,
PRIMARY KEY (id));

CREATE TABLE ProductsEditable(
product_id TEXT NOT NULL,
store_id TEXT NOT NULL,
title TEXT,
description TEXT,
price INT NOT NULL,
features TEXT[],
PRIMARY KEY (product_id, store_id),
FOREIGN KEY (store_id)
REFERENCES stores(id));

# tables summary
\dt

# quit postgres
\q
exit