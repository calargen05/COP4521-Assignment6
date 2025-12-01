# init_db.py
import sqlite3
from pathlib import Path
from crypto_utils import encrypt_str, decrypt_str

DB = Path(__file__).with_name("baking_contest.db")

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def recreate_tables():
    conn = get_conn()
    cur = conn.cursor()

    # Drop tables
    cur.executescript("""
    DROP TABLE IF EXISTS BakingContestEntry;
    DROP TABLE IF EXISTS BakingContestPeople;
    """)

    # Create people table: store encrypted fields as TEXT
    cur.execute("""
    CREATE TABLE BakingContestPeople (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        phone TEXT NOT NULL,
        security_level INTEGER NOT NULL,
        login_password TEXT NOT NULL
    );
    """)

    # Create entries
    cur.execute("""
    CREATE TABLE BakingContestEntry (
        entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        item_name TEXT NOT NULL,
        num_excellent INTEGER NOT NULL,
        num_ok INTEGER NOT NULL,
        num_bad INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES BakingContestPeople(id)
    );
    """)

    conn.commit()
    conn.close()

def seed_data():
    conn = get_conn()
    cur = conn.cursor()

    # three users, security level 1,2,3
    users = [
        ("alice", 21, "111-111-1111", 1, "alicepass"),
        ("bob", 30, "222-222-2222", 2, "bobpass"),
        ("admin", 40, "333-333-3333", 3, "adminpass"),
    ]

    for name, age, phone, level, pw in users:
        enc_name = encrypt_str(name)
        enc_phone = encrypt_str(phone)
        enc_pw = encrypt_str(pw)
        cur.execute(
            """
            INSERT INTO BakingContestPeople (name, age, phone, security_level, login_password)
            VALUES (?, ?, ?, ?, ?)
            """,
            (enc_name, age, enc_phone, level, enc_pw),
        )

    # add some entries (user_id referencing actual inserted rows: 1,2,3)
    entries = [
        (1, "Chocolate Cake", 5, 3, 0),
        (2, "Blueberry Muffins", 2, 4, 1),
        (3, "Apple Pie", 4, 2, 0),
    ]
    cur.executemany(
        """
        INSERT INTO BakingContestEntry
        (user_id, item_name, num_excellent, num_ok, num_bad)
        VALUES (?, ?, ?, ?, ?)
        """,
        entries
    )

    conn.commit()

    # Display all data with decrypted fields (per assignment)
    print("Current BakingContestPeople (decrypted):")
    rows = cur.execute("SELECT id, name, age, phone, security_level, login_password FROM BakingContestPeople").fetchall()
    for r in rows:
        print({
            "id": r["id"],
            "name": decrypt_str(r["name"]),
            "age": r["age"],
            "phone": decrypt_str(r["phone"]),
            "security_level": r["security_level"],
            "login_password": decrypt_str(r["login_password"])
        })

    conn.close()

if __name__ == "__main__":
    recreate_tables()
    seed_data()
    print("Database initialized.")
