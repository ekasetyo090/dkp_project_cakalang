import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv


load_dotenv()

HOST = os.getenv('MYSQL_HOST')
USER = os.getenv('MYSQL_USER')
PASSWORD = os.getenv('MYSQL_PASSWORD')
DATABASE = os.getenv('MYSQL_DATABASE')
PORT = int(os.getenv('MYSQL_PORT'))

def create_connection():
    """Membuat koneksi ke database."""
    try:
        connection = mysql.connector.connect(
            host=HOST,
            user=USER,
            password=PASSWORD,
            database=DATABASE,
            port=PORT
        )
        return connection
    except Error as e:
        raise ConnectionError(f"❌ Gagal membuat koneksi database: {e}")

def create_cursor(connection):
    """Membuat cursor dari koneksi."""
    return connection.cursor(dictionary=True)