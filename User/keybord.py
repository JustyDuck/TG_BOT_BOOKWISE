from __future__ import annotations
from sqlite3 import Row
from typing import Iterable
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram import types
import Database.db as db


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
            types.InlineKeyboardButton(text="Отмена", callback_data="close")
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
    ]
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    return keyboard


async def show_books_keyboard(books: Iterable[Row] | None, callback_data: str, page: int = 0) -> InlineKeyboardMarkup:
    buttons = []
    if books:
        page_items, has_next_page = get_page_from_list(books, page)
        for book in page_items:
            buttons.append([types.InlineKeyboardButton(text=f"{book[1]} - {book[2]}", callback_data=f"open_book:{book[0]}")])
        navigation_buttons_ = get_navigation_buttons(page, has_next_page, callback_data)
        buttons.append(navigation_buttons_)
    else:
        buttons.append([types.InlineKeyboardButton(text="Книг не найдено", callback_data="nothing")])
    buttons.append([types.InlineKeyboardButton(text="Отмена", callback_data="close")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


async def edit_book_keyboard(book_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            types.InlineKeyboardButton(text="Изменить данные", callback_data=f"change page: {book_id}"),
            types.InlineKeyboardButton(text="Удалить книгу", callback_data=f"delete_book:{book_id}"),
        ],
        [
            types.InlineKeyboardButton(text="Отмена", callback_data="close")
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


async def genres_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    genres = await db.get_all_genres()
    for genre in genres:
        buttons.append([types.InlineKeyboardButton(text=f"{genre[1]}", callback_data=f"choose_genre:{genre[0]}")])
    buttons.append([types.InlineKeyboardButton(text="Добавить жанр", callback_data="add_genre")])
    buttons.append([types.InlineKeyboardButton(text="Отмена", callback_data="cancel")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


async def authors_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    authors = await db.get_all_authors()
    for author in authors:
        buttons.append([types.InlineKeyboardButton(text=f"{author[1]}", callback_data=f"choose_author:{author[0]}")])
    buttons.append([types.InlineKeyboardButton(text="Добавить автора", callback_data="add_author")])
    buttons.append([types.InlineKeyboardButton(text="Отмена", callback_data="cancel")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
