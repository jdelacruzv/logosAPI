from pydantic import BaseModel
from typing import List


class Verse(BaseModel):
    book: str
    chapter: int
    verse: int
    text: str


class VersionInfo(BaseModel):
    table_name: str
    full_name: str
    language: str


class ComparisonVerse(BaseModel):
    version_id: str
    version_name: str
    text: str


class ComparisonResponse(BaseModel):
    book: str
    chapter: int
    verse: int
    comparisons: List[ComparisonVerse]


class ChapterResponse(BaseModel):
    version: str
    book: str
    chapter: int
    total_verses: int
    verses: List[Verse]  # Reutilizamos el modelo Verse que ya tienes


class ChapterStructure(BaseModel):
    chapter: int
    total_verses: int


class BookStructureResponse(BaseModel):
    version: str
    book: str
    chapters_count: int
    structure: List[ChapterStructure]


class BookSuggestion(BaseModel):
    book_id: int
    name: str
    language: str
