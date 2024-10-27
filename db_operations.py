import sqlite3
import os
from flask import Flask, g


def get_db():
    if 'db' not in g:
        app = Flask(__name__)
        db_path = os.path.join(app.instance_path, 'bizza.db')
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row  # 辞書形式でデータを取得できるように
    return g.db


def init_db():
    db = get_db()
    cursor = db.cursor()

    # テーブル作成
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(55) UNIQUE,
        name VARCHAR(55),
        email VARCHAR(100) UNIQUE
    )
    ''')

    db.commit()


def load_sample_data():
    db = get_db()
    cursor = db.cursor()

    data = [
        ('leanne', 'Leanne Graham', 'Sincere@april.biz'),
        ('ervin', 'Ervin Howell', 'Shanna@melissa.tv'),
        ('clementine', 'Clementine Bauch', 'Nathan@yesenia.net'),
        ('patricia', 'Patricia Lebsack', 'Julianne.OConner@kory.org'),
    ]

    cursor.executemany(
        'INSERT OR REPLACE INTO users (username, name, email) VALUES (?, ?, ?)',
        data
    )

    db.commit()


def get_all_users():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users')
    return cursor.fetchall()


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
