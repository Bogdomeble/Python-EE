import sqlite3
import sys
import pandas as pd
# task 1

try:
    con = sqlite3.connect('northwind.db');
except sqlite3.Error as e:
    print(f'connection to database has failed! {e}')
    sys.exit()

# print(customers_df, customers_df.shape)

# print(orders_df, orders_df.shape)

# task 2

customers_df = pd.read_sql_query("SELECT * FROM Customers", con)
orders_df = pd.read_sql_query("SELECT * FROM Orders", con)



task2_1 = customers_df['City'].unique()

print(f'Number of unique cities {task2_1}')

task2_2 = customers_df['City'].value_counts()

print(f'{task2_2}')

task2_3 = orders_df[]

con.close()