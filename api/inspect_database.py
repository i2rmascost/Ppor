import sqlite3
import os
import sys
from datetime import datetime

# THE AXIOM: ดึงพิกัดจากแกนกลางเพื่อให้เป็นมาตรฐานเดียวกัน
try:
    from core.config import settings
    DB_PATH = str(settings.DB_PATH)
except ImportError:
    # กรณีรันแยกส่วน ให้ใช้ Path มาตรฐาน
    DB_PATH = os.path.join("data", "system_data.db")

def connect_db():
    if not os.path.exists(DB_PATH):
        print(f"❌ [CRITICAL] ไม่พบไฟล์ฐานข้อมูลที่พิกัด: {DB_PATH}")
        print("กรุณารัน 'run_server.py' ก่อนเพื่อให้ระบบสร้างฐานข้อมูล")
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def show_detailed_report():
    """รายงานวิเคราะห์ประสิทธิภาพการขุดข้อมูลรายวัน"""
    conn = connect_db()
    if not conn: return
    
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"\n--- [ THE AXIOM: DAILY EXTRACTION REPORT ({today}) ] ---")
    
    try:
        # 1. รายงานสรุปจำนวนรายการที่มีการอัปเดตวันนี้
        query = """
            SELECT entity_id, COUNT(*) as count, MAX(created_at) as last_seen, AVG(value) as avg_val
            FROM analytics 
            WHERE date(created_at, 'localtime') = date('now', 'localtime')
            GROUP BY entity_id
            ORDER BY count DESC
        """
        rows = conn.execute(query).fetchall()
        
        if not rows:
            print("⚠️ วันนี้ยังไม่มีข้อมูลใหม่ถูกบันทึกลงในระบบ")
            print("ตรวจสอบสถานะของ Chronos Scheduler ในหน้าจอเซิร์ฟเวอร์")
        else:
            print(f"{'ENTITY_ID':<30} | {'COUNT':<7} | {'AVG_VALUE':<10} | {'LAST_UPDATE'}")
            print("-" * 85)
            for row in rows:
                print(f"{row['entity_id']:<30} | {row['count']:<7} | {row['avg_val']:<10.2f} | {row['last_seen']}")
            
            total_today = sum(r['count'] for r in rows)
            print(f"\n📊 รวมข้อมูลใหม่วันนี้ทั้งหมด: {total_today} รายการ")

        # 2. แสดง 5 รายการล่าสุดในระบบเพื่อตรวจสอบความสดใหม่
        print("\n--- [ 5 LATEST ENTRIES IN SYSTEM ] ---")
        latest = conn.execute("SELECT * FROM analytics ORDER BY created_at DESC LIMIT 5").fetchall()
        for l in latest:
            print(f"[{l['created_at']}] {l['entity_id']}: {l['value']}")

    except Exception as e:
        print(f"❌ Database Report Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    show_detailed_report()