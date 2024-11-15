from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from User.keybord import *
import Database.db as db

router = Router()


class UserStates(StatesGroup):
    set_book_name = State()
    set_genre_name = State()
    set_author_name = State()
    set_book_description = State()
    set_book_pages = State()
    set_pages_read = State()
    update_read_page = State()


@router.message(Command("start"))
async def start(message: Message):
    if not await db.get_user_exists(message.from_user.id):
        await db.add_user(message.from_user.id)
    await message.answer(f"Привет, {message.from_user.first_name}, добро пожаловать в бота!",
                         reply_markup=await main_keyboard())


@router.message(F.text == "Все книги")
async def all_books(message: Message):
    await message.delete()
    books = await db.get_all_books()
    await message.answer("Все книги, которые доступны в библиотеке",
                         reply_markup=await show_books_keyboard(books, "all_books"))


@router.callback_query(F.data.startswith("all_books"))
async def all_books_callback(call: CallbackQuery):
    page = int(call.data.split(":")[1])
    books = await db.get_all_books()
    await call.message.edit_reply_markup(reply_markup=await show_books_keyboard(books, "all_books", page))


@router.callback_query(F.data.startswith("open_book"))
async def open_book(call: CallbackQuery):
    book_id = int(call.data.split(":")[1])
    book = await db.get_book_by_id(book_id)
    if book:
        await call.answer()
        await call.message.answer(
            f"Полная информация о книге\n\nНазвание:{book}",
            # f"\n Автор: {book[2]}\n Жанр: {book[3]}\n "
            # f"Страниц: {book [5]}\n Описание: {book[4]}\n Прочитанно страниц: {book[6]}/{book[5]}",
            reply_markup=await edit_book_keyboard(book_id))
    else:
        await call.answer("Книга не найдена")


@router.callback_query(F.data.startswith("delete_book"))
async def delete_book(call: CallbackQuery):
    book_id = int(call.data.split(":")[1])
    try:
        await db.delete_book(book_id)
        await call.answer("Книга удалена")
        await call.message.delete()
    except:
        await call.answer("Ошибка, книгу не удалось удалить")


@router.message(F.text == "Добавить книгу")
async def add_book(message: Message, state: FSMContext):
    await message.delete()
    m = await message.answer("Добавление книги\n\nВведите название книги",
                             reply_markup=await cancel_keyboard())
    await state.set_state(UserStates.set_book_name)
    await state.update_data(m_id=m.message_id)


@router.message(F.text, UserStates.set_book_name)
async def set_book_name(message: Message, state: FSMContext):
    book_name = message.text
    data = await state.get_data()
    m_id = data["m_id"]
    await state.update_data(book_name=book_name)
    try:
        await message.delete()
    except:
        pass
    await message.bot.edit_message_text(chat_id=message.chat.id, message_id=m_id,
                                        text=f"Добавление книги\n\nНазвание: {book_name}\n\nВыберите жанр книги",
                                        reply_markup=await genres_keyboard())


