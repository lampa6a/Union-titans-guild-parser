from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def get_inline_keyboard():
    kb = [[InlineKeyboardButton(text="Создать таблицу", callback_data="table"),
    InlineKeyboardButton(text="Запланированный запуск", callback_data="sheduler")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)  

    
    return keyboard

