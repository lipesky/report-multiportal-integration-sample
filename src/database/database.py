import sqlite3
import os
db = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', '..', 'sample-report-multiportal-server.db'))
db.execute('''
    CREATE TABLE IF NOT EXISTS user(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(255),
        name VARCHAR(255),
        password VARCHAR(255),
        active TINYINT DEFAULT 1,
        created_at DATETIME DEFAULT NOW
    )
''')