@router.callback_query(F.data == "add_genre")
async def add_genre(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    try:
        m_id = data["m_id"]
        book_name = data["book_name"]
        await call.bot.edit_message_text(chat_id=call.message.chat.id, message_id=m_id,
                                         text=f"Добавление книги\n\n<b>Название: {book_name}\n\nВведите название жанра",
                                         reply_markup=None)
        await state.set_state(UserStates.set_genre_name)
    except:
        await call.message.delete()


@router.message(F.text, UserStates.set_genre_name)
async def set_genre_name(message: Message, state: FSMContext):
    genre_name = message.text
    try:
        await message.delete()
    except:
        pass
    genre_id = await db.add_genre(genre_name)
    data = await state.get_data()
    m_id = data["m_id"]
    book_name = data["book_name"]
    await state.update_data(genre_name=genre_name, genre_id=genre_id)
    await message.bot.edit_message_text(chat_id=message.chat.id, message_id=m_id,
                                        text=f"Добавление книги\n\nНазвание: {book_name}\nЖанр: {genre_name}\n\nВыберите автора книги",
                                        reply_markup=await authors_keyboard())


@router.callback_query(F.data.startswith("choose_genre"))
async def choose_genre(call: CallbackQuery, state: FSMContext):
    try:
        genre_id = int(call.data.split(":")[1])
        genre = await db.get_genre_by_id(genre_id)
        data = await state.get_data()
        m_id = data["m_id"]
        book_name = data["book_name"]
        await state.update_data(genre_name=genre[1], genre_id=genre[0])
        await call.message.bot.edit_message_text(chat_id=call.message.chat.id, message_id=m_id,
                                                 text=f"Добавление книги\n\nНазвание: {book_name}\nЖанр: {genre[1]}\n\nВыберите автора книги",
                                                 reply_markup=await authors_keyboard())
    except:
        await call.answer("Ошибка, попробуйте еще раз")
        await call.message.delete()


@router.callback_query(F.data == "add_author")
async def add_author(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    try:
        m_id = data["m_id"]
        book_name = data["book_name"]
        genre_name = data["genre_name"]
        await call.bot.edit_message_text(chat_id=call.message.chat.id, message_id=m_id,
                                         text=f"Добавление книги\n\nНазвание: {book_name}\nЖанр:{genre_name}\n\nВведите имя автора",
                                         reply_markup=None)
        await state.set_state(UserStates.set_author_name)
    except:
        await call.message.delete()


@router.message(F.text, UserStates.set_author_name)
async def set_author_name(message: Message, state: FSMContext):
    author_name = message.text
    try:
        await message.delete()
    except:
        pass
    author_id = await db.add_author(author_name)
    data = await state.get_data()
    m_id = data["m_id"]
    book_name = data["book_name"]
    genre_name = data["genre_name"]
    await state.update_data(author_name=author_name, author_id=author_id)
    await message.bot.edit_message_text(chat_id=message.chat.id, message_id=m_id,
                                        text=f"Добавление книги\n\nНазвание:{book_name}\nЖанр:{genre_name}\nАвтор:{author_name}\n\nВведите оличество страниц",
                                        reply_markup=await cancel_keyboard())
    await state.set_state(UserStates.set_book_pages)


@router.callback_query(F.data.startswith("choose_author"))
async def choose_author(call: CallbackQuery, state: FSMContext):
    try:
        author_id = int(call.data.split(":")[1])
        author = await db.get_author_by_id(author_id)
        data = await state.get_data()
        m_id = data["m_id"]
        book_name = data["book_name"]
        genre_name = data["genre_name"]
        await state.update_data(author_name=author[1], author_id=author[0])
        await call.message.bot.edit_message_text(chat_id=call.message.chat.id, message_id=m_id,
                                                 text=f"Добавление книги\n\nНазвание:{book_name}\nЖанр:{genre_name}\nАвтор:{author[1]}\n\nВведите количество страниц",
                                                 reply_markup=await cancel_keyboard())
        await state.set_state(UserStates.set_book_pages)
    except:
        await call.answer("Ошибка, попробуйте еще раз")
        await call.message.delete()


@router.message(F.text, UserStates.set_book_pages)
async def set_book_pages(message: Message, state: FSMContext):
    try:
        pages = int(message.text)
        if pages <= 0:
            await message.answer("error")
            return
        data = await state.get_data()
        book_name = data["book_name"]
        author_name = data["author_name"]
        genre_name = data["genre_name"]
        m_id = data["m_id"]

        await state.update_data(pages=pages)
        await message.bot.edit_message_text(chat_id=message.chat.id, message_id=m_id,
                                        text=f"Добавление книги\n\nНазвание:{book_name}\nЖанр:{genre_name}\n"
                                             f"Автор:{author_name}\nКоличество страниц:{pages} "
                                             f"\n\nВведите описание",
                                        reply_markup=await cancel_keyboard())
        await state.set_state(UserStates.set_pages_read)
        await message.delete()
    except:
        await message.answer("error type pages")
        await message.delete()


@router.message(F.text, UserStates.set_pages_read)
async def set_book_pages(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        pages = data["pages"]
        read_pages = int(message.text)
        if read_pages < 0:
            await message.answer("error")
            return
        book_name = data["book_name"]
        author_name = data["author_name"]
        genre_name = data["genre_name"]
        m_id = data["m_id"]
        await state.update_data(read_pages=read_pages)
        await message.bot.edit_message_text(chat_id=message.chat.id, message_id=m_id,
                                        text=f"Добавление книги\n\nНазвание:{book_name}\nЖанр:{genre_name}\n"
                                             f"Автор:{author_name}\nКоличество страниц:{pages}\n "
                                             f"Количество прочяитанных страниц: {read_pages} "
                                             f"\n\nВведите описание книги",
                                        reply_markup=await cancel_keyboard())
        await state.set_state(UserStates.set_book_description)
        await message.delete()
    except:
        await message.answer("error type pages")
        await message.delete()


@router.message(F.text, UserStates.set_book_description)
async def set_book_description(message: Message, state: FSMContext):
    try:
        book_description = message.text
        data = await state.get_data()
        book_name = data["book_name"]
        author_id = data["author_id"]
        genre_id = data["genre_id"]
        pages = data["pages"]
        m_id = data["m_id"]
        read_pages = data["read_pages"]
        try:
            await message.delete()
            await message.bot.delete_message(chat_id=message.chat.id, message_id=m_id)
        except:
            pass
        await db.add_book(book_name, author_id, genre_id, book_description, pages, read_pages)
        await message.answer(f"Книга {book_name} успешно добавлена в библиотеку!")
        await state.clear()
    except:
        await message.answer("Ошибка, попробуйте еще раз")
        await state.clear()


@router.callback_query(F.data.startswith("change page"))
async def change_page_callback(call: CallbackQuery, state: FSMContext):
    book_id = int(call.data.split(":")[1])  # Получаем book_id

    await call.answer()
    await call.message.answer("Введите количество прочитанных страниц:")

    # Сохраняем book_id в состоянии пользователя, чтобы использовать его позже
    await state.update_data(book_id=book_id)
    await state.set_state(UserStates.update_read_page)


@router.message(F.text, UserStates.update_read_page)
async def set_read_page(message: Message, state: FSMContext):
    data = await state.get_data()
    book_id = data.get("book_id")
    try:
        read_page = int(message.text)
        await db.update_read_page(book_id, read_page)  # Обновляем значение в базе данных
        await message.answer(f"Количество прочитанных страниц для книги обновлено на {read_page}.")
        await state.clear()
    except :
        await message.answer("Ошибка")
        await message.delete()


@router.callback_query(F.data == "close")
async def close(call: CallbackQuery):
    await call.message.delete()


@router.callback_query(F.data == "cancel")
async def cancel(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    try:
        await call.message.delete()
    except:
        pass
