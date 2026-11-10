import sqlite3

conn = sqlite3.connect("study.db")
cur = conn.cursor()
cur.executemany(
    "INSERT INTO records (date,subject,minutes,note) VALUES (?,?,?,?)",
     [
        ("2026-11-07", "语文", 20, "好难"),
        ("2026-11-07", "火车", 50, "好难"),
        ("2026-11-07", "地理", 40, "好难"),
        ("2026-11-07", "火车", 70, "好难"),
        ("2026-11-06", "英语", 10, "好难"),
        ("2026-11-06", "地理", 90, "好难"),
     ]
)
conn.commit()

rows = cur.execute("SELECT * FROM records").fetchall()
for r in rows:
    print(r)

conn.close()