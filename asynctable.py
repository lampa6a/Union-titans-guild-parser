import aiohttp
import aiofiles
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from database import get_guild_id, get_token

async def create_session():
    guild_id = await get_guild_id()
    token = await get_token()
    return token, guild_id
    
async def get_header():
    data = await get_statistic()
    if data is None:
        return 'Неизвестная гильдия', 'Неизвестно', 'Неизвестно'
    guild_name = data.get('data', {}).get('name', 'Неизвестная гильдия')
    global_rank = data.get('data', {}).get('rank_fortune_global', 'Неизвестно')
    country_rank = data.get('data', {}).get('rank_fortune_country', 'Неизвестно')
    return guild_name, global_rank, country_rank
    
async def get_statistic():
    async with aiohttp.ClientSession() as session:
        token, guild_id = await create_session()
        url = f"https://union-titans.fr/api/guild/current/{guild_id}/json"
        headers = {"Authorization": f"Bearer {token}"}
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                try:
                    data = await response.json()
                    if 'data' not in data:
                        return None
                    return data
                except ValueError:
                    return None
            else:
                return None


async def get_last_updated():
    last_updated_file = 'last_updated.txt'
    try:
        async with aiofiles.open(last_updated_file, 'r', encoding='utf-8') as f:
            return await f.read()  # Читаем дату последнего запроса
    except FileNotFoundError:
        return None

async def save_last_updated(date_str):
    async with aiofiles.open('last_updated.txt', 'w', encoding='utf-8') as f:
        await f.write(date_str)  # Сохраняем текущую дату в файл
        
async def extract_table_data():
    data = await get_statistic()
    if data is None:
        return [], [], [], "", "", ""

    members = data.get('data', {}).get('members', [])
    if not members:
        return [], [], [], "", "", ""

    nicknames = [member['playerName'] for member in members]
    current_bounties = [int(member['bounty']) for member in members]

    base_filename = "baseline.json"

    if not os.path.exists(base_filename):
        first_updated_at = datetime.now().strftime('%d %B %Y, %H:%M:%S')
        async with aiofiles.open(base_filename, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(dict(zip(nicknames, current_bounties)), ensure_ascii=False, indent=2))
        previous_bounties = [0 for _ in nicknames]
    else:
        async with aiofiles.open(base_filename, 'r', encoding='utf-8') as f:
            previous_data = json.loads(await f.read())
        previous_bounties = [previous_data.get(nick, 0) for nick in nicknames]
        first_updated_at = await get_last_updated() or datetime.now().strftime('%d %B %Y, %H:%M:%S')

    async with aiofiles.open(base_filename, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(dict(zip(nicknames, current_bounties)), ensure_ascii=False, indent=2))

    last_updated_at = datetime.now().strftime('%d %B %Y, %H:%M:%S')
    await save_last_updated(last_updated_at)

    diffs = [cur - prev for cur, prev in zip(current_bounties, previous_bounties)]

    return nicknames, previous_bounties, current_bounties, diffs, first_updated_at, last_updated_at

async def create_table(file_name) -> None:
    nicknames, previous, current, diffs, first_updated_at, last_updated_at = await extract_table_data()
    if not nicknames:
        return None

    # Создаем DataFrame
    df = pd.DataFrame({
        'Никнеймы': nicknames,
        f'Старое ({first_updated_at})': previous,
        f'Новое ({last_updated_at})': current,
        'Разница': diffs
    })

    # Создаем изображение с помощью matplotlib
    fig, ax = plt.subplots(figsize=(10, len(df) * 0.2))  # Размер таблицы зависит от количества строк
    ax.axis('tight')
    ax.axis('off')

    # Отображаем таблицу с улучшенным стилем
    table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center', colColours=["#6fa3ef"]*len(df.columns), cellColours=[['#e8f1ff']*len(df.columns)]*len(df)) 

    # Настройка шрифта и цвета для таблицы
    for (i, j), cell in table.get_celld().items():
        if i == 0:
            cell.set_fontsize(14)
            cell.set_text_props(weight='bold', color='white')  # Белый текст для заголовков
            cell.set_facecolor('#4c75c6')  # Синий цвет для заголовков
        else:
            cell.set_fontsize(12)
            cell.set_text_props(weight='normal', color='black')  # Черный текст для данных
            if j == 3:  # Для колонки "Разница" используем выделение положительных/отрицательных значений
                if df.iloc[i-1, j] > 0:
                    cell.set_facecolor('#d9ffcc')  # Зеленый для положительных
                elif df.iloc[i-1, j] < 0:
                    cell.set_facecolor('#ffcccc')  # Красный для отрицательных
                else:
                    cell.set_facecolor('#ffffff')  # Белый для 0
            else:
                cell.set_facecolor('#ffffff')  # Белый для других данных

    # Убираем лишние поля
    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

    # Сохраняем изображение без белых полей
    plt.savefig(f"images/{file_name}.png", bbox_inches="tight", dpi=300, pad_inches=0.1)
    print(f"Таблица успешно создана и сохранена в images/{file_name}.png")

async def main_table(file_name):
    await create_table(file_name)