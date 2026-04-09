import asyncio
import random
import pandas as pd
from datetime import datetime
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import requests
import sqlite3
import os

# --- 1. WORKER CONFIG ---
BASE_DIR = r"D:\Dev\kaytep\kaytep"
DB_PATH = os.path.join(BASE_DIR, "system_data.db")
CSV_PATH = os.path.join(BASE_DIR, "DB_kaytep - dataH.csv")
API_TOKEN = "AXIOM_SECURE_TOKEN_V3_2026"

# --- 2. SCRAPING ENGINES (Drill-down Implementation) ---
class AxiomWorker:
    @staticmethod
    async def scrape_google_finance(url: str):
        """เจาะลึก Google Finance ด้วย Playwright [9, 3]"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="networkidle")
                # พิกัดมหาภพ: คลาส P6K39c สำหรับราคา [10]
                element = await page.query_selector("div.P6K39c")
                val_text = await element.inner_text() if element else None
                return float(val_text.replace(",", "")) if val_text else None
            finally:
                await browser.close()

    @staticmethod
    def scrape_sanook_lotto(url: str):
        """เจาะลึกหวยไทยด้วย BeautifulSoup [11, 12]"""
        response = requests.get(url, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")
        # ค้นหาข้อความ "รางวัลที่ 1" [11]
        target = soup.find(text=lambda t: "รางวัลที่ 1" in t)
        if target:
            # ลอจิกสกัดตัวเลข 6 หลัก
            import re
            match = re.search(r'\d{6}', target.parent.text)
            return float(match.group()) if match else None
        return None

    @staticmethod
    async def process_all():
        """ลอจิกควบคุมการมุด 130 URLs ตามเวลาใน CSV [1]"""
        df = pd.read_csv(CSV_PATH)
        now_str = datetime.now().strftime("%H:%M")
        
        for _, row in df.iterrows():
            # ตรวจสอบเวลาอัปเดต [1]
            if row == now_str or True: # True สำหรับการทดสอบมุดทันที
                print(f"🚀 ปฏิบัติการมุดพิกัด: {row['Name_EN']} ({row})")
                
                # เลือก Engine ตามลักษณะ URL
                value = None
                if "google.com/finance" in row:
                    value = await AxiomWorker.scrape_google_finance(row)
                elif "sanook.com" in row:
                    value = AxiomWorker.scrape_sanook_lotto(row)
                
                # บันทึกสู่ฐานข้อมูลมหาภพ
                if value is not None:
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("INSERT INTO analytics (entity_id, value) VALUES (?,?)", (row['Name_EN'], value))
                    conn.commit()
                    conn.close()
                    print(f"✅ บันทึกสำเร็จ: {row['Name_EN']} = {value}")

if __name__ == "__main__":
    print("🤖 Avalon Worker Initiated...")
    asyncio.run(AxiomWorker.process_all())