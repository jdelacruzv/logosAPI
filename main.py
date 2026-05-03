from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import get_books_by_version, get_db_connection, get_book_id, search_in_version, get_allowed_versions
from models import BookStructureResponse, BookSuggestion, ComparisonResponse, Verse, VersionInfo, ChapterResponse
from typing import List, Optional
from enum import Enum


class LanguageEnum(str, Enum):
    spanish = "Spanish"
    english = "English"


# Lista global que se llenará al arrancar
VALID_VERSIONS = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lógica de arranque (Startup)
    global VALID_VERSIONS
    VALID_VERSIONS = get_allowed_versions()
    print(f"🚀 LogosAPI (Lifespan) cargada con versiones: {VALID_VERSIONS}")
    yield  # Aquí es donde la app "vive" y atiende peticiones
    # # Lógica de cierre (Shutdown) si fuera necesaria
    print("🧹 Apagando LogosAPI...")


app = FastAPI(
    title="LogosAPI",
    description="Acceso a 24 versiones de la Biblia en múltiples idiomas",
    version="1.0.0",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite cualquier origen (incluyendo tu localhost)
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos los headers
)


# 0. Función para obtener conexión a la base de datos (reutilizada en varios endpoints)
@app.on_event("startup")
async def startup_event():
    global VALID_VERSIONS
    # Reutilizamos tu función existente
    VALID_VERSIONS = get_allowed_versions()
    print(f"🚀 LogosAPI cargada con versiones: {VALID_VERSIONS}")


