# avalon_backend/api/routes.py
import csv
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from core.security import verify_access
from core.database import get_db_connection
from core.config import settings
from engines.heuristics import HeuristicEngine
from engines.scraper import DataScraper

router = APIRouter()
logger = logging.getLogger("AXIOM_API")

@router.get("/dashboard")
async def get_dashboard_feed(_ = Depends(verify_access)):
    """API ส่งข้อมูล 130 รายการให้หน้าบ้าน (Frontend)"""
    conn = None
    lotteries = []
    
    try:
        conn = get_db_connection()
        
        if not settings.CSV_SOURCE.exists():
            raise HTTPException(status_code=500, detail="Master CSV not found")
            
        with open(settings.CSV_SOURCE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                entity_id = row.get('Name_EN')
                name_th = row.get('Name_TH', entity_id)
                time_str = row.get('Time', '00:00')
                
                # Heuristics จำแนกหมวดหมู่
                th_lower = name_th.lower()
                if "vip" in th_lower: cat_id = "cat-vip"
                elif "พิเศษ" in th_lower or "สตาร์" in th_lower: cat_id = "cat-special"
                elif "visa" in th_lower or "วีซ่า" in th_lower: cat_id = "cat-visa"
                elif any(k in th_lower for k in ["ลาว", "สาละวัน", "หลวงพระบาง", "เวียงจันทน์", "ประชาชน"]): cat_id = "cat-laos"
                elif any(k in th_lower for k in ["ฮานอย", "เวียดนาม", "อาเซียน"]): cat_id = "cat-hanoi"
                elif any(k in th_lower for k in ["รัฐบาล", "ออมสิน", "ธ.ก.ส", "มาเลย์", "แม่โขง", "พม่า"]): cat_id = "cat-others"
                else: cat_id = "cat-normal"

                # ดึงข้อมูล 10 ล่าสุดจาก DB
                rows_db = conn.execute(
                    "SELECT value FROM analytics WHERE entity_id = ? ORDER BY created_at DESC LIMIT 10", 
                    (entity_id,)
                ).fetchall()
                
                if rows_db:
                    values = [r['value'] for r in rows_db]
                    values.reverse()
                    
                    latest_val = values[-1]
                    stats = HeuristicEngine.calculate_stats(values)
                    top3, bottom2 = HeuristicEngine.extract_lotto_format(latest_val)
                    
                    flow_raw = [HeuristicEngine.extract_lotto_format(v)[1] for v in values]
                    
                    lotteries.append({
                        "id": entity_id,
                        "categoryId": cat_id,
                        "time": time_str,
                        "name": name_th,
                        "top3": top3,
                        "bottom2": bottom2,
                        "risk": stats['risk_level'],
                        "flow_today": flow_raw[-3:] if len(flow_raw) >= 3 else flow_raw,
                        "flow_history": flow_raw[:-3] if len(flow_raw) > 3 else []
                    })
                else:
                    lotteries.append({
                        "id": entity_id,
                        "categoryId": cat_id,
                        "time": time_str,
                        "name": name_th,
                        "top3": "***",
                        "bottom2": "**",
                        "risk": "WAIT",
                        "flow_today": [],
                        "flow_history": []
                    })
                    
        return {"lotteries": lotteries}
        
    finally:
        if conn:
            conn.close()


# =======================================================
# THE AXIOM: ฟีเจอร์ใหม่ สวิตช์บังคับขุดข้อมูลทันที (Force Mine)
# =======================================================
async def execute_force_mining():
    """ฟังก์ชันวิ่งทะลวงดึงข้อมูลจากทุก URL ที่มีใน TARGET_DIRECTORY ทันที"""
    logger.info("⚡ [FORCE MINE] Initiating manual override extraction...")
    success_count = 0
    conn = None
    try:
        conn = get_db_connection()
        # วิ่งลูปดึงข้อมูลเฉพาะรายการที่มี URL ใน scraper.py
        for entity_id, url in DataScraper.TARGET_DIRECTORY.items():
            val = await DataScraper.extract_value(entity_id)
            if val is not None:
                conn.execute("INSERT INTO analytics (entity_id, value) VALUES (?, ?)", (entity_id, val))
                success_count += 1
        conn.commit()
        logger.info(f"⚡ [FORCE MINE COMPLETE] Successfully extracted {success_count} targets.")
    except Exception as e:
        logger.error(f"Force Mine Error: {e}")
    finally:
        if conn: conn.close()

@router.post("/force-mine")
async def trigger_force_mine(background_tasks: BackgroundTasks, _ = Depends(verify_access)):
    """API รับคำสั่งจากหน้าบ้าน เพื่อสั่งรันการขุดเจาะเป็น Background Process"""
    background_tasks.add_task(execute_force_mining)
    return {"status": "Force mining protocol initiated. Check terminal for live logs."}