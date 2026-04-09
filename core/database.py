# avalon_backend/core/database.py
import sqlite3
import logging
from core.config import settings

logger = logging.getLogger("AXIOM_DB")

def get_db_connection():
    """สร้างการเชื่อมต่อพร้อมกำหนดค่าประสิทธิภาพ (WAL Mode)"""
    try:
        conn = sqlite3.connect(str(settings.DB_PATH), check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row
        # WAL mode ช่วยให้สามารถอ่านและเขียนพร้อมกันได้โดยไม่ Lock
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=30000;")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database Connection Fatal Error: {e}")
        raise

def init_db():
    """สร้างตารางและดัชนีทางยุทธศาสตร์ (Strategic Indexes)"""
    conn = None
    try:
        conn = get_db_connection()
        # ตารางหลักสำหรับเก็บผลรางวัลและสถิติ
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT NOT NULL,
                value REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # ดัชนีช่วยเร่งความเร็วการดึงข้อมูล 10 รายการย้อนหลัง (Flow History)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_entity_time 
            ON analytics(entity_id, created_at DESC)
        """)
        conn.commit()
        logger.info("Database Architecture Initialized Successfully.")
    except Exception as e:
        logger.error(f"Database Initialization Failed: {e}")
    finally:
        if conn: 
            conn.close()