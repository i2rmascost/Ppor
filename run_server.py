# avalon_backend/run_server.py
import uvicorn
import logging
from core.config import settings
from core.database import init_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AXIOM_BOOT")

if __name__ == "__main__":
    logger.info("Initiating THE AXIOM Core Startup Sequence...")
    # ตรวจสอบและสร้างฐานข้อมูลก่อนรันเซิร์ฟเวอร์
    init_db()
    
    # สั่งรัน FastAPI 
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)