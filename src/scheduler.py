# src/scheduler.py

import logging
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .database import AsyncSessionLocal
from . import crud

async def scheduled_cleanup():
    async with AsyncSessionLocal() as session:
        deleted = await crud.cleanup_orphan_users(session)
        if deleted:
            logging.info(f"[CLEANUP] Deleted orphan users: {deleted}")
        else:
            logging.info("[CLEANUP] No orphan users found.")

async def setup_scheduler():
    # считываем cron-строку из таблицы
    async with AsyncSessionLocal() as session:
        cron_str = await crud.get_cleanup_cron(session)

    scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Moscow"))
    trigger = CronTrigger.from_crontab(cron_str, timezone=pytz.timezone("Europe/Moscow"))
    scheduler.add_job(scheduled_cleanup, trigger)
    scheduler.start()
    logging.info(f"[CLEANUP] Orphan cleanup scheduled: {cron_str}")
