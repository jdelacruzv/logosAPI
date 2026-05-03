import sqlite3

DATABASE_NAME = "bibles.sqlite"


def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # Para poder acceder por nombre de columna
    return conn


def get_book_id(book_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Buscamos el ID sin importar mayúsculas/minúsculas
    cursor.execute(
        "SELECT book_id FROM book_names WHERE LOWER(name) = LOWER(?)", (book_name,))
    result = cursor.fetchone()
    conn.close()
    return result['book_id'] if result else None
