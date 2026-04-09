# avalon_backend/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as api_router
from engines.scheduler import start_chronos_engine

app = FastAPI(title="The Axiom Macrocosm Backend", version="7.0.0")

# เปิดทางให้ Frontend ทุกโดเมนเข้ามาดึงข้อมูลได้ (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# ผูก Route ต่างๆ เข้ากับแกนหลัก
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def on_startup():
    """เมื่อเปิดเซิร์ฟเวอร์ ให้ปลุกนาฬิกา Chronos ขึ้นมาทำงานทันที"""
    start_chronos_engine()

@app.get("/")
def health_check():
    return {"status": "The Axiom Backend is Online and Operational."}