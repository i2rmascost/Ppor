# --- THE AXIOM: Aegis Scraper v9.0 [Forensic & Singleton Edition] ---
# วางไว้ที่: D:\Dev\kaytep\avalon_backend\engines\scraper.py
# วัตถุประสงค์: สกัดข้อมูลความแม่นยำสูงพร้อมระบบเก็บหลักฐานความล้มเหลว

import os
import re
import yaml
import httpx
import sqlite3
import asyncio
import logging
import random
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from typing import Optional, Dict, Any

# ระบบบันทึก Log ปฏิบัติการ
logger = logging.getLogger("AXIOM_SCRAPER")

class DataScraper:
    # --- ยุทธศาสตร์พิกัด (Paths) ---
    BASE_DIR = Path(r"D:\Dev\kaytep\avalon_backend")
    CONFIG_PATH = BASE_DIR / "data" / "selector_overrides.yaml"
    DB_PATH = BASE_DIR / "data" / "system_data.db"
    ARTIFACT_DIR = BASE_DIR / "debug_artifacts"
    
    # บัญชีดำเลขขยะ (CSS/Font Artifacts)
    BLACKLIST = [60000.0, 10000.0, 0.0, 200.0, 404.0]
    
    # --- INTERNAL STATE ---
    _config: Dict[str, Any] = {} # แก้ไข Variable Mismatch Bug
    _browser = None
    _playwright = None

    @classmethod
    def load_config(cls):
        """โหลดคลังพิกัดยุทธศาสตร์จาก YAML"""
        if cls.CONFIG_PATH.exists():
            try:
                with open(cls.CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    cls._config = data.get("overrides", {})
                logger.info(f"🛡️ Intelligence Registry Synchronized: {len(cls._config)} targets.")
            except Exception as e:
                logger.error(f"❌ YAML Integrity Error: {e}")
        else:
            logger.warning(f"⚠️ Config not found at {cls.CONFIG_PATH}. Using generic fallback.")
        
        # เตรียมโฟลเดอร์สำหรับพยานหลักฐาน
        cls.ARTIFACT_DIR.mkdir(exist_ok=True, parents=True)

    @classmethod
    async def get_browser(cls):
        """Singleton Browser Instance: รักษาทรัพยากรเครื่องมหาภพ"""
        if not cls._browser:
            cls._playwright = await async_playwright().start()
            cls._browser = await cls._playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            logger.info("📡 Global Stealth Browser Initiated.")
        return cls._browser

    @classmethod
    async def close_browser(cls):
        """ปิดฐานทัพเบราว์เซอร์เมื่อจบภารกิจ"""
        if cls._browser:
            await cls._browser.close()
            await cls._playwright.stop()
            cls._browser = None
            logger.info("🔌 Stealth Browser Decommissioned.")

    @staticmethod
    async def save_forensic_artifacts(entity_id: str, page=None, html: str = None):
        """Forensic Artifacts: บันทึกหลักฐานกรณีขุดเจาะบอด"""
        ts = datetime.now().strftime("%H%M%S")
        prefix = f"{entity_id}_{ts}"
        try:
            if html:
                (DataScraper.ARTIFACT_DIR / f"{prefix}.html").write_text(html, encoding="utf-8")
            if page:
                await page.screenshot(path=str(DataScraper.ARTIFACT_DIR / f"{prefix}.png"), full_page=True)
            logger.info(f"📸 Forensic Artifacts Captured: {prefix}")
        except Exception as e:
            logger.debug(f"Failed to capture artifacts: {e}")

    @staticmethod
    async def fetch_stealth(url: str, entity_id: str, selector: str = None) -> Optional[str]:
        """ยุทธวิธีพรางตัว: ทะลวง 403 Forbidden และรัน JavaScript"""
        browser = await DataScraper.get_browser()
        # สุ่มสภาพแวดล้อมเพื่อเลี่ยงการตรวจจับ
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="th-TH"
        )
        page = await context.new_page()
        content = None
        
        try:
            # เพิ่ม Human-like Jitter
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await page.goto(url, wait_until="domcontentloaded", timeout=50000)
            
            # รอพิกัดเฉพาะ (ถ้ามีระบุใน YAML)
            if selector:
                try:
                    await page.wait_for_selector(selector, timeout=12000)
                except:
                    logger.debug(f"Selector {selector} timeout for {entity_id}, parsing raw content.")
            
            content = await page.content()
        except Exception as e:
            # จุดพลุหลักฐานความล้มเหลว
            await DataScraper.save_forensic_artifacts(entity_id, page=page, html=await page.content() if page else None)
            logger.error(f"🛡️ Stealth Mission Failed for {entity_id}")
        finally:
            await context.close()
            
        return content

    @staticmethod
    async def extract_value(entity_id: str, url: str) -> Optional[float]:
        """แกนบัญชาการขุด: สลับเครื่องมือตามพิกัดเป้าหมาย"""
        conf = DataScraper._config.get(entity_id, {})
        css = conf.get("css")
        
        # 1. ภารกิจความเร็วสูง (HTTPX): สำหรับเว็บทั่วไป
        if conf.get("engine") != "playwright":
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                    resp = await client.get(url, headers=headers)
                    if resp.status_code == 200:
                        val = DataScraper.parse_engine(resp.text, css, entity_id)
                        if val: return val
                    elif resp.status_code == 403:
                        logger.warning(f"🔄 403 Forbidden -> Escalating {entity_id} to Stealth Mode...")
            except:
                pass

        # 2. ภารกิจพรางตัว (Stealth Playwright): สำหรับเว็บที่มีเกราะ
        html = await DataScraper.fetch_stealth(url, entity_id, css)
        if html:
            return DataScraper.parse_engine(html, css, entity_id)
        
        return None

    @staticmethod
    def parse_engine(html: str, css: str, entity_id: str) -> Optional[float]:
        """ตัวสกัดตัวเลข (Parser Engine)"""
        soup = BeautifulSoup(html, 'html.parser')
        raw_val = None
        
        # ค้นหาตามพิกัด CSS เฉพาะตัว
        if css:
            elem = soup.select_one(css)
            raw_val = elem.get_text() if elem else None
        
        # หากพิกัด CSS บอด ให้กวาดล้างด้วย Regex
        if not raw_val:
            # ตัดเลขขยะและค้นหาเลขรางวัล (5-6 หลัก) หรือเลขดัชนี (ทศนิยม)
            clean_text = soup.get_text(separator=' ').replace(',', '').replace(' ', '')
            match = re.search(r'\b\d{5,6}\b', clean_text) or re.search(r'\d{3,6}\.\d{2}', clean_text)
            raw_val = match.group(0) if match else None

        return DataScraper.validate_and_clean(raw_val, entity_id)

    @staticmethod
    def validate_and_clean(text: Any, entity_id: str) -> Optional[float]:
        """ตรวจสอบความถูกต้องและดีดเลขขยะทิ้ง"""
        if text is None: return None
        # เก็บเพียงตัวเลขและจุด
        clean_str = ''.join(c for c in str(text) if c.isdigit() or c == '.')
        try:
            val = float(clean_str)
            # ปิดจุดอ่อน: ดีด Blacklist และค่าที่เป็นศูนย์ทิ้ง
            if val in DataScraper.BLACKLIST or val <= 0:
                logger.warning(f"🚫 False Positive Filtered for {entity_id}: {val}")
                return None
            return val
        except:
            return None