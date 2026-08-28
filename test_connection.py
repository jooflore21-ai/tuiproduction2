import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    print("You are connected to - ", db_version)
    cursor.close()
    conn.close()
except Exception as e:
    print(e)