# 1. Endpoint para comparar un versículo entre todas las versiones
@app.get("/compare/{book_name}/{chapter}/{verse}", response_model=ComparisonResponse, tags=["Verse comparison"])
async def compare_verse(book_name: str, chapter: int, verse: int):
    book_id = get_book_id(book_name)
    if not book_id:
        raise HTTPException(status_code=400, detail="Libro no reconocido")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Obtener todas las versiones registradas para saber dónde buscar
        cursor.execute("SELECT table_name, full_name FROM versions")
        versions = cursor.fetchall()

        comparison_list = []

        # 2. Iterar sobre cada versión y buscar el versículo
        for v in versions:
            table = v['table_name']
            name = v['full_name']

            # Buscamos el texto en la tabla correspondiente
            query = f"SELECT text FROM {table} WHERE book = ? AND chapter = ? AND verse = ?"
            cursor.execute(query, (book_name, chapter, verse))
            result = cursor.fetchone()

            if result:
                comparison_list.append({
                    "version_id": table,
                    "version_name": name,
                    "text": result['text']
                })

        if not comparison_list:
            raise HTTPException(
                status_code=404, detail="Versículo no encontrado en ninguna versión")

        return {
            "book": book_name,
            "chapter": chapter,
            "verse": verse,
            "comparisons": comparison_list
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error en la comparación: {str(e)}")
    finally:
        conn.close()


# 2. Endpoint para ver qué versiones hay disponibles
@app.get("/info/versions", response_model=List[VersionInfo], tags=["Version information"])
async def get_versions(lang: Optional[LanguageEnum] = None):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if lang:
            # Buscamos filtrando por idioma (ignorando mayúsculas/minúsculas)
            query = "SELECT table_name, full_name, language FROM versions WHERE LOWER(language) = LOWER(?)"
            cursor.execute(query, (lang,))
        else:
            # Si no hay filtro, devolvemos todas las 24 versiones
            cursor.execute(
                "SELECT table_name, full_name, language FROM versions")

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al obtener versiones: {str(e)}")
    finally:
        conn.close()


# 3. Endpoint para obtener un versículo específico
@app.get("/read/{version}/{book_name}/{chapter}/{verse}", response_model=Verse, tags=["Reading verse"])
async def get_specific_verse(version: str, book_name: str, chapter: int, verse: int):
    # 1. Obtener el book_id del libro (ej: "Juan" -> 43)
    book_id = get_book_id(book_name)
    if not book_id:
        raise HTTPException(status_code=404, detail="Libro no reconocido")

    conn = get_db_connection()
    cursor = conn.cursor()

    # 2. Buscamos en la tabla de la biblia usando el book_id en lugar del nombre del libro
    query = f"SELECT book, chapter, verse, text FROM {version.lower()} WHERE book_id = ? AND chapter = ? AND verse = ?"
    cursor.execute(query, (book_id, chapter, verse))
    result = cursor.fetchone()
    conn.close()

    if result:
        return dict(result)
    raise HTTPException(status_code=404, detail="Versículo no encontrado")


# 4. Endpoint para obtener un capítulo completo
@app.get("/read/{version}/{book_name}/{chapter}", response_model=ChapterResponse, tags=["Reading verse"])
async def get_full_chapter(version: str, book_name: str, chapter: int):
    # 1. Traducir nombre a ID
    book_id = get_book_id(book_name)
    if not book_id:
        raise HTTPException(status_code=404, detail="Libro no reconocido")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 2. Consultar todos los versículos del capítulo ordenados
        query = f"""
            SELECT book, chapter, verse, text 
            FROM {version.lower()} 
            WHERE book_id = ? AND chapter = ? 
            ORDER BY verse ASC
        """
        cursor.execute(query, (book_id, chapter))
        rows = cursor.fetchall()

        if not rows:
            raise HTTPException(
                status_code=404, detail="Capítulo no encontrado")

        # 3. Formatear la respuesta
        verses_list = [dict(row) for row in rows]

        return {
            "version": version,
            "book": book_name,
            "chapter": chapter,
            "total_verses": len(verses_list),
            "verses": verses_list
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al leer el capítulo: {str(e)}")
    finally:
        conn.close()


# 5. Endpoint para obtener la estructura de un libro (cuántos capítulos y versículos tiene cada capítulo)
@app.get("/info/structure/{version}/{book_name}", response_model=BookStructureResponse, tags=["Version information"])
async def get_book_structure(version: str, book_name: str):
    # 1. Traducir nombre a ID
    book_id = get_book_id(book_name)
    if not book_id:
        raise HTTPException(status_code=404, detail="Libro no reconocido")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 2. Agrupar por capítulo y contar versículos
        # Esta consulta es muy eficiente: nos dice qué capítulos existen y cuántos versos tienen
        query = f"""
            SELECT chapter, COUNT(verse) as total_verses 
            FROM {version.lower()} 
            WHERE book_id = ? 
            GROUP BY chapter
            ORDER BY chapter ASC
        """
        cursor.execute(query, (book_id,))
        rows = cursor.fetchall()

        if not rows:
            raise HTTPException(
                status_code=404, detail="Estructura no encontrada para esta versión")

        # 3. Formatear la respuesta
        structure = [dict(row) for row in rows]

        return {
            "version": version,
            "book": book_name,
            "chapters_count": len(structure),
            "structure": structure
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al obtener estructura: {str(e)}")
    finally:
        conn.close()


# 6. Endpoint para sugerir libros basados en una búsqueda parcial
@app.get("/info/books/suggest", response_model=List[BookSuggestion], tags=["Suggestions/Autocomplete"])
async def suggest_books(q: str):
    """
    Sugiere nombres de libros basados en una búsqueda parcial (mínimo 1 letra).
    Ejemplo: /info/books/suggest?q=Gen -> ["Génesis", "Genesis"]
    """
    if len(q) < 1:
        return []

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Buscamos nombres que empiecen con la letra 'q'
        # El LOWER(?) y el q.lower() aseguran que no importe si es Mayúscula o Minúscula
        query = """
            SELECT book_id, name, language 
            FROM book_names 
            WHERE LOWER(name) LIKE ? 
            ORDER BY name ASC 
            LIMIT 10
        """
        search_term = f"{q.lower()}%"
        cursor.execute(query, (search_term,))
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error en sugerencias: {str(e)}")
    finally:
        conn.close()


# 7. Endpoint para buscar una palabra o frase en una versión específica
@app.get("/search/{version}", tags=["Search"])
async def search(version: str, q: str):
	# Validamos que la versión exista en tu lista de tablas para evitar errores
    allowed_versions = get_allowed_versions()
    if version not in allowed_versions:
        return {
            "error": "Versión no válida",
            "mensaje": f"La versión '{version}' no existe. Intenta con una de estas: {', '.join(allowed_versions[:5])}..."
        }

    if len(q) < 3:
        return {"error": "La búsqueda debe tener al menos 3 caracteres"}

    results = search_in_version(version, q)

    if not results:
        return {"message": "No se encontraron resultados", "results": []}

    return {
        "version": version,
        "query": q,
        "total": len(results),
        "results": results
    }


# 8. Endpoint raíz para verificar que la API está funcionando
@app.get("/", tags=["Root"])
async def home():
    return {
        "message": "Bienvenido a LogosAPI",
        "version": "1.0.0",
        "docs": "/docs",
        "author": "jdelacruzv"
    }


# 9. Endpoint para listar los libros disponibles en una versión específica
@app.get("/info/{version}/books", tags=["Version information"])
async def read_books(version: str):
    v_lower = version.lower()

    # Validación dinámica
    if v_lower not in VALID_VERSIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Versión '{version}' no disponible. Opciones: {VALID_VERSIONS}"
        )

    books = get_books_by_version(v_lower)
    return {
        "version": v_lower,
        "total_books": len(books),
        "books": books
    }
