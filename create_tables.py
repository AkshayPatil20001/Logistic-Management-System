import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    mobile TEXT,
    business_name TEXT,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('owner','developer')),
    profile_image BLOB,
    company_image BLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

c.execute('''CREATE TABLE IF NOT EXISTS trucks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    truck_number TEXT NOT NULL,
    truck_model TEXT,
    driver_name TEXT,
    status TEXT DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(owner_id) REFERENCES users(id)
)''')

conn.commit()
conn.close()
print("✅ Database and tables created successfully!")
