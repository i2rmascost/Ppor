# --- THE AXIOM: Macrocosm Core v9.1 [Retention & Lifecycle] ---
# วางไว้ที่: D:\Dev\kaytep\avalon_backend\original_system_core_v9.py
# วัตถุประสงค์: บริหารจัดการคิวงานขุดเจาะ สถิติ และวงจรชีวิตทรัพยากรระบบ

import os
import sqlite3
import logging
import csv
import asyncio
import random
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# นำเข้าเครื่องจักรมุดข้อมูล Aegis v9.0+
try:
    from engines.scraper import DataScraper
except ImportError:
    print("CRITICAL: engines/scraper.py missing.")
    os._exit(1)

# --- 1. CONFIGURATION (Strategic Intelligence) ---
class Settings:
    TOKEN: str = "AXIOM_SECURE_TOKEN_V3_2026"
    FOLDER_ID: str = "1jvrFhAk1H-XMrjqFpzlPAFmU0GwDoVdl"
    LIFF_URL: str = "https://i2rmascost.github.io/avalon-hub/"
    
    BASE_DIR: str = r"D:\Dev\kaytep\avalon_backend"
    DB_PATH: str = os.path.join(BASE_DIR, "data", "system_data.db")
    CSV_SOURCE: str = os.path.join(BASE_DIR, "data", "DB_kaytep_dataH.csv")
    
    # ยุทธศาสตร์การเก็บข้อมูล: รักษาสถิติไว้สูงสุด 100 งวดต่อรายการ
    HISTORY_LIMIT: int = 100

settings = Settings()

# --- 2. LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AXIOM_CORE")

# --- 3. DATABASE LAYER (WAL Mode Enabled) ---
def get_db_connection():
    """สร้างการเชื่อมต่อฐานข้อมูลที่รองรับ Concurrency สูง"""
    conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;") 
    return conn

def enforce_retention(entity_id: str):
    """ยุทธศาสตร์ Retention: กำจัดข้อมูลส่วนเกิน 100 งวดทิ้งทันที"""
    try:
        with get_db_connection() as conn:
            conn.execute("""
                DELETE FROM analytics 
                WHERE id NOT IN (
                    SELECT id FROM analytics 
                    WHERE entity_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ) AND entity_id = ?
            """, (entity_id, settings.HISTORY_LIMIT, entity_id))
            conn.commit()
    except Exception as e:
        logger.error(f"🧹 Retention Failure for {entity_id}: {e}")

# --- 4. TASK ORCHESTRATION (The Mission Control) ---
async def execute_mission(eid: str, url: str):
    """ปฏิบัติการขุดเจาะ -> บันทึกสถิติ -> ล้างข้อมูลส่วนเกิน"""
    val = await DataScraper.extract_value(eid, url)
    if val is not None:
        try:
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO analytics (entity_id, value) VALUES (?, ?)", 
                    (eid, val)
                )
                conn.commit()
            
            # บังคับใช้กฎ Retention ทันทีหลังบันทึก
            enforce_retention(eid)
            logger.info(f"✅ Integrated: {eid} = {val} [Retention: {settings.HISTORY_LIMIT}]")
        except Exception as e:
            logger.error(f"❌ DB Integration failed for {eid}: {e}")
    else:
        logger.warning(f"❌ Mission Blunted: {eid} (No valid data extracted)")

async def run_global_extraction_sequence():
    """ภารกิจกวาดล้างข้อมูล 130 รายการทั่วโลกแบบต่อเนื่อง"""
    DataScraper.load_config() # รีโหลดพิกัดล่าสุดจาก YAML
    if not os.path.exists(settings.CSV_SOURCE):
        logger.error("CSV Intelligence Source Missing!")
        return

    logger.info("🚀 [ORCHESTRATOR] Starting Global Strategic Mission v9.1...")
    with open(settings.CSV_SOURCE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            eid, url = row.get('Name_EN'), row.get('URL')
            if eid and url and url.startswith('http'):
                await execute_mission(eid, url)
                # Jitter Delay: เลียนแบบการเข้าถึงแบบสุ่มเพื่อเลี่ยงการถูกแบน
                await asyncio.sleep(random.uniform(0.3, 0.7))
    logger.info("🏁 [ORCHESTRATOR] Global Mission Complete.")

# --- 5. LIFESPAN MANAGEMENT (Resource Control) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """จัดการวงจรชีวิตระบบ: เปิด-ปิด Browser และเริ่มภารกิจขุดเจาะ"""
    # [STARTUP]
    logger.info("📡 System Ignition: Initializing Infrastructure...")
    await DataScraper.get_browser() # อุ่นเครื่องเบราว์เซอร์จำลอง
    
    # จุดระเบิดการขุดรอบแรกทันทีใน Background
    asyncio.create_task(run_global_extraction_sequence())
    
    yield
    
    # [SHUTDOWN]
    logger.info("🔌 System Decommissioning: Releasing Resources...")
    await DataScraper.close_browser() # ปิดฐานทัพเบราว์เซอร์อย่างปลอดภัย

# --- 6. API SYSTEM ---
app = FastAPI(title="Avalon Hub Core v9.1", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/v1/dashboard")
async def dashboard_api(x_token: str = Header(None)):
    """เอนด์พอยต์แสดงผลรางวัลและเลขไหลมหาภพ"""
    if x_token != settings.TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized Access")
    
    conn = get_db_connection()
    lotteries = []
    
    try:
        with open(settings.CSV_SOURCE, mode='r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                eid = row.get('Name_EN')
                name_th = row.get('Name_TH', eid)
                
                # Fetch 10 Latest for Flow (ประวัติเลขไหล)
                rows = conn.execute(
                    "SELECT value FROM analytics WHERE entity_id = ? ORDER BY created_at DESC LIMIT 10", 
                    (eid,)
                ).fetchall()
                
                if rows:
                    vals = [r['value'] for r in rows]
                    # แยก บน-ล่าง
                    v_str = str(vals[0]).replace('.', '')
                    top3 = v_str[-3:] if len(v_str) >= 3 else v_str.zfill(3)
                    bottom2 = v_str[-5:-3] if len(v_str) >= 5 else v_str[:2].zfill(2)
                    
                    # รายการเลขไหล (2 ตัวล่างของแต่ละงวด)
                    flows = []
                    for v in vals:
                        vs = str(v).replace('.', '')
                        flows.append(vs[-5:-3] if len(vs) >= 5 else vs[:2].zfill(2))
                    
                    lotteries.append({
                        "id": eid, "name": name_th, "time": row.get('Time'),
                        "top3": top3, "bottom2": bottom2,
                        "risk": "ST" if len(vals) > 5 else "HI",
                        "flow_today": flows[:3],
                        "flow_history": flows[3:],
                        "categoryId": "cat-normal" # ปรับแต่งหมวดหมู่ได้ตามต้องการ
                    })
                else:
                    lotteries.append({
                        "id": eid, "name": name_th, "time": row.get('Time'),
                        "top3": "***", "bottom2": "**", "risk": "WAIT",
                        "flow_today": [], "flow_history": [], "categoryId": "cat-normal"
                    })
        return {"lotteries": lotteries}
    finally:
        conn.close()

@app.post("/api/v1/force-mine")
async def force_mine(background_tasks: BackgroundTasks, x_token: str = Header(None)):
    """ปุ่มกดฉุกเฉิน: บังคับเริ่มภารกิจขุดเจาะทันที"""
    if x_token != settings.TOKEN:
        raise HTTPException(status_code=403)
    background_tasks.add_task(run_global_extraction_sequence)
    return {"status": "Aegis Overdrive Initiated. Watch Terminal logs."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)