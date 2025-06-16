from .connection import get_pool

async def get_user_step(user_id: int) -> int:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT current_step FROM user_algorithm_progress WHERE user_id = %s", (user_id,))
            row = await cur.fetchone()
            return row[0] if row else 0

async def set_user_step(user_id: int, step: int) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "REPLACE INTO user_algorithm_progress (user_id, current_step, updated_at) VALUES (%s, %s, NOW())",
                (user_id, step)
            )

async def get_basic_completed(user_id: int) -> bool:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT basic_completed FROM user_algorithm_progress WHERE user_id = %s", (user_id,))
            row = await cur.fetchone()
            return bool(row[0]) if row else False

async def set_basic_completed(user_id: int, completed: bool) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE user_algorithm_progress SET basic_completed = %s, updated_at = NOW() WHERE user_id = %s",
                (int(completed), user_id)
            )

async def get_advanced_completed(user_id: int) -> bool:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT advanced_completed FROM user_algorithm_progress WHERE user_id = %s", (user_id,))
            row = await cur.fetchone()
            return bool(row[0]) if row else False

async def set_advanced_completed(user_id: int, completed: bool) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE user_algorithm_progress SET advanced_completed = %s, updated_at = NOW() WHERE user_id = %s",
                (int(completed), user_id)
            )

async def clear_user_data(user_id: int) -> None:
    pool = get_pool()
    async with pool.acquire() as conn):
        async with conn.cursor() as cur):
            await cur.execute("DELETE FROM user_algorithm_progress WHERE user_id = %s", (user_id,))
            await cur.execute("DELETE FROM user_memberships WHERE user_id = %s", (user_id,))
