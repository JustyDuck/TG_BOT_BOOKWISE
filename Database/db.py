from __future__ import annotations
from sqlalchemy.exc import OperationalError
from sqlalchemy import Column, Integer, String, ForeignKey, delete, update, Enum as SQLAlchemyEnum
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, selectinload
import enum
from config import *

path = "sqlite+aiosqlite:///Database/base.db"

Base = declarative_base()


class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.USER)
    books = relationship("UserBook", back_populates="user")


class Author(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True, autoincrement=True)
    author = Column(String, nullable=False)

    books = relationship("Book", back_populates="author")


class Genre(Base):
    __tablename__ = 'genres'
    id = Column(Integer, primary_key=True, autoincrement=True)
    genre = Column(String, nullable=False)

    books = relationship("Book", back_populates="genre")


class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey('authors.id'), nullable=False)
    genre_id = Column(Integer, ForeignKey('genres.id'), nullable=False)
    description = Column(String)
    pages = Column(Integer, nullable=False)
    pages_read = Column(Integer, nullable=False)

    author = relationship("Author", back_populates="books")
    genre = relationship("Genre", back_populates="books")
    user_books = relationship("UserBook", back_populates="book")


class UserBook(Base):
    __tablename__ = 'user_books'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)

    user = relationship("User", back_populates="books")
    book = relationship("Book")


async def check_db():
    engine = create_async_engine(path, echo=True)

    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.create_all)
        except OperationalError:
            print("Ошибка при создании таблиц. Возможно, база данных уже существует.")


async_engine = create_async_engine(path, echo=True)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)


async def get_user_exists(user_id: int, session: AsyncSession) -> bool:
    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalars().first()
    return user is not None


async def add_user(user_id: int, session: AsyncSession, admin_user_ids: List[int]):
    role = UserRole.ADMIN if user_id in admin_user_ids else UserRole.USER
    new_user = User(user_id=user_id, role=role)
    session.add(new_user)
    await session.commit()


async def get_user_books(user_id: int, session: AsyncSession):
    result = await session.execute(
        select(Book).options(selectinload(Book.author)).join(UserBook).where(UserBook.user_id == user_id))
    return result.scalars().all()


async def get_user_role(user_id: int, session: AsyncSession) -> UserRole:
    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalars().first()
    return user.role if user else UserRole.USER


async def add_book(name: str, author_id: int, genre_id: int, description: str, pages: int, pages_read: int,
                   session: AsyncSession):
    new_book = Book(name=name, author_id=author_id, genre_id=genre_id, description=description, pages=pages,
                    pages_read=pages_read)
    session.add(new_book)
    await session.commit()
    return new_book.id


async def add_genre(genre: str, session: AsyncSession) -> int:
    result = await session.execute(select(Genre).where(Genre.genre == genre))
    existing_genre = result.scalars().first()

    if existing_genre:
        return existing_genre.id
    else:
        new_genre = Genre(genre=genre)
        session.add(new_genre)
        await session.commit()
        return new_genre.id


async def add_author(author: str, session: AsyncSession) -> str:
    result = await session.execute(select(Author).where(Author.author == author))
    existing_author = result.scalars().first()

    if existing_author:
        return existing_author.id
    else:
        new_author = Author(author=author)
        session.add(new_author)
        await session.commit()
        return new_author.id


async def get_book_by_id(book_id: int, session: AsyncSession) -> Book | None:
    result = await session.execute(select(Book).options(selectinload(Book.author),
                                                        selectinload(Book.genre)).where(Book.id == book_id))
    return result.scalar_one_or_none()


async def get_genre_by_id(genre_id: int, session: AsyncSession) -> Genre | None:
    result = await session.execute(select(Genre).where(Genre.id == genre_id))
    return result.scalar_one_or_none()


async def get_author_by_id(author_id: int, session: AsyncSession) -> Author | None:
    result = await session.execute(select(Author).where(Author.id == author_id))
    return result.scalar_one_or_none()


async def delete_book(book_id: int, session: AsyncSession):
    await session.execute(delete(Book).where(Book.id == book_id))
    await session.commit()


async def delete_genre(genre_id: int, session: AsyncSession):
    await session.execute(delete(Genre).where(Genre.id == genre_id))
    await session.commit()


async def delete_author(author_id: int, session: AsyncSession):
    await session.execute(delete(Author).where(Author.id == author_id))
    await session.commit()


async def update_read_page(book_id: int, read_page: int, session: AsyncSession):
    stmt = update(Book).where(Book.id == book_id).values(pages_read=read_page)
    await session.execute(stmt)
    await session.commit()


async def update_name_genre(genre_id: int, genre: str, session: AsyncSession):
    stmt = update(Genre).where(Genre.id == genre_id).values(genre=genre)
    await session.execute(stmt)
    await session.commit()


async def update_name_author(author_id: int, author: str, session: AsyncSession):
    stmt = update(Author).where(Author.id == author_id).values(author=author)
    await session.execute(stmt)
    await session.commit()


async def change_user_role_directly(user_id: int, new_role: UserRole):
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if user:
            user.role = new_role
            await session.commit()
            print(f"Роль пользователя с ID {user_id} изменена на {new_role}.")
        else:
            print(f"Пользователь с ID {user_id} не найден.")
