import aiosqlite
from config_reader import guild_config

DB_PATH = 'tokens.db'

guild_id, token = guild_config

async def create_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tokens (
                token TEXT NOT NULL,
                guild_id TEXT NOT NULL
            )
        ''')
        await db.commit()

async def insert_initial_data():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT COUNT(*) FROM tokens') as cursor:
            count = await cursor.fetchone()
            if count[0] == 0:
                await db.execute('''
                    INSERT INTO tokens (token, guild_id)
                    VALUES (?, ?)
                ''', (token, guild_id))
                await db.commit()

async def update_token(new_token: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE tokens
            SET token = ?
        ''', (new_token,))
        await db.commit()

async def update_guild_id(new_guild_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE tokens
            SET guild_id = ?
        ''', (new_guild_id,))
        await db.commit()

async def get_token() -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT token FROM tokens') as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def get_guild_id() -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT guild_id FROM tokens') as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None
