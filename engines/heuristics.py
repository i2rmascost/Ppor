# avalon_backend/engines/heuristics.py
import math
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("AXIOM_HEURISTICS")

class HeuristicEngine:
    @staticmethod
    def calculate_stats(values: List[float]) -> Dict[str, Any]:
        """วิเคราะห์ความเสี่ยงและแนวโน้มจากชุดตัวเลขย้อนหลัง"""
        if len(values) < 3:
            return {"mean": None, "z_score": 0.0, "risk_level": "WAIT"}

        n = len(values)
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        std_dev = math.sqrt(variance)

        last_val = values[-1]
        z_score = abs(last_val - mean) / std_dev if std_dev > 0 else 0.0

        risk_level = "CR" if z_score > 2.5 else "HI" if z_score > 1.5 else "ST"

        return {
            "mean": round(mean, 4), 
            "z_score": round(z_score, 4),
            "risk_level": risk_level
        }

    @staticmethod
    def extract_lotto_format(raw_value: float) -> Tuple[str, str]:
        """
        จำลองการแปลงค่าทศนิยม/ดัชนี ให้เป็นฟอร์แมตหวย (3 ตัวบน, 2 ตัวล่าง)
        *ในสถานการณ์จริง คุณอาจต้องเขียน Regex สกัดจากหน้าเว็บของแต่ละที่*
        """
        val_str = str(raw_value).replace('.', '')
        # สกัด 3 ตัวท้ายเป็น 'บน'
        top3 = val_str[-3:] if len(val_str) >= 3 else val_str.zfill(3)
        # สกัด 2 ตัวก่อนหน้าเป็น 'ล่าง' (หรือใช้ตัวแรกๆ ถ้าสั้นไป)
        bottom2 = val_str[-5:-3] if len(val_str) >= 5 else val_str[:2].zfill(2)
        
        return top3, bottom2