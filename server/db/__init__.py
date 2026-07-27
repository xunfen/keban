import os, sqlite3, hashlib, secrets, random, string
from datetime import datetime

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'keban.db')

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    c = get_db()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 0,
            student_name TEXT DEFAULT '',
            subject TEXT NOT NULL DEFAULT '数学',
            topic TEXT DEFAULT '',
            date TEXT NOT NULL,
            content TEXT DEFAULT '',
            image_path TEXT DEFAULT '',
            is_correct BOOLEAN DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 0,
            student TEXT DEFAULT '匿名',
            content TEXT NOT NULL,
            date TEXT NOT NULL,
            handled BOOLEAN DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'student',
            display_name TEXT DEFAULT '', token TEXT, created_at TEXT NOT NULL,
            blocked BOOLEAN DEFAULT 0, plain_password TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER DEFAULT 0,
            student_name TEXT DEFAULT '', message TEXT NOT NULL,
            reply TEXT DEFAULT '', mood TEXT DEFAULT 'neutral',
            has_alert BOOLEAN DEFAULT 0, date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            subject TEXT NOT NULL, score REAL DEFAULT 0, grade TEXT DEFAULT 'E',
            exam_name TEXT DEFAULT '', term TEXT DEFAULT '',
            date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER NOT NULL, from_name TEXT DEFAULT '',
            to_user_id INTEGER DEFAULT 0, content TEXT NOT NULL,
            reply TEXT DEFAULT '', is_read BOOLEAN DEFAULT 0,
            date TEXT NOT NULL, reply_date TEXT
        );
        CREATE TABLE IF NOT EXISTS wrong_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            student_name TEXT DEFAULT '',
            image_path TEXT DEFAULT '',
            subject TEXT DEFAULT '数学',
            question TEXT DEFAULT '',
            explanation TEXT DEFAULT '',
            date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS points_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            points INTEGER NOT NULL,
            type TEXT NOT NULL DEFAULT 'earn',
            reason TEXT DEFAULT '',
            operator_id INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cost INTEGER NOT NULL DEFAULT 10,
            stock INTEGER DEFAULT -1,
            enabled BOOLEAN DEFAULT 1,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS redemptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reward_id INTEGER NOT NULL,
            reward_name TEXT DEFAULT '',
            cost INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL
        );
    ''')
    # 迁移：给已有用户补 plain_password 字段（默认 123456）
    c.execute("UPDATE users SET plain_password='123456' WHERE plain_password IS NULL OR plain_password=''")
    c.commit(); c.close()

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def gen_token():
    return secrets.token_hex(32)

def create_user(username, password, role='student', display_name=''):
    db = get_db()
    try:
        db.execute('INSERT INTO users (username,password_hash,role,display_name,created_at,plain_password) VALUES (?,?,?,?,?,?)',
                   (username, hash_pw(password), role, display_name, datetime.now().isoformat(), password))
        db.commit()
        return True
    except:
        return False
    finally:
        db.close()

def auth_user(username, password):
    db = get_db()
    u = db.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
    db.close()
    if u and u['password_hash'] == hash_pw(password):
        return dict(u)
    return None

def set_token(user_id, token):
    db = get_db()
    db.execute('UPDATE users SET token=? WHERE id=?', (token, user_id))
    db.commit()
    db.close()

def resolve_token(token):
    if not token: return None
    db = get_db()
    u = db.execute('SELECT id,username,role,display_name,blocked FROM users WHERE token=?', (token,)).fetchone()
    db.close()
    return dict(u) if u else None

def gen_pinyin(name):
    try:
        from pypinyin import lazy_pinyin
        return ''.join(lazy_pinyin(name))
    except ImportError:
        result = ''
        for ch in name:
            if '\u4e00' <= ch <= '\u9fff':
                result += 'x'
            else:
                result += ch.lower()
        return result

def auto_username(name):
    base = gen_pinyin(name)
    suffix = ''.join(random.choices(string.digits, k=4))
    username = base + suffix
    db = get_db()
    while db.execute('SELECT id FROM users WHERE username=?', (username,)).fetchone():
        suffix = ''.join(random.choices(string.digits, k=4))
        username = base + suffix
    db.close()
    return username
