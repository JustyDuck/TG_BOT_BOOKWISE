from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from Database import db
from User.keybord import *

router = Router()

async_engine = create_async_engine(path, echo=True)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)


class UserStates(StatesGroup):
    set_book_name = State()
    set_genre_name = State()
    set_author_name = State()
    set_book_description = State()
    set_book_pages = State()
    set_pages_read = State()
    update_read_page = State()
    update_genre = State()
    update_author = State()


@router.message(Command("start"))
async def start(message: Message):
    async with db.AsyncSessionLocal() as session:  # создаем сессию
        if not await db.get_user_exists(message.from_user.id, session):
            await db.add_user(message.from_user.id, session)
        await message.answer(f"Привет, {message.from_user.first_name}, добро пожаловать в бота!",
                             reply_markup=await main_keyboard())


@router.message(F.text == "Все книги")
async def all_books(message: Message):
    async with db.AsyncSessionLocal() as session:  # создаем сессию
        await message.delete()

        # Получаем все книги
        await message.answer(
            "Все книги, которые доступны в библиотеке",
            reply_markup=await show_books_keyboard(session, page=0, callback_data="all_books")  # Передаем session
        )


@router.callback_query(F.data.startswith("all_books"))
async def all_books_callback(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:  # создаем сессию
        await call.message.edit_reply_markup(reply_markup=await show_books_keyboard(session, 0, "all_books"))


@router.callback_query(F.data.startswith("open_book"))
async def open_book(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:  # создаем асинхронную сессию
        book_id = int(call.data.split(":")[1])

        # Убедитесь, что вы используете await
        book = await db.get_book_by_id(book_id, session)

        if book:
            await call.answer()
            await call.message.answer(
                f"Полная информация о книге\n\n"
                f"Название: {book.name}\n"
                f"Автор: {book.author.author}\n"
                f"Жанр: {book.genre.genre}\n"
                f"Страниц: {book.pages}\n"
                f"Описание: {book.description}\n"
                f"Прочитано страниц: {book.pages_read}/{book.pages}",
                reply_markup=await edit_book_keyboard(book.id)  # Убедитесь, что это асинхронный вызов
            )
        else:
            await call.answer("Книга не найдена")


@router.callback_query(F.data.startswith("delete_book"))
async def delete_book(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:  # создаем асинхронную сессию
        book_id = int(call.data.split(":")[1])
        try:
            await db.delete_book(book_id, session)
            await call.answer("Книга удалена")
            await call.message.delete()
        except:
            await call.answer("Ошибка, книгу не удалось удалить")


@router.callback_query(F.data.startswith("change_page"))
async def change_page_callback(call: CallbackQuery, state: FSMContext):
    book_id = int(call.data.split(":")[1])

    await call.answer()
    await call.message.answer("Введите количество прочитанных страниц:")

    await state.update_data(book_id=book_id)
    await state.set_state(UserStates.update_read_page)


@router.message(F.text, UserStates.update_read_page)
async def set_read_page(message: Message, state: FSMContext):
    async with db.AsyncSessionLocal() as session:  # создаем асинхронную сессию
        data = await state.get_data()
        book_id = data.get("book_id")
        try:
            read_page = int(message.text)
            await db.update_read_page(book_id, read_page, session)
            await message.answer(f"Количество прочитанных страниц для книги обновлено на {read_page}.")
            await state.clear()
        except ValueError:
            await message.answer("Ошибка: введите корректное количество прочитанных страниц.")
            await message.delete()


@router.message(F.text == "Добавить книгу")
async def add_book(message: Message, state: FSMContext):
    await message.delete()
    m = await message.answer("Добавление книги\n\nВведите название книги",
                             reply_markup=await cancel_keyboard())
    await state.set_state(UserStates.set_book_name)
    await state.update_data(m_id=m.message_id)


@router.message(F.text, UserStates.set_book_name)
async def set_book_name(message: Message, state: FSMContext):
    async with db.AsyncSessionLocal() as session:  # создаем сессию
        book_name = message.text
        data = await state.get_data()
        m_id = data["m_id"]
        await state.update_data(book_name=book_name)
        try:
            await message.delete()
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

        await message.bot.edit_message_text(chat_id=message.chat.id, message_id=m_id,
                                            text=f"Добавление книги\n\nНазвание: {book_name}\n\nВыберите жанр книги",
                                            reply_markup=await genres_keyboard(session))


@router.callback_query(F.data == "add_genre")
async def add_genre(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    try:
        m_id = data["m_id"]
        book_name = data["book_name"]
        await call.bot.edit_message_text(chat_id=call.message.chat.id, message_id=m_id,
                                         text=f"Добавление книги\n\nНазвание: {book_name}\n\nВведите название жанра",
                                         reply_markup=None)
        await state.set_state(UserStates.set_genre_name)
    except:
        await call.message.delete()


@router.message(F.text, UserStates.set_genre_name)
async def set_genre_name(message: Message, state: FSMContext):
    async with db.AsyncSessionLocal() as session:  # создаем сессию
        genre_name = message.text
        try:
            await message.delete()
        except Exception:
            pass
        genre_id = await db.add_genre(genre_name, session)
        data = await state.get_data()
        m_id = data["m_id"]
        book_name = data["book_name"]
        await state.update_data(genre_name=genre_name, genre_id=genre_id)
        await message.bot.edit_message_text(chat_id=message.chat.id, message_id=m_id,
                                            text=f"Добавление книги\n\nНазвание: {book_name}\nЖанр: {genre_name}\n\nВыберите автора книги",
                                            reply_markup=await authors_keyboard(session))


@router.callback_query(F.data.startswith("choose_genre"))
async def choose_genre(call: CallbackQuery, state: FSMContext):
    async with db.AsyncSessionLocal() as session:  # создаем сессию
        try:
            genre_id = int(call.data.split(":")[1])
            genre = await db.get_genre_by_id(genre_id, session)
            data = await state.get_data()
            m_id = data["m_id"]
            book_name = data["book_name"]
            await state.update_data(genre_name=genre.genre, genre_id=genre.id)
            await call.message.bot.edit_message_text(chat_id=call.message.chat.id, message_id=m_id,
                                                     text=f"Добавление книги\n\nНазвание: {book_name}"
                                                          f"\nЖанр: {genre.genre}\n\nВведите количество страниц",
                                                     reply_markup=await authors_keyboard(session))
        except Exception:
            await call.answer("Ошибка выбора жанра")
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
                                         text=f"Добавление книги\n\nНазвание: {book_name}\nЖанр: {genre_name}"
                                              f"\n\nВведите имя автора",
                                         reply_markup=None)
        await state.set_state(UserStates.set_author_name)
    except Exception:
        await call.message.delete()


@router.message(F.text, UserStates.set_author_name)
async def set_author_name(message: Message, state: FSMContext):
    async with db.AsyncSessionLocal() as session:  # создаем сессию
        author_name = message.text
        try:
            await message.delete()
        except Exception:
            pass
        author_id = await db.add_author(author_name, session)
        data = await state.get_data()
        m_id = data["m_id"]
        book_name = data["book_name"]
        genre_name = data["genre_name"]
        await state.update_data(author_name=author_name, author_id=author_id)
        await message.bot.edit_message_text(chat_id=message.chat.id, message_id=m_id,
                                            text=f"Добавление книги\n\nНазвание: {book_name}\nЖанр: {genre_name}"
                                                 f"\nАвтор: {author_name}\n\nВведите количество страниц",
                                            reply_markup=await cancel_keyboard())
        await state.set_state(UserStates.set_book_pages)


@router.callback_query(F.data.startswith("choose_author"))
async def choose_author(call: CallbackQuery, state: FSMContext):
    async with db.AsyncSessionLocal() as session:  # создаем сессию
        try:
            author_id = int(call.data.split(":")[1])
            author = await db.get_author_by_id(author_id, session)
            data = await state.get_data()
            m_id = data["m_id"]
            book_name = data["book_name"]
            genre_name = data["genre_name"]
            await state.update_data(author_name=author.author, author_id=author.id)
            await call.message.bot.edit_message_text(chat_id=call.message.chat.id, message_id=m_id,
                                                     text=f"Добавление книги\n\nНазвание: {book_name}"
                                                          f"\nЖанр: {genre_name}\nАвтор: {author.author}"
                                                          f"\n\nВведите количество страниц",
                                                     reply_markup=await cancel_keyboard())
            await state.set_state(UserStates.set_book_pages)
        except Exception:
            await call.answer("Ошибка, попробуйте еще раз")
            await call.message.delete()


@router.message(F.text, UserStates.set_book_pages)
async def set_book_pages(message: Message, state: FSMContext):
    try:
        pages = int(message.text)
        if pages <= 0:
            await message.answer("Ошибка: количество страниц должно быть положительным.")
            return
        data = await state.get_data()
        book_name = data["book_name"]
        author_name = data["author_name"]
        genre_name = data["genre_name"]
        m_id = data["m_id"]

        await state.update_data(pages=pages)
        await message.bot.edit_message_text(chat_id=message.chat.id, message_id=m_id,
                                            text=f"Добавление книги\n\nНазвание: {book_name}\nЖанр: {genre_name}\n"
                                                 f"Автор: {author_name} \nКоличество страниц: {pages} "
                                                 f"\n\nВведите количество прочитанных страниц",
                                            reply_markup=await cancel_keyboard())
        await state.set_state(UserStates.set_pages_read)
        await message.delete()
    except:
        await message.answer("Ошибка: введите корректное количество страниц.")
        await message.delete()


@router.message(F.text, UserStates.set_pages_read)
async def set_read_page(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        pages = data["pages"]
        read_pages = int(message.text)
        if read_pages < 0:
            await message.answer("Ошибка: количество прочитанных страниц не может быть отрицательным.")
            return
        book_name = data["book_name"]
        author_name = data["author_name"]
        genre_name = data["genre_name"]
        m_id = data["m_id"]
        await state.update_data(read_pages=read_pages)
        await message.bot.edit_message_text(chat_id=message.chat.id, message_id=m_id,
                                            text=f"Добавление книги\n\nНазвание: {book_name}\nЖанр: {genre_name}\n"
                                                 f"Автор: {author_name}\nКоличество страниц: {pages}\n "
                                                 f"Количество прочитанных страниц: {read_pages} "
                                                 f"\n\nВведите описание книги",
                                            reply_markup=await cancel_keyboard())
        await state.set_state(UserStates.set_book_description)
        await message.delete()
    except ValueError:
        await message.answer("Ошибка: введите корректное количество прочитанных страниц.")
        await message.delete()


@router.message(F.text, UserStates.set_book_description)
async def set_book_description(message: Message, state: FSMContext):
    async with db.AsyncSessionLocal() as session:  # создаем сессию
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
            except Exception:
                pass
            await db.add_book(book_name, author_id, genre_id, book_description, pages, read_pages, session)
            await message.answer(f"Книга {book_name} успешно добавлена в библиотеку!")
        except Exception:
            await message.answer("Ошибка, попробуйте еще раз")
        await state.clear()


@router.message(F.text == "Все жанры")
async def all_genre(message: Message):
    async with db.AsyncSessionLocal() as session:  # создаем сессию
        await message.delete()

        await message.answer("Все имеющиеся жанры",
                             reply_markup=await show_genre_keyboard(session, page=0, callback_data="all_genre"))


@router.callback_query(F.data.startswith("all_genre"))
async def all_genre_callback(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:  # создаем сессию
        await call.message.edit_reply_markup(reply_markup=await show_genre_keyboard(session, 0, "all_genre"))


@router.callback_query(F.data.startswith("open_genre"))
async def open_genre(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:  # создаем сессию
        genre_id = int(call.data.split(":")[1])

        genre = await db.get_genre_by_id(genre_id, session)
        if genre:
            await call.answer()
            await call.message.answer(
                f"Жанр: {genre.genre}",
                reply_markup=await edit_genre_keyboard(genre_id))
        else:
            await call.answer("Жанр не найден")


@router.callback_query(F.data.startswith("delete_genre"))
async def delete_genre(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:  # создаем сессию
        genre_id = int(call.data.split(":")[1])
        try:
            await db.delete_genre(genre_id, session)
            await call.answer("Жанр удален")
            await call.message.delete()
        except Exception:
            await call.answer("Ошибка, жанр не удалось удалить")


@router.callback_query(F.data.startswith("change_genre"))
async def change_genre_callback(call: CallbackQuery, state: FSMContext):
    genre_id = int(call.data.split(":")[1])
    await call.answer()
    await call.message.answer("Введите корректное название жанра:")

    await state.update_data(genre_id=genre_id)
    await state.set_state(UserStates.update_genre)


@router.message(F.text, UserStates.update_genre)
async def update_genre(message: Message, state: FSMContext):
    async with db.AsyncSessionLocal() as session:  # создаем сессию
        data = await state.get_data()
        genre_id = data.get("genre_id")
        try:
            genre = message.text
            await db.update_name_genre(genre_id, genre, session)
            await message.answer(f"Название жанра обновлено на {genre}.")
            await state.clear()
        except Exception:
            await message.answer("Ошибка")
            await message.delete()


@router.message(F.text == "Все авторы")
async def all_author(message: Message):
    async with db.AsyncSessionLocal() as session:
        await message.delete()

        await message.answer("Все имеющиеся авторы",
                             reply_markup=await show_autor_keyboard(session, page=0, callback_data="all_author"))


@router.callback_query(F.data.startswith("all_author"))
async def all_genre_callback(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:
        await call.message.edit_reply_markup(reply_markup=await show_autor_keyboard(session, 0, "all_author"))


@router.callback_query(F.data.startswith("open_author"))
async def open_author(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:
        author_id = int(call.data.split(":")[1])

        author = await db.get_author_by_id(author_id, session)
        if author:
            await call.answer()
            await call.message.answer(
                f"Автор: {author.author}",
                reply_markup=await edit_genre_keyboard(author_id))
        else:
            await call.answer("Автор не найден")


@router.callback_query(F.data.startswith("delete_author"))
async def delete_author(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:
        author_id = int(call.data.split(":")[1])
        try:
            await db.delete_author(author_id, session)
            await call.answer("Автор удален")
            await call.message.delete()
        except Exception:
            await call.answer("Ошибка, автора не удалось удалить")


@router.callback_query(F.data.startswith("change_author"))
async def change_author_callback(call: CallbackQuery, state: FSMContext):
    author_id = int(call.data.split(":")[1])
    await call.answer()
    await call.message.answer("Введите корректное имя автора:")

    await state.update_data(author_if=author_id)
    await state.set_state(UserStates.update_author)


@router.message(F.text, UserStates.update_author)
async def update_genre(message: Message, state: FSMContext):
    async with db.AsyncSessionLocal() as session:
        data = await state.get_data()
        author_id = data.get("author_id")
        try:
            author = message.text
            await db.update_name_author(author_id, author, session)
            await message.answer(f"Имя автора обновлено на {author}.")
            await state.clear()
        except Exception:
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
    except Exception:
        pass
