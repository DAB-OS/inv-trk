import sqlite3

# Connect to the database (this will create the database file if it doesn't exist)
conn = sqlite3.connect('inventory.db')

# Create a cursor object to execute SQL commands
cursor = conn.cursor()

# SQL command to create the 'inventory' table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        expiry_date TEXT NOT NULL,
        min_quantity INTEGER NOT NULL,
        last_used TEXT
    )
''')

# Commit the transaction and close the connection
conn.commit()
conn.close()

print("Database and 'inventory' table created successfully.")
