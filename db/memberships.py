from .connection import get_pool

async def add_user_to_chat(user_id: int, chat_id: int, username: str | None, full_name: str | None) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT IGNORE INTO user_memberships (user_id, chat_id, username, full_name, joined_at) VALUES (%s, %s, %s, %s, NOW())",
                (user_id, chat_id, username, full_name)
            )

async def remove_user_from_chat(user_id: int, chat_id: int) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM user_memberships WHERE user_id = %s AND chat_id = %s", (user_id, chat_id))

async def clear_user_memberships(user_id: int) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM user_memberships WHERE user_id = %s", (user_id,))

async def get_user_membership_count(user_id: int) -> int:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM user_memberships WHERE user_id = %s", (user_id,))
            row = await cur.fetchone()
            return row[0] if row else 0
