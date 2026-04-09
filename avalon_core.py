import sys
import os
import sqlite3
import logging
import math
import csv
import secrets
import asyncio
import random
import re
from datetime import datetime
from typing import Optional, List, Dict, Any

# ตรวจสอบและนำเข้า Dependencies ชั้นสูง
try:
    from fastapi import FastAPI, HTTPException, Header, Depends, status, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    import httpx
    from bs4 import BeautifulSoup
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
except ImportError:
    print("CRITICAL ERROR: Missing ultimate dependencies.")
    print("Execute: pip install fastapi uvicorn httpx beautifulsoup4 playwright apscheduler")
    print("Then execute: playwright install chromium")
    sys.exit(1)

# --- 1. CONFIGURATION (Environment Driven) ---
class Settings:
    TOKEN: str = os.getenv("APP_TOKEN", "AXIOM_SECURE_TOKEN_V3_2026")
    FOLDER_ID: str = os.getenv("FOLDER_ID", "1jvrFhAk1H-XMrjqFpzlPAFmU0GwDoVdl")
    LIFF_URL: str = os.getenv("LIFF_URL", "https://i2rmascost.github.io/avalon-hub/")
    
    BASE_DIR: str = r"D:\Dev\kaytep\kaytep"
    DB_PATH: str = os.path.join(BASE_DIR, "system_data.db")
    CSV_SOURCE: str = os.path.join(BASE_DIR, "DB_kaytep - dataH.csv")
    
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    TIMEZONE: str = "Asia/Bangkok"

settings = Settings()

if not os.path.exists(settings.BASE_DIR):
    os.makedirs(settings.BASE_DIR, exist_ok=True)

# --- 2. LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AXIOM_OMNIPRESENT")

# --- 3. DATABASE LAYER ---
def get_db_connection():
    conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    return conn

def init_db():
    conn = None
    try:
        conn = get_db_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT NOT NULL,
                value REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_entity_time ON analytics(entity_id, created_at)")
        conn.commit()
    except Exception as e:
        logger.error(f"Database Initialization Failed: {e}")
    finally:
        if conn: conn.close()

init_db()

