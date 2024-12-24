from __future__ import annotations
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from Database.db import *


async def cancel_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            types.InlineKeyboardButton(text="Отмена", callback_data="cancel")
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


async def close_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            types.InlineKeyboardButton(text="Закрыть", callback_data="close")
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_navigation_buttons(page: int, has_next_page: bool, callback_data: str) -> list[types.InlineKeyboardButton]:
    navigation_buttons = []
    if page != 0 and has_next_page:
        navigation_buttons.append(
            types.InlineKeyboardButton(text="⬅️", callback_data=f"{callback_data}:{page - 1}"))
        navigation_buttons.append(
            types.InlineKeyboardButton(text="➡️", callback_data=f"{callback_data}:{page + 1}"))
    elif page != 0:
        navigation_buttons.append(
            types.InlineKeyboardButton(text="⬅️", callback_data=f"{callback_data}:{page - 1}"))
    elif has_next_page:
        navigation_buttons.append(
            types.InlineKeyboardButton(text="➡️", callback_data=f"{callback_data}:{page + 1}"))
    return navigation_buttons


def get_page_from_list(list_: list, page: int) -> tuple[list, bool]:
    items_per_page = 10
    start_index = page * items_per_page
    end_index = page * items_per_page + items_per_page
    page_items = list_[start_index:end_index]
    has_next_page = end_index < len(list_)
    return page_items, has_next_page


async def main_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [
            types.KeyboardButton(text="Все книги"),
            types.KeyboardButton(text="Добавить книгу"),
        ],
        [
            types.KeyboardButton(text="Все жанры"),
            types.KeyboardButton(text="Все авторы"),
        ],
    ]
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    return keyboard


async def edit_book_keyboard(book_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            types.InlineKeyboardButton(text="Изменить данные", callback_data=f"change_page: {book_id}"),
            types.InlineKeyboardButton(text="Удалить книгу", callback_data=f"delete_book:{book_id}"),
        ],
        [
            types.InlineKeyboardButton(text="Отмена", callback_data="close")
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


async def edit_genre_keyboard(genre_id: int, is_admin: bool = False) -> InlineKeyboardMarkup:

    buttons = []

    if is_admin:
        buttons.append([
            types.InlineKeyboardButton(text="Изменить данные", callback_data=f"change_genre:{genre_id}"),  # изменение
            types.InlineKeyboardButton(text="Удалить", callback_data=f"delete_genre:{genre_id}")  # удаление
        ])
    else:
        buttons.append([
            types.InlineKeyboardButton(text="У вас нет прав для изменения или удаления жанра", callback_data="no_permission")
        ])
    buttons.append([
        types.InlineKeyboardButton(text="Отмена", callback_data="close")
    ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


async def edit_autor_keyboard(author_id: int, is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    if is_admin:
        buttons.append([
            types.InlineKeyboardButton(text="Изменить данные", callback_data=f"change_author: {author_id}"), # изменение
            types.InlineKeyboardButton(text="Удалить", callback_data=f"delete_author: {author_id}")  # удаление
        ])
    else:
        buttons.append([
            types.InlineKeyboardButton(text="У вас нет прав для изменения или удаления жанра",
                                       callback_data="no_permission")
        ])

    buttons.append([
        types.InlineKeyboardButton(text="Отмена", callback_data="close")
    ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


async def show_books_keyboard(session: AsyncSession, page: int, user_id: int,
                              callback_data: str = "books") -> InlineKeyboardMarkup:
    buttons = []

    user_books = await get_user_books(user_id, session)
    if user_books:
        page_items, has_next_page = get_page_from_list(user_books, page)

        for book in page_items:
            author = book.author.author if book.author else "None"
            buttons.append(
                [types.InlineKeyboardButton(text=f"{book.name} - {author}",
                                            callback_data=f"open_book:{book.id}")]
            )
        navigation_buttons_ = get_navigation_buttons(page, has_next_page, callback_data)
        buttons.append(navigation_buttons_)
    else:
        buttons.append([types.InlineKeyboardButton(text="Книг не найдено", callback_data="nothing")])

    buttons.append([types.InlineKeyboardButton(text="Отмена", callback_data="close")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


async def show_genre_keyboard(session: AsyncSession, page: int = 0, callback_data: str = "genres",
                              is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = []

    result = await session.execute(select(Genre))
    genres = result.scalars().all()

    if genres:
        page_items, has_next_page = get_page_from_list(genres, page)
        for genre in page_items:
            buttons.append(
                [types.InlineKeyboardButton(text=f"{genre.genre}", callback_data=f"open_genre:{genre.id}")])

        navigation_buttons_ = get_navigation_buttons(page, has_next_page, callback_data)
        buttons.append(navigation_buttons_)
    else:
        buttons.append([types.InlineKeyboardButton(text="Жанр не найден", callback_data="nothing")])
    if is_admin:
        buttons.append([types.InlineKeyboardButton(text="Добавить жанр", callback_data="add_genre")])
    buttons.append([types.InlineKeyboardButton(text="Отмена", callback_data="close")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


async def show_author_keyboard(session: AsyncSession, page: int = 0, callback_data: str = "authors",
                               is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = []

    result = await session.execute(select(Author))
    authors = result.scalars().all()

    if authors:
        page_items, has_next_page = get_page_from_list(authors, page)
        for author in page_items:
            buttons.append(
                [types.InlineKeyboardButton(text=f"{author.author}", callback_data=f"open_author:{author.id}")])

        navigation_buttons_ = get_navigation_buttons(page, has_next_page, callback_data)
        buttons.append(navigation_buttons_)
    else:
        buttons.append([types.InlineKeyboardButton(text="Автор не найден", callback_data="nothing")])
    if is_admin:
        buttons.append([types.InlineKeyboardButton(text="Добавить автора", callback_data="add_author")])
    buttons.append([types.InlineKeyboardButton(text="Отмена", callback_data="close")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


async def genres_keyboard(session: AsyncSession, page: int = 0) -> InlineKeyboardMarkup:
    buttons = []

    result = await session.execute(select(Genre))
    genres = result.scalars().all()

    page_items, has_next_page = get_page_from_list(genres, page)
    for genre in page_items:
        buttons.append([types.InlineKeyboardButton(text=f"{genre.genre}", callback_data=f"choose_genre:{genre.id}")])

    navigation_buttons = get_navigation_buttons(page, has_next_page, "genres_page")
    if navigation_buttons:
        buttons.append(navigation_buttons)
    buttons.append([types.InlineKeyboardButton(text="Отмена", callback_data="cancel")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


async def authors_keyboard(session: AsyncSession, page: int = 0) -> InlineKeyboardMarkup:
    buttons = []

    result = await session.execute(select(Author))
    authors = result.scalars().all()

    page_items, has_next_page = get_page_from_list(authors, page)
    for author in page_items:
        buttons.append([types.InlineKeyboardButton(text=f"{author.author}", callback_data=f"choose_author:{author.id}")])

    navigation_buttons = get_navigation_buttons(page, has_next_page, "authors_page")
    if navigation_buttons:
        buttons.append(navigation_buttons)
    buttons.append([types.InlineKeyboardButton(text="Отмена", callback_data="cancel")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

