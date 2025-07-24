# app.py 
import sqlite3
import requests
from config import API_KEY
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# --- ヘルパー関数: APIから詳細データを取得 ---
def get_book_details_from_api(google_books_id):
    url = f"https://www.googleapis.com/books/v1/volumes/{google_books_id}"
    params = {'key': API_KEY}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None
    
    data = response.json()
    volume_info = data.get('volumeInfo', {})
    
    # ISBNを抽出
    isbn_13, isbn_10 = None, None
    for identifier in volume_info.get('industryIdentifiers', []):
        if identifier['type'] == 'ISBN_13':
            isbn_13 = identifier['identifier']
        elif identifier['type'] == 'ISBN_10':
            isbn_10 = identifier['identifier']
    
    return {
        'google_books_id': data.get('id'),
        'title': volume_info.get('title', 'タイトル不明'),
        'authors': ', '.join(volume_info.get('authors', ['著者不明'])),
        'publisher': volume_info.get('publisher', '不明'),
        'published_date': volume_info.get('publishedDate', '不明'),
        'description': volume_info.get('description', '概要はありません。'),
        'page_count': volume_info.get('pageCount'),
        'categories': ', '.join(volume_info.get('categories', [])),
        'average_rating': volume_info.get('averageRating'),
        'ratings_count': volume_info.get('ratingsCount'),
        'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail', ''),
        'preview_link': volume_info.get('previewLink'),
        'isbn': isbn_13 or isbn_10 or '不明'
    }

# --- ルート定義 ---
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/search', methods=['GET', 'POST'])
def search_page():
    search_results = []
    if request.method == 'POST':
        keyword = request.form['keyword']
        url = "https://www.googleapis.com/books/v1/volumes"
        params = {'q': keyword, 'key': API_KEY, 'maxResults': 15}
        response = requests.get(url, params=params)
        response_data = response.json()

        if 'items' in response_data:
            for item in response_data.get('items', []):
                volume_info = item.get('volumeInfo', {})
                search_results.append({
                    'google_books_id': item.get('id'),
                    'title': volume_info.get('title', 'タイトル不明'),
                    'authors': ', '.join(volume_info.get('authors', ['著者不明'])),
                    'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail', '')
                })
    return render_template('search.html', search_results=search_results)

@app.route('/book_detail/<google_books_id>')
def book_detail(google_books_id):
    conn = sqlite3.connect('books.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # まずDBから探す
    cursor.execute("SELECT * FROM books WHERE google_books_id = ?", (google_books_id,))
    book_in_db = cursor.fetchone()

    cursor.execute("SELECT * FROM wishlist WHERE google_books_id = ?", (google_books_id,))
    book_in_wishlist = cursor.fetchone()
    
    conn.close()

    if book_in_db:
        # DBにあればそれを表示
        book = book_in_db
        is_in_bookshelf = True
        is_in_wishlist = False
    elif book_in_wishlist:
        book = book_in_wishlist
        is_in_bookshelf = False
        is_in_wishlist = True
    else:
        # なければAPIで取得
        book = get_book_details_from_api(google_books_id)
        if not book: return "書籍が見つかりませんでした", 404
        is_in_bookshelf = False
        is_in_wishlist = False

    return render_template('book_detail.html', book=book, is_in_bookshelf=is_in_bookshelf, is_in_wishlist=is_in_wishlist)

# --- DB操作 ---
@app.route('/add_book', methods=['POST'])
def add_book():
    google_books_id = request.form['google_books_id']
    book_details = get_book_details_from_api(google_books_id)

    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM wishlist WHERE google_books_id = ?", (google_books_id,)) # Wishlistからは削除
    cursor.execute(
        """INSERT OR IGNORE INTO books (google_books_id, title, authors, publisher, published_date, description, page_count, categories, average_rating, ratings_count, thumbnail, preview_link, isbn)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (book_details['google_books_id'], book_details['title'], book_details['authors'], book_details['publisher'], book_details['published_date'], book_details['description'], book_details['page_count'], book_details['categories'], book_details['average_rating'], book_details['ratings_count'], book_details['thumbnail'], book_details['preview_link'], book_details['isbn'])
    )
    conn.commit()
    conn.close()
    return redirect(url_for('book_detail', google_books_id=google_books_id))

@app.route('/add_to_wishlist', methods=['POST'])
def add_to_wishlist():
    google_books_id = request.form['google_books_id']
    book_details = get_book_details_from_api(google_books_id)

    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()
    cursor.execute(
        """INSERT OR IGNORE INTO wishlist (google_books_id, title, authors, publisher, published_date, description, page_count, categories, average_rating, ratings_count, thumbnail, preview_link, isbn)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (book_details['google_books_id'], book_details['title'], book_details['authors'], book_details['publisher'], book_details['published_date'], book_details['description'], book_details['page_count'], book_details['categories'], book_details['average_rating'], book_details['ratings_count'], book_details['thumbnail'], book_details['preview_link'], book_details['isbn'])
    )
    conn.commit()
    conn.close()
    return redirect(url_for('book_detail', google_books_id=google_books_id))

# 本棚ページとWishlistページのルートは簡略化
@app.route('/bookshelf')
def bookshelf_page():
    conn = sqlite3.connect('books.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books ORDER BY id DESC")
    books = cursor.fetchall()
    conn.close()
    return render_template('bookshelf.html', books=books)

@app.route('/wishlist')
def wishlist_page():
    conn = sqlite3.connect('books.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM wishlist ORDER BY id DESC")
    books = cursor.fetchall()
    conn.close()
    return render_template('wishlist.html', books=books)

# 削除、メモ、ステータス変更のルートも更新
@app.route('/delete_book', methods=['POST'])
def delete_book():
    google_books_id = request.form['google_books_id']
    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE google_books_id = ?", (google_books_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('bookshelf_page'))

@app.route('/edit_memo/<google_books_id>', methods=['POST'])
def edit_memo(google_books_id):
    new_memo = request.form['memo']
    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE books SET memo = ? WHERE google_books_id = ?", (new_memo, google_books_id))
    conn.commit()
    conn.close()
    return redirect(url_for('book_detail', google_books_id=google_books_id))

@app.route('/toggle_status/<google_books_id>', methods=['POST'])
def toggle_status(google_books_id):
    conn = sqlite3.connect('books.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM books WHERE google_books_id = ?", (google_books_id,))
    book = cursor.fetchone()
    if book:
        new_status = 1 - book['status']
        cursor.execute("UPDATE books SET status = ? WHERE google_books_id = ?", (new_status, google_books_id))
        conn.commit()
    conn.close()
    return redirect(url_for('book_detail', google_books_id=google_books_id))

if __name__ == '__main__':
    app.run(debug=True)