# avalon_backend/core/security.py
import secrets
import logging
from fastapi import Header, HTTPException, status
from core.config import settings

logger = logging.getLogger("AXIOM_SECURITY")

def verify_access(x_token: str = Header(None, alias="x-token")):
    """THE AXIOM: ตรวจสอบความถูกต้องของ Token ก่อนอนุญาตให้เข้าถึงฐานข้อมูล"""
    if not x_token:
        logger.warning("Access Denied: Missing Header Token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing Authorization Token"
        )
    
    # ใช้ compare_digest ป้องกัน Timing Attacks
    if not secrets.compare_digest(x_token.encode("utf-8"), settings.TOKEN.encode("utf-8")):
        logger.warning("Access Denied: Invalid Token Signature")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid Token Signature"
        )
    
    return x_token