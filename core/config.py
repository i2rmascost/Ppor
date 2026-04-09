# avalon_backend/core/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# ค้นหาไฟล์ .env จาก Root Directory
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    # ความลับและ API
    TOKEN: str = os.getenv("APP_TOKEN", "AXIOM_SECURE_TOKEN_V3_2026")
    FOLDER_ID: str = os.getenv("FOLDER_ID", "1jvrFhAk1H-XMrjqFpzlPAFmU0GwDoVdl")
    LIFF_URL: str = os.getenv("LIFF_URL", "https://i2rmascost.github.io/avalon-hub/")
    
    # สภาพแวดล้อม
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Bangkok")
    
    # พิกัดไฟล์และฐานข้อมูล (ชี้ไปที่โฟลเดอร์ data/)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = DATA_DIR / "system_data.db"
    CSV_SOURCE: Path = DATA_DIR / "DB_kaytep_dataH.csv"

# สร้างโฟลเดอร์ data อัตโนมัติหากยังไม่มี
settings = Settings()
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)