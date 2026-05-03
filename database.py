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


def get_books_by_version(version: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Obtenemos los nombres únicos de los libros en orden de aparición
        cursor.execute(f"SELECT DISTINCT book FROM {version} ORDER BY id ASC")
        books = [row['book'] for row in cursor.fetchall()]
        return books
    finally:
        conn.close()


def get_allowed_versions():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Obtenemos los nombres de todas las tablas excepto las de sistema y metadatos
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('sqlite_sequence', 'versions', 'book_names');")
    tables = [row['name'] for row in cursor.fetchall()]
    conn.close()
    return tables
	

def search_in_version(version: str, query: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Limpiamos espacios y pasamos a minúsculas en Python
    clean_query = query.strip()
    search_param = f"%{clean_query}%"

    try:
        # 2. Usamos el operador LIKE normal.
        # Por defecto en SQLite, LIKE es case-insensitive para la A-Z.
        query_sql = f"""
            SELECT book, chapter, verse, text 
            FROM {version} 
            WHERE text LIKE ?
            LIMIT 100
        """

        # 3. Si quieres que sea REALMENTE potente, forzamos la búsqueda
        # buscando tanto la versión con mayúscula como en minúscula
        # (Aunque LIKE suele bastar)
        cursor.execute(query_sql, (search_param,))

        results = cursor.fetchall()
        return [dict(row) for row in results]

    except Exception as e:
        print(f"Error en búsqueda: {e}")
        return []
    finally:
        conn.close()
