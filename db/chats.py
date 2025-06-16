from .connection import get_pool

async def upsert_chat(chat_id: int, title: str, type_: str) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "REPLACE INTO chats (id, title, type, added_at) VALUES (%s, %s, %s, NOW())",
                (chat_id, title, type_)
            )

async def delete_chat(chat_id: int) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM chats WHERE id = %s", (chat_id,))

async def get_all_chats() -> list[int]:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id FROM chats")
            rows = await cur.fetchall()
            return [row[0] for row in rows]
