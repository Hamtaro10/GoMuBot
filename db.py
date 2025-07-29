import mysql.connector
import os
from dotenv import load_dotenv
from mysql.connector.cursor import MySQLCursorDict 
import datetime

load_dotenv()

def get_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
        use_pure = True
    )
    cursor = conn.cursor(cursor_class=MySQLCursorDict)
    return conn, cursor

def load_bot_data():
    conn, cursor = get_connection()
    cursor.execute("SELECT * FROM music_bots")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def add_bot_data(bot_id, bot_name):
    conn, cursor = get_connection()
    cursor.execute("INSERT INTO music_bots (id, name) VALUES (%s, %s)", (bot_id, bot_name))
    conn.commit()
    cursor.close()
    conn.close()

def set_afk(user_id: int, reason: str, original_nick: str, since:datetime):
    conn, cursor = get_connection()
    query = """
        REPLACE INTO afk_users (user_id, reason, original_nick, since)
        VALUES (%s, %s, %s)
    """
    cursor.execute(query, (user_id, reason, original_nick, since))
    conn.commit()
    cursor.close()
    conn.close()

def get_afk(user_id: int):
    conn, cursor = get_connection()
    cursor.execute("SELECT * FROM afk_users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def remove_afk(user_id: int):
    conn, cursor = get_connection()
    cursor.execute("DELETE FROM afk_users WHERE user_id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()