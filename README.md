# 🏛️ LogosAPI

**LogosAPI** es un potente motor de consulta bíblica desarrollado con **FastAPI** y **SQLite**. Permite acceder a 24 versiones de la Biblia en múltiples idiomas, por el momento en Español e Inglés a través de una interfaz REST rápida y eficiente.

---

## ✨ Características Principales

*   **Lectura Flexible:** Consulta versículos individuales o capítulos completos en una sola petición.
*   **Búsqueda Global:** Motor de búsqueda que permite encontrar palabras clave en todas las versiones simultáneamente.
*   **Comparación Paralela:** Compara un mismo versículo entre diferentes traducciones e idiomas.
*   **Mapeo Inteligente:** Soporte para nombres de libros en varios idiomas y abreviaturas gracias a una tabla de normalización.
*   **Sugerencias en Tiempo Real:** Endpoint de autocompletado para facilitar la búsqueda de libros.
*   **Alto Rendimiento:** Implementación de Git LFS para manejar bases de datos de gran tamaño (+120MB) y despliegue optimizado en la nube.

## 🛠️ Tecnologías Utilizadas

*   **Lenguaje:** Python 3.10+
*   **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
*   **Base de Datos:** SQLite (con optimización VACUUM)
*   **Gestión de Archivos:** Git LFS (Large File Storage)
*   **Servidor ASGI:** Uvicorn
*   **Despliegue:** Render

## 🚀 Instalación y Uso Local

### 1. Requisitos previos
Asegúrate de tener instalado **Git LFS** para descargar la base de datos correctamente:

### 2. Clonar y configurar
```bash
# 1. Clonar el repositorio
git clone https://github.com/jdelacruzv/logosAPI.git
cd logosAPI

# 2. Asegurar la descarga de la base de datos (LFS)
git lfs pull

# 3. Crear y activar entorno virtual
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Ejecutar la API
uvicorn main:app --reload
```

- **API local:** http://127.0.0.1:8000
- **Documentación interactiva (Swagger):** http://127.0.0.1:8000/docs

## 📌 Endpoints Principales

| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `GET` | `/read/{version}/{book}/{chapter}` | Obtiene un capítulo completo de una versión específica. |
| `GET` | `/read/{version}/{book}/{chapter}/{verse}` | Obtiene un solo versículo específico. |
| `GET` | `/search/{version}?q={query}` | Busca palabras o frases dentro de una versión específica. |
| `GET` | `/compare/{book}/{chapter}/{verse}` | Compara un mismo versículo en todas las biblias disponibles. |
| `GET` | `/info/versions` | Lista todas las versiones y códigos de biblias disponibles (24 versiones). |
| `GET` | `/info/structure/{version}/{book}` | Devuelve la cantidad de capítulos y versículos de un libro específico. |
| `GET` | `/info/books/suggest?q={query}` | Sugerencias de nombres de libros para autocompletado. |

## 🌍 Despliegue en Producción

Este proyecto está configurado para ejecutarse en Render. Gracias a la integración con Git LFS, la base de datos se descarga automáticamente durante el proceso de build.

Desarrollado con ❤️ para facilitar el estudio de las Escrituras.