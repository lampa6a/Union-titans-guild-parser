import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, BaseFilter
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime
from typing import List, Union

from asynctable import get_header, main_table
from database import update_guild_id, update_token, create_db, insert_initial_data
from keyboards import get_inline_keyboard

TOKEN = "7037297011:AAF0j67AXCDyK1To_9ngN3h60G7B8TY6-4U"


ADMIN_IDS: List[str] = [1223634387]

dp = Dispatcher()

class AdminFilter(BaseFilter):
    async def __call__(self, update: Union[Message, CallbackQuery]) -> bool:
        return update.from_user.id in ADMIN_IDS

admin_filter = AdminFilter()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await create_db()
    await insert_initial_data() 
    guild_name, global_rank, country_rank = await get_header()
    await message.answer(
        f"Здравствуй, это гильдия <b>{guild_name}</b>\n"
        f"Наш глобальный ранг: <b>{global_rank}</b>\n"
        f"Рейтинг по стране: <b>{country_rank}</b>", reply_markup=await get_inline_keyboard()
    )

@dp.callback_query(F.data == "table")
async def table_handler(callback: CallbackQuery) -> None:
    file_name = f"{datetime.now().date()}"
    await callback.message.answer("Ваша таблица генерируется, подождите немного...")
    await main_table(file_name)
    await asyncio.sleep(3)
    
    photo = FSInputFile(f"images/{file_name}.png")
    await callback.message.answer_photo(photo=photo, caption="Ваша таблица готова")
    await callback.answer()
    
@dp.message(Command("update_token"), admin_filter)
async def update_token_handler(message: Message) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Пожалуйста, укажите новый токен после команды, например:\n/update_token ваш_токен")
        return
    new_token = parts[1].strip()
    try:
        await update_token(new_token)
        await message.answer('Токен успешно обновлен')
    except Exception as e:
        await message.answer(f'Произошла ошибка при обновлении токена: {str(e)}')

@dp.message(Command("update_guild_id"), admin_filter)
async def update_guild_handler(message: Message) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Пожалуйста, укажите новый ID гильдии после команды, например:\n/update_guild_id ваш_id")
        return
    new_guild_id = parts[1].strip()
    try:
        await update_guild_id(new_guild_id)
        await message.answer("ID гильдии успешно обновлен")
    except Exception as e:
        await message.answer(f"Произошла ошибка при обновлении ID гильдии: {str(e)}")


@dp.message(Command("addadmin"), admin_filter)
async def cmd_addadmin(message: Message):
    try:
        parts = message.text.split(" ")
    except TelegramBadRequest:
        await message.answer('Использование: /addadmin <user_id>')
        return
    if len(parts) != 2 or not parts[1].isdigit():
        return await message.reply("Использование: /addadmin <user_id>")
    
    new_admin_id = int(parts[1])
    ADMIN_IDS.append(new_admin_id)
    await message.answer(f"{new_admin_id} теперь администратор ему открыты следующие уровни доступа:\n "
                             "Смена guild_id: https://union-titans.fr/en/guilds/ [оно находится здесь]\n "
                             "Команда /update_guild_id [новый guild_id]\n"
                             "Так же доступна смена api_token для полноценной работы бота, по команде /update_token [token]"
                             "Найти токен можно по ссылке: https://union-titans.fr/en/guides/api")
    
@dp.message(Command("adminlist"), admin_filter)
async def admin_list_getter(message: Message):
    await message.answer(f"Список: {', '.join(list(map(str, ADMIN_IDS)))}")
        

@dp.callback_query(F.data == "sheduler", admin_filter)
async def start_scheduler(callback: CallbackQuery, count=0):
    # Интервал в секундах - 7 дней
    week_delay = 60 * 60 * 24 * 7

    now = datetime.now()
    weekday = now.weekday()  # Понедельник=0 ... Воскресенье=6

    # Если сегодня воскресенье (6)
    if weekday == 6:
        await callback.message.answer("Сегодня воскресенье! Отправляю таблицу и запускаю еженедельный планировщик.")
        file_name = f"{now.date()}"
        await main_table(file_name)
        photo = FSInputFile(f'images/{file_name}.png')
        await asyncio.sleep(3)
        await callback.message.answer_photo(photo=photo, caption=f"Ваша таблица на {file_name}")

        # Запускаем цикл с недельным интервалом
        while True:
            await asyncio.sleep(week_delay)
            file_name = f"{datetime.now().date()}"
            await main_table(file_name)
            photo = FSInputFile(f'images/{file_name}.png')
            await asyncio.sleep(3)
            await callback.message.answer_photo(photo=photo, caption=f"Ваша таблица на {file_name}")

    else:
        # Сегодня не воскресенье - считаем сколько осталось до ближайшего воскресенья
        days_until_sunday = (6 - weekday) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7  # Если сегодня воскресенье, но на всякий случай

        seconds_until_sunday = days_until_sunday * 24 * 60 * 60

        await callback.message.answer(
            f"Сегодня не воскресенье. Таблица будет отправлена в ближайшее воскресенье через {days_until_sunday} дн."
        )
        await callback.answer()

        # Ждем до ближайшего воскресенья
        await asyncio.sleep(seconds_until_sunday)

        # Отправляем таблицу в воскресенье
        file_name = f"{datetime.now().date()}"
        await main_table(file_name)
        photo = FSInputFile(f'images/{file_name}.png')
        await asyncio.sleep(3)
        await callback.message.answer_photo(photo=photo, caption=f"Ваша таблица на {file_name}")

        # Запускаем цикл с недельным интервалом
        await callback.answer()
        while True:
            await asyncio.sleep(week_delay)
            file_name = f"{datetime.now().date()}"
            await main_table(file_name)
            photo = FSInputFile(f'images/{file_name}.png')
            await asyncio.sleep(3)
            await callback.message.answer_photo(photo=photo, caption=f"Ваша таблица на {file_name}")

@dp.message(F.text)
async def error_message(message: Message):
    await message.answer("Я вас не понял, возможно вы допустили ошибку")

async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
