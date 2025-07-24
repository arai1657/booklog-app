# init_db.py
import sqlite3

connection = sqlite3.connect('books.db')
cursor = connection.cursor()

# 本棚用のbooksテーブル (全データ対応版)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        google_books_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        authors TEXT,
        publisher TEXT,
        published_date TEXT,
        description TEXT,
        page_count INTEGER,
        categories TEXT,
        average_rating REAL,
        ratings_count INTEGER,
        thumbnail TEXT,
        preview_link TEXT,
        isbn TEXT,
        memo TEXT,
        status INTEGER DEFAULT 0
    )
''')

# 読みたい本リスト用のwishlistテーブルも同様に更新
cursor.execute('''
    CREATE TABLE IF NOT EXISTS wishlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        google_books_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        authors TEXT,
        publisher TEXT,
        published_date TEXT,
        description TEXT,
        page_count INTEGER,
        categories TEXT,
        average_rating REAL,
        ratings_count INTEGER,
        thumbnail TEXT,
        preview_link TEXT,
        isbn TEXT
    )
''')

connection.commit()
connection.close()
print("データベースの準備が完了しました。")