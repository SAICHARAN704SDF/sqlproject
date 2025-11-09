import sqlite3
import os

DB_PATH = "stress_chat.db"

def ensure_db():
    created = not os.path.exists(DB_PATH)
    # Use db abstraction so we can optionally switch to MySQL via env var
    from db import get_conn
    conn = get_conn()
    cur = conn.cursor()

    # chats table (conversation history)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        bot TEXT,
        label TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # users table (optional for future features)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # sessions table (track ephemeral sessions)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    # journals table (persisted journaling entries)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS journals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        entry TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    # user_actions table: log user interactions (playlist plays, breath sessions, chat prompts)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS user_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action_type TEXT,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    # resources table (seed helpful links used by the app)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        url TEXT,
        category TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()

    # Seed resources if table empty
    try:
        cur.execute('SELECT COUNT(1) FROM resources')
        row = cur.fetchone()
        count = row[0] if isinstance(row, (list, tuple)) else list(row.values())[0] if isinstance(row, dict) else 0
    except Exception:
        count = 0
    if count == 0:
        seeds = [
            ("Breathing exercise guide", "https://www.healthline.com/health/breathing-exercise", "Anxiety"),
            ("Pomodoro Technique", "https://francescocirillo.com/pages/pomodoro-technique", "Work/Academic"),
            ("Sleep hygiene tips", "https://www.sleepfoundation.org/sleep-hygiene", "sleep"),
            ("Mental health resources", "https://www.mentalhealth.gov/get-help", "general"),
            ("Suicide prevention (international)", "https://www.opencounseling.com/suicide-hotlines", "suicidal"),
            ("Calmful Spotify playlist", "https://open.spotify.com/playlist/37i9dQZF1DX3PIPIT6lEg5", "music")
        ]
        # executemany param style differs between sqlite3 (?) and pymysql (%s)
        try:
            cur.executemany('INSERT INTO resources (title, url, category) VALUES (?, ?, ?)', seeds)
        except Exception:
            # try alternative param style for MySQL drivers
            cur.executemany('INSERT INTO resources (title, url, category) VALUES (%s, %s, %s)', seeds)
        conn.commit()

    conn.close()
    if created:
        print(f"Created and initialized {DB_PATH} with tables: chats, users, sessions, resources")
    else:
        print(f"Ensured {DB_PATH} schema exists and resources seeded")


if __name__ == '__main__':
    ensure_db()
