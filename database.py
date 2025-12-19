import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

# --- Configurações de Banco de Dados ---
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_conn():
    return psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, 
        host=DB_HOST, port=DB_PORT, 
        cursor_factory=psycopg2.extras.RealDictCursor
    )