import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from datetime import datetime

from asynctable import get_header, main_table
from database import update_guild_id, update_token, create_db, insert_initial_data

TOKEN = "6918113998:AAGONq-xqSqvsvjjVK-Ils2Iylx8J1LrURw"
ADMIN_IDS = [1223634387]

dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await create_db()
    await insert_initial_data()
    guild_name, global_rank, country_rank = await get_header()
    await message.answer(
        f"Здравствуй, это гильдия <b>{guild_name}</b>\n"
        f"Наш глобальный ранг: <b>{global_rank}</b>\n"
        f"Рейтинг по стране: <b>{country_rank}</b>"
    )

@dp.message(Command("table"))
async def table_handler(message: Message) -> None:
    file_name = f"{datetime.now().date()}"
    await message.answer("Ваша таблица генерируется, подождите немного...")
    await main_table(file_name)
    await asyncio.sleep(3)
    
    photo = FSInputFile(f"images/{file_name}.png")
    try:
        await message.answer_photo(photo=photo, caption="Ваша таблица готова")
    except Exception as e:
        await message.answer(f"Произошла ошибка при отправке таблицы")
    
@dp.message(Command("update_token"))
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

@dp.message(Command("update_guild_id"))
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

        
@dp.message(Command("append_admin"))
async def append_admin(message: Message):
    if len(message.text.split(" ")) == 2:
        admin_id = int(message.text.split(" ")[1])
        ADMIN_IDS.append(admin_id)
        await message.answer(f"{admin_id} теперь администратор ему открыты следующие уровни доступа:\n "
                             "Смена guild_id: https://union-titans.fr/en/guilds/ [оно находится здесь]\n "
                             "Команда /update_guild_id [новый guild_id]\n"
                             "Так же доступна смена api_token для полноценной работы бота, по команде /update_token <token>"
                             "Найти токен можно по ссылке: https://union-titans.fr/en/guides/api")
    else:
        await message.answer('Что-то пошло не так')


@dp.message(Command("startsheduler"))
async def start_sheduler(message: Message, count = 0, stop_func = 100):
    splitted = message.text.split(" ")
    delay = 60*60*24*7
    if len(splitted) == 2:
        print(count)
        if count == 0:
            print('work1')
            if splitted[1] == "stop":
                stop_func = 0
                return
            if len(splitted) == 2:
                if splitted[1] == "hour":
                    delay = 60*60
                    print('work2')
                elif splitted[1] == "day":
                    delay = 60*60*24
                    print('work3')
                elif splitted[1] == "week":
                    delay = 60*60*24*7
                    print('work4')
    
    await message.answer(f'Планировщик запущен на {delay//(60*60)} час(а)')
    if stop_func == 0:
        return
    else:
        file_name = f"{datetime.now().date()}"
        photo = FSInputFile(f'images/{file_name}.png')
        await asyncio.sleep(delay)
        await main_table(file_name)
        await asyncio.sleep(3)
        count += 1
        await message.answer_photo(photo=photo, caption=f'Ваша таблица на {file_name}')
        if stop_func == 0:
            await start_sheduler(message, count, stop_func)
        else:
            await start_sheduler(message, count)
            

async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
