
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("IMS_DB_HOST", "localhost"),
        port=int(os.getenv("IMS_DB_PORT", "3306")),
        user=os.getenv("IMS_DB_USER", "root"),
        password=os.getenv("IMS_DB_PASSWORD", ""),
        database=os.getenv("IMS_DB_NAME", "I_M_S_Real"),
    )

def test_connection():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT DATABASE()")
        return cur.fetchone()[0]
    finally:
        conn.close()
