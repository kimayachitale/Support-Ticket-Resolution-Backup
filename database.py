import sqlite3
from datetime import datetime

DATABASE = "tickets.db"


def create_table():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            complaint TEXT,

            category TEXT,

            pnr_number TEXT,

            decision TEXT,

            created_at TEXT

        )
    """)

    conn.commit()
    conn.close()



def save_ticket(complaint, category, pnr_number, decision):

    complaint = complaint.replace("\n", " ").strip()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    created_at = datetime.now().strftime("%d-%m-%Y %H:%M")

    cursor.execute("""
        INSERT INTO tickets
        (complaint, category, pnr_number, decision, created_at)

        VALUES (?, ?, ?, ?, ?)

    """,
    (
        complaint,
        category,
        pnr_number,
        decision,
        created_at
    ))

    conn.commit()
    conn.close()



def get_history():

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM tickets"
    )

    data = cursor.fetchall()

    conn.close()

    return data



def clear_history():

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tickets"
    )

    conn.commit()

    conn.close()



# -------- Dashboard Functions --------

def get_total_tickets():

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM tickets"
    )

    total = cursor.fetchone()[0]

    conn.close()

    return total



def get_category_count(category):

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM tickets WHERE category=?",
        (category,)
    )

    count = cursor.fetchone()[0]

    conn.close()

    return count



create_table()