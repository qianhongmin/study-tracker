import sqlite3

conn = sqlite3.connect("study.db")
Cur = conn.cursor()

Cur.execute("""
    CREATE TABLE records (
        date    TEXT,
        subject TEXT,
        minutes INTEGER,
        note    TEXT
    )
""")

conn.commit()
conn.close()
