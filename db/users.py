from .connection import get_pool

async def add_user(user_id: int, username: str | None, full_name: str | None) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "REPLACE INTO users (user_id, username, full_name, started_at) VALUES (%s, %s, %s, NOW())",
                (user_id, username, full_name)
            )

async def delete_user(user_id: int) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))

async def get_all_users() -> list[int]:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT user_id FROM users")
            rows = await cur.fetchall()
            return [row[0] for row in rows]

async def cleanup_inactive_users() -> None:
    from .memberships import get_user_membership_count
    users = await get_all_users()
    for user_id in users:
        count = await get_user_membership_count(user_id)
        if count == 0:
            await delete_user(user_id)