# --- 4. SECURITY GATE ---
def verify_access(x_token: str = Header(None)):
    if not x_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Token")
    if not secrets.compare_digest(x_token.encode("utf-8"), settings.TOKEN.encode("utf-8")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Token")
    return x_token

# --- 5. RISK & EVOLUTION ENGINE ---
class EvolutionEngine:
    @staticmethod
    def calculate_stats(values: List[float]) -> Dict[str, Any]:
        if len(values) < 3:
            return {
                "mean": None, "z_score": 0.0, 
                "ema": values[-1] if values else 0.0,
                "is_anomaly": False, "risk_level": "INITIALIZING"
            }

        n = len(values)
        mean = sum(values) / n
        std_dev = math.sqrt(sum((x - mean) ** 2 for x in values) / n)
        last_val = values[-1]
        z_score = abs(last_val - mean) / std_dev if std_dev > 0 else 0.0

        alpha = 2 / (n + 1)
        ema = values[0]
        for v in values[1:]:
            ema = alpha * v + (1 - alpha) * ema

        risk_level = "CRITICAL" if z_score > 3.0 else "HIGH" if z_score > 2.0 else "STABLE"

        return {
            "mean": round(mean, 4), "z_score": round(z_score, 4),
            "ema": round(ema, 4), "is_anomaly": z_score > 3.0,
            "risk_level": risk_level
        }

# --- 6. OMNIPRESENT DATA MINER (Stealth & Heuristics) ---
class DataMiner:
    # ฐานข้อมูลกฎการแยกแยะเชิงกลุ่ม (Template Clustering)
    TEMPLATE_MAP = {
        "google_finance": {"type": "css", "selector": "div.YMlKec.fxKbKc"},
        "sanook_lotto": {"type": "css", "selector": "strong#number-first"},
        "visa_network": {"type": "css", "selector": "div.result-number"},
        "magnum_my": {"type": "css", "selector": "div.draw-result"},
    }

    ENTITY_ROUTING = {
        "dji": "google_finance",
        "goverment": "sanook_lotto",
        "hangsengvisaafternoon": "visa_network",
        "hanoivisa": "visa_network",
        "magnum4d": "magnum_my"
    }

    @staticmethod
    def fallback_regex_search(text: str) -> Optional[float]:
        """Oracle Heuristics: ระบบค้นหาเชิงบริบทขั้นสูงสุด"""
        patterns = [
            r'(?i)(?:result|ผลรางวัล|ปิดตลาด|index|value|close).*?(\d{2,6}(?:\.\d{1,2})?)',
            r'(?i)(\d{2,6}(?:\.\d{1,2})?).*?(?:baht|points|ดัชนี)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try: return float(match.group(1))
                except ValueError: continue
        return None

    @staticmethod
    def _parse_html(html_content: str, entity_id: str) -> Optional[float]:
        soup = BeautifulSoup(html_content, 'html.parser')
        template_key = DataMiner.ENTITY_ROUTING.get(entity_id)
        if template_key and template_key in DataMiner.TEMPLATE_MAP:
            rule = DataMiner.TEMPLATE_MAP[template_key]
            target_elem = soup.select_one(rule["selector"])
            if target_elem:
                raw_value = ''.join(c for c in target_elem.text if c.isdigit() or c == '.')
                try: return float(raw_value)
                except ValueError: pass
        
        clean_text = soup.get_text(separator=' ').replace(',', '')
        return DataMiner.fallback_regex_search(clean_text)

    @staticmethod
    async def extract_via_httpx(url: str, entity_id: str) -> Optional[float]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return DataMiner._parse_html(response.text, entity_id)
        except Exception:
            return None

    @staticmethod
    async def extract_via_playwright(url: str, entity_id: str) -> Optional[float]:
        """Aegis Stealth Protocol: ระบบพรางตัวทะลวง JavaScript"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"] # หลบเลี่ยง Anti-Bot
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": random.randint(1024, 1920), "height": random.randint(768, 1080)}
                )
                page = await context.new_page()
                await page.goto(url, wait_until="networkidle", timeout=25000)
                
                # จำลองการเลื่อนเมาส์พรางตัว (Human Jitter)
                await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                html_content = await page.content()
                await browser.close()
                return DataMiner._parse_html(html_content, entity_id)
        except Exception as e:
            logger.warning(f"Stealth Engine failed for {entity_id}: {e}")
            return None

    @staticmethod
    async def target_execution_protocol(entity_id: str, url: str):
        """โพรโทคอลขุดเจาะแบบเจาะจงเป้าหมาย"""
        logger.info(f"[CHRONOS] Scheduled extraction initiated for: {entity_id}")
        val = await DataMiner.extract_via_httpx(url, entity_id)
        
        if val is None:
            logger.info(f"[AEGIS] Engaging Stealth Engine for {entity_id}...")
            val = await DataMiner.extract_via_playwright(url, entity_id)
            
        if val is not None:
            conn = None
            try:
                conn = get_db_connection()
                conn.execute("INSERT INTO analytics (entity_id, value) VALUES (?, ?)", (entity_id, val))
                conn.commit()
                logger.info(f"[SUCCESS] {entity_id} = {val}")
            except Exception as e:
                logger.error(f"DB Error: {e}")
            finally:
                if conn: conn.close()
        else:
            logger.error(f"[FAILED] Omnipresent engines failed to extract data from {entity_id}.")

# --- 7. CHRONOS SCHEDULER (ระบบจัดการวงจรเวลาอัตโนมัติ) ---
scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)

def start_chronos_engine():
    """อ่าน CSV และสร้างตารางเวลา (Cron Jobs) ล่วงหน้าทั้งหมด"""
    if not os.path.exists(settings.CSV_SOURCE):
        logger.error(f"Chronos Error: CSV not found at {settings.CSV_SOURCE}")
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
                    # แปลงเวลา 11:00 เป็น Hour: 11, Minute: 00
                    hour, minute = map(int, time_str.split(':'))
                    scheduler.add_job(
                        DataMiner.target_execution_protocol,
                        CronTrigger(hour=hour, minute=minute, timezone=settings.TIMEZONE),
                        args=[entity_id, url],
                        id=f"job_{entity_id}",
                        replace_existing=True
                    )
                    job_count += 1
                except Exception as e:
                    logger.warning(f"Chronos: Failed to parse time '{time_str}' for {entity_id}. Skipping.")

    scheduler.start()
    logger.info(f"[CHRONOS] Omnipresent Scheduler Active. Tracking {job_count} targets automatically.")

# --- 8. CORE API SYSTEM ---
app = FastAPI(title="The Axiom Core v6.0 (Omnipresent Edition)", version="6.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    start_chronos_engine()

# --- 9. ENDPOINTS ---
@app.get("/api/v1/sync")
async def sync_status(_ = Depends(verify_access)):
    conn = None
    try:
        conn = get_db_connection()
        count = conn.execute("SELECT COUNT(*) FROM analytics").fetchone()[0]
        
        # ตรวจสอบว่าระบบมี Job รันอยู่กี่ตัว
        jobs = [job.id for job in scheduler.get_jobs()]
        return {
            "status": "omnipresent_active",
            "total_records": count,
            "scheduled_targets": len(jobs),
            "folder_target": settings.FOLDER_ID,
            "timestamp": datetime.utcnow()
        }
    finally:
        if conn: conn.close()

@app.get("/analyze/{entity_id}")
async def analyze(entity_id: str, _ = Depends(verify_access)):
    conn = None
    try:
        conn = get_db_connection()
        rows = conn.execute("SELECT value FROM analytics WHERE entity_id = ? ORDER BY created_at ASC", (entity_id,)).fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="Entity ID not found")
        values = [row['value'] for row in rows]
        return {
            "entity_id": entity_id, "data_points": len(values),
            "statistics": EvolutionEngine.calculate_stats(values),
            "liff_url": settings.LIFF_URL, "timestamp": datetime.utcnow()
        }
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    import uvicorn
    logger.info(f"AXIOM Omnipresent Core starting at {settings.BASE_DIR}")
    uvicorn.run(app, host="0.0.0.0", port=8000)