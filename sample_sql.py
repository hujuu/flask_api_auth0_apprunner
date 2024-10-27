import sqlite3
import os
from flask import Flask

app = Flask(__name__)
db_path = os.path.join(app.instance_path, 'bizza.db')
# Make sure instance directory exists
os.makedirs(app.instance_path, exist_ok=True)


def load_data():
    data = [
        ('leanne', 'Leanne Graham', 'Sincere@april.biz'),
        ('ervin', 'Ervin Howell', 'Shanna@melissa.tv'),
        ('clementine', 'Clementine Bauch', 'Nathan@yesenia.net'),
        ('patricia', 'Patricia Lebsack', 'Julianne.OConner@kory.org'),
    ]

    print(f"Database path: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(55) UNIQUE,
            name VARCHAR(55),
            email VARCHAR(100) UNIQUE
        )
        ''')

        # Clear existing data
        cursor.execute('DELETE FROM users')

        # Insert new data
        cursor.executemany(
            'INSERT INTO users (username, name, email) VALUES (?, ?, ?)',
            data
        )

        # Commit the changes
        conn.commit()

        # Verify the data
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        print("\nInserted users:")
        for user in users:
            print(user)

    except Exception as e:
        print(f"Error: {str(e)}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    load_data()
