# avalon_backend/engines/scheduler.py
import csv
import logging
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from core.config import settings
from core.database import get_db_connection
from engines.scraper import DataScraper

logger = logging.getLogger("AXIOM_CHRONOS")
scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)

async def execute_mining_task(entity_id: str, url: str):
    """โพรโทคอลขุดเจาะเมื่อถึงเวลาที่กำหนด"""
    logger.info(f"[CHRONOS] Scheduled extraction triggered for: {entity_id}")
    
    val = await DataScraper.extract_value(url, entity_id)
    
    if val is not None:
        conn = None
        try:
            conn = get_db_connection()
            conn.execute("INSERT INTO analytics (entity_id, value) VALUES (?, ?)", (entity_id, val))
            conn.commit()
            logger.info(f"[SUCCESS] {entity_id} Data Integrated.")
        except Exception as e:
            logger.error(f"DB Error on {entity_id}: {e}")
        finally:
            if conn: conn.close()
    else:
        logger.warning(f"[FAILED] Could not extract data for {entity_id}. Awaiting manual rule definition.")

def start_chronos_engine():
    """โหลดพิกัดจาก CSV และสร้างตารางเวลาอัตโนมัติ 130 เป้าหมาย"""
    if not settings.CSV_SOURCE.exists():
        logger.error(f"Chronos Error: Master CSV not found at {settings.CSV_SOURCE}")
        return

    job_count = 0
    with open(settings.CSV_SOURCE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entity_id = row.get('Name_EN')
            url = row.get('URL')
            time_str = row.get('Time')
            
            if entity_id and url and time_str and url.startswith('http'):
                try:
                    hour, minute = map(int, time_str.split(':'))
                    scheduler.add_job(
                        execute_mining_task,
                        CronTrigger(hour=hour, minute=minute, timezone=settings.TIMEZONE),
                        args=[entity_id, url],
                        id=f"job_{entity_id}",
                        replace_existing=True
                    )
                    job_count += 1
                except Exception as e:
                    logger.warning(f"Chronos: Skipping {entity_id} due to invalid time format '{time_str}'.")

    scheduler.start()
    logger.info(f"[CHRONOS] Omnipresent Scheduler Active. Tracking {job_count} targets automatically.")