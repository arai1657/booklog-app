# update_db_v1.py
import sqlite3

conn = sqlite3.connect('books.db')
cursor = conn.cursor()

try:
    # booksテーブルにstatus列を追加 (0: 未読, 1: 読了)
    # 既存のデータはデフォルトで0（未読）に設定
    cursor.execute("ALTER TABLE books ADD COLUMN status INTEGER DEFAULT 0")
    print("データベースを更新しました: 'status'列が追加されました。")
except sqlite3.OperationalError as e:
    # すでに列が存在する場合のエラーを無視
    if "duplicate column name" in str(e):
        print("すでに'status'列は存在しているため、スキップしました。")
    else:
        raise e

conn.commit()
conn.close()