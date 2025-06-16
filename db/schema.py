from .connection import get_pool

async def create_all_tables():
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    full_name VARCHAR(255),
                    started_at DATETIME
                )
            """)
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id BIGINT PRIMARY KEY,
                    title VARCHAR(256),
                    type VARCHAR(50),
                    added_at DATETIME
                )
            """)
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS user_memberships (
                    user_id BIGINT,
                    chat_id BIGINT,
                    username VARCHAR(255),
                    full_name VARCHAR(255),
                    joined_at DATETIME,
                    PRIMARY KEY (user_id, chat_id)
                )
            """)
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS invite_links (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,
                    chat_id BIGINT,
                    invite_link VARCHAR(512),
                    expires_at DATETIME
                )
            """)
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS user_algorithm_progress (
                    user_id BIGINT PRIMARY KEY,
                    current_step TINYINT,
                    basic_completed TINYINT,
                    advanced_completed TINYINT,
                    updated_at DATETIME
                )
            """)
