from aiogram import Router
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
    from config import config
    async with db.AsyncSessionLocal() as session:
        admin_user_ids = config.get_admin_user_ids()
        user_id = message.from_user.id
        if not await db.get_user_exists(message.from_user.id, session):
            await db.add_user(message.from_user.id, session, admin_user_ids)
        if user_id in admin_user_ids:
            await change_user_role_directly(user_id, UserRole.ADMIN)
        await message.answer(f"Привет, {message.from_user.first_name}, добро пожаловать в бота!",
                             reply_markup=await main_keyboard())


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


@router.message(F.text == "Все книги")
async def all_books(message: Message):
    async with db.AsyncSessionLocal() as session:
        await message.delete()

        await message.answer(
            "Все книги, которые вы добавили в библиотеку:",
            reply_markup=await show_books_keyboard(session, page=0, user_id=message.from_user.id,
                                                   callback_data="all_books"))


@router.callback_query(F.data.startswith("all_books"))
async def all_books_callback(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:
        _, page = call.data.split(":")
        page = int(page)
        await call.message.edit_reply_markup(
            reply_markup=await show_books_keyboard(session, page, call.from_user.id, "all_books"))


@router.callback_query(F.data.startswith("open_book"))
async def open_book(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:
        book_id = int(call.data.split(":")[1])
        book = await db.get_book_by_id(book_id, session)

        if book:
            await call.answer()
            author = book.author.author if book.author else "None"
            genre = book.genre.genre if book.genre else "None"
            await call.message.answer(
                f"Полная информация о книге\n\n"
                f"Название: {book.name}\n"
                f"Автор: {author}\n"
                f"Жанр: {genre}\n"
                f"Страниц: {book.pages}\n"
                f"Описание: {book.description}\n"
                f"Прочитано страниц: {book.pages_read}/{book.pages}",
                reply_markup=await edit_book_keyboard(book.id)
            )
        else:
            await call.answer("Книга не найдена")


@router.callback_query(F.data.startswith("delete_book"))
async def delete_book(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:
        book_id = int(call.data.split(":")[1])
        try:
            await session.execute(delete(UserBook).where(UserBook.book_id == book_id))
            await session.execute(delete(Book).where(Book.id == book_id))
            await session.commit()
            await call.answer("Книга удалена")
            await call.message.delete()

        except Exception:
            await call.answer("Ошибка, книгу не удалось удалить")


@router.callback_query(F.data.startswith("change_page"))
async def change_page_callback(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите количество прочитанных страниц:",
                              reply_markup=await cancel_keyboard())
    book_id = int(call.data.split(":")[1])
    await call.answer()
    await state.update_data(book_id=book_id)
    await state.set_state(UserStates.update_read_page)


@router.message(F.text, UserStates.update_read_page)
async def update_read_page(message: Message, state: FSMContext):
    async with db.AsyncSessionLocal() as session:

        data = await state.get_data()
        book_id = data.get("book_id")
        book = await db.get_book_by_id(book_id, session)
        try:
            read_page = int(message.text)
            if not (read_page < 0 or read_page > book.pages):
                await db.update_read_page(book_id, read_page, session)
                await message.answer(f"Количество прочитанных страниц для книги обновлено на {read_page}.")
                await state.clear()
            else:
                await message.answer("Ошибка: введите корректное количество прочитанных страниц.")
        except ValueError:
            await message.answer("Ошибка: введите корректное количество прочитанных страниц.")


@router.message(F.text == "Добавить книгу")
async def add_book(message: Message, state: FSMContext):
    await message.delete()
    m = await message.answer("Добавление книги\n\nВведите название книги",
                             reply_markup=await cancel_keyboard())
    await state.set_state(UserStates.set_book_name)
    await state.update_data(m_id=m.message_id)


@router.message(F.text, UserStates.set_book_name)
async def set_book_name(message: Message, state: FSMContext):
    async with db.AsyncSessionLocal() as session:
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
                                            reply_markup=await genres_keyboard(session, page=0))


@router.callback_query(F.data.startswith("choose_genre"))
async def choose_genre(call: CallbackQuery, state: FSMContext):
    async with db.AsyncSessionLocal() as session:
        try:
            genre_id = int(call.data.split(":")[1])
            genre = await db.get_genre_by_id(genre_id, session)
            data = await state.get_data()
            m_id = data["m_id"]
            book_name = data["book_name"]
            await state.update_data(genre_name=genre.genre, genre_id=genre.id)
            await call.message.bot.edit_message_text(chat_id=call.message.chat.id, message_id=m_id,
                                                     text=f"Добавление книги\n\nНазвание: {book_name}"
                                                          f"\nЖанр: {genre.genre}\n\nВыберите автора",
                                                     reply_markup=await authors_keyboard(session, page=0))
        except Exception:
            await call.answer("Ошибка выбора жанра")
            await call.message.delete()


@router.callback_query(F.data.startswith("genres_page"))
async def genres_page_callback(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:
        _, page = call.data.split(":")
        page = int(page)
        await call.message.edit_reply_markup(reply_markup=await genres_keyboard(session, page=page))


@router.callback_query(F.data.startswith("choose_author"))
async def choose_author(call: CallbackQuery, state: FSMContext):
    async with db.AsyncSessionLocal() as session:
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


@router.callback_query(F.data.startswith("authors_page"))
async def authors_page_callback(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:
        _, page = call.data.split(":")
        page = int(page)
        await call.message.edit_reply_markup(reply_markup=await authors_keyboard(session, page=page))


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
    async with db.AsyncSessionLocal() as session:
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
            new_book_id = await db.add_book(book_name, author_id, genre_id, book_description, pages, read_pages,
                                            session)
            user_id = message.from_user.id
            user_book = UserBook(user_id=user_id, book_id=new_book_id)
            session.add(user_book)
            await session.commit()
            await message.answer(f"Книга {book_name} успешно добавлена в библиотеку!")
        except Exception:
            await message.answer("Ошибка, попробуйте еще раз")
        await state.clear()


@router.message(F.text == "Все авторы")
async def all_author(message: Message):
    async with db.AsyncSessionLocal() as session:
        await message.delete()
        user_id = message.from_user.id
        user_role = await get_user_role(user_id, session)

        admin_status = user_role == UserRole.ADMIN

        await message.answer("Все имеющиеся авторы",
                             reply_markup=await show_author_keyboard(session, page=0,
                                                                     callback_data="all_author", is_admin=admin_status))


@router.callback_query(F.data.startswith("all_author"))
async def all_genre_callback(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:
        user_id = call.from_user.id
        user_role = await get_user_role(user_id, session)

        admin_status = user_role == UserRole.ADMIN
        _, page = call.data.split(":")
        page = int(page)
        await call.message.edit_reply_markup(reply_markup=await show_author_keyboard(session, page,
                                                                                     "all_author",
                                                                                     is_admin=admin_status))


@router.callback_query(F.data.startswith("open_author"))
async def open_author(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:
        author_id = int(call.data.split(":")[1])
        author = await db.get_author_by_id(author_id, session)
        user_id = call.from_user.id
        user_role = await get_user_role(user_id, session)
        admin_status = user_role == UserRole.ADMIN
        if author:
            await call.answer()
            await call.message.answer(
                f"Автор: {author.author}",
                reply_markup=await edit_autor_keyboard(author_id, is_admin=admin_status))
        else:
            await call.answer("Автор не найден")


@router.callback_query(F.data == "add_author")
async def add_author(call: CallbackQuery, state: FSMContext):
    await call.answer()
    try:
        await call.message.edit_text("Введите автора:", reply_markup=await cancel_keyboard())
        await state.set_state(UserStates.set_author_name)
    except Exception:
        await call.message.delete()


@router.message(F.text, UserStates.set_author_name)
async def set_author_name(message: Message, state: FSMContext):
    async with db.AsyncSessionLocal() as session:
        author_name = message.text
        try:
            await message.delete()
            await db.add_author(author_name, session)
            await message.answer(f"Автор '{author_name}' добавлен.")
        except Exception:
            await message.answer("Произошла ошибка при добавлении автора.")
        finally:
            await state.clear()


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

    await state.update_data(author_id=author_id)
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


@router.message(F.text == "Все жанры")
async def all_genre(message: Message):
    async with db.AsyncSessionLocal() as session:
        await message.delete()
        user_id = message.from_user.id
        user_role = await get_user_role(user_id, session)

        admin_status = user_role == UserRole.ADMIN

        await message.answer("Все имеющиеся жанры",
                             reply_markup=await show_genre_keyboard(session, page=0,
                                                                    callback_data="all_genre", is_admin=admin_status))


@router.callback_query(F.data.startswith("all_genre"))
async def all_genre_callback(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:
        user_id = call.from_user.id
        user_role = await get_user_role(user_id, session)

        admin_status = user_role == UserRole.ADMIN
        _, page = call.data.split(":")
        page = int(page)
        await call.message.edit_reply_markup(reply_markup=await show_genre_keyboard(session, page,
                                                                                    "all_genre",
                                                                                    is_admin=admin_status))


@router.callback_query(F.data.startswith("open_genre"))
async def open_genre(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:
        genre_id = int(call.data.split(":")[1])
        genre = await db.get_genre_by_id(genre_id, session)
        user_id = call.from_user.id
        user_role = await get_user_role(user_id, session)
        admin_status = user_role == UserRole.ADMIN
        if genre:
            await call.answer()
            await call.message.answer(
                f"Жанр: {genre.genre}",
                reply_markup=await edit_genre_keyboard(genre_id, is_admin=admin_status))
        else:
            await call.answer("Жанр не найден")


@router.callback_query(F.data == "add_genre")
async def add_genre(call: CallbackQuery, state: FSMContext):
    await call.answer()
    try:
        await call.message.edit_text("Введите название жанра:", reply_markup=await cancel_keyboard())
        await state.set_state(UserStates.set_genre_name)
    except:
        await call.message.delete()


@router.message(F.text, UserStates.set_genre_name)
async def set_genre_name(message: Message, state: FSMContext):
    async with db.AsyncSessionLocal() as session:
        genre_name = message.text
        try:
            await message.delete()
            await db.add_genre(genre_name, session)
            await message.answer(f"Жанр '{genre_name}' добавлен.")
        except Exception:
            pass
        finally:
            await state.clear()


@router.callback_query(F.data.startswith("delete_genre"))
async def delete_genre(call: CallbackQuery):
    async with db.AsyncSessionLocal() as session:
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


@router.message(Command("promote"))
async def promote(message: Message):
    async with db.AsyncSessionLocal() as session:
        is_admin = await get_user_role(message.from_user.id, session) == UserRole.ADMIN

        if is_admin:
            user_id_to_promote = message.text.split()[1] if len(message.text.split()) > 1 else None

            if user_id_to_promote and user_id_to_promote.isdigit():
                user_id_to_promote = int(user_id_to_promote)
                if await db.get_user_exists(user_id_to_promote, session):
                    await change_user_role_directly(user_id_to_promote, UserRole.ADMIN)
                    await message.answer(f"Пользователь с ID {user_id_to_promote} повышен до администратора.")
                else:
                    await message.answer(f"Пользователь с ID {user_id_to_promote} не найден в базе данных.")
            else:
                await message.answer("Пожалуйста, укажите корректный ID пользователя.")
        else:
            await message.answer("У вас нет прав для выполнения этой команды.")


@router.message(Command("demote"))
async def demote(message: Message):
    async with db.AsyncSessionLocal() as session:
        is_admin = await get_user_role(message.from_user.id, session) == UserRole.ADMIN

        if is_admin:
            user_id_to_demote = message.text.split()[1] if len(message.text.split()) > 1 else None

            if user_id_to_demote and user_id_to_demote.isdigit():
                user_id_to_demote = int(user_id_to_demote)
                if await db.get_user_exists(user_id_to_demote, session):
                    await change_user_role_directly(user_id_to_demote, UserRole.USER)
                    await message.answer(f"Пользователь с ID {user_id_to_demote} понижен до обычного пользователя.")
                else:
                    await message.answer(f"Пользователь с ID {user_id_to_demote} не найден в базе данных.")
            else:
                await message.answer("Пожалуйста, укажите корректный ID пользователя.")
        else:
            await message.answer("У вас нет прав для выполнения этой команды.")
