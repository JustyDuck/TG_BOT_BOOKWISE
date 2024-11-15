from __future__ import annotations
from sqlite3 import Row
from typing import Iterable, Any
import aiosqlite
from os import system

path = "Database/base.db"


async def check_db():
    system("cls")
    async with aiosqlite.connect(path) as db:
        cursor = await db.cursor()
        try:
            await cursor.execute("SELECT * FROM users")
        except aiosqlite.OperationalError:
            await cursor.execute("""CREATE TABLE "users" (
"user_id"	INTEGER 
)""")
            await cursor.execute("""CREATE TABLE "authors" (
"id"	INTEGER UNIQUE,
"author"	TEXT NOT NULL,
PRIMARY KEY("id" AUTOINCREMENT)
)""")
            await cursor.execute("""CREATE TABLE "genres" (
"id"	INTEGER UNIQUE,
"genre"	TEXT NOT NULL,
PRIMARY KEY("id" AUTOINCREMENT)
)""")
            await cursor.execute("""CREATE TABLE "books" (
"id"	INTEGER UNIQUE,
"name"	TEXT NOT NULL,
"author_id"	INTEGER NOT NULL,
"genre_id"	INTEGER NOT NULL,
"description"	TEXT,
"pages"	INTEGER NOT NULL,
"pages_read"	INTEGER NOT NULL,
FOREIGN KEY("genre_id") REFERENCES "genres"("id"),
FOREIGN KEY("author_id") REFERENCES "authors"("id"),
PRIMARY KEY("id" AUTOINCREMENT)
)""")
            await db.commit()


async def get_user_exists(user_id) -> bool:
    async with aiosqlite.connect(path) as db:
        cursor = await db.cursor()
        await cursor.execute(f"SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = await cursor.fetchone()
        if user is None:
            return False
        else:
            return True


async def add_user(user_id):
    async with aiosqlite.connect(path) as db:
        cursor = await db.cursor()
        await cursor.execute(f"INSERT INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()


async def add_genre(genre: str) -> str | Any:
    async with aiosqlite.connect(path) as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT * FROM genres WHERE genre = ?", (genre,))
        existing_genre = await cursor.fetchone()
        if existing_genre:
            return existing_genre[0]
        else:
            await cursor.execute("INSERT INTO genres (genre) VALUES (?)", (genre,))
            await db.commit()
            await cursor.execute("SELECT * FROM genres WHERE genre = ?", (genre,))
            genre = await cursor.fetchone()
            return genre[0]


async def add_author(author: str) -> str | Any:
    async with aiosqlite.connect(path) as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT * FROM authors WHERE author = ?", (author,))
        existing_autor = await cursor.fetchone()
        if existing_autor:
            return existing_autor[0]
        else:
            await cursor.execute("INSERT INTO authors (author) VALUES (?)", (author,))
            await db.commit()
            await cursor.execute("SELECT * FROM authors WHERE author = ?", (author,))
            author = await cursor.fetchone()
            return author[0]


async def delete_book(book_id: int):
    async with aiosqlite.connect(path) as db:
        cursor = await db.cursor()
        await cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        await db.commit()


async def add_book(name: str, author_id: int, genre_id: int, description: str, pages: int, pages_read: int):
    async with aiosqlite.connect(path) as db:
        cursor = await db.cursor()
        await cursor.execute("INSERT INTO books (name, author_id, genre_id, description, pages, pages_read) "
                             "VALUES (?, ?, ?, ?, ?, ?)",
                             (name, author_id, genre_id, description, pages, pages_read))
        await db.commit()


async def update_read_page(book_id: int, read_page: int):
    async with aiosqlite.connect(path) as db:
        cursor = await db.cursor()
        await cursor.execute("UPDATE books SET pages_read = ? WHERE id = ?",
                             (read_page, book_id))
        await db.commit()


async def get_all_books() -> Iterable[Row] | None:
    async with aiosqlite.connect(path) as db:
        cursor = await db.cursor()
        await cursor.execute("""SELECT books.id, books.name, authors.author, genres.genre, books.description, books.pages
FROM ((books
INNER JOIN authors ON books.author_id = authors.id)
INNER JOIN genres ON books.genre_id = genres.id)
""")
        books = await cursor.fetchall()
        return books


async def get_all_genres() -> Iterable[Row] | None:
    async with aiosqlite.connect(path) as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT * FROM genres")
        genres = await cursor.fetchall()
        return genres


async def get_all_authors() -> Iterable[Row] | None:
    async with aiosqlite.connect(path) as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT * FROM authors")
        authors = await cursor.fetchall()
        return authors


async def get_book_by_id(book_id: int) -> Row | None:
    async with aiosqlite.connect(path) as db:
        cursor = await db.cursor()
        await cursor.execute("""SELECT books.id, books.name, authors.author, genres.genre, 
        books.description, books.pages, books.pages_read
FROM ((books
INNER JOIN authors ON books.author_id = authors.id)
INNER JOIN genres ON books.genre_id = genres.id)
WHERE books.id = ?
""", (book_id,))
        book = await cursor.fetchone()
        return book


async def get_genre_by_id(genre_id: int) -> Row | None:
    async with aiosqlite.connect(path) as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT * FROM genres WHERE id = ?", (genre_id,))
        genre = await cursor.fetchone()
        return genre


async def get_author_by_id(author_id: int) -> Row | None:
    async with aiosqlite.connect(path) as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT * FROM authors WHERE id = ?", (author_id,))
        author = await cursor.fetchone()
        return author
