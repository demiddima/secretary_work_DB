from .connection import get_pool

async def save_invite_link(user_id: int, chat_id: int, invite_link: str, expires_at) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO invite_links (user_id, chat_id, invite_link, expires_at) VALUES (%s, %s, %s, %s)",
                (user_id, chat_id, invite_link, expires_at)
            )

async def get_valid_invite_links(user_id: int):
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT chat_id, invite_link FROM invite_links WHERE user_id = %s AND (expires_at IS NULL OR expires_at > NOW())",
                (user_id,)
            )
            return await cur.fetchall()

async def delete_invite_links(user_id: int) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM invite_links WHERE user_id = %s", (user_id,))
