"""
Lightweight DB abstraction: prefers MySQL if environment variable USE_MYSQL=1 and PyMySQL is available,
otherwise falls back to SQLite using the local `stress_chat.db` file.

Functions:
 - get_conn(): returns a DB connection object (sqlite3.Connection or pymysql connection-like)
 - query helper utilities may be added here as needed.
"""
import os
import sqlite3
import urllib.parse

USE_MYSQL = os.environ.get('USE_MYSQL') == '1' or bool(os.environ.get('DATABASE_URL'))
DB_PATH = os.path.join(os.path.dirname(__file__), 'stress_chat.db')

def get_conn():
    """Return a DB connection. If MySQL requested and available, try to connect, else SQLite."""
    if USE_MYSQL:
        try:
            import pymysql
        except Exception:
            # PyMySQL not available — fall back to sqlite
            return sqlite3.connect(DB_PATH)

        db_url = os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL')
        if not db_url:
            # try default mysql connect params
            return sqlite3.connect(DB_PATH)

        # Expecting format mysql://user:pass@host:port/dbname
        parsed = urllib.parse.urlparse(db_url)
        user = parsed.username
        password = parsed.password
        host = parsed.hostname or 'localhost'
        port = parsed.port or 3306
        dbname = parsed.path.lstrip('/')

        conn = pymysql.connect(host=host, user=user, password=password, db=dbname, port=port, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor, autocommit=True)
        return conn

    # Default: SQLite
    conn = sqlite3.connect(DB_PATH)
    # return sqlite3 rows as tuples (existing app code expects this)
    return conn
