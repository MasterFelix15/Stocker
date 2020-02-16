#!/usr/bin/python

import sqlite3

conn = sqlite3.connect('stocker.db')
print("Opened database successfully")

conn.execute('''
CREATE TABLE USER(
    ID INT PRIMARY KEY     NOT NULL,
    NAME           TEXT    NOT NULL
);''')

conn.execute('''
CREATE TABLE STOCK(
    USERID      INT     NOT NULL,
    SYMBOL      TEXT    NOT NULL,
    NUM_SHARES  INT     NOT NULL,
    MARGIN      FLOAT   NOT NULL,
    PRIMARY KEY (USERID, SYMBOL),
    FOREIGN KEY(USERID) REFERENCES USER(ID) ON UPDATE CASCADE
);''')

print("Table created successfully")

conn.commit()

conn.close()
